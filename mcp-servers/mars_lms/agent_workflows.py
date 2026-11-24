"""Read-only student evidence and draft-only reception analysis."""
from datetime import date
import math
import re
import unicodedata

from scoped_client import LMSClient

DEFAULT_CRITERIA = {
    'attendance_min_percent': 80,
    'grade_min_percent': 60,
    'missing_homework_min': 2,
    'min_observed_lessons': 3,
}
ROLES = {'payment': 'Moliya mas’uli', 'schedule': 'Administrator',
         'education': 'Mentor', 'technical': 'Texnik yordam', 'other': 'Administrator'}

def ok(data, **extra):
    return {'success': True, 'status': 200, 'source': 'mcp', 'data': data, **extra}

def identifier(value):
    return str(value.get('_id', '')) if isinstance(value, dict) else str(value or '')

def valid_id(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-fA-F]{24}', value) is not None

def day(value):
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None

def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

async def roster(api):
    reply = await api.get('/students')
    if not reply['success']:
        return reply
    rows = (reply.get('data') or {}).get('students')
    if not isinstance(rows, list):
        return LMSClient.error(502, 'Unexpected students response shape', 'contract')
    students = [{'student_id': identifier(row), 'fullname': row.get('fullname'),
                 'group_id': identifier(row.get('group'))}
                for row in rows if isinstance(row, dict)]
    return ok({'students': students, 'source_endpoint': '/students'})

async def group_records(api, kind, group_id):
    if kind not in {'attendance', 'homework'} or not valid_id(group_id):
        return LMSClient.error(400, 'A valid group ObjectId is required')
    reply = await api.get(f'/{kind}/group/{group_id}')
    if not reply['success']:
        return reply
    rows = (reply.get('data') or {}).get(kind)
    if not isinstance(rows, list):
        return LMSClient.error(502, f'Unexpected {kind} response shape', 'contract')
    # Keep only workflow fields; omit student phones and unrelated staff salaries.
    if kind == 'attendance':
        rows = [{'id': identifier(row), 'date': row.get('date'), 'day': row.get('day'),
                 'records': [{'student_id': identifier(item.get('student')),
                              'present': item.get('present'), 'confirmation': item.get('confirmation')}
                             for item in row.get('records', []) if isinstance(item, dict)]}
                for row in rows if isinstance(row, dict)]
    else:
        rows = [{'id': identifier(row), 'title': row.get('title'), 'topic': row.get('topic'),
                 'due_date': row.get('dueDate'), 'max_score': row.get('maxScore'),
                 'submissions': [{'student_id': identifier(item.get('student')),
                                  'submitted_at': item.get('submittedAt'), 'grade': item.get('grade')}
                                 for item in row.get('submissions', []) if isinstance(item, dict)]}
                for row in rows if isinstance(row, dict)]
    return ok({kind: rows, 'source_endpoint': f'/{kind}/group/{group_id}'})

