# Mars LMS — C-level agentlar

Har bir agent ikki fayldan iborat:

| Fayl | Nima yoziladi |
|---|---|
| `soul.md` | Agent **kim**: xarakter, ovoz ohangi, nimaga javob beradi, chegaralari |
| `agents.md` | Agent **nima qiladi**: vazifalar, hisobot, sub-agentlar, tool'lar, ish zanjiri, nima qilmaydi |

## Ierarxiya

```
CEO (mars-ceo) — Kamollidin
├── COO (mars-coo) — Saidabzal: operatsiya
│   ├── attendance-controller
│   ├── homework-controller
│   └── schedule-planner
├── CFO (mars-cfo) — Muhammadrizo: moliya
│   ├── debt-collector
│   └── cashier-reporter
├── CTO (mars-cto) — Rustam: platforma
│   ├── mcp-maintainer
│   └── dashboard-operator
├── CMO (mars-cmo) — Muhammadsolih: o'sish
│   ├── lead-nurturer
│   └── growth-analyst
├── CPO (mars-cpo) — Muhammadali "Chihuahua": mahsulot
│   ├── product-analyst
│   └── quality-coordinator
└── HR (mars-hr) — Islom: odamlar
    ├── mentor-coach
    └── recruiter
```

## O'rnatish

```bash
cd <repo>                     # repo ildizi (git toplevel)
bash agents/install.sh        # 7 ta Hermes profilini yaratadi va SOUL.md ni yozadi
bash agents/install.sh --check  # 7/7 holatini ko'rsatadi
hermes profile list           # mars-ceo ... mars-hr, mars-cpo ko'rinadi
hermes -p mars-cfo chat       # agent bilan suhbat
```

Barcha 7 agent yozilgan: har bir a'zo faqat `git pull` qilib, o'z agentini ochib ko'radi va
kerak bo'lsa o'z `soul.md` / `agents.md` faylini tahrirlaydi (keyin yana `install.sh`).

> **Mualliflik (ochiq):** `cto/` — Rustam (@rustam106) namunasi. Qolgan 6 rolning
> `soul.md` + `agents.md` skeleti Team Lead tomonidan yozib berilgan; har bir a'zo o'z
> faylini o'qib, o'z ishiga moslashtiradi va o'z nomidan tasdiqlaydi.

`install.sh` har bir profil uchun:
1. `hermes profile create mars-<role> --clone --description "<rol>"` — model/kalitlar
   nusxalanadi, sessiya va tarix **nusxalanmaydi**;
2. `soul.md` + `agents.md` ni bitta `profiles/mars-<role>/SOUL.md` ga yozadi
   (Hermes persona va qoidalarni bitta fayldan o'qiydi);
3. `terminal.cwd` ni repo ildiziga qo'yadi — agent MCP server va repo fayllarini ko'radi.

Qayta o'rnatish xavfsiz: `SOUL.md` qayta yoziladi, qolgan state saqlanadi.

## Fayllar holati

| Papka | Agent | Holat |
|---|---|---|
| `ceo/` | CEO | to'liq yozilgan — Kamollidin (egasi ko'rib chiqadi) |
| `coo/` | COO | to'liq yozilgan — Saidabzal |
| `cfo/` | CFO | to'liq yozilgan — Muhammadrizo |
| `cto/` | CTO | to'liq yozilgan (namuna) — Rustam |
| `cmo/` | CMO | to'liq yozilgan — Muhammadsolih |
| `cpo/` | CPO | to'liq yozilgan — Muhammadali (Chihuahua) |
| `hr/` | HR | to'liq yozilgan — Islom |

## Qoidalar (barcha agentlar uchun majburiy)

1. **Pul va tashqi ta'sirli amal faqat inson tasdig'i bilan.** To'lov qabul qilish,
   refund, oylik to'lash, o'quvchini o'chirish — agent bajarmaydi, faqat loyiha/hisobot beradi.
2. **Xabar yuborish yo'q.** `message_drafts` / `reply_drafts` — matn loyihasi, yuborish odam ishi.
3. **Ma'lumot manbai — faqat `mcp__mars_lms__*` tool'lari.** Raqamni taxmin qilish,
   "o'ylab topish" taqiqlanadi. Tool xato bersa — xatoni aytadi, raqam to'qimaydi.
4. **Har bir javobda manba:** qaysi tool, qaysi davr (`month`), qaysi filial.
5. **Shaxsiy ma'lumot (o'quvchi telefoni, qarzi) faqat ish uchun va faqat ichki hisobotda.**
6. **Eskalatsiya:** 403 (rol yetarli emas), takroriy 401, backend 5xx → CTO/CEO ga, taxmin qilmasdan.
