# YB-3110 — 1-topshiriq: Mars jamoasining LMS repo va konteksti

**Jamoa:** Mars (LMS — o'quv markaz boshqaruv tizimi)
**Team Lead:** Rustam — @rustam106 (CTO)
**Topshiruvchi:** @bmt_430 | **Muddat:** bugun 21:30

---

## 1. Repolar

### Backend va agentlar platformasi

| Repo | Nima qiladi | GitHub |
|---|---|---|
| `Rustam-hermesi` | Hermes AI-agent platformasi: `mars_lms` MCP serveri, skill'lar, dashboard runner, agentlar. Jamoa shu repo ustida ishlaydi (branch `rustam`). | https://github.com/nF-2781/Rustam-hermesi |
| `mars-backend` | LMS backend'i (Node.js, JWT auth, filial / moliya / davomat / uy vazifasi API'lari). | https://github.com/nF-2781/mars-backend.git |
| `mars-lms-mcp` | MCP server reposi: JWT login va LMS tool'lari (birinchi versiya 11 tool; hozirgi `mcp-servers/mars_lms` — 22 tool). | https://github.com/nF-2781/mars-lms-mcp.git |

- Backend prod: https://mars-backend-six.vercel.app
- Swagger: https://mars-backend-six.vercel.app/api-docs/
- Backend lokal: http://localhost:7000 (Docker)

### Frontend (har biri alohida repo va alohida deploy)

| Repo | Kim uchun | GitHub | Deploy |
|---|---|---|---|
| `mars-admin` | Admin panel (filial, guruh, o'quvchi, moliya) | https://github.com/nF-2781/mars-admin.git | https://mars-admin-beta.vercel.app |
| `mars-branch-manager` | Filial menejeri | https://github.com/nF-2781/mars-branch-manager.git | https://mars-branch-manager.vercel.app |
| `mars-finance` | Moliya bo'limi | https://github.com/nF-2781/mars-finance.git | https://mars-finance-orpin.vercel.app |
| `mars-intern` | Amaliyotchi (intern) | https://github.com/nF-2781/mars-intern.git | https://mars-intern.vercel.app |
| `mars-mentor` | Mentor | https://github.com/nF-2781/mars-mentor.git | https://mars-mentor.vercel.app |
| `mars-parent` | Ota-ona | https://github.com/nF-2781/mars-parent.git | https://mars-parent.vercel.app |
| `mars-student` | O'quvchi | https://github.com/nF-2781/mars-student.git | https://mars-student.vercel.app |
| `mars-tutor` | Tutor / repetitor | https://github.com/nF-2781/mars-tutor.git | https://mars-tutor.vercel.app |

Barcha repolar bitta GitHub tashkilotda: https://github.com/nF-2781 (backend va agentlar
platformasi ham shu yerda).

- Lokal monorepo: `C:\Users\user\Desktop\Mars`

## 2. Arxitektura

```
Foydalanuvchi ──▶ Frontend (mars-admin, mars-student, ... Vercel)
                        │ HTTPS/JWT
                        ▼
                  mars-backend (Vercel)  ◀── Swagger /api-docs
                        ▲ HTTPS/JWT
                        │
Hermes agent ── stdio (MCP) ──▶ mcp-servers/mars_lms/server.py
   (mars-ceo ... mars-cpo)            22 tool: 10 workflow + 12 yordamchi
                        │
                        ▼
              dashboard :9120 (run_mars_dashboard.sh)
```

- Hermes loyihasi: `hermes project list` → `* mars  Mars  [1 folder(s)]`
- MCP ulanishi: `hermes mcp test mars_lms` → `✓ Connected`, `✓ Tools discovered: 22`
- Tool nomlari Hermes ichida: `mcp__mars_lms__<tool>`

## 3. Hozir nima ishlaydi (jonli tekshirilgan)

