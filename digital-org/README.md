# Digital Organization (AI OS) — MARS LMS v2.0.0 ustidagi AaaS qatlami

Bu papka — **7 kishilik C-level jamoa** (`agents/`, `mars-ceo` … `mars-hr`) ustiga
quriladigan **9 ta funksional AI agent** qatlami: ularning yo'riqnomalari, MCP serverlari,
skillari, xotirasi, xavfsizlik devorlari va agentlararo (A2A) aloqasi.

| Nuqta | Nima bor |
|---|---|
| **A (bugun)** | MARS LMS SaaS — 130+ REST endpoint, JWT auth; Hermes AI OS — 7 profil, `mcp-servers/mars_lms` (28 tool), `skills/` |
| **B (maqsad)** | AaaS: 9 ixtisoslashgan agent, Identity → RBAC → ABAC, Obsidian + DB (RAG) xotira, A2A iyerarxiya, Self-Improvement sikli |

## Ikki qatlamni aralashtirmaslik kerak

| Qatlam | Papka | Nima | Profil |
|---|---|---|---|
| **Odamlar** (1-topshiriq) | `agents/` | 7 a'zo — 7 C-level agent | `mars-ceo`, `mars-coo`, `mars-cfo`, `mars-cto`, `mars-cmo`, `mars-cpo`, `mars-hr` |
| **Funksiya** (2-topshiriq) | `digital-org/agents/` | 9 ish jarayoni agenti | `mars-ai-orchestrator` … `mars-ai-student` |

Ikkisi bir-birini almashtirmaydi: C-level agentlar **strategik egasi** (kim javobgar),
`digital-org` agentlari esa **jarayon ijrochisi** (qaysi ish qanday bajariladi).
Profil nomlari shu sabab `mars-ai-` prefiksi bilan ajratilgan.

## Tuzilma

```text
digital-org/
├── README.md                     # shu fayl — indeks va holat
├── install.sh                    # 9 profilni Hermes'ga o'rnatadi (--check bilan tekshirish)
├── agents/                       # 1 ta Orchestrator + 8 ta ixtisoslashgan agent
│   ├── 00-orchestrator/          #   soul.md + agents.md + workflow.md
│   ├── 01-ceo-strategist/
│   ├── 02-academic-manager/
│   ├── 03-branch-manager/
│   ├── 04-finance-payroll/
│   ├── 05-auditor-security/
│   ├── 06-mentor-assistant/
│   ├── 07-tutor-intern/
│   └── 08-student-parent/
├── mcp/
│   ├── README.md                 # 6 + 1 modulli MCP server rejasi va mavjud server bilan bog'lanish
│   ├── servers.json              # mashina o'qiydigan registr: server → endpointlar → agentlar
│   ├── verify_registry.py        # registrni jonli Swagger bilan solishtiradi
│   └── registry_report.json      # oxirgi tekshiruv: 188/188 operation topildi
├── skills/
│   └── README.md                 # 7 skill katalogi (trigger, qadam, tool, to'xtash sharti)
├── security/
│   ├── security_sandbox.py       # ishlaydigan hard guardrail (2-qavat himoya)
│   ├── audit_log.py              # Identity + observability: JSONL harakat jurnali
│   ├── rbac_matrix.json          # Identity → RBAC → ABAC matritsasi
│   ├── a2a_schema.json           # A2A xabar konverti (JSON Schema)
│   └── tests/                    # guardrail + audit testlari
├── state/
│   └── task_store.py             # A2A vazifa holati (SQLite holat mashinasi, TTL, tarix)
├── memory/
│   ├── README.md                 # 2 qatlamli xotira, chunking, hybrid RAG
│   └── vault/                    # Obsidian vault skeleti (00_system … 06_self_improve)
├── a2a/README.md                 # 4 ta biznes zanjiri (kim kimni uyg'otadi)
└── docs/…                        # topshirish hujjati: docs/yb-3110/4-digital-org.md
```