def analyze_progress(student_id, group_id, period_start, period_end, attendance, homework,
                     criteria=None, criteria_confirmed=False):
    start, end = day(period_start), day(period_end)
    if not start or not end or start > end or len(period_start) != 10 or len(period_end) != 10 or end > date.today():
        return LMSClient.error(400, 'Use an ordered past/present YYYY-MM-DD period')
    rules = dict(DEFAULT_CRITERIA)
    if criteria:
        if set(criteria) - set(rules):
            return LMSClient.error(400, 'Unknown criteria key')
        rules.update(criteria)
    for key, value in rules.items():
        if not number(value) or value < 0 or (key.endswith('percent') and value > 100):
            return LMSClient.error(400, 'Criteria must contain finite valid thresholds')
        if key in {'missing_homework_min', 'min_observed_lessons'} and (value < 1 or int(value) != value):
            return LMSClient.error(400, 'Count criteria must be positive integers')
    present = absent = unknown = invalid_dates = 0
    confirmations = []
    for row in attendance:
        observed = day(row.get('day') or row.get('date'))
        if observed is None:
            invalid_dates += 1
            continue
        if not start <= observed <= end:
            continue
        records = [item for item in row['records'] if item['student_id'] == student_id]
        if len(records) != 1 or not isinstance(records[0].get('present'), bool):
            unknown += 1
            continue
        record = records[0]
        state = record.get('confirmation')
        confirmed_present = state in {'confirmed', 'approved'} and record['present'] is True
        confirmed_absent = state in {'rejected', 'not_needed'} and record['present'] is False
        if not (confirmed_present or confirmed_absent):
            unknown += 1
            confirmations.append(row['id'])
            continue
        present += confirmed_present
        absent += confirmed_absent
    assignments = []
    percentages = []
    missing = 0
    for row in homework:
        due = day(row.get('due_date'))
        if due is None:
            invalid_dates += 1
            continue
        if not start <= due <= end:
            continue
        submissions = [item for item in row['submissions'] if item['student_id'] == student_id]
        # Do not arbitrarily choose among duplicate submissions.
        submission = submissions[0] if len(submissions) == 1 else None
        grade = submission.get('grade') if submission else None
        maximum = row.get('max_score')
        percent = (round(100 * grade / maximum, 2)
                   if number(grade) and number(maximum) and maximum > 0 and 0 <= grade <= maximum else None)
        if percent is not None:
            percentages.append(percent)
        missing += not submissions
        assignments.append({'homework_id': row['id'], 'title': row.get('title'), 'topic': row.get('topic'),
                            'submitted': bool(submissions), 'ambiguous_submissions': len(submissions) > 1,
                            'grade_percent': percent})
    observed = present + absent
    rate = round(100 * present / observed, 2) if observed else None
    average = round(sum(percentages) / len(percentages), 2) if percentages else None
    signals = []
    if rate is not None and observed >= rules['min_observed_lessons'] and rate < rules['attendance_min_percent']:
        signals.append({'key': 'low_attendance', 'observed_percent': rate,
                        'threshold': rules['attendance_min_percent'], 'help': 'Mentor bilan davomat to‘sig‘ini aniqlash va qatnashish rejasini tuzish.'})
    if average is not None and average < rules['grade_min_percent']:
        signals.append({'key': 'low_graded_homework', 'observed_percent': average,
                        'threshold': rules['grade_min_percent'], 'help': 'Past natijali topshiriq mavzusini birga qayta ishlash va qisqa qayta tekshiruv.'})
    if missing >= rules['missing_homework_min']:
        signals.append({'key': 'missing_group_submissions', 'count': missing,
                        'threshold': rules['missing_homework_min'],
                        'help': 'Avval topshiriqlar shu o‘quvchiga tegishli bo‘lganini tekshirish, keyin topshirish rejasini kelishish.'})
    return ok({'student_id': student_id, 'group_id': group_id,
               'period': {'from': period_start, 'to': period_end,
                          'date_basis': 'attendance.day (Tashkent) when available; otherwise backend ISO date prefix'},
               'attendance': {'present': present, 'absent': absent, 'unknown_records': unknown,
                              'observed_lessons': observed, 'rate_percent': rate,
                              'unconfirmed_record_ids': confirmations},
               'homework': {'group_assignments': len(assignments), 'missing_submissions': missing,
                            'graded_count': len(percentages), 'average_percent': average, 'items': assignments},
               'criteria': rules, 'criteria_status': 'confirmed_by_caller' if criteria_confirmed else 'unconfirmed_example',
               'signals': signals, 'assessment': 'provisional' if not criteria_confirmed else 'requires_mentor_review',
               'limitations': ['Current-group evidence only; transfer history/exams are not covered.',
                              'Group assignments do not prove individual enrollment or assignment eligibility.',
                              'Missing records and grades are unknown, not zero or 100 percent.',
                              'Signals describe observations; personal causes are hypotheses for mentor verification.'],
               'invalid_date_records': invalid_dates})

async def student_progress(api, student_id, period_start, period_end, criteria=None, criteria_confirmed=False):
    if not valid_id(student_id):
        return LMSClient.error(400, 'A valid student ObjectId is required')
    validation = analyze_progress(student_id, '', period_start, period_end, [], [], criteria, criteria_confirmed)
    if not validation['success']:
        return validation
    students = await roster(api)
    if not students['success']:
        return students
    matches = [item for item in students['data']['students'] if item['student_id'] == student_id]
    if len(matches) != 1:
        return LMSClient.error(404, 'Student not found in the authorized roster')
    group_id = matches[0]['group_id']
    if not valid_id(group_id):
        return LMSClient.error(422, 'Student has no current group; progress cannot be inferred')
    attendance = await group_records(api, 'attendance', group_id)
    if not attendance['success']:
        return attendance
    homework = await group_records(api, 'homework', group_id)
    if not homework['success']:
        return homework
    return analyze_progress(student_id, group_id, period_start, period_end,
                            attendance['data']['attendance'], homework['data']['homework'],
                            criteria, criteria_confirmed)

