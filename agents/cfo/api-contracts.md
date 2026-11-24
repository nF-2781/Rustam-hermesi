# CFO API Contracts & Data Specifications

## 1. Manbalar va Kontekst

Ushbu spetsifikatsiya MARS LMS backend tizimi (`https://mars-backend-six.vercel.app`) va uning FastAPI/OpenAPI manbasi (`/api-docs.json`) asosida tuzilgan.
Tizim kodlari bazasi (`mars-backend/src`):
- `router/auth.router.js` (`POST /api/auth/login`)
- `router/branchAdmin.router.js` (`GET /api/branch/overview`, `GET /api/branch/students`)
- `router/finance.router.js` (`GET /api/finance/overview`, `GET /api/branch/debtors`, `GET /api/branch/payments`)

Akkaunt ma'lumotlari faqat git'ga kiritilmaydigan lokal `.env` faylida saqlanadi (`MARS_PHONE` va `MARS_PASSWORD`).

---

## 2. CFO Tomonidan Ishlatiladigan Read-Only Kontraktlar

| Endpoint | HTTP Metod | Vazifasi va CFO Ishlatishi | Cheklovlar / Filtrlash |
|---|---|---|---|
| `/api/auth/login` | POST | CFO sessiyasini ochish va JWT tokenni xotirada saqlash | Token tashqariga chiqarilmaydi |
| `/api/branch/overview` | GET | Filial umumiy oylik ko'rsatkichlari (oylik filtr bilan) | Faqat joriy filial doirasida |
| `/api/finance/overview` | GET | Tushum, xarajatlar moddasi, sof foyda va kassa balansi | Boshqaruv darajasidagi moliya |
| `/api/branch/debtors` | GET | Qarzdor o'quvchilar ro'yxati, kechikish kunlari, summasi | Sahifalangan ro'yxat |
| `/api/branch/payments` | GET | Barcha to'lovlar (Naqd, Uzcard, Humo) tranzaksiyalar jurnali | Oy va sana bo'yicha filtr |

---

## 3. FastMCP Toollarining Ishlash Qoidalari

1. **`daily_finance_report`**:
   - Parametr: `compare=true` (kechagi kun va o'tgan oy bilan taqqoslash).
   - Chiqish: `gross_revenue`, `expenses`, `net_balance`, `cash_breakdown`, `anomaly_detected`.
   - Natija: Kassa kamomadi yoki kutilmagan tafovut bo'lsa zudlik bilan bayon qilinadi.

2. **`get_debts` & `debt_control_agent`**:
   - Parametr: `min_days_overdue` (masalan 14 yoki 30).
   - Chiqish: Qarzdorlik summasi, muddati va tavsiya etiladigan eslatma loyihasi (`message_drafts`).
   - PII filtri: Telefon raqamlari qat'iy ravishda maskalangan (`+998 90 *** ** 45`).

3. **`get_payments`**:
   - Tranzaksiya ID, sana, to'lovchi ID, summa va to'lov turi.
   - CFO uchun: To'lov usullari diversifikatsiyasi va dublikat to'lovlarni tekshirish.

---

## 4. Dalil va Ma'lumot Sifati Qoidalari (Evidence Rules)

- **Moliyaviy aniqlik:** Har bir raqam manbasi (tool nomi) bilan beriladi; hisoblanmagan raqam "kiritilmagan" deb belgilanadi.
- **PII himoyasi:** Karta raqamlari yoki to'lovchining to'liq telefon raqamlari ochiq chiqarilmaydi.
- **O'qish rejimi (Read-only):** CFO agenti to'lov yechish, bekor qilish (refund), qarz o'chirish kabi yozish/o'zgartirish amallarini bajarmaydi.
