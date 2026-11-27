# YB-3110 · 2-topshiriq — Self-Improvement / Digital Organization / AIOS (AaaS)

**Muallif:** Rustam (nF-2781) — yakka tartibdagi ish
**Sana:** 27.11.2026 · **Muddat:** 28.11.2026, 18:00
**Repo:** https://github.com/nF-2781/Rustam-hermesi (branch `rustam`)
**Shu fayl:** `docs/yb-3110/5-aios-topshiriq.md`
**Asosiy kod:** `digital-org/`, `mcp-servers/mars_finance/`, `mcp-servers/obsidian_rag/`

---

## 0. Qisqa xulosa

MARS LMS API'sidan (OpenAPI 3.0.3, **218 path / 264 operation**) kelib chiqib, uning
ustiga **9 ta funksional agent** va **6 ta majburiy qatlam** qurildi:

| Talab | Qanday yopildi | Tekshiruv |
|---|---|---|
| **Identity** | JWT (`/api/auth/login|refresh|me`), har agent o'z tokeni, `audit_log.py` da actor | 6 test |
| **RBAC** | `security/rbac_matrix.json` + server-side `RBAC_AGENT` / `RBAC_READ_ONLY` | 19 test (finance) |
| **ABAC** | `branch_id`, `mentor_id`, `student_id`, `parent_id → child_id`, `period` | `ABAC_BRANCH` testlari |
| **State** | `state/task_store.py` — SQLite holat mashinasi, TTL, tarix | 15 test |
| **Memory** | Obsidian vault + `obsidian_rag/indexer.py` (BM25 + hashed-vector) | 16 test |
| **A2A** | `security/a2a_schema.json` + 4 zanjir + `task_id` bilan State | sxema + zanjirlar |

**Eng muhim raqam:** registrdagi **188 operation** API spec'i bilan solishtirildi —
**188 tasi topildi, 0 tasi yo'q**. Ya'ni hujjatda to'qilgan endpoint yo'q.
Jonli API'da 20 endpoint tekshirildi: **19 × 200**, 1 × 403 (owner-only), **0 × 404**.

---

## 1. A nuqta → B nuqta

