---
name: mars-tasdiqlarni-jamlovchi-yordamchi
description: Chegirma va muzlatish sorovlarini jamlab taqdim etish.
version: 1.0.0
author: Saidabza1, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mars-lms, approval, requests, discount-requests, branch-management]
---

# MARS LMS — Tasdiqlarni Jamlovchi Yordamchi Agent

Chegirma, o'quvchini muzlatish (freeze), kassa tuzatishlari va boshqa ruxsat talab etuvchi so'rovlarni bir joyga to'playdi, muhimligi va kutilgan vaqtiga ko'ra tizimlashtiradi hamda mas'ul rahbarlarga qaror qabul qilish uchun tayyor hisobot beradi.

## When to Use
- Rahbariyatning kunlik ertalabki rejalashtirish majlisida.
- 24 soatdan ortiq vaqt tasdiqlanmasdan yotib qolgan so'rovlar aniqlanganda.
- Chegirma yoki to'lovni bekor qilish so'rovlari bo'yicha tezkor qaror talab etilganda.

## Prerequisites
- `mars-lms` MCP serveri (`login`, `pending_requests` toollari mavjud).

## Ish Zanjiri (Chain of Action)
1. `login(phone, password, role="admin")` orqali tizimga kirish.
2. `pending_requests()` tooli orqali barcha kutilayotgan so'rovlarni olish.
3. So'rovlarni toifa va mas'ul roliga ko'ra guruhlash:
   - **Chegirmalar (Discount Requests):** Filial Direktori tasdig'i.
   - **Muzlatish (Freeze Requests):** Finance Manager tasdig'i.
   - **Kassa tuzatish (Adjustment Requests):** Bosh Bugalter tasdig'i.
4. Kutilgan kunlar (days waiting) va summaga ko'ra tartiblash.
5. Qaror qabul qiluvchi rahbar uchun yakuniy ko'rib chiqish blokini tuzish.

## Chiqish Formati (Output Template)

```markdown
### 📑 TASDIQ KUTILAYOTGAN SO'ROVLAR JURNALI
**Filial:** MARS Space — Yunusobod
**Sana:** {YYYY-MM-DD}
**Jami ochiq so'rovlar:** {count} ta

| ID | So'rov Turi | Talaba / Xodim | Summa | Asos / Sabab | Kutmoqda | Mas'ul Rahbar |
|----|-------------|----------------|-------|--------------|----------|---------------|
| {ID}| 🏷 Chegirma | {Ism}          | {Sum} | {Sabab}      | {Kun} kun| Direktor      |
| {ID}| ❄️ Muzlatish| {Ism}          | 0 UZS | {Sabab}      | {Kun} kun| Finance Mgr   |

#### ⚡️ Zudlik bilan ko'rib chiqilishi kerak bo'lganlar:
- **{ID} ({Talaba}):** {Sabab}. {Kun} kundan beri kutilmoqda.
  - [Tasdiqlash] tugmasi havolasi: `/api/branch/requests/{id}/approve`
  - [Rad etish] tugmasi havolasi: `/api/branch/requests/{id}/reject`
```

## Verification
- MCP `pending_requests` orqali qaytgan har bir so'rovda `approverRole`, `amount` va `daysWaiting` maydonlari mavjudligi tekshirilsin.
