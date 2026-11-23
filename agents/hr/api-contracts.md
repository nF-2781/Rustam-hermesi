# HR API Contracts & Data Specifications

## 1. Manbalar va Kontekst

Ushbu spetsifikatsiya MARS LMS backend tizimi (`https://mars-backend-six.vercel.app`) va uning FastAPI/OpenAPI manbasi (`/api-docs.json`) asosida tuzilgan.
Tizim kodlari bazasi (`mars-backend/src`):
- `router/auth.router.js` (`POST /api/auth/login`)
- `router/branchAdmin.router.js` (`GET /api/branch/groups`, `GET /api/branch/overview`)
- `router/branchAdminExtra.router.js` (`GET /api/branch/capacity`, `GET /api/branch/workload-planning`)
- `models/attendance.models.js` (`GET /attendance`)
- `models/homework.models.js` (`GET /homework`)

Akkaunt ma'lumotlari faqat git'ga kiritilmaydigan lokal `.env` faylida saqlanadi (`MARS_PHONE` va `MARS_PASSWORD`).

---

## 2. HR Tomonidan Ishlatiladigan Read-Only Kontraktlar

| Endpoint | HTTP Metod | Vazifasi va HR Ishlatishi | Cheklovlar / Filtrlash |
|---|---|---|---|
| `/api/auth/login` | POST | HR sessiyasini ochish va JWT tokenni xotirada saqlash | Token tashqariga chiqarilmaydi |
| `/api/branch/overview` | GET | Filial umumiy ko'rsatkichlari (mentorlar, xodimlar, guruhlar soni) | Faqat joriy filial doirasida |
| `/api/branch/groups` | GET | Filialdagi barcha guruhlar, dars vaqtlari va biriktirilgan mentorlar | Dars soatlari va guruhlar sonini hisoblash |
| `/api/branch/capacity` | GET | Xonalar sig'imi, slotlar va guruhlarning bandlik rejasi | Mentorlarning parallel darslarini aniqlash |
| `/attendance` | GET | Filial va guruhlar bo'yicha darslar davomati | Mentorlarning dars jurnallarini yuritishi |
| `/homework` | GET | Uy vazifalari tekshiruvi va topshirilishi ko'rsatkichlari | Mentorning o'quvchilar bilan ishlash sifati |

---

## 3. FastMCP Toollarining Ishlash Qoidalari

1. **`mentor_workload_analysis`**:
   - Parametr: `max_groups_per_mentor` (standart me'yor: 3).
   - Chiqish: Filialdagi barcha mentorlarning guruhlari soni, limitdan oshgan guruhlar soni, kadr ehtiyoji balansi.
   - Natija: Agar guruhlar soni `mentorlar_soni * max_groups_per_mentor` dan oshsa, kadr yetishmovchiligi ko'rsatiladi.

2. **`list_groups`**:
   - Guruh ID, nomi, yo'nalishi (Frontend, Backend, Foundation), mentor ismi va dars kunlari.
   - HR uchun: Mentorlar yuklamasini guruhma-guruh xaritalash.

3. **`get_attendance` & `get_homework`**:
   - Davomat va uy vazifasi tahlili mentorlar kesimida guruhlanadi.
   - 80% dan past davomat yoki 70% dan past uy vazifasi bo'yicha metodik ogohlantirish beriladi.

---

## 4. Dalil va Ma'lumot Sifati Qoidalari (Evidence Rules)

- **Haqiqiy boshlanish vaqti:** Dars sanasi darsning haqiqiy boshlanish daqiqasini bildirmaydi; kechikishlar faqat administrator qaydlarida mavjud bo'lsa hisoblanadi.
- **Noma'lum holat:** Jurnal to'ldirilmagan bo'lsa, "o'quvchi kelmadi" yoki "dars bo'lmadi" deb hisoblanmaydi; "ma'lumot kiritilmagan" deb belgilanadi.
- **PII himoyasi:** Telefon raqamlar doimo `+998 90 *** ** 45` shaklida maskalanadi; pasport seriyalari loglarda saqlanmaydi.
- **O'qish rejimi (Read-only):** HR agenti ma'lumotlar bazasiga yozish yoki o'zgartirish (mutation) amallarini bajarmaydi.
