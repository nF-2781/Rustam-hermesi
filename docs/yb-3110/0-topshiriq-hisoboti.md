# YB-3110 — yakuniy hisobot

**Jamoa:** Mars (LMS)
**Team Lead:** Rustam — @rustam106 (CEO agenti, `mars-ceo`, https://github.com/ahshdhdh)
**Topshiruvchi:** @bmt_430
**Muddat:** 24.11.2026, 18:40
**Holat:** 7 rol tayinlangan, hujjatlar `origin/rustam` da. `ceo` va `cto` fayllari ustoz
tomonidan qabul qilingan; `coo` Kamollidin branchidagi ishi asosida birlashtirildi va Team Lead
o'z qabulidan o'tkazdi (§8, §10); `cfo` Islom branchidan birlashtirildi (24.11); qolgan 3 rol faylini a'zoning o'zi
yozmaguncha "bajarildi" hisoblanmaydi (§8, §11).

---

## 1. Ustoz izohlari (kfc) → qanday yopildi

| # | Izoh | Holat | Qayerda |
|---|---|---|---|
| 1 | Ro'yxatda ismlar | ✅ 7 a'zo: ism + Telegram + GitHub | `2-agent-roster.md` §2 |
| 2 | CEO o'z jamoangdan | ✅ Rustam (@rustam106) — tashqi `@jamkaILZ` butunlay olib tashlandi | `2-agent-roster.md` §1–§2 |
| 3 | GitHub linklar | ✅ har bir a'zo uchun + barcha repolar `nF-2781` | `2-agent-roster.md` §2, `1-lms-context.md` §1 |
| 4 | Frontend manzili | ✅ 8 frontend repo + 8 deploy havolasi | `1-lms-context.md` §1 |
| 5 | Parol almashtirilganini yozish | ✅ yozildi, **parolning o'zi hech qayerda yo'q** | `1-lms-context.md` §4 |
| 6 | CTO `soul.md` + `agents.md` fayl sifatida | ✅ ikkita alohida fayl, repoda commit qilingan | `agents/cto/soul.md`, `agents/cto/agents.md` |
| 7 | Jonli suhbat namunasi (4-band) | ✅ `mars-cto` profili bilan o'tkazildi | shu fayl, §7 |
| 8 | Yangi rol: Rustam — CEO, `agents/ceo/` | ✅ **qabul** (o'zi yozgan, vaqt hisobga olindi) | `agents/ceo/soul.md`, `agents/ceo/agents.md` |

## 2. Jamoa va agentlar (7 kishi — 7 agent)

| # | Ism | Telegram | GitHub | Agent | Lavozim |
|---|---|---|---|---|---|
| 1 | Rustam | @rustam106 | https://github.com/ahshdhdh | `mars-ceo` | CEO |
| 2 | Kamollidin | @k_mukhamedov | https://github.com/MukhamedovK | `mars-coo` | COO |
| 3 | Islom | @vxrnox | https://github.com/muxsimovislom98-sketch | `mars-cfo` | CFO |
| 4 | Saidabzal | @Saidabza1 | https://github.com/vmio75494-bot | `mars-cto` | CTO |
| 5 | Muhammadrizo | @rizo_x7k | https://github.com/rizo04684-sudo | `mars-cmo` | CMO |
| 6 | Muhammadsolih | @muhammad_solih13 | https://github.com/muhammadsolihtolqinxojaev13-bot | `mars-cpo` | CPO |
| 7 | Muhammadali (Chihuahua) | Chihuahua | https://github.com/muhammadali850 | `mars-hr` | HR |

Ierarxiya: **CEO → C-level → sub-agentlar** (sub-agentlar `agents.md` ichida belgilangan).

## 3. CTO fayllari (mazmun — Rustam namunasi, hozirgi egasi — Saidabzal)

| Fayl | Mazmuni | Holat |
|---|---|---|
| `agents/cto/soul.md` | agent **kim**: xarakter, ovoz ohangi, javob beradigan savollar, chegaralar, namuna | ✅ yozilgan |
| `agents/cto/agents.md` | agent **nima qiladi**: rol, hisobot zanjiri, sub-agentlar (`mcp-maintainer`, `dashboard-operator`), 7 vazifa, tool'lar, nosozlik zanjiri, nima qilmaydi, chiqish shakli | ✅ yozilgan |
| `agents/cto/charter.md` | Saidabzalning batafsil CTO charteri (17 bo'lim): kontraktlar, RBAC, risk registri, hisobot formati | ✅ birlashtirildi — lokal yo'l va ierarxiya gapi repo rosterga moslandi |

Namuna sifatida yozilgan bu ikki fayl qolgan 6 rol uchun andoza bo'ldi — hammasi bir xil formatda.

## 4. Frontend manzillari

| Repo | Deploy |
|---|---|
| `mars-admin` | https://mars-admin-beta.vercel.app |
| `mars-branch-manager` | https://mars-branch-manager.vercel.app |
| `mars-finance` | https://mars-finance-orpin.vercel.app |
| `mars-intern` | https://mars-intern.vercel.app |
| `mars-mentor` | https://mars-mentor.vercel.app |
| `mars-parent` | https://mars-parent.vercel.app |
| `mars-student` | https://mars-student.vercel.app |
| `mars-tutor` | https://mars-tutor.vercel.app |

Backend: https://mars-backend-six.vercel.app · Swagger: `/api-docs/`

## 5. Parol holati

- LMS owner akkauntining paroli **almashtirildi** va **23.11 holatiga o'zgarmadi** — jamoa shu
  parolda ishlashda davom etadi (qayta almashtirish talab qilinmadi).
- Qiymat **faqat lokal `.env`** faylida (`MARS_PHONE` / `MARS_PASSWORD`); `.env` `.gitignore` da.
- Parol repo'ga, hujjatga, commitga va chatga **yozilmagan** — `.env` git'ga qo'shilmaydi.

## 6. Tekshirish (takrorlanadigan)

```bash
cd <repo>
bash agents/install.sh --check        # → 7/7 tayyor
hermes mcp test mars_lms              # → 28 tool (22 asosiy + 6 COO: coo_login + 5 audit)
hermes -p mars-cto chat               # CTO agenti bilan suhbat
```

## 7. Jonli suhbat namunasi (topshiriqning 4-bandi)

Profil: `mars-cto` · sessiya: `20261122_171216_c2b076` · sana: 22.11.2026

```bash
$ hermes -p mars-cto chat -Q -q "Qisqa javob: sen kim va nima qilasiz?"

Men — Mars CTO, Mars LMS platformasining texnik direktori agentiman.
Backend, mars_lms MCP server, dashboard va agentlar infratuzilmasi sog'ligini
kuzataman, nosozliklarni ildizi bilan topaman.
Diagnostika, test va lokal tuzatishlarni o'zim qilaman; prod deploy faqat
odam tasdig'i bilan.
```

Namuna `soul.md` dagi shaxsiyat va chegaralar (`prod deploy — faqat odam tasdig'i bilan`)
SOUL.md orqali profilga haqiqatan yuklanganini ko'rsatadi.

> Eslatma: bir xil so'rovni platforma holati bo'yicha qayta yuborishda provayder
> `HTTP 429 — model temporarily at capacity` qaytardi (bizning kalit limiti emas).
> Shu sababli dalil sifatida birinchi muvaffaqiyatli javob keltirildi.

## 8. Ustozning oxirgi tekshiruvi (22.11) → tuzatishlar

| Tekshirilgan | Natija | Tuzatish |
|---|---|---|
| Ro'yxat va kontekst (`1-lms-context.md`, `2-agent-roster.md`) | ✅ **qabul** | — |
| `agents/cto/soul.md` | ✅ **qabul**, 1 izoh | `403` misoli olib tashlandi: endi agent rol almashtirmaydi — kerakli ruxsatni nomlab, tasdiqni odamdan oladi |
| `agents/cto/agents.md` | ✅ **qabul**, 2 izoh | 1) pul va shaxsiy ma'lumot uchun **inson tasdig'i** qoidasi qo'shildi; 2) `6 agent` → `7 agent` (profil soni ham 7) |
| `agents/ceo/agents.md` — ish zanjiri | ⚠️ izoh | 4-qadamda CTO tushib qolgan edi → `COO/CFO/CTO/CMO/CPO/HR` ga qo'shildi |
| Ro'yxatdagi “hammasi yozilgan” da'vosi | ⚠️ izoh | faqat `ceo` + `cto` (namuna) qabul qilingan. Roster, `agents/README.md` va shu hisobotda endi halol yozilgan: qolgan 5 rol fayli — skelet |
| Qolgan agentlar (CMO/CPO/HR) | ⏳ kutilmoqda | har bir a'zo **o'z faylini o'zi** yozadi/tasdiqlaydi, shundan keyingina “bajarildi” |
| CFO — Islom (`origin/islom` = `origin/mars-cfo`) | ✅ **birlashtirildi** (24.11) | `agents/cfo/` to'liq: `soul.md`, `agents.md`, 3 sub-agent, `api-contracts.md`, `hierarchy.json`; 5 tool nomi serverdagi 28 tool bilan solishtirildi; yo'q `/finance/debts` → `/api/branch/debtors`, `/api/finance/daily` → kompozit endpoint tuzatildi; `install.py/install.ps1` dublikat sifatida olinmadi |
| COO — Kamollidin (`origin/kamoliddin`) | ✅ **birlashtirildi** (23.11) | `agents/c-level/02-coo/` → `agents/coo/` strukturasiga moslandi: 5 read-only tool (`coo_login`, `coo_branch_context`, `coo_attendance_audit`, `coo_schedule_audit`, `coo_status_request_sla`, `coo_delegation_plan`), 3 sub-agent, `api-contracts.md`, `hierarchy.json`; eskirgan “CEO agent yo'q” gapi va `.env` commit'i ko'chirilmadi |
| CTO — Saidabzal (`origin/said`) | ✅ **birlashtirildi** (23.11) | repo ildizidagi `agent.md` → `agents/cto/charter.md`; lokal `C:/Users/User/OneDrive/...` yo'li va “LMS repo'da CEO/CTO yo'q” gapi rosterga moslandi |
| COO qabuli | ✅ **Team Lead qabuli** (23.11) | ustoz ko'rigi kutilmasdan, o'z qabulimizdan o'tkazildi: `install.sh --check` 7/7, 16 test, 28 MCP tool, jonli audit 6/6 (§10) |

**Mualliflik (ochiq yozilgan):** `ceo/` — Rustam o'zi yozgan (ustoz qabul qildi); `cto/` mazmuni —
Rustam namunasi (qabul qilingan, egasi Saidabzal). Qolgan 5 rol skeleti Team Lead tomonidan
yozib berilgan — a'zo o'z faylini o'zi yozib, o'z nomidan tasdiqlagachgina hisobga olinadi.

**Rol taqsimoti (22.11, Team Lead qarori):** tartib yuqoridan pastga — 1 Rustam (CEO),
2 Kamollidin (COO), 3 Islom (CFO), 4 Saidabzal (CTO), 5 Muhammadrizo (CMO),
6 Muhammadsolih (CPO), 7 Muhammadali (HR). Profil nomlari (`mars-<rol>`) va fayl tuzilishi
o'zgarmadi — faqat har bir rolning egasi almashtirildi; `install.sh` qayta ishga tushirildi.

## 9. Jamoa uchun bir qatorli ko'rsatma

```bash
git pull && bash agents/install.sh && bash agents/install.sh --check && hermes -p mars-<rol> chat
```

Har bir a'zo o'z papkasini (`agents/<rol>/`) ochib ko'radi; o'zgartirsa — qayta `install.sh`.

## 10. COO jonli audit (23.11.2026)

`mars_lms` MCP serveri stdio orqali ishga tushirildi, `coo_login` lokal `.env`
akkaunti bilan kirdi (parol o'zgartirilmadi), so'ng 5 audit tool haqiqiy backend'da
chaqirildi. Davr: `2026-11-01 … 2026-11-23`, `sla_hours=24`, `consecutive_absences=2`.
Shaxsiy ma'lumot (ism, telefon, token) chiqarilmadi.

| Tool | Lokal backend (`localhost:7000`) | Production (`mars-backend-six.vercel.app`) |
|---|---|---|
| `coo_login` | ✅ 200 | ✅ 200 |
| `coo_branch_context` | ✅ `Test Branch` (filial ID olindi) | ✅ `Test Branch` |
| `coo_attendance_audit` | ✅ 200 — 0 yozuv, qoplama to'liq | ✅ 200 — 0 yozuv, qoplama to'liq |
| `coo_schedule_audit` | ✅ 200 — 1 guruh, 0 to'qnashuv, 1 noma'lum jadval → `partial` | ✅ 200 — 2 guruh, 0 to'qnashuv, 2 noma'lum → `partial` |
| `coo_status_request_sla` | ✅ 200 — 0 `pending` so'rov | ✅ 200 — 0 `pending` so'rov |
| `coo_delegation_plan` | ✅ 200 — 3 ta `delegate_task` paketi, `dispatched=false` | ✅ 200 — 3 ta paket |

Xulosa: **6/6 tool xatosiz javob berdi**, filial chegarasi va o'qish-only rejim
saqlandi. Ma'lumot bo'shligi (davomat/status yozuvi yo'q, jadval o'qilmadi) — bu
"muammo yo'q" degani emas; hisobotda `partial`/`unavailable` deb qaytdi. Bu test
filialida tekshirish uchun ma'lumot yo'q, shuning uchun raqamli xulosa berilmadi.

## 11. A'zolar branchlari va birlashtirish holati (24.11.2026)

`git fetch --all` dan keyingi holat. Har bir a'zo o'z branchiga push qilgan; quyida
nima olingani va nimasi olinmagani ko'rsatilgan.

| A'zo | Branch | Hissa | Holat |
|---|---|---|---|
| Islom (CFO) | `islom`, `mars-cfo` | `agents/cfo/` (soul, agents, api-contracts, hierarchy, 3 sub-agent), `docs/3-cfo-agent.md`, `skills/mars-cfo-agent/` | ✅ birlashtirildi (24.11) |
| Kamollidin (COO) | `kamoliddin` | `agents/c-level/02-coo/`, `mcp-servers/mars_lms` COO tool'lari | ✅ birlashtirildi (23.11) + 24.11 dagi PII qoidasi va ierarxiya tuzatishi olindi |
| Saidabzal (CTO) | `said` | `agent.md` → `agents/cto/charter.md` | ✅ birlashtirildi (23.11), yangi commit yo'q |
| Rizo (CMO/MCP) | `mars-mcp-server` | `mars-mcp-server/` — MCP server va finance tool'lari | ✅ allaqachon `mcp-servers/mars_lms` asosi (branch to'liq merj qilingan); CMO agenti hali yo'q |
| — | `main` | Kamollidin `agents/c-level/*` konsolidatsiyasi (CPO/HR evallari, registry) | ⏳ olinmadi: CPO/HR a'zolari o'z ishini tugatgach ko'chiriladi |

Olinmagan narsalar (ataylab): branchlardagi `.env`, `profiles/*/.env`, `state.db`,
`shared-state.db`, `logs/`, `spawn-ledger.json`, `cache/` — bular ishchi muhit
holati, agent ta'rifi emas. Islomning `agents/install.py` va `install.ps1` i ham
olinmadi: repoda bitta kanonik o'rnatuvchi `agents/install.sh` bor, ikkinchisi bilan
ikki xil profil yasash xavfi bor.

## 12. CFO jonli tekshiruvi (24.11.2026)

Birlashtirilgandan keyin Islomning CFO zanjiri haqiqiy backend'da bir marta
chaqirildi (`lms_login` + finance tool'lari, lokal `.env`, faqat o'qish).
Shaxsiy ma'lumot chiqarilmadi.

| Tool | Natija |
|---|---|
| `lms_login` | ✅ sessiya ochildi |
| `daily_finance_report(compare=true)` | ✅ 200 — 2026-11, kassa qoldig'i 1 550 000 UZS, 6 oylik trend |
| `get_finance_report()` | ✅ 200 — oylik `finance` bloki (tushum, xarajat, sof foyda) |
| `get_debts(limit=3)` | ✅ 200 — 0 qarzdor, `total_remaining = 0` |
| `get_payments(page=1, limit=3)` | ✅ 200 — 2 ta to'lov yozuvi |
| `debt_control_agent(min_days_overdue=30)` | ✅ 200 |

Xulosa: CFO hujjatlarida yozilgan tool nomlari serverdagi 28 tool bilan bir xil
ishlaydi; `agents/install.sh` dan keyin `mars-cfo` profili 12 953 bayt SOUL.md bilan
o'rnatildi. Test filialida qarzdorlik yo'q, shuning uchun "qarz ishi" tomoni faqat
bo'sh javob bilan tasdiqlandi.
