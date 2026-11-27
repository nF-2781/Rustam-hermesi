# WORKFLOW — Branch Manager

## Triggerlar

| Vaqt / hodisa | Amal |
|---|---|
| Har kuni 09:00 | Kunlik tayyorlik: `substitutions`, `noise-incidents`, guruh jadvali |
| `GROUP_LAUNCH_ORDER` (A2A) | Guruh ochish zanjiri |
| `substitutions/request` (mentor) | Zamena tayinlash |
| `noise-incidents` yoki `noise-analytics` ogohlantirishi | Akustika tekshiruvi |
| Transfer so'rovi | Meros bilan ko'chirish |
| Haftada (juma) | Xona yuklamasi va keyingi hafta jadvali |

## Algoritm — guruh ochish (buyurtma bilan)

```text
1. Buyurtmani tekshir: kurs, mentor_id, vaqt, waitlist_ids[] — to'liqmi? yo'q bo'lsa qaytarish.
2. Xona: GET /api/branch/noise-analytics?date=<kun>
         bo'sh xonalar + qo'shni shovqin < 55 dB bo'lganini tanla.
3. To'qnashuv: mentor shu vaqtda boshqa guruhda emasmi? (GET /api/branch/groups)
4. Guruh: POST /api/branch/groups {course, mentor_id, room_id, schedule}
5. O'quvchilar: har waitlist_id uchun POST /api/branch/waitlist/{id}/enroll
6. Jadval: PATCH /api/workspace/groups/{id}/schedule (tasdiqlangan vaqt)
7. Xabar: student-parent (o'quvchi + ota-ona), mentor-assistant (guruh), finance-payroll (to'lov rejasi)
8. Yoz: vault_append("03_branch/daily-ops/<sana>.md", nima ochildi, kim, qaysi xona)
```

## Algoritm — zamena

```text
1. GET /api/branch/substitutions?status=requested
2. Bo'sh mentorlar: GET /api/branch/mentors + workload (shu vaqtda darsi yo'q).
3. POST /api/branch/substitutions {lesson_id, substitute_mentor_id}
4. finance-payroll ga A2A: "bu dars to'lovi o'rinbosarga" (14 551 UZS asosida).
5. student-parent ga A2A: vaqtinchalik o'qituvchi haqida xabar loyihasi.
6. Darsdan keyin: zamena bajarilganini tekshir, `cancel` kerak bo'lsa sabab bilan.
```

## Qoida tekshiruvlari

| Tekshiruv | Amal |
|---|---|
| Xona bir vaqtda ikki guruhga berilmaydi | to'qnashuv → boshqa xona yoki vaqt |
| Shovqin > 55 dB qo'shni xona | jadval ko'chiriladi yoki `noise-incidents` ochiladi |
| `DELETE` (guruh/o'quvchi) | `security_sandbox` → odam tasdig'i, `reason` majburiy |
| Filial chegarasi | `branchId` mos emas → 403, to'xtash |

## Xato holatlari

| Holat | Amal |
|---|---|
| Bo'sh xona yo'q | vaqtni ko'chirish varianti 2 ta bilan qaytarish |
| Mentor topilmadi | darsni `cancel` qilish tavsiyasi + ota-onaga xabar |
| `noise-analytics` bo'sh | "o'lchov yo'q" deb yozish, taxmin qilmaslik |
| 5xx | 1 marta qayta urinish, keyin `auditor-security` + odam |

## O'lchov

- Bekor qilingan darslar ulushi (maqsad < 3%).
- Zamena topilish vaqti (so'rovdan tasdiqqacha, maqsad < 2 soat).
- Shovqin incidentlarining takrorlanishi (bir xonada oyiga ≤ 2).
