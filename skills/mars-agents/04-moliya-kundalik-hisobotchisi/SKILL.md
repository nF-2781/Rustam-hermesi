---
name: mars-moliya-kundalik-hisobotchisi
description: Filial kundalik daromad va xarajat hisobotini tuzish.
version: 1.0.0
author: vxrnox, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mars-lms, finance, daily-report, revenue, executive-summary]
---

# MARS LMS — Moliya Kundalik Hisobotchisi Agent

Filialning kunlik moliyaviy oqimini (tushum, kassa xarajatlari, to'lov turlari va sof kassa qoldig'i) umumlashtirib, filial rahbari va moliya bo'limi uchun ixcham, tushunarli kundalik boshqaruv hisobotini tayyorlaydi.

## When to Use
- Har kuni kechki kassa yopilishi vaqtida (masalan, 20:00 da).
- Filial rahbari kundalik kassa tushumini talab qilganda.
- Daromad va xarajatlar dinamikasini kechagi kun bilan taqqoslashda.

## Prerequisites
- `mars-lms` MCP serveri (`login`, `finance_daily_report`, `payments` toollari mavjud).

## Ish Zanjiri (Chain of Action)
1. `login(phone, password, role="financeManager")` orqali moliya huquqi bilan tizimga kirish.
2. `finance_daily_report(date)` toolini chaqirib, kunlik moliyaviy ko'rsatkichlarni olish.
3. Ko'rsatkichlarni guruhlash:
   - Jami tushum (Gross Revenue) va to'lov usullari (Click, Payme, Naqd, Bank o'tkazmasi).
   - Filial xarajatlari (Ofis ta'minoti, internet, tadbirlar).
   - Sof kunlik kassa oqimi (Net Cashflow) va joriy kassa qoldig'i.
   - Oldingi kun bilan dinamik taqqoslash.
4. Rahbariyat uchun Hermes boshqaruv paneli formatida hisobot tuzish.

## Chiqish Formati (Output Template)

```markdown
### 💰 MARS IT SCHOOL — KUNDALIK MOLIYA HISOBOTI
**Filial:** MARS Space — Yunusobod
**Sana:** {YYYY-MM-DD}
**Kassa holati:** ✅ Yopiq

| Ko'rsatkich | Summa (UZS) | Izoh / Dinamika |
|-------------|-------------|-----------------|
| 🟢 Bugungi tushum (Revenue) | **{Revenue}** | {N} ta to'lov qabul qilindi |
| 🔴 Bugungi xarajatlar | **{Expenses}** | Asosiy moddalar bo'yicha |
| 💎 Sof kunlik tushum | **{NetCashflow}** | Tushum minus xarajat |
| 🏦 Kassa jami qoldig'i | **{CashboxBalance}** | Kassa xavfsiz holatda |

#### 💳 To'lov manbalari:
- Click: {ClickSum} UZS
- Payme: {PaymeSum} UZS
- Naqd: {CashSum} UZS
- Bank o'tkazmasi: {BankSum} UZS

#### 📈 Tahliliy xulosa:
> "Bugungi tushum kechagiga nisbatan {Farq}% ga oshdi. Kassa qoldig'i va to'lovlar mosligi to'liq tasdiqlandi. Kassa hisobida tafovutlar mavjud emas."
```

## Verification
- MCP `finance_daily_report` tooli qaytargan `dailyNetCashflow == dailyRevenue - dailyExpenses` ekanligi tasdiqlansin.
