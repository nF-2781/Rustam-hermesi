# YB-3110 — 1-topshiriq: Mars jamoasining LMS repo va konteksti

**Jamoa:** Mars (LMS — o'quv markaz boshqaruv tizimi)
**Teamleadlar:** @jamkaILZ, @rustam106
**Topshiruvchi:** @bmt_430 | **Muddat:** bugun 21:30

---

## 1. Repolar

| Repo | Nima qiladi | Manzil |
|---|---|---|
| `Rustam-hermesi` | Hermes AI-agent platformasi: `mars_lms` MCP serveri, skill'lar, dashboard runner, agentlar. Jamoa shu repo ustida ishlaydi. | https://github.com/nF-2781/Rustam-hermesi (branch `rustam`) |
| `mars-mcp-server` | LMS uchun birinchi (soddaroq) MCP server: 11 tool, JWT login, filial/moliya o'qish. Hozir `mcp-servers/mars_lms` uning kengaytirilgan versiyasi. | lokal: `mars-mcp-server/` (repo linki teamlead tomonidan tasdiqlanadi) |
| `mars-backend` | LMS backend'i (Node.js, JWT auth, filial/moliya/davomat/uy vazifasi API'lari). | Prod: https://mars-backend-six.vercel.app <br> Lokal: http://localhost:7000 (Docker) |

> **Frontend:** bu ish muhitida frontend repo/kodi yo'q — manzili teamlead tomonidan
> to'ldirilishi kerak (quyidagi "Aniqlashtirish kerak" bo'limiga qarang).

## 2. Arxitektura

```
Foydalanuvchi / Hermes agent
        │  (chat, dashboard)
        ▼
Hermes (Mars loyihasi, dashboard :9120)
        │  stdio (MCP)
        ▼
mcp-servers/mars_lms/server.py  ──HTTPS/JWT──▶  mars-backend-six.vercel.app
        │                                        (yoki lokal :7000)
        └── 22 tool: 10 workflow-agent + 12 yordamchi
```

- Hermes loyihasi: `hermes project list` → `* mars  Mars  [1 folder(s)]`
- MCP ulanishi: `hermes mcp test mars_lms` → `✓ Connected`, `✓ Tools discovered: 22`
- Tool nomlari Hermes ichida: `mcp__mars_lms__<tool>`

## 3. Hozir nima ishlaydi (jonli tekshirilgan)

| Imkoniyat | Holat | Dalil |
|---|---|---|
| JWT login (`lms_login`) + 401 da avtomatik re-login | ✅ | jonli backend, admin akkaunt |
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

## 4. Hozir nima ishlamaydi / cheklangan

| Muammo | Ta'sir | Yechim |
|---|---|---|
| Xabar yuborish (Telegram/SMS/email) MCP serverda yo'q | agent faqat **matn loyihasi** (`message_drafts`, `reply_drafts`) beradi | inson tasdig'idan keyin alohida integratsiya |
| Pul operatsiyalari (to'lov qabul qilish, refund, oylik to'lash) | ataylab yopilgan | faqat hisobot; amal — backend UI'da odam tomonidan |
| Ba'zi endpoint yo'q: xona bo'shligi, jadval to'qnashuvi, mentor yuklamasi | lokal hisoblanadi (guruh `schedule` parse) → noaniqlik bo'lishi mumkin | backend'ga endpoint qo'shilsa, tool'lar soddalashadi |
| Rollar: faqat `admin`/`owner` to'liq ishlaydi | `mentor`/`financeManager` da 403 | rol bo'yicha ruxsat matritsasi kerak |
| Frontend repo/manzili hujjatlashtirilmagan | jamoa konteksti to'liq emas | teamlead to'ldiradi |
| Credentials bir marta git tarixiga tushib qolgan | xavfsizlik | fayllar tracking'dan chiqarildi; parol/kalitlarni almashtirish qolgan |
| Dashboard standart porti 9119 band (gateway ichki dashboardi) | `BACKEND_PORT_IN_USE` | `run_mars_dashboard.sh` 9120 ni tanlaydi |

## 5. Aniqlashtirish kerak (teamlead to'ldiradi)

1. Frontend repo linki va deploy manzili (Vercel/Netlify).
2. `mars-backend` repo linki (hozir faqat prod URL ma'lum).
3. Nechta filial/oy live ma'lumot bilan sinovdan o'tgan.
4. Jamoa a'zolari ro'yxati (agentlarni bo'lish uchun — 2-topshiriq).

## 6. Qanday tekshirish (takrorlanadigan)

```bash
cd <repo>                                    # repo ildizi
export HERMES_HOME="$PWD" PYTHONPATH="$PWD/hermes-agent"
python -m hermes_cli.main mcp test mars_lms  # ✓ 22 tools
python mcp-servers/mars_lms/chain_demo.py    # 6-qadamli zanjir → chain_report.md
bash skills/hermes_mars_dashboard/run_mars_dashboard.sh start   # dashboard :9120
```
