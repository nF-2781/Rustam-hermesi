# MCP serverlar — 6 + 1 modul

Bitta ulkan serverga 130+ endpointni tiqish kontekstni to'ldiradi va xavfsizlikni
buzadi: har agent o'ziga kerak bo'lmagan tool'ni ko'radi. Shuning uchun API guruhlari
**6 ta domen serveri + 1 xotira serveri**ga bo'linadi.

| Server | API guruhi | Kim ulanadi |
|---|---|---|
| `mcp-mars-auth` | `/api/auth/*`, `/api/health` | barcha agentlar (faqat o'z tokeni) |
| `mcp-mars-branch` | `/api/branch/*`, `/api/workspace/*` | Branch, Academic, Auditor |
| `mcp-mars-finance` | `/api/finance/*`, `/api/branch/{payments,expenses,debtors}` | Finance, CEO (faqat `GET`) |
| `mcp-mars-mentor` | `/api/mentor/*`, `/attendance/*`, `/api/tutor-bookings/*`, `/api/intern/*` | Mentor, Tutor & Intern |
| `mcp-mars-portal` | `/students/me/*`, `/api/student*`, `/api/parent/*`, `/parents/*`, `/api/teams`, `/api/rating` | Student & Parent |
| `mcp-mars-analytics` | `/api/ai/analytics/*`, `/api/branch/demand-stats`, `/api/branch/curriculum-topic-analytics` | CEO, Academic, Auditor |
| `mcp-obsidian-rag` | Vault (Markdown o'qish/yozish + vector/BM25 qidiruv) | Orchestrator + barcha (o'z papkasi) |

Mashina o'qiydigan registr: [`servers.json`](servers.json) — har server uchun `endpoints`,
`agents`, `write_ops`, `guardrails`.

## Bugungi holat bilan bog'lanish (halol)

2026-11-27 holatiga **uchta** server ishlaydi:

| Server | Kod | Tool | Test |
|---|---|---|---|
| `mcp-servers/mars_lms` | `server.py` + `lms_client.py` | 28 | 16 |
| `mcp-servers/mars_finance` | `server.py` (umumiy `lms_client` + `security_sandbox`) | 13 | **19** |
| `mcp-servers/obsidian_rag` | `server.py` + `indexer.py` | 4 | **16** |

Ya'ni birinchi domen (`mcp-mars-finance`) va xotira serveri (`mcp-obsidian-rag`)
spetsifikatsiyadan kodga aylandi. Qolgan 5 domen (`auth`, `branch`, `mentor`,
`portal`, `analytics`) hali registr darajasida.

Eski yagona server `mcp-servers/mars_lms` (28 tool) quyidagi 4 guruhni **birga** beradi
va u o'chirilmagan — orqaga qaytish yo'li saqlanadi:

| Bugungi tool oilasi | Kelajakdagi server |
|---|---|
| `lms_login`, `lms_context` | `mcp-mars-auth` |
| `coo_*` (5 tool), `get_attendance`, `list_groups`, `list_students` | `mcp-mars-branch` |
| `daily_finance_report`, `get_finance_report`, `get_debts`, `get_payments`, `debt_control_agent` | `mcp-mars-finance` |
| `homework_control_agent`, `room_schedule_assistant`, `reception_router`, `pending_approvals_digest`, `get_student_progress` | `mcp-mars-branch` / `mcp-mars-mentor` |

Migratsiya qoidasi bajarildi va davom etadi: har yangi server `mcp-servers/<nom>/server.py`
bo'lib chiqadi, `lms_client.py` umumiy qoladi (endpointlar bitta joyda), va eski
`mars_lms` serveri yangisi ishlab turmaguncha o'chirilmaydi.

Birinchi migratsiya namunasi — `mcp-servers/mars_finance/`: 13 tool, har yozuvchi tool
`security_sandbox.check()` dan o'tadi, CEO uchun `RBAC_READ_ONLY`, `428` = inson tasdig'i
kerak (amal bajarilmagan).

## Har server uchun majburiy qoidalar

1. `stdout` faqat JSON-RPC uchun; loglar `stderr` ga (mavjud `server.py` konvensiyasi).
2. Javob yagona konvertda: `error / status_code / message / endpoint / details`.
3. Token xotirada; diskka, logga, Obsidian'ga chiqmaydi.
4. Yozuvchi tool'lar ro'yxati `servers.json` da `write_ops` — ular `security_sandbox`
   orqali o'tadi (approval / reason / ABAC).
5. `GET` tool'lari `period` yoki `date` ni majburiy parametr qiladi (davr ko'rsatilmagan
   hisobot — taqiqlangan).
6. Har tool `agent` nomini oladi va `rbac_matrix.json` bo'yicha tekshiradi.

## Kontekst iqtisodi

Har agent uchun faqat 2–3 server ulanadi. Taxminiy tool soni: auth 5 + branch 25 +
finance 12 + mentor 20 + portal 18 + analytics 4 ≈ **84 tool**, lekin bitta agentda
ko'pi bilan ~30 ko'rinadi. Bu `mcp-mars-analytics` ni alohida ajratishning asosiy sababi:
CEO va Academic umumiy ro'yxatdan chuqur analitikani ko'radi, mentorga esa umuman
ko'rinmaydi.
