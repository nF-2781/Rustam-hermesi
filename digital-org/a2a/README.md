# A2A — agentlararo aloqa

Agentlar bir-biriga "erkin matn" yozmaydi. Har xabar — `security/a2a_schema.json`
bo'yicha JSON konvert va **Orchestrator** orqali o'tadi. Shu tufayli har zanjir
kuzatiladi (`task_id`), to'xtab qolgan joy ko'rinadi va qoida buzilishi logga tushadi.

## Konvert

```json
{
  "task_id": "6f1c2b9e-…",
  "from_agent": "academic-manager",
  "to_agent": "branch-manager",
  "event_type": "GROUP_LAUNCH_ORDER",
  "priority": "high",
  "payload": { "summary": "…", "ids": ["wl_101"], "numbers": { "waitlist": 12 },
               "next_step": "…", "requires_human_approval": false },
  "context": { "sources": [{ "endpoint": "/api/branch/demand-stats", "period": "2026-11" }],
               "vault_chunks": ["02_academic/mentor-cards/d-yusupova.md"] },
  "status": "queued",
  "created_at": "2026-11-27T09:02:11Z",
  "expires_at": "2026-11-27T09:17:11Z",
  "guardrails": { "checked": true, "decision": "ALLOW", "approval_by": null }
}
```

| Maydon | Nega kerak |
|---|---|
| `task_id` | butun zanjir bo'ylab o'zgarmaydi — log, Obsidian, nizo tekshiruvi shu bo'yicha |
| `event_type` | marshrutizatsiya jadvali kaliti (erkin matn emas) |
| `payload.ids` | faqat ID — PII konvertda tashilmaydi |
| `context.sources` | har raqam qaysi endpoint/davrdan olinganini isbotlaydi |
| `expires_at` | 15 daqiqada javob bo'lmasa `blocked` → eskalatsiya |
| `guardrails` | `security_sandbox` qarori yozib qo'yiladi |

## Iyerarxiya

```text
                    [ orchestrator — 0 ]
                       │            │
        ┌──────────────┘            └──────────────┐
        ▼                                          ▼
 [ ceo-strategist — 1 ]                    [ auditor-security — 2 ]
        │                                     (kuzatuv + nizolar)
   ┌────┼─────────────┐
   ▼    ▼             ▼
[academic 2] ──► [branch 2] ◄──► [finance 2]
   │              │                 ▲
   ├──────┬───────┼────────┐        │
   ▼      ▼       ▼        ▼        │
[mentor 3] [tutor 3] [student 3] ───┘
```

---

## 1-zanjir — Yangi guruh ochish

```text
branch-manager   : o'quvchilarni waitlist ga yig'adi (POST /api/branch/waitlist)
academic-manager : demand 12 → mentor tanlaydi → GROUP_LAUNCH_ORDER (high)
branch-manager   : noise-analytics → xona → POST /api/branch/groups
                   → POST /api/branch/waitlist/{id}/enroll → GROUP_LAUNCHED
student-parent   : o'quvchi + ota-onaga jadval va to'lov xabari
mentor-assistant : guruh biriktirildi (LESSON_PLAN)
finance-payroll  : to'lov rejasi (PAYMENT_DUE)
```

**To'xtash nuqtasi:** waitlist 10 dan kam bo'lsa zanjir boshlanmaydi; xona topilmasa
Academic'ga qaytadi (vaqt varianti bilan).

## 2-zanjir — Davomat → tasdiq → nizo → maosh

```text
mentor-assistant : POST /api/mentor/attendance  (darsdan keyin)
student-parent   : POST /students/me/attendance/{id}/respond  (yes / no)
auditor-security : no yoki overdue → attendance-confirmations → dalil → resolve (approved/rejected)
finance-payroll  : oy oxiri → mentor-earnings → POST /api/finance/salaries (draft)
human            : 2FA tasdiq → PATCH .../status = paid
```

**Qoida:** `resolve` da `reason` bo'sh bo'lsa `security_sandbox` bloklaydi;
`paid` — faqat odam tasdig'i bilan.

## 3-zanjir — Churn rescue (o'quvchini ushlab qolish)

```text
academic-manager : attendance-risks + inactive-students (har kuni 20:00)
                   sabab: mavzu / jadval / to'lov / mentor / noma'lum
academic → tutor : TUTOR_BOOKING (tutor-bookings) — mavzu bo'yicha
academic → mentor: LESSON_PLAN (extra-lessons) — qo'shimcha dars
academic → finance: PAYMENT_DUE — to'lov sababi bo'lsa
academic → student-parent: RETENTION_ALERT — o'quvchi + ota-ona xabari
academic-manager : 14 kun → attendance-risks/{id}/resolve yoki qayta reja
```

## 4-zanjir — Zamena va to'lovni qayta yo'naltirish

```text
mentor-assistant : POST /api/mentor/substitutions/request
branch-manager   : bo'sh mentor → POST /api/branch/substitutions → SUBSTITUTION_ASSIGNED
finance-payroll  : dars to'lovi o'rinbosar mentorga (14 551 UZS) — PAYROLL_DRAFT ga izoh
student-parent   : guruhga vaqtinchalik o'qituvchi haqida xabar
```

**Tekshirish:** zamena darsi auditor tomonidan davomat tasdiqlashda alohida ko'riladi —
o'rinbosar va asosiy mentor ikkalasi ham to'lov olmaydi.

---

## Xato va eskalatsiya

| Holat | Kim | Nima qiladi |
|---|---|---|
| 15 daqiqada javob yo'q | orchestrator | `blocked` + odamga 1 qator sabab |
| 403 (rol yetarli emas) | agent | agentni almashtirish; yana 403 → odam (CTO) |
| ikki agent zid raqam | orchestrator | ikkalasi ko'rsatiladi, qaror odamda |
| `guardrails.decision != ALLOW` | agent | bajarilmaydi; `APPROVAL_REQUEST` yoki rad sababi |
| qoida buzilishi (urinish) | auditor-security | incident + `06_self_improve/lessons_learned.md` |
