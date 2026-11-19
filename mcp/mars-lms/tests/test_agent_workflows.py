import asyncio
from contextlib import contextmanager
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
import unittest

import httpx
from mcp import Client, StdioServerParameters

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import agent_workflows as workflow
from lms_client import LMSClient

STUDENT = 'a' * 24
GROUP = 'b' * 24
OTHER = 'c' * 24
START, END = '2025-01-01', '2025-01-31'

def backend_data(path):
    if path == '/students':
        return {'success': True, 'students': [{'_id': STUDENT, 'fullname': 'Fixture',
                 'phone': 'secret-not-returned', 'group': {'_id': GROUP}}]}
    if path == f'/attendance/group/{GROUP}':
        return {'success': True, 'attendance': [{'_id': 'lesson', 'date': '2025-01-10',
                 'records': [{'student': {'_id': STUDENT, 'phone': 'secret'}, 'present': False,
                              'confirmation': 'not_needed'}]}]}
    if path == f'/homework/group/{GROUP}':
        return {'success': True, 'homework': [{'_id': 'work', 'title': 'Fractions', 'topic': 'Math',
                 'dueDate': '2025-01-15', 'maxScore': 10,
                 'submissions': [{'student': STUDENT, 'grade': 5, 'submittedAt': '2025-01-14'}]}]}
    if path.startswith('/api/branch/curriculum-topic-analytics'):
        return {'success': True, 'analytics': {'summary': {}, 'topics': [], 'recommendations': []}}
    return None

@contextmanager
def agent_backend():
    calls = []
    class Handler(BaseHTTPRequestHandler):
        def reply(self, code, body):
            payload = json.dumps(body).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        def do_POST(self):
            calls.append(('POST', self.path))
            body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))))
            valid = self.path == '/api/auth/login' and body.get('phone') == 'fixture' and body.get('password') == 'fixture'
            self.reply(200 if valid else 401, {'success': valid, 'token': 'fixture-token'} if valid else {'success': False})
        def do_GET(self):
            calls.append(('GET', self.path))
            payload = backend_data(self.path)
            if self.headers.get('Authorization') != 'Bearer fixture-token':
                self.reply(401, {'success': False})
            else:
                self.reply(200 if payload else 404, payload or {'success': False})
        def log_message(self, *_):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}', calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)

