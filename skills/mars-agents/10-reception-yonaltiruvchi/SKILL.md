---
name: mars-reception-yonaltiruvchi
description: Kiruvchi murojaatlarni toifalab masullarga yonaltirish.
version: 1.1.0
author: muhammad_solih13, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mars-lms, reception, ticket-routing, triage, customer-care]
---

# MARS LMS — Reception So‘rovlarini Yo‘naltiruvchi Agent

O‘quvchi va ota-onalardan tushgan barcha yangi murojaatlarni toifalarga (to‘lov, jadval, ta’lim, texnik muammo, boshqa) ajratadi, to‘g‘ri mas’ul xodimni belgilaydi, administratorga yo‘naltirish ro‘yxati va javob loyihasini taqdim etadi hamda tushunarsiz murojaatlarni alohida ko‘rsatadi.

## When to Use
- Kun davomida yangi kiruvchi murojaatlar paydo bo'lganda (SLA tezkorligi: 15 daqiqa).
- Murojaatlarni mas'ullar o'rtasida to'g'ri taqsimlashda.
- Noaniq yoki tushunarsiz yozilgan xabarlar bilan tezkor qayta bog'lanishda.

## Prerequisites
- `mars-lms` MCP serveri (`login`, `incoming_requests` toollari mavjud).

## Ish Zanjiri (Chain of Action)
1. `login(phone, password, role="admin")` orqali tizimga kirish.
2. `incoming_requests(status="open")` tooli orqali yangi murojaatlarni olish.
3. Murojaat matnini tahlil qilib toifalarga ajratish:
   - 💳 **To‘lov (Payment):** Kvitansiya, to'lov xatolari, qarz -> Bosh Bugalter / Moliya menejeri.
   - 🕒 **Jadval (Schedule):** Smena almashtirish, guruh ko'chirish -> Katta Administrator / Reception.
   - 🎓 **Ta’lim (Education):** Mavzu tushunmaslik, qo'shimcha dars, konsultatsiya -> Mentor & O'quv bo'limi.
   - 💻 **Texnik muammo (Technical):** Kompyuter, internet, proyektor nosozligi -> IT Administrator / Xo'jalik.
   - 📦 **Boshqa (Other):** Yo'qolgan buyumlar, umumiy savollar -> Administrator.
   - ❓ **Tushunarsiz murojaatlar (Unclear):** Ma'nosi noaniq, kontekstsiz xabarlar -> Alohida blokda ko'rsatiladi va qayta qo'ng'iroq qilish vazifasi qo'yiladi.
4. Tegishli mas’ul xodimni biriktirish va mijoz uchun javob loyihasini (response draft) shakllantirish.
5. Administrator uchun umumiy hisobot va yo'naltirish ro'yxatini chiqarish.

## Chiqish Formati (Output Template)

```markdown
### 🛎 RECEPTION SO'ROVLARINI YO'NALTIRISH HISOBOTI
**Filial:** MARS Space — Yunusobod
**Sana:** {YYYY-MM-DD HH:mm}
**Jami kiruvchi murojaatlar:** {total} ta | **Toifalangan:** {categorized} ta | **Tushunarsiz:** {unclear} ta

#### 📋 TOIFALANGAN VA BIRIKTIRILGAN MUROJAATLAR:
| ID | Murojaatchi | Toifa | Qisqacha Mazmuni | Mas'ul Xodim | Muhimlik |
|----|-------------|-------|------------------|--------------|----------|
| {ID}| {Ism}      | 💳 To'lov | {Mazmun}      | Bosh Bugalter| O'rtacha |
| {ID}| {Ism}      | 🕒 Jadval | {Mazmun}      | Katta Admin  | 🔴 Yuqori|
| {ID}| {Ism}      | 🎓 Ta'lim | {Mazmun}      | Mentor       | O'rtacha |
| {ID}| {Ism}      | 💻 Texnik | {Mazmun}      | IT Admin     | 🔴 Yuqori|

#### ⚠️ TUSHUNARSIZ / ANIKLASHTIRISH TALAB ETILADIGAN MUROJAATLAR:
- ❓ **ID: {ID}** — Murojaatchi: **{Ism}** (Tel: `{Tel}`)
  - **Kelgan matn:** *"{Xabar matni}"*
  - **Harakat:** Reception xodimi telefon orqali bog'lanib, so'rov mazmunini aniqlashtirishi zarur.
  - **Tavsiya etilgan javob:** *"Assalomu alaykum! Murojaatingiz qaysi masala yuzasidan ekanligini aniqlashtirib bersangiz, yordam berishdan mamnun bo'lamiz."*

#### 💬 Tayyor Javob Loyihalari:
1. **{Ism} ({Toifa}):**
   > "{Tayyor javob matni}"
```

## Amalga Oshirish Eslatmasi (Implementation Notes)
- **Avtomatlashtirish:** Ushbu agent har 15 daqiqada Cron / Task Scheduler orqali avtomatik ishga tushirilishi mumkin.
- **Xabarnomalar:** Aniqlangan toifalar va mas'ullarga Telegram Bot (Webhook / SendMessage API) yoki Email orqali to'g'ridan-to'g'ri bildirishnoma yuborish alohida integratsiya qilinadi.
- **Backend API:** Yangi tool backenddagi `/branch-manager/requests` va `/issues` endpointlari bilan bevosita sinxronlashadi.
