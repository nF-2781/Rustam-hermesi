---
name: mars-qarzdorlik-nazoratchisi
description: Qarzdor oquvchilarni aniqlash va eslatma yuborish.
version: 1.0.0
author: Muhammadali Baxtiyorov, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mars-lms, finance, debts, reminders, automated-audit]
---

# MARS LMS — Qarzdorlik Nazoratchisi Agent

To‘lov muddatini o‘tkazib yuborgan o‘quvchilarni real vaqt rejimida aniqlaydi, qarz summasi va kechikish muddatiga ko‘ra xavf toifalariga ajratadi hamda filial administratoriga yuborishga tayyor eslatma xabarlarini taqdim etadi.

## When to Use
- Har kuni ertalabki moliyaviy audit va to'lov nazorati jarayonida.
- Filial administratori oylik qarzdorlar ro'yxatini talab qilganda.
- Kechikish muddati 7 kundan oshgan o'quvchilarga ogohlantirish yuborishda.

## Prerequisites
- `mars-lms` MCP serveri faol bo'lishi kerak (`login`, `debts`, `students` toollari mavjud).

## Ish Zanjiri (Chain of Action)
1. `login(phone, password, role="admin")` orqali tizimga kirish va tokenni tasdiqlash.
2. `debts(month, urgency)` toolini chaqirib, filial bo'yicha barcha qarzdorlarni olish.
3. Ma'lumotlarni saralash va filtrlash:
   - **Kritik (20+ kun kechikkan):** Zudlik bilan administrator aralashuvi talab qilinadi.
   - **Yuqori (10-19 kun kechikkan):** Ota-ona bilan bevosita telefon orqali aloqa.
   - **O'rtacha (1-9 kun kechikkan):** Yumshoq SMS/Telegram eslatmasi.
4. Administrator uchun umumiy hisobot jadvali va yuborishga tayyor xabarlar loyihasini tayyorlash.

## Chiqish Formati (Output Template)

```markdown
### 📊 QARZDORLIK NAZORATCHISI HISOBOTI
**Filial:** MARS Space — Yunusobod
**Sana:** {YYYY-MM-DD}
**Jami qarzdorlar soni:** {count} nafar
**Jami qarzdorlik summasi:** {summa} UZS

| № | O'quvchi | Guruh | Qarz Summasi | Kechikkan Kun | Xavf Darajasi | Ota-ona Tel |
|---|----------|-------|--------------|---------------|---------------|-------------|
| 1 | {Ism}    | {Guruh}| {Summa} UZS  | {Kun} kun     | 🔴 Kritik     | {Tel}       |

#### 📱 Yuborishga tayyor SMS / Telegram shablonlari:
**Ota-onaga eslatma (Kritik holat):**
> "Assalomu alaykum, hurmatli {Ota-ona}! Farzandingiz {Oquvchi}ning MARS IT School {Guruh} kursi bo'yicha to'lovi {Kun} kunga kechikmoqda (Qarz: {Summa} UZS). O'qish jarayoni to'xtab qolmasligi uchun to'lovni amalga oshirishingizni so'raymiz. To'lov havolasi: https://marsit.uz/pay/{id}"
```

## Verification
- MCP `debts` chaqiruvi muvaffaqiyatli JSON qaytarganini tekshirish.
- Har bir qarzdor uchun to'lov summasi va kechikkan kunlar musbat son ekanligi tasdiqlansin.