class AnalysisTests(unittest.TestCase):
    def test_missing_evidence_is_unknown_not_perfect_or_zero(self):
        reply = workflow.analyze_progress(STUDENT, GROUP, START, END, [], [])
        self.assertTrue(reply['success'])
        self.assertIsNone(reply['data']['attendance']['rate_percent'])
        self.assertIsNone(reply['data']['homework']['average_percent'])
        self.assertEqual(reply['data']['signals'], [])
        self.assertEqual(reply['data']['criteria_status'], 'unconfirmed_example')

    def test_scores_normalize_per_assignment_and_ignore_unknowns(self):
        homework = [{'id': 'one', 'due_date': '2025-01-10', 'max_score': 10,
                     'submissions': [{'student_id': STUDENT, 'grade': 5}]},
                    {'id': 'two', 'due_date': '2025-01-11', 'max_score': 20,
                     'submissions': [{'student_id': STUDENT, 'grade': 20}]},
                    {'id': 'unknown', 'due_date': '2025-01-12', 'max_score': 20,
                     'submissions': [{'student_id': STUDENT, 'grade': None}]}]
        data = workflow.analyze_progress(STUDENT, GROUP, START, END, [], homework)['data']
        self.assertEqual(data['homework']['average_percent'], 75)
        self.assertEqual(data['homework']['graded_count'], 2)

    def test_record_for_other_student_is_unknown_and_minimum_sample_applies(self):
        attendance = [{'id': 'one', 'date': '2025-01-10',
                       'records': [{'student_id': OTHER, 'present': True}]},
                      {'id': 'two', 'date': '2025-01-11',
                       'records': [{'student_id': STUDENT, 'present': False, 'confirmation': 'not_needed'}]}]
        data = workflow.analyze_progress(STUDENT, GROUP, START, END, attendance, [])['data']
        self.assertEqual(data['attendance']['unknown_records'], 1)
        self.assertEqual(data['attendance']['rate_percent'], 0)
        self.assertEqual(data['signals'], [])

    def test_pending_false_records_are_unknown_without_low_attendance_signal(self):
        rows = [{'id': str(i), 'date': f'2025-01-{i+10:02d}',
                 'records': [{'student_id': STUDENT, 'present': False, 'confirmation': 'pending'}]}
                for i in range(3)]
        data = workflow.analyze_progress(STUDENT, GROUP, START, END, rows, [])['data']
        self.assertEqual(data['attendance']['unknown_records'], 3)
        self.assertEqual(data['attendance']['observed_lessons'], 0)
        self.assertIsNone(data['attendance']['rate_percent'])
        self.assertEqual(data['signals'], [])

    def test_confirmation_states_and_inconsistent_or_missing_states(self):
        values = [('confirmed', True), ('approved', True), ('not_needed', False),
                  ('rejected', False), ('pending', True), ('disputed', False),
                  ('confirmed', False), ('rejected', True), (None, True)]
        rows = [{'id': str(i), 'date': f'2025-01-{i+10:02d}',
                 'records': [{'student_id': STUDENT, 'present': present, 'confirmation': state}]}
                for i, (state, present) in enumerate(values)]
        data = workflow.analyze_progress(STUDENT, GROUP, START, END, rows, [])['data']
        self.assertEqual(data['attendance']['observed_lessons'], 4)
        self.assertEqual(data['attendance']['unknown_records'], 5)
        self.assertEqual(data['attendance']['rate_percent'], 50)

    def test_attendance_prefers_backend_tashkent_day(self):
        rows = [{'id': 'boundary', 'date': '2024-12-31T20:00:00.000Z', 'day': '2025-01-01',
                 'records': [{'student_id': STUDENT, 'present': True, 'confirmation': 'confirmed'}]}]
        data = workflow.analyze_progress(STUDENT, GROUP, START, END, rows, [])['data']
        self.assertEqual(data['attendance']['present'], 1)

    def test_period_and_criteria_reject_invalid_or_future(self):
        for start, end, criteria in [(END, START, {}), (START, 'invalid', {}),
                                     (START, (date.today()+timedelta(days=1)).isoformat(), {}),
                                     (START, END, {'grade_min_percent': 101}),
                                     (START, END, {'missing_homework_min': 0}),
                                     (START, END, {'grade_min_percent': float('nan')}),
                                     (START, END, {'typo': 5})]:
            self.assertFalse(workflow.analyze_progress(STUDENT, GROUP, start, end, [], [], criteria)['success'])

    def test_topic_evidence_and_thresholds_stay_provisional(self):
        homework = [{'id': 'one', 'title': 'Fractions', 'topic': 'Math', 'due_date': '2025-01-10',
                     'max_score': 10, 'submissions': [{'student_id': STUDENT, 'grade': 2}]}]
        data = workflow.analyze_progress(STUDENT, GROUP, START, END, [], homework)['data']
        self.assertEqual(data['signals'][0]['key'], 'low_graded_homework')
        self.assertEqual(data['homework']['items'][0]['topic'], 'Math')
        self.assertEqual(data['assessment'], 'provisional')

    def test_triage_categories_ambiguity_and_no_delivery(self):
        texts = ["To‘lovni tekshiring", 'Dars jadvali kerak', 'Uy vazifani tushunmadim',
                 'Parol ishlamayapti', 'Salom', 'To‘lov va dars jadvali']
        rows = [{'id': str(i), 'text': text} for i, text in enumerate(texts)]
        result = workflow.reception_triage(rows)['data']
        self.assertEqual([row['category'] for row in result['items']],
                         ['payment', 'schedule', 'education', 'technical', 'other', 'other'])
        self.assertEqual(result['needs_clarification'], ['4', '5'])
        self.assertTrue(all(row['sent'] is False for row in result['items']))
        self.assertEqual([row['request_id'] for row in result['items']], [row['id'] for row in rows])

    def test_missing_inbox_explicit_and_input_validation(self):
        reply = workflow.incoming_requests()
        self.assertFalse(reply['success'])
        self.assertEqual((reply['status'], reply['source']), (501, 'capability'))
        self.assertFalse(workflow.incoming_requests([{'id': '1', 'text': 'a'}, {'id': '1', 'text': 'b'}])['success'])
        self.assertFalse(workflow.incoming_requests([{'id': '1', 'text': ''}])['success'])