def incoming_requests(requests=None):
    if requests is None:
        return {**LMSClient.error(501, 'The verified backend has no generic reception inbox endpoint.', 'capability'),
                'fallback': 'Provide a manual array of {id, text}. Frozen-status requests are not a general inbox.'}
    if not isinstance(requests, list) or len(requests) > 100:
        return LMSClient.error(400, 'Provide at most 100 requests')
    seen = set()
    for item in requests:
        if not isinstance(item, dict) or not isinstance(item.get('id'), str) or not item['id'].strip():
            return LMSClient.error(400, 'Every request needs a nonempty string id')
        if item['id'] in seen or not isinstance(item.get('text'), str) or not 0 < len(item['text'].strip()) <= 10000:
            return LMSClient.error(400, 'Request ids must be unique and text nonempty, at most 10000 characters')
        seen.add(item['id'])
    return ok({'requests': [{'id': item['id'], 'text': item['text']} for item in requests],
               'source': 'manual_input', 'backend_inbox_available': False})

KEYWORDS = {
    'payment': ['to\'lov', 'tolov', 'qarz', 'оплат', 'платеж', 'payment', 'refund'],
    'schedule': ['jadval', 'dars vaqti', 'расписан', 'schedule', 'reschedule'],
    'education': ['uy vazifa', 'vazifani', 'tushunmadim', 'o\'zlashtir', 'baho', 'домашн', 'оценк', 'homework', 'lesson topic'],
    'technical': ['parol', 'login', 'xatolik', 'ochilmay', 'ishlamay', 'парол', 'ошибк', 'error', 'password'],
}
REPLIES = {
    'payment': 'To‘lov bo‘yicha murojaatingiz qabul qilindi. Hisob holatini moliya mas’uli tekshirishi uchun administratorga taqdim etamiz.',
    'schedule': 'Jadval bo‘yicha murojaatingiz qabul qilindi. Guruh va sizga qulay vaqtni aniqlashtirishni so‘raymiz.',
    'education': 'Ta’lim bo‘yicha savolingiz qabul qilindi. Qaysi mavzu yoki topshiriqda yordam kerakligini mentorga aniqlashtirib beramiz.',
    'technical': 'Texnik muammo bo‘yicha murojaatingiz qabul qilindi. Xatolik matnini yuboring; parol yoki token yubormang.',
    'other': 'Murojaatingizni aniqlashtirish uchun qaysi masala bo‘yicha yordam kerakligini yozing.',
}

def reception_triage(requests, responsible_roles=None):
    validated = incoming_requests(requests)
    if not validated['success']:
        return validated
    roles = dict(ROLES)
    if responsible_roles:
        if set(responsible_roles) - set(roles) or any(not isinstance(v, str) or not v.strip() for v in responsible_roles.values()):
            return LMSClient.error(400, 'Use nonempty responsible role labels for known categories')
        roles.update(responsible_roles)
    routed = []
    for item in validated['data']['requests']:
        normalized = unicodedata.normalize('NFKC', item['text']).lower()
        normalized = normalized.translate(str.maketrans({'‘': "'", '’': "'", 'ʻ': "'", 'ʼ': "'"}))
        matches = {category: [word for word in words if re.search(r'(?<!\w)' + re.escape(word), normalized)]
                   for category, words in KEYWORDS.items()}
        matches = {category: words for category, words in matches.items() if words}
        category = next(iter(matches)) if len(matches) == 1 else 'other'
        routed.append({'request_id': item['id'], 'category': category,
                       'suggested_responsible_role': roles[category], 'matched_keywords': matches,
                       'needs_clarification': len(matches) != 1, 'draft_reply': REPLIES[category],
                       'routing_status': 'proposal_only', 'sent': False})
    return ok({'source': 'manual_input', 'items': routed,
               'needs_clarification': [row['request_id'] for row in routed if row['needs_clarification']],
               'limitations': ['Keyword-based suggestions require administrator review.',
                              'Roles are proposed labels, not verified employee assignments.',
                              'No requests were forwarded and no replies were sent.']})
