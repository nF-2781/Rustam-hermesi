# WORKFLOW — Orchestrator

## Triggerlar

| Vaqt / hodisa | Amal |
|---|---|
| Har soatda (cron `0 * * * *`) | `GET /api/health` → nosozlik bo'lsa `auditor-security` + odam |
| Har kuni 08:50 | Ertalabki zanjirni tayyorlash: `finance-payroll`, `branch-manager` |
| Har kuni 19:50 | Kechki zanjir: `student-parent`, `academic-manager` |
| Oy oxiri (28–31) | `auditor-security` → `finance-payroll` → `academic-manager` |
| Foydalanuvchi so'rovi | tasniflash → yo'naltirish |
| Agentdan `blocked` | eskalatsiya (odam) |

## Algoritm

```text
1. So'rovni ol: matn, foydalanuvchi (JWT → role, branchId), til.
2. `GET /api/auth/me` — rolni tasdiqla. 401 → qayta login (1 marta), keyin to'xta.
3. event_type ni aniqlang:
   - kalit so'z: to'lov/qarz/oylik → PAYROLL_*; guruh/xona/zamena → BRANCH_*;
     davomat/dars/uy vazifasi → LESSON_*; o'quvchi/ota-ona → PORTAL_*;
     nizo/audit/qoida → AUDIT_*; KPI/filial/foyda → STRATEGY_*.
   - aniqlanmasa: bitta aniqlashtiruvchi savol (taxmin qilma).
4. Kontekst: vault_search(query, folder=tegishli papka, k=5) + davr (oy/kun) + filial.
5. A2A konvertni yig' (schema: security/a2a_schema.json), task_id ber (uuid4).
6. Yubor va kut: done | blocked | needs_human (15 daqiqa timeout).
7. Natijani tekshir: raqamlar manbali mi? ikkita agent zid raqam berganmi?
8. Birlashtir: 3 xulosa + kim/qachon; ziddiyat bo'lsa ikkalasi ham ko'rsatiladi.
9. Yoz: audit_log_write(...) va Obsidian `05_audit/` (task_id bilan).
```

## Xato holatlari

| Holat | Amal |
|---|---|
| 401 (token muddati) | `POST /api/auth/refresh` → yana 401 bo'lsa odamga |
| 403 (rol yetarli emas) | agentni almashtir; agent ham 403 olsa — odam (CTO) |
| 5xx (backend) | 1 marta qayta urinish (5 s), keyin `auditor-security` + odam |
| Timeout (15 daq) | `blocked` deb belgila, sabab bilan odamga |
| Ikki agent zid javob | ikkalasi ko'rsatiladi, "qaysi biri to'g'ri" — odam qarori |

## O'lchov

- Yo'naltirish aniqligi: noto'g'ri agentga ketgan so'rovlar ulushi (maqsad < 5%).
- `blocked` ulushi va o'rtacha yechim vaqti.
- Har so'rovda kontekst yuklash hajmi (maqsad: 3–5 chunk, taxminan 2–4k token).
