---
name: mars-davomat-nazoratchisi
description: Muntazam dars qoldiruvchilarni aniqlash va ogohlantirish.
version: 1.0.0
author: Hacker, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mars-lms, attendance, retention, alerts, student-tracking]
---

# MARS LMS — Davomat Nazoratchisi Agent

Darslarni muntazam va ketma-ket qoldirayotgan (surunkali sababsiz darsga kelmagan) o‘quvchilarni erta aniqlaydi, xavf darajasini baholaydi hamda mentor, ota-ona va filial ma'muriyatiga zudlik bilan signal yuboradi.

## When to Use
- Har kuni darslar tugagandan so'ng kunlik davomat tahlili uchun.
- O'quvchi ketma-ket 2 yoki undan ortiq darsga kelmaganda erta ogohlantirish uchun.
- O'quvchini kursdan sovuqlashib ketishining (churn) oldini olishda.

## Prerequisites
- `mars-lms` MCP serveri (`login`, `attendance`, `groups` toollari mavjud).

## Ish Zanjiri (Chain of Action)
1. `login(phone, password, role="admin")` orqali tizimga kirish.
2. `groups()` orqali faol guruhlar va ularning dars jadvallarini olish.
3. `attendance(consecutive_threshold=2)` orqali so'nggi davomat yozuvlarini yuklab olish.
4. Ketma-ket dars qoldirish mezonlari bo'yicha saralash:
   - **4+ ta dars ketma-ket qoldirgan:** 🔴 Kritik xavf (O'qishni tashlab ketish xavfi juda yuqori).
   - **2-3 ta dars ketma-ket qoldirgan:** 🟡 O'rtacha xavf (Sababini aniqlash zarur).
5. Mentor uchun harakat rejasi va ota-onaga xabar loyihasini shakllantirish.

## Chiqish Formati (Output Template)

```markdown
### 🚨 DAVOMAT NAZORATCHISI — XAVF SIGNAL XABARNOMASI
**Filial:** MARS Space — Yunusobod
**Sana:** {YYYY-MM-DD}
**Aniqlangan surunkali dars qoldiruvchilar:** {count} nafar

| № | O'quvchi | Guruh | Ketma-ket qoldirgan | Umumiy Davomat | Mentor | Aloqa (Tel) |
|---|----------|-------|---------------------|----------------|--------|-------------|
| 1 | {Ism}    | {Guruh}| {N} ta dars        | {Foiz}%        | {Mentor}| {Tel}       |

#### 📢 Mentor va Ma'muriyatga Signal:
> "DIQQAT: {Oquvchi} oxirgi {N} ta darsda qatnashmadi. Mentor {Mentor} bugun o'quvchi bilan bog'lanib sababini aniqlashi, qoldirilgan mavzular bo'yicha konsultatsiya rejalashtirishi so'raladi."

#### 📱 Ota-onaga Ogohlantirish Xabari:
> "Assalomu alaykum, hurmatli ota-ona! Farzandingiz {Oquvchi} MARS IT School {Guruh} guruhida {Sana} sanalaridagi darslarda ishtirok etmadi. Iltimos, dars qoldirilishi sababini bilish uchun ma'muriyat bilan bog'lanishingizni so'raymiz: +998712000001"
```

## Verification
- MCP `attendance` tooli orqali qaytgan ma'lumotlarda `consecutiveAbsentLessons >= threshold` sharti to'g'ri tekshirilgani tasdiqlansin.
