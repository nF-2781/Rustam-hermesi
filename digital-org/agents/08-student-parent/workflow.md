# WORKFLOW — Student & Parent

## Triggerlar

| Vaqt / hodisa | Amal |
|---|---|
| Har kuni 20:00 | Eslatma: ertangi dars + bajarilmagan vazifa |
| Darsdan keyin 2 soat | Davomat tasdig'i so'rovi (`respond`) |
| Yakshanba 18:00 | Ota-onaga haftalik holat |
| `finance-payroll` → `PAYMENT_DUE` | To'lov eslatmasi loyihasi |
| `branch-manager` → `SCHEDULE_CHANGED` | O'quvchi va ota-onaga xabar |
| Space quest yangilandi | Check-in va quest taklifi |

## Algoritm — kunlik eslatma

```text
1. Auth: POST /api/student-portal/login yoki POST /api/auth/login.
2. GET /students/me/schedule?date=<ertaga> → dars vaqti, xona, mentor.
3. GET /students/me/homework?status=pending → bajarilmagan vazifalar.
4. Xabar: 1 qator holat + 1 qator nima kerak + muddat (20:00 da, kechqurun).
5. Yuborish: `student-parent` kanali orqali (odam tasdig'i bilan, agar qoida talab qilsa).
```

## Algoritm — ota-ona haftalik hisoboti

```text
1. POST /parents/login → GET /api/parent/me (parentId).
2. GET /parents/{parentId}/children → childId ro'yxati (faqat o'ziniki).
3. Har child: GET /api/parent/children/{childId}/summary
   qo'shimcha: /attendance, /grades, /homework, /schedule, /payments (kerak bo'lsa).
4. Hisobot: 5 qator — davomat, vazifa, baho trendi, to'lov, keyingi qadam.
5. Ogohlantirish: 3+ qoldirilgan dars yoki 7+ kun nofaol → academic-manager ga A2A.
6. Yoz: Obsidian `02_academic/parent-reports/<childId>/<hafta>.md` (PII minimal).
```

## Algoritm — diagnostika

```text
1. GET /students/me/lessons/{id}/diagnostic → savollar.
2. O'quvchi javob beradi (agent javob yozmaydi — faqat topshiradi).
3. POST /students/me/lessons/{id}/diagnostic/submit
4. Natija: mavzu bo'yicha kuchli/zaif tomonlar → mentor-assistant ga A2A.
```

## Qoida tekshiruvlari

| Tekshiruv | Amal |
|---|---|
| Boshqa `childId` | 403, rad + sabab |
| `DELETE .../extra-lessons/{id}/book` < 1 soat | bloklanadi |
| Boshqa o'quvchi ID bilan `me` endpoint | rad (token egasi bo'yicha) |
| To'lov yozish so'rovi | rad — Finance ishi |

## Xato holatlari

| Holat | Amal |
|---|---|
| Jadval bo'sh | "dars yo'q" deb yozish, keyingi darsni ko'rsatish |
| To'lov ma'lumoti 5xx | "ko'rsatib bo'lmadi" — summani taxmin qilmaslik |
| Ota-ona bog'lanmagan | "kabinet ochilmagan" + branch-manager ga so'rov |
| Diagnostika yopilgan | "muddat o'tgan" + mentorga xabar |

## O'lchov

- Davomat tasdig'i javob berish ulushi (maqsad > 80%).
- Ota-ona hisobotini ochish ulushi.
- Churn signalidan keyin qaytgan o'quvchilar ulushi.
