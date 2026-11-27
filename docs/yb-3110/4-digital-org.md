# YB-3110 — Digital Organization (AI OS) arxitekturasi

**Loyiha:** MARS LMS v2.0.0 + Hermes AI OS | **Sana:** 27.11.2026
**A nuqta:** ishlab turgan MARS LMS SaaS (130+ REST endpoint) + 7 kishilik C-level agent jamoasi
**B nuqta:** shu SaaS ustiga qurilgan **AaaS** qatlami — 9 funksional agent, Identity/RBAC/ABAC,
Obsidian + DB (RAG) xotira, A2A iyerarxiya, Self-Improvement

**Fayllar:** `digital-org/` (arxitektura, 9 agent, himoya, MCP rejasi, xotira), `mcp-servers/mars_finance/`,
`mcp-servers/obsidian_rag/`
**Tekshiruv:** `security_sandbox.py` — **17 test**, `mars_finance` — **19 test**,
`obsidian_rag` — **16 test** (jami **52**, pastda §8)

---

## 1–2. Agentlar ro'yxati va real API xaritasi

Har agent ishni `POST /api/auth/login` → `POST /api/auth/refresh` → `GET /api/auth/me`
bilan boshlaydi: token, rol va `branchId` tasdiqlanmasa hech qanday amal bajarilmaydi.

| # | Agent (profil) | Daraja | Mas'uliyat | Fayl |
|---|---|---|---|---|
| 1 | **Orchestrator** (`mars-ai-orchestrator`) | 0 — markaz | marshrutizatsiya, kontekst, cron, A2A kuzatuv | `digital-org/agents/00-orchestrator/` |
| 2 | **CEO Strategist** (`mars-ai-ceo`) | 1 — C-level | KPI, filial foydasi, yangi yo'nalish qarori | `…/01-ceo-strategist/` |
| 3 | **Academic Manager** (`mars-ai-academic`) | 2 — boshqaruv | talab, waitlist, mentor tanlash, metodika | `…/02-academic-manager/` |
| 4 | **Branch Manager** (`mars-ai-branch`) | 2 — operatsiya | guruh, o'quvchi, transfer, zamena, akustika | `…/03-branch-manager/` |
| 5 | **Finance & Payroll** (`mars-ai-finance`) | 2 — moliya | tushum, xarajat, kassa, qarzdorlik, oylik | `…/04-finance-payroll/` |
| 6 | **Auditor & Security** (`mars-ai-auditor`) | 2 — nazorat | audit log, nizo, RBAC/ABAC, observability | `…/05-auditor-security/` |
| 7 | **Mentor Assistant** (`mars-ai-mentor`) | 3 — ijro | jadval, davomat, uy vazifasi, kod tekshiruv | `…/06-mentor-assistant/` |
| 8 | **Tutor & Intern** (`mars-ai-tutor`) | 3 — ijro | 1-ga-1 bron, intern topshiriq/Space | `…/07-tutor-intern/` |
| 9 | **Student & Parent** (`mars-ai-student`) | 3 — mijoz | portal, tasdiq, diagnostika, ota-ona | `…/08-student-parent/` |

