# WORKFLOW — CEO Strategist

## Triggerlar

| Vaqt / hodisa | Amal |
|---|---|
| Dushanba 09:00 | Haftalik brifing (skill `skill-ceo-briefing`) |
| Har oy 15 va oxirgi kun | Prognoz va reja bajarilishi |
| `academic-manager` → `DEMAND_ALERT` | Yangi yo'nalish/filial tahlili |
| `auditor-security` → `RISK_ALERT` | Xavf ro'yxatiga qo'shish va brifingga chiqarish |
| Odam so'rovi | 1 sahifalik javob |

## Algoritm (haftalik brifing)

```text
1. Auth: POST /api/auth/login → GET /api/auth/me (rol: owner/admin).
2. Pul:     GET /api/finance/owner/summary?period=<oy>
            GET /api/finance/reports/branches?period=<oy>
            GET /api/finance/overview?period=<oy>
3. O'sish:  GET /api/ai/analytics/branch-overview
            GET /api/ai/analytics/debtors-summary
4. Sifat:   GET /api/ai/analytics/attendance-summary
            GET /api/branch/feature-analytics
5. Solishtir: o'tgan davr bilan farq → sabab 1 qator (guruh yopilgan, narx, davomat).
6. Obsidian: vault_search("brifing", folder="01_ceo", k=3) — o'tgan hafta bilan izchillik.
7. Yoz:      3 xulosa + 3 xavf + 3 tavsiya (kim/qachon) + keyingi tekshiruv sanasi.
8. Saqla:    vault_append("01_ceo/weekly/<YYYY-WW>.md", hisobot).
```

## Qoida tekshiruvlari

| Tekshiruv | Amal |
|---|---|
| Har raqam yonida endpoint/davr bormi? | yo'q bo'lsa — raqam chiqarilmaydi |
| Prognoz `forecast: true` bilan belgilanganmi? | yo'q bo'lsa — qayta yoziladi |
| `POST`/`PATCH`/`DELETE` bormi? | `security_sandbox` dan o'tkaziladi, pul bo'lsa odam tasdig'i |
| Ikki manba zidmi? | ikkalasi ko'rsatiladi, sabab izohlanadi |

## Xato holatlari

| Holat | Amal |
|---|---|
| 403 (owner emas) | faqat o'z filiali kesimini ko'rsat, cheklovni ayt |
| Bo'sh davr (yangi oy) | "ma'lumot hali yo'q" + o'tgan davr bilan solishtirish |
| Analytics 5xx | asosiy finance endpointlar bilan hisobot, "analitika ishlamadi" izohi |
| Timeout | brifingni qisman chiqarish, yetishmagan bo'limni belgilash |

## O'lchov

- Brifing tayyorlash vaqti (maqsad < 60 s) va chiqish uzunligi (1 sahifa).
- Tavsiyalarning bajarilish foizi (keyingi haftada tekshiriladi).
