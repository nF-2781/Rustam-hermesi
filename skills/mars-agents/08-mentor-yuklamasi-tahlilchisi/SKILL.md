---
name: mars-mentor-yuklamasi-tahlilchisi
description: Mentorlar yuklamasini tahlil qilib guruh tavsiya etish.
version: 1.0.0
author: rizo_x7k, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mars-lms, mentors, workload, capacity-planning, hr-audit]
---

# MARS LMS — Mentor Yuklamasi Tahlilchisi Agent

Filial mentorlari o'rtasida dars soatlari va guruhlar taqsimotini tahlil qiladi, ortiqcha yuklama olgan (burnout xavfi bor) hamda bo'sh resursga ega bo'lgan mentorlarni aniqlaydi va yangi ochilayotgan guruhni eng mos mentorga biriktirish bo'yicha tavsiya beradi.

## When to Use
- Yangi guruh rejalashtirilayotganda mentor tanlash jarayonida.
- Oylik akademik resurslar va o'qituvchilar yuklamasini muvozanatlashda.
- Mentorlar dars sifatini saqlash va charchashining oldini olishda.

## Prerequisites
- `mars-lms` MCP serveri (`login`, `mentor_workload`, `mentors`, `groups` toollari mavjud).

## Ish Zanjiri (Chain of Action)
1. `login(phone, password, role="admin")` orqali tizimga kirish.
2. `mentor_workload(maxGroupsThreshold=3)` tooli orqali mentorlar holatini olish.
3. Har bir mentor bo'yicha ko'rsatkichlarni hisoblash:
   - Faol guruhlar soni va yuklama foizi (`loadPercent`).
   - Yangi guruh qabul qila olish imkoniyati (`canTakeNewGroup`).
   - Mutaxassislik yo'nalishi (Frontend, Python, Design).
4. O'quv bo'limi boshlig'i (Academic Manager) uchun taqqoslash jadvali va tavsiyalar blokini tuzish.

## Chiqish Formati (Output Template)

```markdown
### 👨‍🏫 MENTORLAR ISH YUKLAMASI VA BALANS TAHLILI
**Filial:** MARS Space — Yunusobod
**Sana:** {YYYY-MM-DD}
**Jami faol mentorlar:** {count} nafar | **Maksimal me'yor:** 3 ta guruh

| Mentor Ismi | Yo'nalishi | Faol Guruhlar | Yuklama % | Bo'sh O'rin | Yangi guruh berish mumkinmi? |
|-------------|------------|---------------|-----------|-------------|------------------------------|
| Sardor Aliyev | Frontend  | 2 ta          | 67%       | 1 ta guruh  | ✅ Ha (Tavsiya etiladi)      |
| Jasur Oripov  | Backend   | 3 ta          | 100%      | 0 ta guruh  | ⛔️ Yo'q (To'liq band)        |
| Nilufar Qodirova| UI/UX   | 1 ta          | 33%       | 2 ta guruh  | 🟢 Ha (Erkin resurs)         |
| Bekzod Umarov | Frontend  | 1 ta          | 33%       | 2 ta guruh  | 🟢 Ha (Erkin resurs)         |

#### 💡 O'quv bo'limiga tavsiyalar:
- **Yangi Frontend guruhi:** Sardor Aliyev yoki Bekzod Umarovga biriktirilsin.
- **Yangi Dizayn guruhi:** Nilufar Qodirovaga to'liq mos keladi.
- **Diqqat:** Jasur Oripov 3 ta guruh bilan to'liq yuklamada ishlamoqda, yangi backend guruhi uchun yangi mentor jalb qilish tavsiya etiladi.
```

## Verification
- MCP `mentor_workload` tooli qaytargan yuklama foizlari va bo'sh o'rinlar to'g'ri hisoblanganini tasdiqlash.