Har agentning `agents.md` faylida **to'liq endpoint ro'yxati** bor (jami ~130 ta, Swagger
bo'yicha guruhlangan). Asosiy taqsimot:

| Agent | Asosiy endpoint guruhlari |
|---|---|
| Orchestrator | `/api/auth/*`, `/api/health`, `/api/assistant`, `/api/chat` |
| CEO | `/api/branch`, `/api/finance/owner/*`, `/api/finance/reports/*`, `/api/ai/analytics/*` |
| Academic | `demand-stats`, `waitlist`, `workload-planning`, `curriculum-topic-*`, `attendance-risks`, `inactive-students`, `feature-feedback` |
| Branch | `groups`, `students`, `waitlist`, `transfers`, `substitutions`, `noise-*`, `rooms/{id}/acoustics`, `staff-accounts`, `parents` |
| Finance | `/api/finance/{payments,expenses,salaries,debtors}`, `/api/branch/{payments,expenses,debtors}`, `status-requests` |
| Auditor | `audit-logs`, `attendance-confirmations`, `/api/branch/attendance/{id}/resolve`, `/api/workspace/*` |
| Mentor | `/api/mentor/*`, `/attendance/*`, `code-compare`, `test-cases/run`, `extra-lessons` |
| Tutor/Intern | `/api/tutor-bookings/*`, `/api/intern/*` |
| Student/Parent | `/students/me/*`, `/api/student-portal/*`, `/api/parent/*`, `/parents/*` |

**Muhim:** agentlarga **o'chirish** huquqi berilmagan. `DELETE` faqat inson tasdig'i bilan,
sabab yozilgan holda (`security/rbac_matrix.json` → `deny` / `approval_required`).

## 3. MCP serverlar va skillar

Bitta ulkan server o'rniga **6 domen serveri + 1 xotira serveri**: har agent faqat 2–3
server ko'radi (kontekst iqtisodi, xavfsizlik). Registr: `digital-org/mcp/servers.json`.

| Server | API | Kim ulanadi |
|---|---|---|
| `mcp-mars-auth` | `/api/auth/*`, `/api/health` | barchasi |
| `mcp-mars-branch` | `/api/branch/*`, `/api/workspace/*` | Branch, Academic, Auditor |
| `mcp-mars-finance` | `/api/finance/*`, `branch/{payments,expenses,debtors}` | Finance, CEO (faqat GET) |
| `mcp-mars-mentor` | `/api/mentor/*`, `/attendance/*`, tutor, intern | Mentor, Tutor |
| `mcp-mars-portal` | `/students/me/*`, `/api/parent/*`, `/parents/*` | Student & Parent |
| `mcp-mars-analytics` | `/api/ai/analytics/*`, `demand-stats`, `curriculum-topic-*` | CEO, Academic, Auditor |
| `mcp-obsidian-rag` | vault (Markdown + vector/BM25) | hammasi (o'z papkasi) |

**Bajarilgan migratsiya (2026-11-27):** `mcp-mars-finance` — 13 tool, `security_sandbox`
bilan bog'langan (403 = blok, 428 = inson tasdig'i kerak), CEO uchun read-only;
`mcp-obsidian-rag` — 4 tool + BM25/hashed-vector indeksator. Ikkisi stdio orqali
tekshirilgan (13 va 4 tool ro'yxatga chiqadi). Qolgan 5 domen — registr darajasida.

7 skill (`digital-org/skills/README.md`): `skill-group-launch`, `skill-smart-grading`,
`skill-dispute-payroll`, `skill-churn-rescue`, `skill-debt-collection`,
`skill-acoustic-shield`, `skill-ceo-briefing` — har birida trigger, qadamlar,
**to'xtash sharti** va natija yozilgan.

## 4. Instructions — 3 fayl

| Fayl | Mazmun |
|---|---|
| `soul.md` | kim, ohang, nimaga javob beradi, chegaralar, namuna |
| `agents.md` | vazifalar, API/MCP xaritasi, hisobot zanjiri, nima qilmaydi |
| `workflow.md` | trigger jadvali, qadam-baqadam algoritm, xato/eskalatsiya, o'lchov |

Umumiy operatsion sikl: har soatda health + nizo skani; 09:00 kassa va filial tayyorgarligi;
20:00 retention va Space; oy oxirida nizo → maosh → keyingi oy rejasi.

O'rnatish (majburiy emas): `bash digital-org/install.sh` → 9 profil (`mars-ai-*`),
har biri alohida `SOUL.md` bilan.

## 5. Memory — 2 qatlam + RAG

- **Sessiya xotirasi:** joriy so'rov, `task_id`, faol token, API kesh (TTL). Agent
  `sleep` bo'lganda o'chadi; faqat xulosa doimiy xotiraga ko'chadi.
- **Doimiy xotira:** (a) MARS LMS bazasi — haqiqat manbai, faqat API orqali;
  (b) Obsidian vault — xulosalar, sifat kartalari, `lessons_learned`
  (`00_system` … `06_self_improve`, har agent faqat o'z papkasiga yozadi).
- **SAC:** tizim prompti (~0.4%) + skill ro'yxati (~1%) + MCP sxemalari (2–4%) oldindan.
- **Hybrid RAG:** `##` bo'yicha chunking (200–400 token) → vector top-8 + BM25 top-5 →
  3–5 chunk. BM25 aniq ID/guruh/summa uchun, vector ma'no uchun.
  **Kod:** `mcp-servers/obsidian_rag/indexer.py` (BM25 k1=1.5/b=0.75 + 256 o'lchovli
  hashed-vector, 50/50). Haqiqiy embedding modeli ataylab ulanmagan — kalit/pul/tarmoq
  talab qiladi; `hashed_vector()` ni almashtirish kifoya, `search()` interfeysi o'zgarmaydi.
- **PII filtri:** chunkda `pii: none` bo'lmasa indeksga tushmaydi. Test bilan qat'iy:
  `pii: contains` va metadatasiz fayl indeksga umuman kirmaydi.

## 6. Rules, xavfsizlik, observability

**1-qavat — Identity → RBAC → ABAC** (`security/rbac_matrix.json`): JWT, `branchId`
chegarasi, mentor/o'quvchi/ota-ona/intern uchun `me` va `child_id` qoidasi, default `deny`.

**2-qavat — kod devori** (`security/security_sandbox.py`, ishlaydi):

| Qoida | Nima bloklaydi |
|---|---|
| `HUMAN_APPROVAL` | oylik yaratish, `status=paid`, > 1 000 000 UZS xarajat, har qanday `DELETE`/`void` |
| `REASON_REQUIRED` | to'lov/xarajatni o'zgartirishda bo'sh `reason` |
| `CANCEL_WINDOW` | darsga 1 soatdan kam qolganda bron bekor qilish (vaqt noma'lum bo'lsa ham) |
| `PROMPT_INJECTION` | matndagi "oldingi qoidalarni unut", "100 ball" → `<user_data>` + `grade/payment` blok |
| `LEGACY_ENDPOINT` | eski `POST /api/payments` |
| `ABAC_BRANCH` | boshqa filial resursiga yozish |

**Observability:** har harakat JSON log (`ts`, `agent`, `task_id`, `tool`, `status`,
`branch_id`, `thinking_summary`, `violations`, `approval`) → Auditor → anomaliya →
`06_self_improve/lessons_learned.md` → qoida → kod + test. Sikl yopiladi.

## 7. A2A iyerarxiya va 4 zanjir

Konvert: `security/a2a_schema.json` (`task_id`, `from_agent`, `to_agent`, `event_type`,
`payload`, `priority`, `context.sources`, `expires_at`, `guardrails`).
To'liq tavsif: `digital-org/a2a/README.md`.

1. **Guruh ochish:** waitlist → demand 12 → mentor tanlovi → `GROUP_LAUNCH_ORDER` →
   xona + guruh + enroll → o'quvchi/ota-ona + mentor + finance xabari.
2. **Davomat → maosh:** `attendance` → o'quvchi tasdig'i → nizo bo'lsa Auditor `resolve` →
   `mentor-earnings` (14 551 UZS) → `salaries` draft → **odam 2FA** → paid.
3. **Churn rescue:** `attendance-risks` + `inactive-students` → sabab → tutor/extra-lesson →
   ota-ona xabari → 14 kun → `resolve`.
4. **Zamena:** `substitutions/request` → bo'sh mentor → `substitutions` → to'lov qayta
   yo'naltiriladi → guruhga xabar.

## 8. Tekshiruv natijalari

| Tekshiruv | Buyruq | Natija |
|---|---|---|
| Guardrail testlari | `pytest digital-org/security/tests -q` | **17 passed** |
| Moliya serveri testlari | `pytest mcp-servers/mars_finance/tests -q` | **19 passed** |
| RAG testlari | `pytest mcp-servers/obsidian_rag/tests -q` | **16 passed** |
| Python sintaksisi | `python -m py_compile …` (3 modul) | OK |
| JSON sxemalar | `json.load` × 3 (`servers.json`, `rbac_matrix.json`, `a2a_schema.json`) | OK |
| Installer sintaksisi | `bash -n digital-org/install.sh` | OK |
| Agent fayllari | 9 × (`soul.md` + `agents.md` + `workflow.md`) | 27/27 mavjud |
| Profillar | `bash digital-org/install.sh --check` | **9/9 tayyor** |
| MCP stdio handshake | `tools/list` (finance + rag) | 13 + 4 tool |
| Vault indeksi | `indexer.py build` | 3 hujjat, 6 chunk, 0 o'tkazib yuborilgan |

**Halol holat:** `mcp-mars-finance` (13 tool) va `mcp-obsidian-rag` (4 tool) kodga
aylandi va mock/vault testlari bilan tekshirilgan. Lekin:

1. Guardrail yo'li **mock backend** bilan sinalgan; jonli backend'da to'liq oqim
   (login → to'lov → 428 tasdiq → paid) hali o'tkazilmagan — haqiqiy akkaunt va
   tasdiqlash oynasi kerak.
2. RAG indeksi repo skeletida (3 hujjat) qurilgan; haqiqiy Obsidian vault (minglab
   yozuv) bilan hajm sinovi yo'q.
3. Embedding — hashed bag-of-words, semantik model emas (ongli qaror: kalitsiz ishlaydi).
4. Qolgan 5 domen serveri (`auth`, `branch`, `mentor`, `portal`, `analytics`) hali
   faqat registrda; `mars_lms` (28 tool) ular uchun ishlab turibdi.

Ya'ni arxitektura + himoya + **birinchi domen** + **xotira** ishlaydi; migratsiyaning
qolgan yarmi va jonli E2E — keyingi bosqich.

## 9. 1-topshiriq bilan bog'lanish

| 1-topshiriq (odamlar) | 2-topshiriq (funksiyalar) |
|---|---|
| 7 a'zo — 7 C-level agent (`mars-ceo` … `mars-hr`) | 9 ish jarayoni agenti (`mars-ai-*`) |
| "Kim javobgar?" | "Ish qanday bajariladi?" |
| `agents/install.sh` | `digital-org/install.sh` |

Ikkisi zid emas: C-level agent — **egasi**, funksional agent — **ijrochi**. Masalan
CFO (Islom) `mars-cfo` orqali strategik moliyani kuzatadi, `mars-ai-finance` esa kunlik
kassa va oylik loyihasini tayyorlaydi.