Har bir agent uchta fayldan iborat:

| Fayl | Savolga javob beradi |
|---|---|
| `soul.md` | **Kim** — xarakter, ohang, nimaga javob beradi, chegarasi |
| `agents.md` | **Nima qiladi** — vazifa, API/MCP xaritasi, hisobot, nima qilmaydi |
| `workflow.md` | **Qanday** — trigger, qadam-baqadam algoritm, xato va eskalatsiya |

`install.sh` uchtasini bitta `profiles/mars-ai-<slug>/SOUL.md` ga yig'adi — Hermes persona
va qoidalarni bitta fayldan o'qiydi (xuddi `agents/install.sh` kabi).

## Tekshirish

```bash
# 1. Xavfsizlik devorlari (haqiqiy pytest, tarmoqsiz)
./mcp-servers/mars_lms/.venv/Scripts/python.exe -m pytest digital-org/security/tests -q

# 2. Registr ↔ API spec (to'qilgan endpoint yo'qligini isbotlaydi)
./mcp-servers/mars_lms/.venv/Scripts/python.exe digital-org/mcp/verify_registry.py \
  --swagger https://mars-backend-six.vercel.app/swagger.json \
  --report digital-org/mcp/registry_report.json

# 3. Guardrail'ni qo'lda sinash (JSON stdin → qaror)
echo '{"agent":"finance-payroll","method":"POST","path":"/api/finance/salaries","args":{"amount":4500000}}' \
  | python digital-org/security/security_sandbox.py

# 3. Yangi MCP serverlar (mock backend + vault)
./mcp-servers/mars_lms/.venv/Scripts/python.exe -m pytest mcp-servers/mars_finance/tests mcp-servers/obsidian_rag/tests -q

# 4. Vault indeksi va qidiruv
./mcp-servers/mars_lms/.venv/Scripts/python.exe mcp-servers/obsidian_rag/indexer.py build \
  --vault digital-org/memory/vault --out mcp-servers/obsidian_rag/.index/vault.json

# 5. Profil holati (o'rnatilmagan bo'lsa "yo'q" ko'rsatadi)
bash digital-org/install.sh --check

# 4. JSON fayllar sintaksisi
python -c "import json;[json.load(open(f,encoding='utf-8')) for f in ['digital-org/mcp/servers.json','digital-org/security/rbac_matrix.json','digital-org/security/a2a_schema.json']];print('JSON OK')"
```

## Holat (halol)

| Bo'lak | Holat |
|---|---|
| Agent yo'riqnomalari (9 × 3 fayl) | ✅ yozilgan |
| `security_sandbox.py` + `audit_log.py` + 23 test | ✅ ishlaydi (pytest) |
| State — `task_store.py` (SQLite holat mashinasi) | ✅ 15 test |
| RBAC/ABAC matritsasi, A2A sxemasi | ✅ yozilgan |
| API registr ↔ Swagger | ✅ **188/188 operation**, 0 to'qilgan |
| Yakuniy topshiriq hujjati | ✅ `docs/yb-3110/5-aios-topshiriq.md` |
| `mcp-mars-finance` | ✅ kod: 13 tool, 19 test, guardrail 428/403 bilan |
| `mcp-obsidian-rag` | ✅ kod: 4 tool + BM25/hashed-vector indeksator, 16 test |
| Qolgan 5 MCP domen (`auth`, `branch`, `mentor`, `portal`, `analytics`) | 📋 registr (`mcp/servers.json`) — keyingi bosqich |
| Obsidian vault | ✅ skelet + `pii: none` sharti + qurilgan indeks (3 hujjat, 6 chunk) |
| Profillar | ✅ 9/9 o'rnatildi (`bash digital-org/install.sh --check`) |

Ya'ni: arxitektura, qoidalar, **birinchi domen serveri** va **xotira qatlami** tayyor.
Migratsiya davom etadi: keyingi server — `mcp-mars-branch` (eng katta endpoint guruhi).
