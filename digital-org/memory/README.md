# Xotira — 2 qatlam va RAG

Agent "hamma narsani eslab qolmaydi": real faktlar bazada, xulosalar Obsidian'da,
ishlayotgan kontekst esa sessiyada. Uchtasi aralashtirilmaydi.

## A. Sessiya xotirasi (vaqtinchalik)

| Nima saqlanadi | Qayerda | Qachon o'chadi |
|---|---|---|
| joriy so'rov, `task_id`, faol `access_token` | agent jarayoni xotirasi | agent `sleep` bo'lganda |
| oraliq API javoblari (kesh) | xotira (TTL 5–15 daqiqa) | TTL tugaganda |
| tool natijalari | kontekst oynasi | navbatdagi so'rovda qisqartiriladi |

Qoida: sessiya tugaganda faqat **xulosa** (qaror, sabab, havola) doimiy xotiraga
ko'chiriladi. Xom API javobi Obsidian'ga yozilmaydi — u bazada bor.

## B. Doimiy xotira

1. **MARS LMS backend (MongoDB) — haqiqat manbai.** O'quvchi balansi, to'lov tarixi,
   davomat, baholar faqat API/MCP orqali o'qiladi va yoziladi. Obsidian'da nusxa
   saqlanmaydi (dublikat = ziddiyat manbai).
2. **Obsidian vault — kontekst va saboq.** Agent xulosalari, mentor sifat kartalari,
   biznes qoidalari, `lessons_learned`. Papka tuzilmasi qat'iy:

```text
mars-ai-vault/
├── 00_system/         SOUL.md, AGENTS.md, RULES.md, RBAC_matrix.json (nusxa emas — havola)
├── 01_ceo/            haftalik brifinglar, KPI trendlar, filial strategiyasi
├── 02_academic/       mentor sifat kartalari, metodik xatolar, talab prognozlari, retention
├── 03_branch/         xona akustika xaritasi, zamena tarixi, kundalik operatsiyalar
├── 04_finance/        kassa xulosalari, qarzdorlik dinamikasi, maosh loyihalari
├── 05_audit/          observability loglar, nizo yechimlari, xavfsizlik hodisalari
└── 06_self_improve/   lessons_learned.md (xato → sabab → qoida)
```

Yozish huquqi: har agent faqat **o'z papkasiga** yozadi (`05_audit` — Auditor,
`06_self_improve` — Auditor/Orchestrator). Boshqasining papkasini o'qish mumkin,
o'zgartirish — yo'q.

## C. Kontekst yuklash: SAC + Hybrid RAG

### 1. Static Context (SAC) — oldindan yuklanadi

| Bo'lak | Taxminiy hajm |
|---|---|
| tizim prompti (soul + asosiy qoidalar) | ~0.4% kontekst |
| skilllar ro'yxati (faqat sarlavha + trigger) | ~1% |
| agentga ulangan MCP sxemalari (2–3 server) | ~2–4% |

Ya'ni agent uyg'onganda "o'zini" biladi, lekin butun vault'ni o'qimaydi.

### 2. Dinamik qidiruv (Hybrid RAG)

```text
so'rov
  ├── 1) chunking:    Markdown → ## sarlavha bo'yicha bo'lak (200–400 token, 15% overlap)
  ├── 2) vector:      embedding → eng yaqin 8 chunk (ma'no bo'yicha)
  ├── 3) BM25:        aniq ID, telefon, guruh (Frontend-106), summa → 5 chunk
  └── 4) rerank:      dublikat olib tashlanadi, 3–5 chunk kontekstga qo'shiladi
```

Nega ikkisi kerak: vektor "qarzdorlik siyosati" ni topadi, BM25 esa aynan
`Frontend-106` yoki `14 551` kabi aniq qiymatni topadi. Faqat vektor bilan ID qidirish
ishlamaydi; faqat BM25 bilan "ma'no" yo'qoladi.

### 3. Chunk metadata (majburiy)

```yaml
---
path: 02_academic/mentor-cards/d-yusupova.md
agent: academic-manager
branch_id: bran_01
period: 2026-11
updated_at: 2026-11-27
source: manual | agent | api
pii: none
---
```

`pii: none` bo'lmasa chunk indeksga tushmaydi — bu PII sizib chiqishining oldini oladi.

## D. Self-Improvement sikli

1. Har qoida buzilishi / xato → `06_self_improve/lessons_learned.md` ga yozuv:
   **nima bo'ldi → sabab → yangi qoida taklifi → kim tasdiqladi**.
2. Auditor oyiga bir marta takrorlangan saboqlarni `00_system/RULES.md` ga ko'chirishni
   taklif qiladi (odam tasdig'i bilan).
3. Qoida kodga aylansa — `security/security_sandbox.py` ga test bilan qo'shiladi.
   Shu tarzda "oqibat" sikli yopiladi: xato → saboq → qoida → kod → test.

## E. Nima saqlanmaydi (qat'iy)

- parol, token, API kalit, `.env` qiymati;
- o'quvchi telefoni, uy manzili, ota-ona shaxsiy ma'lumoti;
- to'liq API javobi (faqat xulosa + havola);
- boshqa filial ma'lumoti (ABAC).
