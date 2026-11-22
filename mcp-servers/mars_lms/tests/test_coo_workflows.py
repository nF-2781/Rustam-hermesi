import asyncio
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
import unittest

import httpx
from mcp import StdioServerParameters

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import coo_workflows as coo
from scoped_client import LMSClient
from smoke import connected_client

BRANCH, OTHER, GROUP, GROUP2, STUDENT, ROOM, MENTOR = [letter*24 for letter in 'abcdef0']


def api_for(respond):
    api = LMSClient('https://fixture.local', transport=httpx.MockTransport(respond))
    api.token = 'fixture'
    return api


def me():
    return {'success': True, 'branch': {'_id': BRANCH, 'name': 'Fixture branch'},
            'admin': {'phone': 'private-not-returned'}}


class EvidenceTests(unittest.TestCase):
    def test_missing_intermediate_student_mark_interrupts_absence_streak(self):
        rows = [{'_id':str(day), 'group':GROUP, 'date':f'2025-01-0{day}T10:00:00Z',
                 'records':[] if day == 2 else [{'student':STUDENT,'present':False,'confirmation':'not_needed'}]}
                for day in [3,2,1]]
        row = coo.attendance_report(rows,date(2025,1,1),date(2025,1,3),2)['students'][0]
        self.assertEqual(row['latest_confirmed_absence_streak'],1)
        self.assertEqual(row['unknown'],1)
        self.assertFalse(row['needs_review'])

    def test_missing_latest_mark_does_not_report_a_current_absence_streak(self):
        rows = [{'_id':str(day), 'group':GROUP, 'date':f'2025-01-0{day}T10:00:00Z',
                 'records':[] if day == 3 else [{'student':STUDENT,'present':False,'confirmation':'not_needed'}]}
                for day in [3,2,1]]
        row = coo.attendance_report(rows,date(2025,1,1),date(2025,1,3),2)['students'][0]
        self.assertEqual(row['latest_confirmed_absence_streak'],0)
        self.assertEqual(row['unknown'],1)
        self.assertFalse(row['needs_review'])

    def test_sla_utc_threshold_missing_naive_and_future_timestamps(self):
        now = datetime(2026, 1, 2, tzinfo=timezone.utc)
        rows = [{'_id': str(i), 'status': 'pending', 'createdAt': value,
                 'phone': 'private', 'reason': 'private'} for i, value in enumerate([
            '2026-01-01T00:00:00Z', '2025-12-31T23:59:00Z', None,
            '2026-01-01T10:00:00', '2027-01-01T00:00:00Z'])]
        report = coo.sla_report(rows, 24, now)
        states = {row['request_id']: row['sla_state'] for row in report['requests']}
        self.assertEqual(states, {'0':'within_threshold', '1':'threshold_exceeded',
                                 '2':'unknown', '3':'unknown', '4':'unknown'})
        self.assertEqual(report['unknown_age_count'], 3)
        self.assertNotIn('private', json.dumps(report))
        self.assertTrue(all(not row['sent'] and not row['assigned'] for row in report['requests']))

    def test_confirmed_attendance_unknown_breaks_streak_and_timezone_day(self):
        def lesson(hour, present, confirmation):
            return {'_id':str(hour), 'group':GROUP, 'date':f'2025-01-01T{hour:02}:00:00Z',
                    'records':[{'student':STUDENT, 'present':present, 'confirmation':confirmation}]}
        rows = [lesson(21, False, 'not_needed'), lesson(20, False, 'pending'),
                lesson(19, False, 'not_needed'), lesson(18, True, 'approved')]
        report = coo.attendance_report(rows, date(2025,1,1), date(2025,1,2), 2)
        row = report['students'][0]
        self.assertEqual((row['present'],row['absent'],row['unknown']), (1,2,1))
        self.assertEqual(row['latest_confirmed_absence_streak'], 1)
        self.assertFalse(row['needs_review'])
        self.assertEqual(row['evidence'][0]['day'], '2025-01-02')
        self.assertEqual(report['actual_lesson_start'], 'unavailable')

    def test_unknown_attendance_is_not_zero_or_perfect(self):
        rows = [{'_id':'r', 'group':GROUP, 'day':'2025-01-01', 'date':'2025-01-01T00:00:00Z',
                 'records':[{'student':STUDENT,'present':False,'confirmation':'disputed'}]}]
        row = coo.attendance_report(rows,date(2025,1,1),date(2025,1,1),2)['students'][0]
        self.assertIsNone(row['attendance_percent'])
        self.assertEqual(row['absent'],0)

    def test_interval_overlap_different_starts_and_adjacent_no_overlap(self):
        groups = [{'_id':GROUP, 'room':{'_id':ROOM},'mentor':{'_id':MENTOR},'schedule':'Du-Chor-Ju 18:00-20:00'},
                  {'_id':GROUP2,'room':ROOM,'mentor':MENTOR,'schedule':'Du-Chor-Ju 19:00-21:00'}]
        report = coo.schedule_report(groups)
        self.assertEqual(len(report['conflicts']),6)
        self.assertTrue(all(row['overlap_start_minute']==19*60 for row in report['conflicts']))
        groups[1]['schedule']='Du-Chor-Ju 20:00-22:00'
        self.assertEqual(coo.schedule_report(groups)['conflicts'],[])

    def test_missing_end_or_resources_are_unknown_not_false_conflicts(self):
        groups = [{'_id':GROUP,'schedule':'Se-Pay-Shanba 18:00-20:00'},
                  {'_id':GROUP2,'schedule':'Se-Pay-Shanba 18:00-20:00'},
                  {'_id':OTHER,'schedule':'Mon Wed Fri 18:00'}]
        report = coo.schedule_report(groups)
        self.assertEqual(report['conflicts'],[])
        self.assertEqual(len(report['unknown']),3)
        self.assertEqual(coo.schedule_report([dict(groups[0],isActive=False)])['inactive_skipped'],[GROUP])

    def test_period_validation_and_no_invented_duration(self):
        self.assertIsNone(coo.reporting_period('2025-02-30','2025-03-01'))
        self.assertIsNone(coo.reporting_period('2025-03-01','2025-01-01'))
        self.assertIsNone(coo.reporting_period('2025-01-01','2099-01-01'))
        self.assertIsNone(coo.schedule_slots('Du 20:00'))
        self.assertIsNone(coo.schedule_slots('Du 22:00-01:00'))


class ContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_unusable_attendance_is_partial_but_padding_exclusion_is_not(self):
        valid={'_id':'valid','group':GROUP,'date':'2025-01-02T10:00:00Z',
               'records':[{'student':STUDENT,'present':True,'confirmation':'confirmed'}]}
        outside={'_id':'outside','group':GROUP,'date':'2024-12-31T10:00:00Z','records':[]}
        invalid={'_id':'invalid','group':GROUP,'date':'broken-date','records':[]}
        async def audit(rows):
            def respond(req):
                return httpx.Response(200,json=me() if req.url.path.endswith('/me') else
                    {'attendance':rows,'pagination':{'total':len(rows)}})
            return await coo.attendance_audit(api_for(respond),'2025-01-01','2025-01-31')
        reply=await audit([valid,invalid])
        self.assertEqual(reply['data']['assessment'],'partial')
        self.assertEqual(reply['data']['skipped_records'],1)
        for unusable in [dict(valid,group=None), dict(valid,records=[{'student':None}]),
                         dict(valid,records=valid['records']*2), dict(valid,records=[])]:
            reply=await audit([unusable])
            self.assertEqual(reply['data']['assessment'],'partial')
        reply=await audit([valid,outside])
        self.assertEqual(reply['data']['assessment'],'complete_observed_records')
        self.assertEqual(reply['data']['skipped_records'],0)
        self.assertEqual(reply['data']['excluded_outside_period'],1)

    async def test_unauthenticated_and_wrong_branch_stop_before_data_reads(self):
        calls=[]
        api=api_for(lambda req:(calls.append(req.url.path) or httpx.Response(200,json=me())))
        denied=await coo.attendance_audit(api,'2025-01-01','2025-01-31',branch_id=OTHER)
        self.assertEqual(denied['status'],403)
        self.assertEqual(calls,['/api/branch/me'])
        api.token=None;calls.clear()
        denied=await coo.branch_context(api)
        self.assertEqual(denied['status'],401)
        self.assertEqual(calls,[])

    async def test_paginated_requests_full_and_capped_coverage(self):
        calls=[]
        def respond(req):
            calls.append(req.url.path)
            if req.url.path.endswith('/me'):return httpx.Response(200,json=me())
            page=int(req.url.params['page'])
            rows=[{'_id':str(i),'status':'pending','createdAt':'2025-01-01T00:00:00Z'} for i in (range(100) if page==1 else [100])]
            return httpx.Response(200,json={'requests':rows,'pagination':{'page':page,'total':101}})
        reply=await coo.status_request_sla(api_for(respond),24,max_pages=2)
        self.assertTrue(reply['data']['coverage']['complete'])
        self.assertEqual(len(reply['data']['requests']),101)
        self.assertEqual(reply['data']['policy_status'],'unconfirmed_example')
        reply=await coo.status_request_sla(api_for(respond),24,max_pages=1)
        self.assertFalse(reply['data']['coverage']['complete'])

    async def test_invalid_sla_is_local_and_second_page_failure_propagates(self):
        calls=[]
        def respond(req):
            calls.append(req.url.path)
            if req.url.path.endswith('/me'):return httpx.Response(200,json=me())
            if req.url.params['page']=='2':return httpx.Response(403,json={'success':False,'message':'denied'})
            return httpx.Response(200,json={'requests':[{'_id':'r','status':'pending'}],'pagination':{'total':2}})
        api=api_for(respond)
        for bad in [0,-1,float('nan'),float('inf'),True]:
            self.assertEqual((await coo.status_request_sla(api,bad))['status'],400)
        self.assertEqual(calls,[])
        self.assertEqual((await coo.status_request_sla(api,24,max_pages=2))['status'],403)

    async def test_duplicate_or_missing_pagination_contract_rejected(self):
        for body in [{'requests':[]}, {'requests':[{'_id':'r'},{'_id':'r'}],'pagination':{'total':2}}]:
            reply=await coo.paged(api_for(lambda req:httpx.Response(200,json=body)),'/fixture','requests',{},2)
            self.assertEqual(reply['status'],502)

    async def test_group_details_supply_room_and_private_fields_are_discarded(self):
        calls=[]
        def respond(req):
            calls.append(req.url.path)
            if req.url.path.endswith('/me'):body=me()
            elif req.url.path.endswith('/groups'):body={'groups':[{'_id':GROUP}]}
            else:body={'group':{'_id':GROUP,'room':ROOM,'mentor':MENTOR,'schedule':'Du 18:00-20:00'},
                       'students':[{'phone':'private-student','balance':999}]}
            return httpx.Response(200,json=body)
        reply=await coo.schedule_audit(api_for(respond))
        self.assertTrue(reply['success'])
        self.assertEqual(reply['data']['groups'][0]['room_id'],ROOM)
        self.assertEqual(calls[-1],'/api/branch/groups/'+GROUP)
        self.assertNotIn('private-student',json.dumps(reply))
        self.assertNotIn('balance',json.dumps(reply))

    async def test_role_plan_contains_actual_soul_agent_and_supported_fields(self):
        reply=await coo.delegation_plan(api_for(lambda req:httpx.Response(200,json=me())),
                                        '2025-01-01','2025-01-31',24)
        data=reply['data'];self.assertFalse(data['dispatched'])
        tasks=data['delegate_task_arguments']['tasks']
        self.assertEqual(len(tasks),3)
        roles=[]
        for task in tasks:
            self.assertEqual(set(task),{'goal','context','output_schema'})
            packet=json.loads(task['context']);roles.append(packet['role_id'])
            self.assertIn('# ',packet['trusted_role_soul'])
            self.assertIn('# ',packet['trusted_role_agent'])
            self.assertEqual(packet['arguments']['branch_id'],BRANCH)
            self.assertNotIn('password',packet)
        self.assertEqual(set(roles),set(coo.ROLES))

    async def test_real_unified_stdio_coo_audits_and_plan(self):
        calls=[]
        class Handler(BaseHTTPRequestHandler):
            def reply(self,code,body):
                raw=json.dumps(body).encode();self.send_response(code)
                self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
                self.end_headers();self.wfile.write(raw)
            def do_POST(self):
                calls.append(('POST',self.path));body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                valid=body.get('phone')=='fixture' and body.get('password')=='fixture'
                self.reply(200 if valid else 401,{'token':'fixture-token'} if valid else {'success':False})
            def do_GET(self):
                calls.append(('GET',self.path))
                if self.headers.get('Authorization')!='Bearer fixture-token':return self.reply(401,{'success':False})
                if self.path.endswith('/me'):body=me()
                elif self.path=='/api/branch/groups':body={'groups':[{'_id':GROUP}]}
                elif self.path=='/api/branch/groups/'+GROUP:body={'group':{'_id':GROUP,'room':ROOM,'mentor':MENTOR,'schedule':'Du 18:00-20:00'}}
                elif self.path.startswith('/api/branch/status-requests'):body={'requests':[{'_id':'r','student':STUDENT,'status':'pending','createdAt':'2025-01-01T00:00:00Z'}],'pagination':{'total':1}}
                elif self.path.startswith('/api/branch/attendance'):body={'attendance':[], 'pagination':{'total':0}}
                else:return self.reply(404,{'success':False})
                self.reply(200,{'success':True,**body})
            def log_message(self,*args):pass
        backend=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=backend.serve_forever,daemon=True);thread.start()
        try:
            params=StdioServerParameters(command=sys.executable,args=[str(ROOT/'server.py')],env={'MARS_API_URL':f'http://127.0.0.1:{backend.server_port}'})
            async with connected_client(params) as client:
                self.assertEqual(len((await client.list_tools()).tools),41)
                denied=await client.call_tool('coo_branch_context',{})
                self.assertTrue(denied.isError);self.assertEqual(calls,[])
                logged=await client.call_tool('login',{'phone':'fixture','password':'fixture'})
                self.assertFalse(logged.isError)
                arguments={'period_start':'2025-01-01','period_end':'2025-01-31'}
                for tool,args in [('coo_branch_context',{}),('coo_attendance_audit',arguments),
                                  ('coo_schedule_audit',{}),('coo_status_request_sla',{'sla_hours':24}),
                                  ('coo_delegation_plan',{**arguments,'sla_hours':24})]:
                    reply=await client.call_tool(tool,args)
                    self.assertFalse(reply.isError,tool)
                    self.assertTrue(reply.structuredContent['success'])
                self.assertTrue(all(method=='GET' or path=='/api/auth/login' for method,path in calls))
        finally:
            backend.shutdown();backend.server_close();thread.join(5)


if __name__=='__main__':
    unittest.main()