| | A (bugun, ishlab turgan) | B (qurilgan qatlam) |
|---|---|---|
| Platforma | MARS LMS SaaS: 264 operation, JWT, filial izolyatsiyasi | o'zgarmaydi — API yagona haqiqat manbai |
| Boshqaruv | 7 kishilik C-level jamoa (`agents/`) | 9 funksional agent (`digital-org/agents/`) |
| Ruxsat | rol → endpoint (qo'lda) | Identity → RBAC → ABAC (matritsa + kod) |
| Xotira | sessiya + odam xotirasi | 2 qatlam: DB (API) + Obsidian vault (RAG) |
| Aloqa | odam → odam | A2A konvert + `task_id` bilan kuzatiladigan zanjir |
| Sifat | xato → og'zaki tuzatish | audit → `lessons_learned` → qoida → **kod + test** |

Ikki qatlam aralashmaydi: `agents/` — **kim javobgar** (odamlar), `digital-org/` —
**ish qanday bajariladi** (funksiyalar). Profil nomlari shu sabab `mars-ai-*`.

---

## 2. API ro'yxati: qanday olindi va tekshirildi

### 2.1 Manba — backendning o'z spec'i

| Ko'rsatkich | Qiymat |
|---|---|
| Spec | `https://mars-backend-six.vercel.app/swagger.json` |
| OpenAPI | **3.0.3**, `MARS LMS — Complete Backend, Finance & AI API` v**2.0.0** |
| Path | **218** |
| Operation (method × path) | **264** |
| Auth | JWT Bearer; `POST /api/auth/login`, `/refresh`, `GET /api/auth/me` |
| Health | `GET /api/health` → 200 |

Endpointlar **qo'lda yozilmagan**: `digital-org/mcp/servers.json` registri shu spec
asosida tuzildi, so'ng `digital-org/mcp/verify_registry.py` har yozuvni spec bilan
avtomatik solishtiradi (parametr nomi emas, marshrut shakli bo'yicha).

### 2.2 Tekshiruv natijasi (takrorlanadigan)

```bash
python digital-org/mcp/verify_registry.py \
  --swagger https://mars-backend-six.vercel.app/swagger.json \
  --report digital-org/mcp/registry_report.json
```

```text
Spec: MARS LMS — Complete Backend, Finance & AI API v2.0.0 — 218 path, 264 operation
Registr: 7 server, 188 operation — topildi 188, yo'q 0
[mcp-mars-auth] 5/5      [mcp-mars-branch] 50/50    [mcp-mars-finance] 33/33
[mcp-mars-mentor] 43/43  [mcp-mars-portal] 43/43    [mcp-mars-analytics] 14/14
[mcp-obsidian-rag] 0/0 (vault serveri — API'siz)
```

To'liq mashina o'qiydigan hisobot: `digital-org/mcp/registry_report.json`.

### 2.3 API jonli ishlayaptimi

Admin akkaunti bilan `https://mars-backend-six.vercel.app` ga login qilinib, har domendan
vakil endpoint so'raldi (javob tanasi chiqarilmadi — faqat status):

| Endpoint | Status | Endpoint | Status |
|---|---|---|---|
| `GET /api/auth/me` | 200 | `GET /api/finance/overview` | 200 |
| `GET /api/branch/me` | 200 | `GET /api/finance/salaries` | 200 |
| `GET /api/branch/overview` | 200 | `GET /api/finance/owner/mentor-earnings` | **403** (owner-only) |
| `GET /api/branch/groups` | 200 | `GET /api/ai/analytics/branch-overview` | 200 |
| `GET /api/branch/students` | 200 | `GET /api/ai/analytics/debtors-summary` | 200 |
| `GET /api/branch/payments` | 200 | `GET /api/branch/demand-stats` | 200 |
| `GET /api/branch/expenses` | 200 | `GET /api/branch/audit-logs` | 200 |
| `GET /api/branch/debtors` | 200 | `GET /api/branch/status-requests` | 200 |
| `GET /api/branch/attendance` | 200 | `GET /api/branch/waitlist` | 200 |
| `GET /api/branch/mentors` | 200 | `GET /homework` | 200 |

**Jami: 19 × 2xx, 1 × 403 (ruxsat chegarasi, marshrut mavjud), 0 × 404.**
403 — bu ham dalil: RBAC ishlayapti, endpoint bor.

### 2.4 API imkoniyati bu tizimga yetadimi

| Qatlam | API nima beradi | Yetadimi |
|---|---|---|
| Identity | login / refresh / me, JWT, rol | ✅ |
| RBAC | rol bo'yicha 403, filial admini / mentor / o'quvchi / ota-ona rollari | ✅ |
| ABAC | `branchId`, mentor/o'quvchi/ota-ona bog'lanishi, `month`/`from`-`to` davr | ✅ |
| State | resurs holatlari (`status-requests`, `attendance-confirmations`, `salaries.status`) | ✅ (+ bizning `task_id` ombori) |
| Memory | tarixiy yozuvlar (davomat, to'lov, audit-log, homework submissions) | ✅ |
| A2A | **yo'q** — API'da agentlararo kanal yo'q | ⚠️ o'zimiz quramiz (konvert + Orchestrator) |
| Event/stream | websocket/SSE yo'q, faqat polling | ⚠️ cron/polling bilan |

Ya'ni **5 qatlam API'dan to'liq oziqlanadi**, A2A transporti esa API'dan tashqarida —
shuning uchun u alohida konvert va holat ombori bilan qurildi (2.4 dagi halol cheklov).

---

## 3. Agentlar — API'dan kelib chiqib

Agentlar "o'ylab" bo'linmagan: har biri API'dagi **resurs egaligi** va **rol chegarasi**
asosida ajratilgan. Har agent faqat o'z domenidagi endpointlarni ko'radi.

| # | Agent (profil) | Daraja | MCP serverlar | Endpoint | Asosiy vazifa |
|---|---|---|---|---|---|
| 1 | `mars-ai-orchestrator` | 0 | auth, rag | 5 | marshrut, `task_id`, TTL/eskalatsiya |
| 2 | `mars-ai-ceo` | 1 | auth, finance (read-only), analytics, rag | 52 | KPI, filial foydasi, qaror |
| 3 | `mars-ai-academic` | 2 | auth, branch, analytics, rag | 69 | talab, waitlist, mentor tanlash, metodika |
| 4 | `mars-ai-branch` | 2 | auth, branch, rag | 55 | guruh, o'quvchi, transfer, zamena, akustika |
| 5 | `mars-ai-finance` | 2 | auth, finance, rag | 38 | kassa, xarajat, qarzdorlik, oylik loyihasi |
| 6 | `mars-ai-auditor` | 2 | auth, branch, analytics, rag | 69 | audit log, davomat nizosi, RBAC/ABAC nazorati |
| 7 | `mars-ai-mentor` | 3 | auth, mentor, rag | 48 | dars, davomat, uy vazifasi, kod tekshiruv |
| 8 | `mars-ai-tutor` | 3 | auth, mentor, rag | 48 | 1-ga-1 bron, intern topshiriq/Space |
| 9 | `mars-ai-student` | 3 | auth, portal, rag | 48 | portal, tasdiq, diagnostika, ota-ona |

> "Endpoint" — shu agentga ko'rinadigan operationlar soni (server registridan).
> Har agentning to'liq ro'yxati **Ilova A** da: metod + yo'l + qaysi agentlar.

**Bugun ishlaydigan MCP tool'lari** (endpoint emas, tool darajasi):

| Server | Tool | Holat |
|---|---|---|
| `mcp-servers/mars_lms` | 28 | ishlaydi (7 C-level agent uchun) |
| `mcp-servers/mars_finance` | 13 | **yangi** — guardrail bilan |
| `mcp-servers/obsidian_rag` | 4 | **yangi** — xotira |

Kontekst iqtisodi: bitta agentda ko'pi bilan ~30 tool ko'rinadi, 188 emas.

---

## 4. Identity — agent va odam kimligi

**Odam:** MARS LMS foydalanuvchisi (`admin`, `bm`, `owner`, `mentor`, o'quvchi, ota-ona) —
JWT bilan. **Agent:** Hermes profili (`mars-ai-*`) + o'z API sessiyasi.

| Qoida | Qayerda |
|---|---|
| `POST /api/auth/login` → `accessToken` + `refreshToken` + `role` + `branch` | `lms_client.py` |
| Har agent **o'z** tokeni bilan ishlaydi; boshqa agent tokeni ishlatilmaydi | `rbac_matrix.json → identity.rules` |
| Token faqat xotirada; disk/log/Obsidian'ga chiqmaydi | `lms_client.py` + `audit_log._scrub` |
| 401 → 1 marta refresh, yana 401 → odamga eskalatsiya | `LMSClient.fetch` |
| Har harakatda `agent`, `branch_id`, `task_id`, `decision` yoziladi | `security/audit_log.py` |

Audit yozuvi (JSONL, append-only) — `digital-org/state/audit.jsonl`:

```json
{"ts":"2026-11-27T14:20:03+00:00","agent":"finance-payroll","action":"create_payment",
 "method":"POST","endpoint":"/api/branch/payments","status_code":200,"decision":"ALLOW",
 "task_id":"6f1c2b9e-…","branch_id":"b1","details":{"amount":800000,"password":"***"}}
```

Testlar: `security/tests/test_audit_log.py` — 6 ta (redaksiya, PII maskalash, append-only).

---

## 5. RBAC — rol bo'yicha ruxsat

Manba: `digital-org/security/rbac_matrix.json` — 9 agent × `read` / `write` /
`approval_required` / `deny`, **default deny**.

| Agent | O'qish | Yozish | Taqiq |
|---|---|---|---|
| orchestrator | auth, health, assistant | — | finance, branch, mentor, parent |
| ceo-strategist | branch, finance/owner, analytics | faqat inson tasdig'i bilan | `DELETE`, to'lov, oylik `paid` |
| academic-manager | demand, waitlist, workload, curriculum | directions, feature-feedback | guruh yaratish, to'lov |
| branch-manager | groups, students, waitlist, transfers | groups, students, enroll, transfer, substitutions | finance, to'lov, xarajat |
| finance-payroll | finance/*, branch/payments, expenses, debtors | payments, expenses, debtors | eski `POST /api/payments` |
| auditor-security | audit-logs, attendance, workspace | attendance resolve (+`reason`) | finance, mentor yozuvi |
| mentor-assistant | mentor/*, lessons, homework | lessons, attendance, homework | finance, guruh, davomat resolve |
| tutor-intern | tutor-bookings, intern/* | bookings, submit, check-in/out | finance, groups |
| student-parent | `me`, parent→child | respond, submit, book, read | finance, branch, mentor, begona ID |

**Kodda:** har tool chaqiruvida `security_sandbox.check()`; yangi moliya serverida
qo'shimcha ikki qoida — `RBAC_AGENT` (serverga ulanmagan agent) va `RBAC_READ_ONLY`
(CEO yozuvga urinsa). Test: `test_ceo_cannot_write`, `test_unknown_agent_blocked`.

---

## 6. ABAC — atribut bo'yicha ruxsat

RBAC "qaysi rol" desa, ABAC "qaysi obyekt" deydi. O'lchovlar:
`branch_id`, `mentor_id`, `student_id`, `intern_id`, `parent_id → child_id`, `period`.

| Qoida | Amalda |
|---|---|
| Filial chegarasi | `actor_branch ≠ resource_branch` + yozuv → `ABAC_BRANCH` (403), tarmoqqa chiqmaydi |
| Mentor | faqat o'z `mentor_id` guruhlari (`/api/mentor/*`) |
| O'quvchi | faqat `/students/me/*` — ID parametri yo'q, "me" API darajasida |
| Ota-ona | faqat `parent_id → child_id` bog'lanishi |
| Intern | faqat o'z topshiriq/davomat/Space |
| Davr | `month`/`period` ko'rsatilmagan hisobot chiqarilmaydi (`list_debtors`, `list_salaries`) |

Kod: `security_sandbox.check(..., actor_branch=…, resource_branch=…)` +
`mcp-servers/mars_finance/server.py::_guard` (o'qishda ham filialni tekshiradi).
Testlar: `test_abac_blocks_foreign_branch_read`, `test_abac_branch_*`.

---

## 7. State — holat

Ikki daraja:

**a) Resurs holati** — API'ning o'zida: `status-requests.status`, `salaries.status`
(`draft|review|paid`), `attendance-confirmations`, `tutor-bookings.status`. Agent
holatni **o'zi o'ylab topmaydi**, API'dan o'qiydi.

**b) Vazifa holati (A2A)** — `digital-org/state/task_store.py`, SQLite:

```text
queued ──► running ──► done
  │           ├──► waiting_approval ──► done | failed
  │           ├──► failed ──► queued (qayta urinish)
  └──► blocked ──► queued | failed | expired
queued | running | waiting_approval ──(TTL)──► expired
```

| Xususiyat | Nega |
|---|---|
| `task_id` + `event_type` | butun zanjir bo'ylab bitta identifikator |
| `expires_at` (15 daq) | javob bo'lmasa `expired` → Orchestrator eskalatsiya qiladi |
| `approval_by` | inson tasdig'i kim tomonidan berilgani |
| `task_events` jadvali | har o'tish tarixi: `from → to`, actor, izoh |
| `attempts`, `last_error` | qayta urinish va 502/504 tahlili |
| taqiqlangan o'tish | `queued → done` rad etiladi (`ValueError`) |

Testlar: 15 ta (`state/tests/test_task_store.py`) — o'tishlar, tasdiq, TTL, qayta
urinish, qayta ochilgandan keyin saqlanish.

---

## 8. Memory — xotira

| Qatlam | Nima | Qayerda |
|---|---|---|
| Sessiya | joriy so'rov, `task_id`, token, kesh (TTL) | agent jarayoni xotirasi |
| Doimiy — fakt | MARS LMS bazasi (o'quvchi, to'lov, davomat) | faqat API orqali |
| Doimiy — bilim | Obsidian vault: qarorlar, mentor kartalari, `lessons_learned` | `digital-org/memory/vault/` |

**RAG (ishlaydigan kod):** `mcp-servers/obsidian_rag/`

```text
vault/*.md → frontmatter (pii: none shart) → ## bo'yicha chunk (≤320 so'z)
           → BM25 (k1=1.5, b=0.75) + hashed-vector (256 o'lchov) → 50/50 hybrid
```

| Qoida | Amalda |
|---|---|
| `pii: none` bo'lmasa indeksga tushmaydi | `build_index(require_pii_none=True)` + test |
| Har agent faqat o'z papkasiga yozadi | `WRITE_SCOPES` (9 agent) |
| Path traversal yo'q | `resolve_path()` — `..`, absolyut yo'l, symlink rad |
| Maxfiy qiymat yozilmaydi | `_check_secret()` — parol/token/kalit naqshi bloklanadi |

Indeks bugun: **3 hujjat, 6 chunk**; qidiruv "qarzdorlik nazorati" → `00_system/RULES.md`
birinchi natija. Testlar: 16 ta.

> Halol: embedding — **hashed bag-of-words**, semantik model emas (kalit/pul/tarmoq
> kerak emas). `hashed_vector()` ni almashtirish kifoya, `search()` interfeysi o'zgarmaydi.

---

## 9. A2A — agentlararo aloqa

Agentlar erkin matn yozmaydi: har xabar `security/a2a_schema.json` bo'yicha konvert va
**Orchestrator** orqali o'tadi.

```json
{"task_id":"6f1c2b9e-…","from_agent":"academic-manager","to_agent":"branch-manager",
 "event_type":"GROUP_LAUNCH_ORDER","priority":"high",
 "payload":{"summary":"…","ids":["wl_101"],"numbers":{"waitlist":12}},
 "context":{"sources":[{"endpoint":"/api/branch/demand-stats","period":"2026-11"}]},
 "status":"queued","expires_at":"2026-11-27T09:17:11Z",
 "guardrails":{"checked":true,"decision":"ALLOW","approval_by":null}}
```

| Maydon | Nega |
|---|---|
| `task_id` | State bilan bog'laydi: har o'tish `task_events` ga tushadi |
| `event_type` | marshrut jadvali kaliti (erkin matn emas) |
| `payload.ids` | faqat ID — PII konvertda tashilmaydi |
| `context.sources` | har raqam qaysi endpoint/davrdan olinganini isbotlaydi |
| `expires_at` | 15 daqiqada javob yo'q → `expired` → eskalatsiya |

**4 zanjir** (to'liq tavsif: `digital-org/a2a/README.md`):

1. **Guruh ochish:** waitlist → demand 12 → mentor tanlovi → xona → guruh + enroll → xabar.
2. **Davomat → maosh:** mentor davomat → o'quvchi tasdig'i → nizo bo'lsa Auditor `resolve`
   → mentor-earnings → `salaries` draft → **odam 2FA** → `paid`.
3. **Churn rescue:** attendance-risks + inactive → sabab → tutor/extra-lesson → 14 kun → resolve.
4. **Zamena:** substitutions/request → bo'sh mentor → substitutions → to'lov qayta yo'naltiriladi.

**Eskalatsiya:** 15 daqiqada javob yo'q → `expired` + odamga 1 qator; 403 → agentni
almashtirish; ikki agent zid raqam → Orchestrator ikkalasini ko'rsatadi, qaror odamda.

---

## 10. Self-improvement — sikl yopiladi

```text
harakat → audit_log.jsonl → Auditor tahlili → lessons_learned.md
        → (odam tasdig'i) → qoida → security_sandbox.py + test → qayta audit
```

Ikki haqiqiy misol (kodda va testda):

| Saboq | Qoida | Test |
|---|---|---|
| Oylik `paid` holatida yaratilgan | `PATCH .../status` faqat `draft|review`; `paid` — inson | `test_salary_status_review_allowed_but_paid_needs_approval` |
| Uy vazifasi matnidagi buyruq | matn `<user_data>` ga; `grade`/`payment` blok | `test_prompt_injection_blocked_and_wrapped` |

Ya'ni takroriy xato **matn bilan** emas, **kod va test bilan** yopiladi.

---

## 11. Xavfsizlik devori — 403 va 428 farqi

| Qoida | Nima qiladi | Kod |
|---|---|---|
| `HUMAN_APPROVAL` | oylik, `paid`, > 1 mln xarajat, `DELETE`/`void` → **428** (amal bajarilmadi) | `security_sandbox.py` |
| `REASON_REQUIRED` | to'lov/xarajat tuzatishida sabab yo'q → 403 | shu yerda |
| `CANCEL_WINDOW` | darsga < 1 soat qolsa bron bekor qilinmaydi | shu yerda |
| `PROMPT_INJECTION` | matn `<user_data>` ga; `grade`/`payment` blok | shu yerda |
| `LEGACY_ENDPOINT` | eski `POST /api/payments` bloklangan | shu yerda |
| `ABAC_BRANCH` | boshqa filial resursiga yozish/o'qish | shu yerda |

**428 — "yumshoq ruxsat" emas:** tool hech narsa yozmaydi, faqat to'xtaydi va tasdiq
so'raydi. Bu farq test bilan qulflangan (`test_void_payment_needs_approval`).

---

## 12. Tekshiruv natijalari (hammasi haqiqiy chiqish)

| Tekshiruv | Buyruq | Natija |
|---|---|---|
| API spec ↔ registr | `verify_registry.py --swagger …` | **188/188 topildi, 0 yo'q** |
| Jonli API | login + 20 GET | **19 × 200, 1 × 403, 0 × 404** |
| Guardrail | `pytest digital-org/security/tests` | **17 + 6 = 23 passed** |
| State | `pytest digital-org/state/tests` | **15 passed** |
| Moliya serveri | `pytest mcp-servers/mars_finance/tests` | **19 passed** |
| RAG | `pytest mcp-servers/obsidian_rag/tests` | **16 passed** |
| Mavjud server (regressiya) | `pytest mcp-servers/mars_lms/tests` | **16 passed** |
| MCP stdio | `tools/list` | finance **13**, rag **4** tool |
| Profillar | `bash digital-org/install.sh --check` | **9/9 tayyor** |
| Sintaksis / JSON / YAML | `py_compile`, `json.load` × 3, `yaml.safe_load` | OK |
| **Jami test** | — | **89 passed** |

---

## 13. Halol cheklovlar

1. **A2A transporti API'da yo'q** — konvert + SQLite holat ombori bizning qatlam; bu
   "to'qilgan endpoint" emas, alohida modul (`state/task_store.py`, 15 test).
2. **Event/stream yo'q** — API faqat polling beradi; A2A "real vaqt" emas, cron/trigger.
3. **Jonli E2E to'liq o'tkazilmagan** — login + 20 GET tekshirildi, lekin to'lov yozish →
   428 tasdiq → `paid` oqimi mock backend'da sinalgan (haqiqiy yozuv qilish uchun odam
   tasdig'i va ish akkaunti kerak — bu ataylab).
4. **RAG hajmi** — repo skeleti (3 hujjat) indekslandi; minglab yozuvli vault sinovi yo'q.
5. **Qolgan 5 domen MCP serveri** (`auth`, `branch`, `mentor`, `portal`, `analytics`) hali
   registr darajasida; ular uchun `mars_lms` (28 tool) ishlab turibdi.

---

## 14. Repo va tekshirish

```bash
git clone https://github.com/nF-2781/Rustam-hermesi && cd Rustam-hermesi
git checkout rustam
PY=./mcp-servers/mars_lms/.venv/Scripts/python.exe   # Windows; Linux/macOS: .venv/bin/python

$PY -m pytest digital-org/security/tests digital-org/state/tests \
                mcp-servers/mars_finance/tests mcp-servers/obsidian_rag/tests -q

$PY digital-org/mcp/verify_registry.py \
    --swagger https://mars-backend-six.vercel.app/swagger.json

bash digital-org/install.sh --check
```

| Papka | Nima |
|---|---|
| `digital-org/agents/` | 9 agent × (`soul.md`, `agents.md`, `workflow.md`) = 27 fayl |
| `digital-org/security/` | `security_sandbox.py`, `audit_log.py`, `rbac_matrix.json`, `a2a_schema.json` |
| `digital-org/state/` | `task_store.py` — holat mashinasi |
| `digital-org/memory/` | vault + qoidalar; `mcp-servers/obsidian_rag/` — indeksator |
| `digital-org/mcp/` | `servers.json`, `README.md`, `verify_registry.py`, `registry_report.json` |
| `digital-org/a2a/` | 4 zanjir, iyerarxiya, eskalatsiya |
| `digital-org/skills/` | 7 skill (trigger → qadam → to'xtash → natija) |
| `mcp-servers/mars_finance/` | 13 tool, guardrail bilan |

---

## Ilova A — agent → endpoint (spec bilan tekshirilgan)

Har jadval `digital-org/mcp/servers.json` dan avtomatik yasalgan; har yozuv
`registry_report.json` da `verified: true`. "Agentlar" ustuni — shu endpointni
ko'radigan agentlar (registrdagi server–agent bog'lanishi bo'yicha).

### A1. `mcp-mars-auth` — 5 operation

**Agentlar:** `orchestrator`, `ceo-strategist`, `academic-manager`, `branch-manager`, `finance-payroll`, `auditor-security`, `mentor-assistant`, `tutor-intern`, `student-parent`

| # | Metod | Endpoint | Spec |
|---|---|---|---|
| 1 | POST | `/api/auth/login` | ✅ |
| 2 | POST | `/api/auth/logout` | ✅ |
| 3 | GET | `/api/auth/me` | ✅ |
| 4 | POST | `/api/auth/refresh` | ✅ |
| 5 | GET | `/api/health` | ✅ |

### A2. `mcp-mars-branch` — 50 operation

**Agentlar:** `branch-manager`, `academic-manager`, `auditor-security`

| # | Metod | Endpoint | Spec |
|---|---|---|---|
| 1 | GET | `/api/branch/admins` | ✅ |
| 2 | POST | `/api/branch/admins` | ✅ |
| 3 | DELETE | `/api/branch/admins/{}` | ✅ |
| 4 | PATCH | `/api/branch/admins/{}` | ✅ |
| 5 | GET | `/api/branch/attendance` | ✅ |
| 6 | GET | `/api/branch/attendance-confirmations` | ✅ |
| 7 | POST | `/api/branch/attendance/{}/resolve` | ✅ |
| 8 | GET | `/api/branch/audit-logs` | ✅ |
| 9 | GET | `/api/branch/groups` | ✅ |
| 10 | POST | `/api/branch/groups` | ✅ |
| 11 | DELETE | `/api/branch/groups/{}` | ✅ |
| 12 | GET | `/api/branch/groups/{}` | ✅ |
| 13 | PATCH | `/api/branch/groups/{}` | ✅ |
| 14 | POST | `/api/branch/groups/{}/students` | ✅ |
| 15 | POST | `/api/branch/groups/{}/students/{}/freeze` | ✅ |
| 16 | POST | `/api/branch/groups/{}/students/{}/remove` | ✅ |
| 17 | GET | `/api/branch/me` | ✅ |
| 18 | GET | `/api/branch/noise-analytics` | ✅ |
| 19 | POST | `/api/branch/noise-incidents` | ✅ |
| 20 | PATCH | `/api/branch/noise-incidents/{}/resolve` | ✅ |
| 21 | GET | `/api/branch/overview` | ✅ |
| 22 | GET | `/api/branch/parents` | ✅ |
| 23 | POST | `/api/branch/parents` | ✅ |
| 24 | PATCH | `/api/branch/parents/{}` | ✅ |
| 25 | GET | `/api/branch/reports/groups` | ✅ |
| 26 | PATCH | `/api/branch/rooms/{}/acoustics` | ✅ |
| 27 | GET | `/api/branch/staff-accounts` | ✅ |
| 28 | POST | `/api/branch/staff-accounts` | ✅ |
| 29 | PATCH | `/api/branch/staff-accounts/{}/{}` | ✅ |
| 30 | GET | `/api/branch/students` | ✅ |
| 31 | POST | `/api/branch/students` | ✅ |
| 32 | DELETE | `/api/branch/students/{}` | ✅ |
| 33 | GET | `/api/branch/students/{}` | ✅ |
| 34 | PATCH | `/api/branch/students/{}` | ✅ |
| 35 | POST | `/api/branch/students/{}/transfer` | ✅ |
| 36 | GET | `/api/branch/students/{}/transferred-summary` | ✅ |
| 37 | GET | `/api/branch/students/{}/transfers` | ✅ |
| 38 | GET | `/api/branch/substitutions` | ✅ |
| 39 | POST | `/api/branch/substitutions` | ✅ |
| 40 | POST | `/api/branch/substitutions/{}/cancel` | ✅ |
| 41 | GET | `/api/branch/transfers` | ✅ |
| 42 | GET | `/api/branch/waitlist` | ✅ |
| 43 | POST | `/api/branch/waitlist` | ✅ |
| 44 | PATCH | `/api/branch/waitlist/{}` | ✅ |
| 45 | POST | `/api/branch/waitlist/{}/enroll` | ✅ |
| 46 | PATCH | `/api/workspace/groups/{}/schedule` | ✅ |
| 47 | GET | `/api/workspace/me` | ✅ |
| 48 | GET | `/api/workspace/overview` | ✅ |
| 49 | GET | `/api/workspace/sections/logs/export` | ✅ |
| 50 | GET | `/api/workspace/sections/{}` | ✅ |

### A3. `mcp-mars-finance` — 33 operation

**Agentlar:** `finance-payroll`, `ceo-strategist`

| # | Metod | Endpoint | Spec |
|---|---|---|---|
| 1 | GET | `/api/branch/debtors` | ✅ |
| 2 | POST | `/api/branch/debtors` | ✅ |
| 3 | GET | `/api/branch/expenses` | ✅ |
| 4 | POST | `/api/branch/expenses` | ✅ |
| 5 | DELETE | `/api/branch/expenses/{}` | ✅ |
| 6 | PATCH | `/api/branch/expenses/{}` | ✅ |
| 7 | POST | `/api/branch/expenses/{}/void` | ✅ |
| 8 | GET | `/api/branch/payments` | ✅ |
| 9 | POST | `/api/branch/payments` | ✅ |
| 10 | DELETE | `/api/branch/payments/{}` | ✅ |
| 11 | GET | `/api/branch/payments/{}` | ✅ |
| 12 | PATCH | `/api/branch/payments/{}` | ✅ |
| 13 | GET | `/api/branch/payments/{}/receipt` | ✅ |
| 14 | POST | `/api/branch/payments/{}/void` | ✅ |
| 15 | GET | `/api/branch/status-requests` | ✅ |
| 16 | POST | `/api/branch/students/{}/freeze-current` | ✅ |
| 17 | GET | `/api/branch/students/{}/payments` | ✅ |
| 18 | GET | `/api/finance/debtors` | ✅ |
| 19 | GET | `/api/finance/expenses` | ✅ |
| 20 | POST | `/api/finance/expenses` | ✅ |
| 21 | GET | `/api/finance/overview` | ✅ |
| 22 | GET | `/api/finance/owner/mentor-earnings` | ✅ |
| 23 | GET | `/api/finance/payments` | ✅ |
| 24 | POST | `/api/finance/payments` | ✅ |
| 25 | DELETE | `/api/finance/payments/{}` | ✅ |
| 26 | GET | `/api/finance/payments/{}` | ✅ |
| 27 | PATCH | `/api/finance/payments/{}/status` | ✅ |
| 28 | GET | `/api/finance/salaries` | ✅ |
| 29 | POST | `/api/finance/salaries` | ✅ |
| 30 | GET | `/api/finance/salaries/{}` | ✅ |
| 31 | PATCH | `/api/finance/salaries/{}/status` | ✅ |
| 32 | GET | `/api/finance/staff` | ✅ |
| 33 | POST | `/api/finance/staff` | ✅ |

### A4. `mcp-mars-mentor` — 43 operation

**Agentlar:** `mentor-assistant`, `tutor-intern`

| # | Metod | Endpoint | Spec |
|---|---|---|---|
| 1 | GET | `/api/intern/attendance` | ✅ |
| 2 | POST | `/api/intern/attendance/check-in` | ✅ |
| 3 | POST | `/api/intern/attendance/check-out` | ✅ |
| 4 | GET | `/api/intern/grades` | ✅ |
| 5 | GET | `/api/intern/profile` | ✅ |
| 6 | GET | `/api/intern/space` | ✅ |
| 7 | GET | `/api/intern/tasks` | ✅ |
| 8 | GET | `/api/intern/tasks/{}` | ✅ |
| 9 | GET | `/api/intern/tasks/{}/status` | ✅ |
| 10 | POST | `/api/intern/tasks/{}/submit` | ✅ |
| 11 | GET | `/api/mentor/attendance` | ✅ |
| 12 | POST | `/api/mentor/attendance` | ✅ |
| 13 | POST | `/api/mentor/code-compare` | ✅ |
| 14 | GET | `/api/mentor/earnings` | ✅ |
| 15 | GET | `/api/mentor/extra-lessons` | ✅ |
| 16 | POST | `/api/mentor/extra-lessons` | ✅ |
| 17 | POST | `/api/mentor/extra-lessons/{}/cancel` | ✅ |
| 18 | GET | `/api/mentor/groups` | ✅ |
| 19 | GET | `/api/mentor/groups/{}` | ✅ |
| 20 | GET | `/api/mentor/homework` | ✅ |
| 21 | POST | `/api/mentor/homework` | ✅ |
| 22 | GET | `/api/mentor/homework/{}` | ✅ |
| 23 | PATCH | `/api/mentor/homework/{}` | ✅ |
| 24 | PATCH | `/api/mentor/homework/{}/grade` | ✅ |
| 25 | GET | `/api/mentor/inactive-students` | ✅ |
| 26 | GET | `/api/mentor/lessons` | ✅ |
| 27 | POST | `/api/mentor/lessons` | ✅ |
| 28 | PATCH | `/api/mentor/lessons/{}/reschedule` | ✅ |
| 29 | GET | `/api/mentor/me` | ✅ |
| 30 | GET | `/api/mentor/notifications` | ✅ |
| 31 | GET | `/api/mentor/substitutions` | ✅ |
| 32 | POST | `/api/mentor/substitutions/request` | ✅ |
| 33 | POST | `/api/mentor/test-cases/run` | ✅ |
| 34 | POST | `/api/tutor-bookings` | ✅ |
| 35 | GET | `/api/tutor-bookings/my` | ✅ |
| 36 | GET | `/api/tutor-bookings/tutors` | ✅ |
| 37 | GET | `/api/tutor-bookings/workspace` | ✅ |
| 38 | DELETE | `/api/tutor-bookings/{}` | ✅ |
| 39 | PATCH | `/api/tutor-bookings/{}/status` | ✅ |
| 40 | POST | `/api/workspace/lessons` | ✅ |
| 41 | GET | `/attendance` | ✅ |
| 42 | POST | `/attendance/create` | ✅ |
| 43 | GET | `/attendance/group/{}` | ✅ |

### A5. `mcp-mars-portal` — 43 operation

**Agentlar:** `student-parent`

| # | Metod | Endpoint | Spec |
|---|---|---|---|
| 1 | GET | `/api/parent/children/{}/summary` | ✅ |
| 2 | GET | `/api/parent/me` | ✅ |
| 3 | GET | `/api/payments` | ✅ |
| 4 | GET | `/api/rating` | ✅ |
| 5 | GET | `/api/student` | ✅ |
| 6 | PUT | `/api/student` | ✅ |
| 7 | GET | `/api/student-portal/billing` | ✅ |
| 8 | POST | `/api/student-portal/login` | ✅ |
| 9 | GET | `/api/student-portal/me` | ✅ |
| 10 | GET | `/api/student-portal/payments` | ✅ |
| 11 | GET | `/api/teams` | ✅ |
| 12 | POST | `/api/teams` | ✅ |
| 13 | POST | `/parents/create` | ✅ |
| 14 | POST | `/parents/login` | ✅ |
| 15 | GET | `/parents/{}` | ✅ |
| 16 | GET | `/parents/{}/children` | ✅ |
| 17 | POST | `/parents/{}/children` | ✅ |
| 18 | GET | `/parents/{}/notifications` | ✅ |
| 19 | PATCH | `/parents/{}/notifications/{}/read` | ✅ |
| 20 | GET | `/students/me` | ✅ |
| 21 | PATCH | `/students/me` | ✅ |
| 22 | GET | `/students/me/attendance` | ✅ |
| 23 | POST | `/students/me/attendance/{}/respond` | ✅ |
| 24 | GET | `/students/me/extra-lessons` | ✅ |
| 25 | DELETE | `/students/me/extra-lessons/{}/book` | ✅ |
| 26 | POST | `/students/me/extra-lessons/{}/book` | ✅ |
| 27 | GET | `/students/me/grades` | ✅ |
| 28 | GET | `/students/me/group` | ✅ |
| 29 | GET | `/students/me/homework` | ✅ |
| 30 | POST | `/students/me/homework/{}/resubmit` | ✅ |
| 31 | PATCH | `/students/me/homework/{}/submission` | ✅ |
| 32 | POST | `/students/me/homework/{}/submit` | ✅ |
| 33 | GET | `/students/me/lessons/{}/diagnostic` | ✅ |
| 34 | POST | `/students/me/lessons/{}/diagnostic/submit` | ✅ |
| 35 | GET | `/students/me/notifications` | ✅ |
| 36 | PATCH | `/students/me/notifications/{}/read` | ✅ |
| 37 | GET | `/students/me/payments` | ✅ |
| 38 | GET | `/students/me/progress` | ✅ |
| 39 | GET | `/students/me/schedule` | ✅ |
| 40 | GET | `/students/me/space` | ✅ |
| 41 | POST | `/students/me/space/checkin` | ✅ |
| 42 | POST | `/students/me/space/quests/{}/claim` | ✅ |
| 43 | PUT | `/students/me/space/theme` | ✅ |

### A6. `mcp-mars-analytics` — 14 operation

**Agentlar:** `ceo-strategist`, `academic-manager`, `auditor-security`

| # | Metod | Endpoint | Spec |
|---|---|---|---|
| 1 | GET | `/api/ai/analytics/attendance-summary` | ✅ |
| 2 | GET | `/api/ai/analytics/branch-overview` | ✅ |
| 3 | GET | `/api/ai/analytics/debtors-summary` | ✅ |
| 4 | GET | `/api/ai/analytics/finance-summary` | ✅ |
| 5 | GET | `/api/ai/analytics/student-performance` | ✅ |
| 6 | GET | `/api/branch` | ✅ |
| 7 | GET | `/api/branch/curriculum-topic-analytics` | ✅ |
| 8 | GET | `/api/branch/demand-stats` | ✅ |
| 9 | GET | `/api/branch/feature-analytics` | ✅ |
| 10 | GET | `/api/branch/workload-planning` | ✅ |
| 11 | GET | `/api/finance/owner/mentor-earnings` | ✅ |
| 12 | GET | `/api/finance/owner/monthly-fees` | ✅ |
| 13 | GET | `/api/finance/owner/summary` | ✅ |
| 14 | GET | `/api/finance/reports/branches` | ✅ |

---

_Ilova `digital-org/mcp/servers.json` + `registry_report.json` dan avtomatik yasalgan; qo'lda kiritilgan endpoint yo'q._