class ScopeTests(unittest.IsolatedAsyncioTestCase):
    async def test_student_outside_roster_makes_no_group_requests(self):
        calls = []
        def respond(request):
            calls.append(request.url.path)
            return httpx.Response(200, json=backend_data('/students'))
        api = LMSClient(transport=httpx.MockTransport(respond))
        api.token = 'fixture'
        reply = await workflow.student_progress(api, OTHER, START, END)
        self.assertEqual(reply['status'], 404)
        self.assertEqual(calls, ['/students'])

    async def test_backend_denial_is_not_transformed_into_missing_grades(self):
        def respond(request):
            return httpx.Response(200, json=backend_data('/students')) if request.url.path == '/students' else httpx.Response(403, json={'success': False})
        api = LMSClient(transport=httpx.MockTransport(respond))
        api.token = 'fixture'
        reply = await workflow.student_progress(api, STUDENT, START, END)
        self.assertFalse(reply['success'])
        self.assertEqual(reply['status'], 403)

    async def test_real_stdio_login_roster_progress_curriculum_and_reception(self):
        with agent_backend() as (url, calls):
            params = StdioServerParameters(command=sys.executable, args=[str(ROOT / 'agents_server.py')],
                                           env={'MARS_API_URL': url})
            async with Client(params) as client:
                tools = {tool.name for tool in (await client.list_tools()).tools}
                self.assertTrue({'login', 'students', 'student_progress', 'attendance', 'homework',
                                 'curriculum', 'incoming_requests', 'reception_triage'} <= tools)
                denied = await client.call_tool('students', {})
                self.assertTrue(denied.is_error)
                self.assertEqual(calls, [])
                logged = await client.call_tool('login', {'phone': 'fixture', 'password': 'fixture'})
                self.assertFalse(logged.is_error)
                self.assertNotIn('token', logged.structured_content)
                roster = (await client.call_tool('students', {})).structured_content
                self.assertNotIn('phone', json.dumps(roster))
                progress = await client.call_tool('student_progress', {'student_id': STUDENT, 'period_start': START, 'period_end': END})
                self.assertFalse(progress.is_error)
                self.assertEqual(progress.structured_content['data']['homework']['average_percent'], 50)
                curriculum = await client.call_tool('curriculum', {})
                self.assertFalse(curriculum.is_error)
                missing = await client.call_tool('incoming_requests', {})
                self.assertTrue(missing.is_error)
                self.assertEqual(missing.structured_content['status'], 501)
                manual = [{'id': 'r1', 'text': 'To‘lov bo‘yicha savol'}]
                ingested = await client.call_tool('incoming_requests', {'requests': manual})
                self.assertFalse(ingested.is_error)
                routed = await client.call_tool('reception_triage', {'requests': manual})
                self.assertFalse(routed.is_error)
                self.assertFalse(routed.structured_content['data']['items'][0]['sent'])
            self.assertTrue(all(method == 'GET' or path == '/api/auth/login' for method, path in calls))

if __name__ == '__main__':
    unittest.main()
