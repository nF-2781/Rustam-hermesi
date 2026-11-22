---
name: mars-lms-operations
description: "MARS IT LMS bo'yicha kunlik operatsion zanjir: qarzdorlik, davomat, uy vazifasi va moliya hisobotini mars_lms MCP tool'lari orqali bir zanjirda yig'ish."
version: 1.0.0
author: Rustam
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mars, lms, mcp, finance, attendance, homework, workflow, uzbekistan]
    related_skills: [hermes-agent]
---

# MARS LMS — kunlik operatsion zanjir

Bu skill `mars_lms` MCP serverining tool'larini ketma-ket ishlatib, filial
bo'yicha **bitta kunlik holat hisobotini** yig'adi. Har bir qadam oldingi
qadam natijasiga tayanadi — shuning uchun tartibni buzmaslik kerak.

Tool nomlari Hermes ichida `mcp__mars_lms__<tool>` ko'rinishida chaqiriladi.

## Zanjir

```
lms_login  →  lms_context  →  get_debts  →  get_payments
                                    ↘            ↓
                                  debt_control_agent  →  daily_finance_report
```

| # | Tool | Nima uchun | Asosiy argumentlar |
|---|---|---|---|
| 1 | `lms_login` | Token olish (xotirada saqlanadi, 401 da avtomatik yangilanadi) | — |
| 2 | `lms_context` | Filial kesimida umumiy holat: guruhlar, o'quvchilar, mentorlar | — |
| 3 | `get_debts` | Qarzdorlar reyestri: summa, kechikish, oylik to'lov | `month` (`YYYY-MM`), `limit` |
| 4 | `get_payments` | Oxirgi tushumlar — qarzni yopish dinamikasi uchun | `month`, `limit` |
| 5 | `debt_control_agent` | Qarzdorlarni saralash + eslatma matnlari (`message_drafts`) | `month` |
| 6 | `daily_finance_report` | Tushum, xarajat, receivable va oldingi davr farqi | `month` |

## Qadamlar

1. **Autentifikatsiya.** `lms_login` ni chaqiring. `error` bo'lsa to'xtang va
   `MARS_PHONE` / `MARS_PASSWORD` / `MARS_ROLE` ni tekshiring — keyingi
   qadamlar tokensiz ishlamaydi.
2. **Kontekst.** `lms_context` dan `groups`, `students`, `mentors` sonini oling.
   Bu raqamlar keyingi hisobot sarlavhasida ishlatiladi.
3. **Qarzdorlik.** `get_debts` ni joriy oy uchun chaqiring (oy berilmasa —
   joriy oy). `details.debtors` massividan `student`, `amount`, `group` ni oling.
4. **Tushumlar.** `get_payments` bilan shu oydagi to'lovlarni oling; qarzdor
   ro'yxatidagi o'quvchilar bilan kesishmasi "to'lov qilgan qarzdorlar" ni beradi.
5. **Eslatmalar.** `debt_control_agent` ni chaqiring va `details.message_drafts`
   dan tayyor matnlarni oling. **Matnlarni yubormang** — yuborish inson
   tasdig'idan keyin alohida integratsiya orqali bo'ladi.
6. **Yakuniy hisobot.** `daily_finance_report` ni chaqirib, umumiy tushum,
   xarajat, sof qoldiq va receivable'ni bitta jadvalga birlashtiring.

## Chiqish shakli

Foydalanuvchiga quyidagi tuzilmada javob bering:

```markdown
## MARS LMS — kunlik holat (YYYY-MM-DD)
- Guruhlar: N | O'quvchilar: N | Mentorlar: N
- Tushum: ... UZS | Xarajat: ... UZS | Qoldiq: ... UZS
- Qarzdorlar: N ta, jami ... UZS

### Eng katta qarzdorlar
| O'quvchi | Guruh | Summa | Kechikish |
|---|---|---|---|

### Eslatma loyihalari (yuborilmagan)
1. ...
```

## Qoidalar

- **Pul operatsiyalari faqat inson tasdig'i bilan.** `daily_finance_report` va
  `debt_control_agent` faqat hisobot va loyiha tayyorlaydi; to'lov qabul
  qilish, refund yoki ish haqi to'lash bu skill'ning vazifasi emas.
- Oylar har doim `YYYY-MM` formatida (`2026-11`). Noto'g'ri format backend
  tomonidan `400` bilan rad etiladi — qayta urinmang, formatni tuzating.
- Har bir javob `{"error", "status_code", "message", "endpoint", "details"}`
  konvertida keladi: avval `error` ni tekshiring, keyin `details` ni o'qing.
- Takroriy `401` → `MARS_API_URL` noto'g'ri yoki akkaunt bloklangan; foydalanuvchiga
  ayting, cheksiz qayta login qilmang.

## Tekshirish

Skill ishlayotganini tekshirish uchun zanjirni skript orqali bir marta
yurgizish mumkin:

```bash
cd mcp-servers/mars_lms
.venv/Scripts/python.exe chain_demo.py
```

Skript MCP stdio orqali aynan shu 6 qadamni bajaradi va `chain_report.md` faylini
yozadi. Agar `tools: 22` va `chain OK` chiqsa, zanjir ishlayapti.

## Moslashtirish

- **Lokal backend:** `MARS_API_URL=http://localhost:7000` (Docker'dagi mars-backend).
- **Boshqa filial/oy:** tool'larga `month` argumentini bering.
- **Davomat/uy vazifasi qo'shish:** zanjirga `attendance_control_agent` va
  `homework_control_agent` ni 5-qadamdan keyin qo'shing — ular bir xil konvertda
  `report_markdown` qaytaradi.
