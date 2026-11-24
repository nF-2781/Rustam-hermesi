# CMO API Contracts

## Tekshirilgan Integratsiya (Checked Implementation)

CMO va uning barcha sub-agentlari MARS LMS tizimiga faqat o'qish (Strict Read-Only) rejimida ulanadi. Barcha tahlillar `mcp-servers/mars_lms` yoki stdio `mars-mcp-server` orqali xavfsiz amalga oshiriladi.

| Tool | Parametrlar | API va Backend funksiyasi | Vazifasi va Natijasi |
| --- | --- | --- | --- |
| `lms_login` | phone, password, role | POST `/api/auth/login` | Sessiya JWT tokeni va autentifikatsiya |
| `lms_context` / `branch_me` | yo'q | GET `/api/branch/me` | Filial profili, ish vaqti va xonalar soni |
| `new_student_followup` | status, search, limit | GET `/api/branch/students?status=lead` | Yangi lidlar, kuzatuv holati va konversiya |
| `list_students` | search, group_id, status, limit | GET `/api/branch/students` | O'quvchilar ro'yxati va holati tahlili |
| `list_groups` | page, limit | GET `/api/branch/groups` | Guruhlar, to'lganlik darajasi, yangi kurslar |
| `get_payments` | month, page, limit | GET `/api/branch/payments` | Sinov darsidan keyingi to'lovlar va CAC hisobi |
| `get_finance_report` | month | GET `/api/finance/overview` | Marketing ROI, xarajatlar va tushumlar balansi |
| `get_pending_approvals` | limit | GET `/api/branch/approvals` | Kutilayotgan arizalar va murojaatlar navbati |

## Dalillar va Chegaralar (Evidence and Limits)

- **Mutlaq Faqat O'qish (Strict Read-Only):** LMS bazasiga hech qanday yozish (POST/PUT/DELETE) qilinmaydi.
- **Shaxsiy Ma'lumotlar Maxfiyligi (PII):** O'quvchilar va ota-onalar telefon raqamlari, ism-familiyalari yoki to'lov ma'lumotlari hisobotlarda ochiqlanmaydi; faqat ichki ID va agregat statistikalar ishlatiladi.
- **Manbali Ko'rsatkichlar:** Barcha raqamlar manba tooli va tahlil davri bilan ko'rsatiladi.