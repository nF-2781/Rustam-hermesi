# mcp-obsidian-rag — vault xotirasi va hybrid qidiruv

`digital-org/memory/README.md` da tasvirlangan 2 qatlamli xotiraning **ikkinchi qismi**
ishlaydigan kodga aylandi: Obsidian vault (Markdown) + lokal indeks.

Tashqi embedding API, kalit va internet kerak emas: indeks `BM25` + `hashing-vector`
(bag-of-words'ni 256 o'lchovga hash qilish) bilan quriladi.

```text
digital-org/memory/vault/*.md
        │  indexer.build_index()   pii: none shart
        ▼
mcp-servers/obsidian_rag/.index/vault.json     (chunk + tf + 256 o'lchovli vektor)
        │  indexer.search()
        ▼
vault_search → top-K chunk (hybrid: BM25 0.5 + vector 0.5)
```

## Tool'lar (4)

| Tool | Nima qiladi | Chegara |
|---|---|---|
| `vault_search` | hybrid qidiruv, top-K chunk | faqat `pii: none` fayllar indeksda |
| `vault_read` | `.md` o'qish | `..`, absolyut yo'l, boshqa kengaytma — rad |
| `vault_append` | fayl oxiriga yozish | faqat agentning o'z papkasi + secret filtr |
| `vault_lessons_add` | `06_self_improve/lessons_learned.md` | umumiy fayl, matn filtri bilan |

## Yozuv papkalari (WRITE_SCOPES)

| Agent | Papka |
|---|---|
| `ceo-strategist` | `01_ceo/` |
| `academic-manager`, `mentor-assistant`, `tutor-intern` | `02_academic/` |
| `branch-manager` | `03_branch/` |
| `finance-payroll` | `04_finance/` |
| `auditor-security` | `05_audit/`, `06_self_improve/` |
| `orchestrator`, `student-parent` | yozmaydi (faqat o'qiydi) |

## Chunking va PII

- Frontmatter: `path`, `agent`, `branch_id`, `period`, `updated_at`, `source`, `pii`.
- `pii: none` bo'lmasa fayl **butunlay** indeksga tushmaydi (test bilan qat'iy).
- `##` sarlavhasi bo'yicha chunk; 320 so'zdan uzun bo'lak kesiladi.
- Chunk matni 1 200 belgigacha qaytadi (kontekstni to'ldirmaslik uchun).

## Nima uchun "hashed-vector", "embedding" emas

Haqiqiy embedding modeli (OpenAI, bge, e5) yaxshiroq ma'no qidiruvi beradi, lekin
kalit, pul va tarmoq talab qiladi. Bu yerda maqsad — **ishlaydigan, tekshiriladigan
poydevor**: BM25 aniq ID/summa/guruh nomini topadi, hashed-vector esa so'z birgaligini
qo'shadi. Kelajakda `indexer.hashed_vector()` ni embedding chaqiruvi bilan almashtirish
kifoya — `search()` interfeysi o'zgarmaydi.

## Buyruqlar

```bash
PY=./mcp-servers/mars_lms/.venv/Scripts/python.exe

# Indeks qurish (repo vault'i)
$PY mcp-servers/obsidian_rag/indexer.py build \
    --vault digital-org/memory/vault --out mcp-servers/obsidian_rag/.index/vault.json

# Qidiruv (CLI)
$PY mcp-servers/obsidian_rag/indexer.py search "qarzdorlik nazorati" \
    --index mcp-servers/obsidian_rag/.index/vault.json --top 5

# Statistika
$PY mcp-servers/obsidian_rag/indexer.py stats --index mcp-servers/obsidian_rag/.index/vault.json

# Testlar
$PY -m pytest mcp-servers/obsidian_rag/tests -q
```

Hermes `config.yaml`:

```yaml
mcp_servers:
  obsidian_rag:
    command: C:/Users/user/Documents/Hermes-2/mcp-servers/mars_lms/.venv/Scripts/python.exe
    args: [C:/Users/user/Documents/Hermes-2/mcp-servers/obsidian_rag/server.py]
    env:
      OBSIDIAN_VAULT: C:/Users/user/Documents/Hermes-2/digital-org/memory/vault
      PYTHONIOENCODING: utf-8
    enabled: true
```

Indeks fayli `.index/` ichida — git'ga kirmaydi (`.gitignore`).

## Holat (halol)

- Indeks, chunking, PII-shart, papka chegarasi va secret filtr — **testlar bilan** tekshirilgan.
- Jonli Obsidian vault (minglab yozuv) bilan katta hajmda sinalmagan; hozir repo skeleti
  (3 fayl) indekslanadi.
- Haqiqiy embedding modeli ulanmagan — bu ongli qaror (yuqorida sabab).
