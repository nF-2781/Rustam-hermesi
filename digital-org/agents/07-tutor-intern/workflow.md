# WORKFLOW — Tutor & Intern

## Triggerlar

| Vaqt / hodisa | Amal |
|---|---|
| `academic-manager` → `RETENTION_ALERT` | Tutor slotlarini tekshirish va taklif |
| Har kuni 08:00 | Intern topshiriqlari holati + davomat |
| Topshiriq topshirildi (`submit`) | Tekshirish navbatiga qo'shish |
| Seansdan 1 kun oldin | Eslatma loyihasi (`student-parent` orqali) |
| Haftada (shanba) | Leaderboard va Space quest yakuni |
| Bekor qilish so'rovi | 1 soat qoidasini tekshirish |

## Algoritm — tutor broni

```text
1. Auth → GET /api/auth/me (rol, o'quvchi/intern ID).
2. Slotlar: GET /api/tutor-bookings/tutors?course=<kurs>&date=<kun>
3. Tanlov: eng yaqin 2 variant (vaqt + tutor reytingi). Bo'sh bo'lsa — alternativa.
4. Bron: POST /api/tutor-bookings {tutor_id, slot, student_id, topic}
5. Tasdiq: o'quvchi/ota-ona tasdig'i (talab bo'lsa) — bron `pending`.
6. Eslatma: student-parent ga A2A (seans vaqti, joy/format).
7. Natija: 7 kundan keyin `attendance-risks` dan chiqqanini tekshir.
```

## Algoritm — intern topshirig'i

```text
1. GET /api/intern/tasks?status=assigned
2. Har topshiriq: deadline, talab, mentor izohi.
3. Topshirilgan: GET /api/intern/tasks/{id}/status → tekshirish holati.
4. Feedback: bajarilgan ish bo'yicha 2 nuqta (nima yaxshi, nima tuzatish kerak).
5. Baho: GET /api/intern/grades — mentor qo'ygan; agent faqat o'qiydi.
6. Space: GET /api/intern/space → bajarilgan questlar; claim faqat ruxsat bo'lsa.
7. Yoz: Obsidian `02_academic/interns/<intern>.md` — haftalik progress.
```

## Qoida tekshiruvlari

| Tekshiruv | Amal |
|---|---|
| `DELETE /api/tutor-bookings/{id}` vaqtgacha < 1 soat | bloklanadi |
| Bron sloti band | takroriy bron rad etiladi |
| Boshqa intern ID | 403, to'xtash |
| `quests/claim` mavjud bo'lmagan kalit | rad, "quest topilmadi" |

## Xato holatlari

| Holat | Amal |
|---|---|
| Slot yo'q | 2 alternativa (boshqa kun / qo'shimcha dars) |
| Bron to'qnashuvi | eng yaqin bo'sh slot taklifi |
| Intern topshirmagan | eslatma loyihasi, 3 kundan keyin mentorga xabar |
| Balans 5xx | moliyaviy xulosa bermaslik, faqat "ko'rsatib bo'lmadi" |

## O'lchov

- Tutor seansidan keyin davomat yaxshilanishi (maqsad > 60% holatda).
- Bron bekor qilish ulushi (maqsad < 10%).
- Intern topshiriqlarining o'z vaqtida bajarilishi (maqsad > 80%).
