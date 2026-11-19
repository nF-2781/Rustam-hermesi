# MARS LMS MCP server (Hermes ichida)

Hermes `config.yaml` da `mars_lms` nomi bilan ro'yxatga olingan stdio MCP server.
U MARS IT LMS backend'i (`mars-backend`) bilan ishlaydi va 10 ta workflow-agent
toolini hamda ular uchun ma'lumot beruvchi yordamchi tool'larni taqdim etadi.

```
Hermes (agent) ──stdio──> server.py ──HTTPS──> https://mars-backend-six.vercel.app
```

## Tuzilma

| Fayl | Vazifa |
|---|---|
| `server.py` | FastMCP server: 22 tool (10 workflow-agent + 12 yordamchi) |
| `lms_client.py` | HTTP klient: token xotirada, 401 da bir marta re-login, yagona xato konverti |
| `test_tools.py` | 24 ta mock-backend testi (`httpx.MockTransport`) |
| `test_client.py` | Haqiqiy stdio klient testi (`tools/list` + jonli tool chaqiruvlari) |
| `.env` | Maxfiy sozlamalar (git'ga qo'shilmaydi) |
| `.env.example` | Namunaviy sozlamalar |

## Ishga tushirish

```bash
cd C:/Users/user/Documents/Hermes-2/mcp-servers/mars_lms
uv venv --python 3.11 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
cp .env.example .env   # qiymatlarni to'ldiring
```

Hermes tomonida (`C:/Users/user/Documents/Hermes-2/config.yaml`):

```yaml
mcp_servers:
  mars_lms:
    command: "C:/Users/user/Documents/Hermes-2/mcp-servers/mars_lms/.venv/Scripts/python.exe"
    args: ["C:/Users/user/Documents/Hermes-2/mcp-servers/mars_lms/server.py"]
    enabled: true
    timeout: 180
```

Tekshirish: `hermes mcp test mars_lms` → `✓ Connected`, `✓ Tools discovered: 22`.
Hermes sessiyasida `/reload-mcp` yoki yangi sessiya orqali tool'lar `mcp__mars_lms__*`
nomi bilan ko'rinadi.

## Backend bilan moslik (jonli tekshirilgan)

Har bir endpoint `mars-backend/src/router/*.js` dan o'qildi va haqiqiy backend'da
`admin` akkaunti bilan sinovdan o'tkazildi.

| Tool | Backend endpoint |
|---|---|
| `lms_login` | `POST /api/auth/login` |
| `lms_context` | `GET /api/branch/overview` |
| `list_groups` | `GET /api/branch/groups` |
| `list_students` | `GET /api/branch/students` |
| `get_debts`, `debt_control_agent` | `GET /api/branch/debtors` |
| `get_attendance`, `attendance_control_agent`, `student_progress_audit` | `GET /api/branch/attendance` |
| `get_homework`, `homework_control_agent` | `GET /homework` |
| `get_finance_report`, `daily_finance_report` | `GET /api/branch/overview`, `GET /api/finance/overview` |
| `get_payments` | `GET /api/branch/payments` |
| `get_pending_approvals`, `pending_approvals_digest`, `reception_router` | `GET /api/branch/status-requests`, `GET /api/branch/waitlist` |
| `get_room_plan`, `room_schedule_assistant`, `mentor_workload_analysis` | `GET /api/branch/workload-planning`, `GET /api/branch/groups`, `GET /api/branch/mentors` |
| `get_student_progress`, `new_student_followup` | `GET /api/branch/students`, `GET /api/branch/attendance`, `GET /homework` |

Backend'da alohida endpoint bo'lmagan tool'lar mavjud ma'lumotlardan hisoblanadi:

- `room_availability` / `schedule_conflicts` → guruh `schedule` matni
  (`Se-Pay-Shanba 18:00-20:00`) parse qilinadi, `workload-planning` ning
  `rooms`/`timeslots` maydonlari bilan solishtiriladi.
- `pending_enrollments` → o'quvchining `group`, `billing.paid`, `direction`,
  `createdAt` maydonlari bo'yicha jarayon bosqichlari.
- `student_progress` → davomat yozuvlari, uy vazifasi `submissions` va
  `billing` ko'rsatkichlari yig'indisi.
- `incoming_requests` → `waitlist` + `status-requests` yozuvlari, matn bo'yicha
  toifalash (to'lov / jadval / ta'lim / texnik / boshqa).

## 10 workflow-agent

| # | Tool | Nima qiladi |
|---|---|---|
| 1 | `debt_control_agent` | Qarzdorlarni summa va kechikish bo'yicha saralaydi, eslatma matnlari va hisobot beradi |
| 2 | `attendance_control_agent` | Ketma-ket dars qoldirganlarni aniqlaydi, mentor va admin uchun ogohlantirish |
| 3 | `homework_control_agent` | Muddati o'tib topshirilmagan vazifalarni ajratadi, o'quvchi/mentor ro'yxatlari |
| 4 | `daily_finance_report` | Tushum, xarajat, qoldiq, qarzdorlik va oldingi davr farqi |
| 5 | `new_student_followup` | Guruhga biriktirilmagan yoki to'lov qilmagan yangi o'quvchilar |
| 6 | `pending_approvals_digest` | Tasdiq kutayotgan so'rovlarni turi va kutish vaqti bo'yicha guruhlaydi |
| 7 | `room_schedule_assistant` | Mentor/xona ikki marta band qilinishini topadi, bo'sh slotlarni taklif qiladi |
| 8 | `mentor_workload_analysis` | Mentorlar yuklamasini solishtiradi, yangi guruh uchun tavsiya beradi |
| 9 | `student_progress_audit` | Davomat, uy vazifasi, to'lov va nofaollik bo'yicha ortda qolganlarni aniqlaydi |
| 10 | `reception_router` | Murojaatlarni toifalab mas'ulga yo'naltiradi, javob loyihasini tayyorlaydi |

Har bir agent `details` ichida `report_markdown` (Hermes dashboardida ko'rsatish uchun),
`message_drafts` yoki `reply_drafts` (yuborishga tayyor matn) va `next_actions` qaytaradi.
Xabar yuborish va davriy ishga tushirish (cron/Telegram/email) bu serverga kirmaydi —
u alohida integratsiya sifatida ulanadi.

## Xato siyosati

Har bir javob yagona konvertda:

```json
{"error": null, "status_code": 200, "message": "success", "endpoint": "/api/branch/debtors", "details": {}}
```

Xato bo'lsa `error` va `message` agent uchun harakatga undovchi matn bo'ladi:

- `401` → `lms_login` ni qayta chaqirish, `MARS_PHONE`/`MARS_PASSWORD` ni tekshirish;
- `403` → rol yetarli emas, `admin`/`owner` akkaunti kerak;
- `400` → `month` `YYYY-MM` formatida bo'lishi kerak va h.k.

## Testlar

```bash
.venv/Scripts/python.exe -m unittest discover -s . -p "test_tools.py" -v   # 24 mock test
.venv/Scripts/python.exe test_client.py                                    # jonli stdio
.venv/Scripts/python.exe test_client.py --no-live                          # faqat tools/list
```
