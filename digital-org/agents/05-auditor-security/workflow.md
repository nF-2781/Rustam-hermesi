# WORKFLOW — Auditor & Security

## Triggerlar

| Vaqt / hodisa | Amal |
|---|---|
| Har soatda | `GET /api/health` + `attendance-confirmations` skani |
| Har kuni 08:00 | Audit log anomaliyasi (403/401/5xx, g'alati tool) |
| Har kuni 09:30 | RBAC/ABAC tekshiruvi (chegaradan chiqqan so'rov) |
| `GUARDRAIL_VIOLATION` (event) | Incident yozish + `lessons_learned.md` |
| Oy oxiri | Barcha nizolarni yopish → `finance-payroll` ga uzatish |
| MCP server xatosi | `mars-cto` (odam) ga eskalatsiya |

## Algoritm — davomat nizosi

```text
1. GET /api/branch/attendance-confirmations?status=disputed&period=<oy>
2. Har nizo uchun dalil yig':
   - GET /api/branch/attendance?lesson_id=<id>      (mentor belgisi)
   - GET /api/branch/audit-logs?lesson_id=<id>      (tizimga kirish/chiqish)
   - GET /api/ai/analytics/attendance-summary       (umumiy kontekst)
   - dars diagnostikasi (mentor-assistant dan A2A so'rov) — vaqt mosligi
3. Qoida bilan solishtir: dars davomiyligi, tasdiq oynasi (masalan 24 soat), qayta yozish izi.
4. Qaror tavsiyasi: approved | rejected + `reason` (1–2 qator, dalilga havola).
5. POST /api/branch/attendance/{id}/resolve  (reason majburiy)
6. Oy oxirida: tasdiqlangan darslar ro'yxati → finance-payroll (`ATTENDANCE_APPROVED_MONTH`).
7. Saboq: agar qoida noaniq bo'lsa — lessons_learned + qoida taklifi (odam tasdiqlaydi).
```

## Algoritm — observability skani

```text
1. GET /api/branch/audit-logs?from=<24 soat>
2. Anomaliyalar: 403 ko'p (rol xatosi), 401 takroriy (token), 5xx (backend), 
   bir agentda g'alati endpoint kombinatsiyasi (masalan mentor → /api/finance/*).
3. Har anomaliya uchun: agent, task_id, tool, soni, birinchi/oxirgi vaqt.
4. 3 tadan ko'p takrorlansa — incident: odamga + agent egasiga.
5. Natija Obsidian `05_audit/incidents/<sana>.md` + JSON log.
```

## Qoida tekshiruvlari

| Tekshiruv | Amal |
|---|---|
| `resolve` da `reason` bo'sh | bloklanadi (`security_sandbox`) |
| Nizo bir tomon dalili bilan | yopilmaydi — "dalil yetarli emas" |
| Audit logini o'chirish so'rovi | rad + incident |
| Token/parol logda | darhol `redacted`, incident yoziladi |

## Xato holatlari

| Holat | Amal |
|---|---|
| `attendance-confirmations` bo'sh | "ochiq nizo yo'q" deb yozish (0 bilan aralashtirmaslik) |
| Log eksport 5xx | qo'lda tekshirish ro'yxati + `mars-cto` |
| Zid dalil (log vs diagnostika) | ikkalasi ko'rsatiladi, odam qaroriga qoldiriladi |
| Timeout | skanni qisman chiqarish, qolganini belgilash |

## O'lchov

- Ochiq nizolarning o'rtacha yopilish vaqti (maqsad < 48 soat).
- Qoida buzilishlari soni (oyiga) va takrorlanishi (maqsad 0 takror).
- `lessons_learned` yozuvlaridan qoidaga aylanganlari ulushi.
