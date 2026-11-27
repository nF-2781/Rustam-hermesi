# WORKFLOW — Academic Manager

## Triggerlar

| Vaqt / hodisa | Amal |
|---|---|
| Har kuni 09:00 | Talab skani: `demand-stats` + `waitlist` → guruh ochish nomzodlari |
| Har kuni 20:00 | Churn skani: `attendance-risks` + `inactive-students` |
| Haftada (dushanba) | Yuklama va metodika: `workload-planning`, `curriculum-topic-analytics` |
| `TUTOR_BOOKING_DONE` (A2A) | Natijani o'quvchi kartasiga yozish, 7 kun kuzatish |
| Yangi feedback (event) | `feature-feedback` ni ko'rib chiqish ro'yxatiga |

## Algoritm — guruh ochish (`skill-group-launch`)

```text
1. Auth → GET /api/auth/me (filial, rol).
2. Talab: GET /api/branch/demand-stats?branch=<id>&period=<oy>
          GET /api/branch/waitlist?course=<kurs>
   shart: waitlist >= 10 va o'rtacha kutish >= 14 kun.
3. Mentor: GET /api/branch/workload-planning → bo'sh mentorlar
           sifat kartasi (Obsidian `02_academic/mentor-cards/`) + diagnostika natijasi.
4. Metodika: GET /api/branch/curriculum-topic-analytics → qaysi mavzu qiyin.
5. Xona talabi: 1 smena, 2×90 daqiqa — xonani tanlash branch-manager'da.
6. Buyurtma yig': kurs, mentor_id, vaqt, waitlist_ids[], sabab (raqamlar bilan).
7. A2A: GROUP_LAUNCH_ORDER → branch-manager (priority: high).
8. Kuzatish: 7 kun — guruh ochildimi? 30 kun — churn < 10%?
9. Yoz: vault_append("02_academic/launches/<sana>-<kurs>.md", qaror + natija).
```

## Algoritm — churn qutqaruv (`skill-churn-rescue`)

```text
1. GET /api/branch/attendance-risks (3+ ketma-ket qoldirgan)
2. GET /api/branch/inactive-students (7+ kun kirmagan)
3. Har o'quvchi uchun: sabab toifasi — mavzu / jadval / to'lov / mentor / noma'lum.
   - to'lov → finance-payroll ga A2A (qarzdorlik tekshiruvi)
   - mavzu  → tutor-intern (tutor sloti) yoki mentor-assistant (qo'shimcha dars)
4. student-parent ga A2A: o'quvchi + ota-onaga ehtiyotkor xabar loyihasi.
5. 14 kundan keyin: POST /api/branch/attendance-risks/{id}/resolve (sabab bilan).
6. Natija → Obsidian `02_academic/retention/` + lessons_learned.
```

## Qoida tekshiruvlari

| Tekshiruv | Amal |
|---|---|
| Guruh ochish uchun waitlist ≥ 10? | yo'q bo'lsa buyurtma berilmaydi |
| Mentor yuklamasi 6 guruhdan oshmaydimi? | oshsa zaxira mentor tanlanadi |
| O'quvchi PII hisobotda bormi? | olib tashlanadi, faqat ID |
| `PATCH curriculum-topic-review` odam tasdig'i bilanmi? | yo'q bo'lsa — tavsiya sifatida qoldiriladi |

## O'lchov

- Waitlist → guruhga aylanish foizi (maqsad > 70%, 30 kun).
- Churn qutqaruvdan qaytgan o'quvchilar ulushi.
- Metodik tuzatishdan keyin mavzu o'zlashtirish o'sishi.
