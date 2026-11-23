---
name: mars-xona-va-jadval-yordamchisi
description: Bosh xonalar va jadval toqnashuvlarini tahlil qilish.
version: 1.0.0
author: rizo_x7k, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mars-lms, rooms, scheduling, timetable, conflict-resolution]
---

# MARS LMS — Xona va Jadval Yordamchisi Agent

Filialdagi barcha o'quv xonalarining bandlik matritsasini tahlil qiladi, jadvaldagi to'qnashuvlarni (bir xonaga yoki bir mentorga bir vaqtda 2 ta guruh to'g'ri kelib qolishi) aniqlaydi va yangi darslar uchun bo'sh vaqt slotlarini taklif etadi.

## When to Use
- Yangi o'quv guruhi ochilayotganda bo'sh xona va vaqt tanlashda.
- Dars jadvali o'zgarganda to'qnashuvlar yo'qligini tekshirishda.
- Filial xonalaridan foydalanish samaradorligini (room capacity utilization) oshirishda.

## Prerequisites
- `mars-lms` MCP serveri (`login`, `room_availability`, `groups` toollari mavjud).

## Ish Zanjiri (Chain of Action)
1. `login(phone, password, role="admin")` orqali tizimga kirish.
2. `groups()` orqali faol guruhlar jadvalini olish.
3. `room_availability(checkConflicts=True)` tooli orqali xonalar bandligini tekshirish.
4. Vaqt matritsasini tekshirib to'qnashuvlarni (conflicts) aniqlash.
5. Yangi darslar uchun eng qulay bo'sh slotlar va to'qnashuvni bartaraf etish rejasini taqdim etish.

## Chiqish Formati (Output Template)

```markdown
### 🏫 XONALAR VA DARS JADVALI OPTIMALLASHTIRISH HISOBOTI
**Filial:** MARS Space — Yunusobod
**Sana:** {YYYY-MM-DD}
**Jami xonalar:** {count} ta | **Aniqlangan to'qnashuvlar:** {conflicts_count} ta

#### ⚠️ ANIQLANGAN JADVAL TO'QNASHUVI:
- **Xona:** Xona 2 (Backend Room)
- **Vaqt:** Seshanba - Payshanba - Shanba, 16:00 - 18:00
- **To'qnashgan tadbirlar:**
  1. `PY-205 (FastAPI & Microservices)` — Guruh darsi
  2. `Mehmon Master-klass (Open Lesson)` — Qo'shimcha tadbir
- **Yechim tavsiyasi:** Master-klassni Xona 4 (Robotics & STEM) ga ko'chirish (u yerda ushbu vaqtda xona 100% bo'sh).

#### 🟢 YANGI GURUHLAR UCHUN BO'SH XONA VA VAQT SLOTLARI:
1. **Xona 1 (Frontend Lab):** Dushanba - Chorshanba - Juma | 14:00 - 16:00 (16 ta kompyuter bo'sh)
2. **Xona 3 (Design Studio):** Seshanba - Payshanba - Shanba | 09:00 - 11:00 (14 ta planshet bo'sh)
3. **Xona 4 (Robotics & STEM):** Barcha kunlar | 14:00 - 18:00
```

## Verification
- MCP `room_availability` tooli bo'sh slotlar va to'qnashuvlar ro'yxatini aniq qaytarganini tekshirish.
