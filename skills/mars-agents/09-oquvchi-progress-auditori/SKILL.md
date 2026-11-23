---
name: mars-oquvchi-progress-auditori
description: Akademik ortda qolishni aniqlab yordam rejasini tuzish.
version: 1.0.0
author: k_mukhamedov, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mars-lms, student-progress, academic-audit, diagnostics, tutoring]
---

# MARS LMS — O‘quvchi Progress Auditori Agent

O‘quvchilarning fan bo'yicha progressi, davomati, uy vazifasi va imtihon natijalarini kompleks tahlil qiladi, o'zlashtirishda ortda qolayotgan (at-risk) o'quvchilarni diagnostika qiladi va mentorlar uchun individual yordam rejasini taklif etadi.

## When to Use
- Modul o'rtasida va modul yakunida akademik audit o'tkazishda.
- O'quvchining baholari va o'zlashtirishi 60% dan pastga tushganda.
- O'quvchini kursdan qolib ketishining oldini olish uchun individual repetitorlik (tutoring) rejalashtirishda.

## Prerequisites
- `mars-lms` MCP serveri (`login`, `student_progress`, `homework`, `attendance` toollari mavjud).

## Ish Zanjiri (Chain of Action)
1. `login(phone, password, role="admin")` orqali tizimga kirish.
2. `student_progress(at_risk_only=True)` tooli orqali xavf guruhidagi o'quvchilar ro'yxatini olish.
3. Asosiy to'sqinlik qiluvchi omillarni diagnostika qilish:
   - Dars qoldirish sabablimi? (Davomat < 70%)
   - Amaliyot yetishmasligimi? (Uy vazifasi < 50%)
   - Tushunmovchilik qaysi mavzuda yuz bergan? (Struggling topics)
4. Mentor va tutor uchun individual harakatlar rejasini shakllantirish.

## Chiqish Formati (Output Template)

```markdown
### 📈 O'QUVCHI PROGRESSI VA DIAGNOSTIKA AUDITI
**Filial:** MARS Space — Yunusobod
**Sana:** {YYYY-MM-DD}
**Xavf guruhidagi o'quvchilar:** {count} nafar

| O'quvchi | Guruh | Umumiy Progress | Davomat | Uy Vazifasi | Aniqlangan Asosiy To'siq |
|----------|-------|-----------------|---------|-------------|--------------------------|
| {Ism}    | {Guruh}| 🔴 {Prog}%     | {Dav}%  | {Vaz}%      | {Asosiy Sabab}           |

#### 🔍 O'quvchilar bo'yicha individual harakatlar rejasi:
1. **{Ism} ({Guruh}):**
   - **Qiyinchilik tug'dirgan mavzular:** {Mavzular}
   - **Tavsiya etilgan chora:** {Chora (Masalan: Tutor bilan individual amaliyot)}
   - **Mas'ul:** Mentor {Mentor} va Tutor
```

## Verification
- MCP `student_progress` tooli o'quvchilar bo'yicha progress ko'rsatkichlari va qiyinlashgan mavzularni to'liq qaytarganini tekshirish.