| Imkoniyat | Holat | Dalil |
|---|---|---|
| JWT login (`lms_login`) + 401 da avtomatik re-login | ✅ | jonli backend, owner akkaunt |
| Filial kesimi: guruhlar, o'quvchilar, mentorlar (`lms_context`) | ✅ | 1 guruh, 2 faol o'quvchi |
| Qarzdorlik (`get_debts`, `debt_control_agent`) | ✅ | summa + kechikish + eslatma loyihalari |
| Davomat (`get_attendance`, `attendance_control_agent`) | ✅ | ketma-ket qoldirishlar aniqlanadi |
| Uy vazifasi (`get_homework`, `homework_control_agent`) | ✅ | muddati o'tganlar ro'yxati |
| Moliya (`get_finance_report`, `daily_finance_report`, `get_payments`) | ✅ | tushum/xarajat/qoldiq |
| Tasdiqlar va murojaatlar (`pending_approvals_digest`, `reception_router`) | ✅ | status-requests + waitlist |
| Yuklama va xona (`mentor_workload_analysis`, `room_schedule_assistant`) | ✅ | guruh `schedule` matni parse qilinadi |
| O'quvchi auditi (`student_progress_audit`, `new_student_followup`) | ✅ | davomat+uy vazifasi+to'lov yig'indisi |
| Kunlik 6-qadamli zanjir → `chain_report.md` | ✅ | `chain_demo.py`, `chain OK` |
| Testlar | ✅ | 24 mock test + jonli stdio klient testi |
| Hermes dashboard (:9120) | ✅ | `GET /` → 200, `/api/status` → v0.21.2 |
| Skill'lar: `mars-lms-operations`, `hermes-mars-dashboard` | ✅ | `hermes skills list` → enabled |
| 7 ta C-level agent (soul.md + agents.md) | ✅ | `bash agents/install.sh --check` → 7/7 tayyor |

## 4. Hozir nima ishlamaydi / cheklangan

| Muammo | Ta'sir | Yechim |
|---|---|---|
| Xabar yuborish (Telegram/SMS/email) MCP serverda yo'q | agent faqat **matn loyihasi** (`message_drafts`, `reply_drafts`) beradi | inson tasdig'idan keyin alohida integratsiya |
| Pul operatsiyalari (to'lov qabul qilish, refund, oylik to'lash) | ataylab yopilgan | faqat hisobot; amal — backend UI'da odam tomonidan |
| Ba'zi endpoint yo'q: xona bo'shligi, jadval to'qnashuvi, mentor yuklamasi | lokal hisoblanadi (guruh `schedule` parse) → noaniqlik bo'lishi mumkin | backend'ga endpoint qo'shilsa, tool'lar soddalashadi |
| Rollar: faqat `admin`/`owner` to'liq ishlaydi | `mentor`/`financeManager` da 403 | rol bo'yicha ruxsat matritsasi kerak |
| Credentials bir marta git tarixiga tushib qolgan | xavfsizlik | fayllar tracking'dan chiqarildi; parol/kalit almashtirish qolgan |
| Dashboard standart porti 9119 band (gateway ichki dashboardi) | `BACKEND_PORT_IN_USE` | `run_mars_dashboard.sh` 9120 ni tanlaydi |

## 5. Aniqlashtirish kerak

1. Nechta filial/oy live ma'lumot bilan sinovdan o'tgan.
2. Har bir a'zoning agent bo'yicha yakuniy tasdig'i (2-topshiriq: `2-agent-roster.md`).

## 6. Qanday tekshirish (takrorlanadigan)

```bash
cd <repo>                                    # repo ildizi
export HERMES_HOME="$PWD" PYTHONPATH="$PWD/hermes-agent"
# login: owner test akkaunti (.env: MARS_PHONE / MARS_PASSWORD — repo'ga yozilmaydi)
python -m hermes_cli.main mcp test mars_lms  # ✓ 22 tools
python mcp-servers/mars_lms/chain_demo.py    # 6-qadamli zanjir → chain_report.md
bash skills/hermes_mars_dashboard/run_mars_dashboard.sh start   # dashboard :9120
bash agents/install.sh --check               # 7 agent profili
```
