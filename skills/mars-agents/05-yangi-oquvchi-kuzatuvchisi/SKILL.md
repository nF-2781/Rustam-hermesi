---
name: mars-yangi-oquvchi-kuzatuvchisi
description: 1-tolov kutilayotgan yangi oquvchilarni follow-up qilish.
version: 1.0.0
author: Saidabza1, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mars-lms, enrollments, leads, conversion, reception-followup]
---

# MARS LMS — Yangi O‘quvchi Kuzatuvchisi Agent

Ro‘yxatdan o‘tgan, ammo birinchi to‘lovi yoki guruhga biriktirilishi yakunlanmagan yangi o‘quvchilarni (leads/waitlist) kuzatadi, qaysi bosqichda to'xtab qolganini aniqlaydi va reception xodimiga tezkor follow-up ro‘yxatini beradi.

## When to Use
- Kuniga 2 marta: 11:00 da va 17:00 da qabul qilingan arizalarni tahlil qilishda.
- Sinov darsidan keyin to'lov qilmagan yangi talabalarni saralashda.
- Yangi ochilayotgan guruhlarni to'ldirish (conversion rate oshirish) jarayonida.

## Prerequisites
- `mars-lms` MCP serveri (`login`, `pending_enrollments`, `students`, `groups` toollari mavjud).

## Ish Zanjiri (Chain of Action)
1. `login(phone, password, role="admin")` orqali tizimga kirish.
2. `pending_enrollments()` tooli orqali arizalar holatini yuklab olish.
3. Jarayon bosqichlarini aniqlash:
   - `pending_first_payment`: Ro'yxatdan o'tgan, lekin 1-to'lov kutilmoqda.
   - `pending_group_slot`: To'lov qilgan, lekin guruh vaqti hali tasdiqlanmagan.
4. Muhimlik (priority) bo'yicha saralash va reception xodimi uchun harakatlar rejasini tuzish.
5. Mijoz bilan telefon orqali gaplashish ssenariysi va Telegram xabar loyihasini tayyorlash.

## Chiqish Formati (Output Template)

```markdown
### 🎯 YANGI O'QUVCHI FOLLOW-UP HISOBOTI
**Filial:** MARS Space — Yunusobod
**Sana:** {YYYY-MM-DD}
**Jami kutilayotgan arizalar:** {count} nafar

| № | Talaba Ismi | Tanlangan Kurs | Ro'yxatdan o'tgan | Joriy Bosqich | Prioritet | Telefon |
|---|-------------|----------------|-------------------|---------------|-----------|---------|
| 1 | {Ism}       | {Kurs}         | {Sana}            | ⏳ 1-to'lov   | 🔴 Yuqori | {Tel}   |

#### 📞 Reception uchun Qo'ng'iroq Ssenariysi:
> "Assalomu alaykum, {Ism}! MARS IT School qabul bo'limidan qo'ng'iroq qilyapmiz. Siz {Kurs} kursimizga qiziqish bildirgan edingiz. Guruhda so'nggi 2 ta bo'sh o'rin qoldi. Dars jadvalingizni tasdiqlash va boshlang'ich bonusni faollashtirish uchun yordam bera olamanmi?"

#### 📲 SMS / Telegram xabar loyihasi:
> "Salom, {Ism}! MARS IT Schoolda {Kurs} guruhida joyingizni band qilish uchun to'lov havolasi tayyor: https://marsit.uz/enroll/{id}. Savollaringiz bo'lsa, adminga yozishingiz mumkin: @mars_admin"
```

## Verification
- MCP `pending_enrollments` chaqirilib, har bir ariza bo'yicha bosqich va ustuvorlik aniqlangani tekshirilsin.
