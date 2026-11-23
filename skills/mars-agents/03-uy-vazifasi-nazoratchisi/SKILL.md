---
name: mars-uy-vazifasi-nazoratchisi
description: Topshirilmagan uy vazifalarini kuzatish va eslatish.
version: 1.0.0
author: vxrnox, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mars-lms, homework, assignments, student-tracking, automated-lms]
---

# MARS LMS — Uy Vazifasi Nazoratchisi Agent

Topshirish muddati (deadline) o'tgan, lekin hali topshirilmagan uy vazifalarini kuzatadi, mentorlarning qo'lda tekshirish vaqtini tejaydi hamda o'quvchilarga avtomatik eslatmalar tayyorlaydi.

## When to Use
- Uy vazifasi muddati tugaganidan keyin 2 soat ichida.
- Yangi dars boshlanishidan oldin topshiriqlar holatini mentorga taqdim etishda.
- Amaliyot topshirilmagani sababli o'zlashtirish tushib ketishini oldini olishda.

## Prerequisites
- `mars-lms` MCP serveri (`login`, `homework`, `groups` toollari mavjud).

## Ish Zanjiri (Chain of Action)
1. `login(phone, password, role="admin")` orqali tizimga kirish.
2. `groups()` orqali faol guruhlarni olish.
3. `homework(overdue_only=True)` tooli orqali muddati o'tgan vazifalarni tekshirish.
4. Topshirmagan o'quvchilar ro'yxatini ajratish va ularning aloqa ma'lumotlarini jamlash.
5. O'quvchilar uchun Telegram/SMS eslatma matni va mentor uchun tayyor tekshiruv xulosasini shakllantirish.

## Chiqish Formati (Output Template)

```markdown
### 📚 UY VAZIFALARI NAZORATI HISOBOTI
**Filial:** MARS Space — Yunusobod
**Sana:** {YYYY-MM-DD}
**Kuzatilgan vazifalar soni:** {count} ta
**Jami topshirmagan o'quvchilar:** {missing_total} nafar

| Guruh | Vazifa Nomi | Muddat (Deadline) | Topshirgan / Jami | Qolganlar |
|-------|-------------|-------------------|-------------------|-----------|
| {Guruh}| {Mavzu}    | {Sana, Soat}      | {N}/{Total}       | ⚠️ {M} nafar |

#### 📋 Topshirmagan o'quvchilar ro'yxati:
- **{Guruh} ({Mentor}):**
  1. {Ism} — Tel: {Tel}
  2. {Ism} — Tel: {Tel}

#### 💬 O'quvchiga Shaxsiy Eslatma Xabari:
> "Salom, {Oquvchi}! MARS LMS tizimida '{Mavzu}' mavzusidagi uy vazifangiz muddati o'tib ketgan. Amaliy ko'nikmalarni mustahkamlash va keyingi darsga tayyor bo'lish uchun vazifani bugun soat 22:00 gacha platformaga yuklang: https://marsspace.uz/homework/{id}"
```

## Verification
- MCP `homework` tooli muddati o'tgan (`isOverdue == True`) va `unsubmittedStudents` ro'yxati mavjud vazifalarni to'g'ri qaytarganini tasdiqlash.
