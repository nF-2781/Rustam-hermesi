# Mars LMS — C-level agentlar

Har bir agent ikki fayldan iborat:

| Fayl | Nima yoziladi |
|---|---|
| `soul.md` | Agent **kim**: xarakter, ovoz ohangi, nimaga javob beradi, chegaralari |
| `agents.md` | Agent **nima qiladi**: vazifalar, hisobot, sub-agentlar, tool'lar, ish zanjiri, nima qilmaydi |

## Ierarxiya

```
CEO (mars-ceo)
├── COO (mars-coo) — operatsiya
│   ├── attendance-controller
│   ├── homework-controller
│   └── schedule-planner
├── CFO (mars-cfo) — moliya
│   ├── debt-collector
│   └── cashier-reporter
├── CTO (mars-cto) — platforma
│   ├── mcp-maintainer
│   └── dashboard-operator
├── CMO (mars-cmo) — o'sish
│   ├── lead-nurturer
│   └── growth-analyst
└── HR (mars-hr) — odamlar
    ├── mentor-coach
    └── recruiter
```

## O'rnatish

```bash
cd <repo>                     # repo ildizi (git toplevel)
bash agents/install.sh        # 6 ta Hermes profilini yaratadi va SOUL.md ni yozadi
hermes profile list           # mars-ceo ... mars-hr ko'rinadi
hermes -p mars-cfo chat       # agent bilan suhbat
```

`install.sh` har bir profil uchun:
1. `hermes profile create mars-<role> --clone --description "<rol>"` — model/kalitlar
   nusxalanadi, sessiya va tarix **nusxalanmaydi**;
2. `soul.md` + `agents.md` ni bitta `~/.hermes/profiles/mars-<role>/SOUL.md` ga yozadi
   (Hermes persona va qoidalarni bitta fayldan o'qiydi);
3. `terminal.cwd` ni repo ildiziga qo'yadi — agent MCP server va repo fayllarini ko'radi.

Qayta o'rnatish xavfsiz: `SOUL.md` qayta yoziladi, qolgan state saqlanadi.

## Qoidalar (barcha agentlar uchun majburiy)

1. **Pul va tashqi ta'sirli amal faqat inson tasdig'i bilan.** To'lov qabul qilish,
   refund, oylik to'lash, o'quvchini o'chirish — agent bajarmaydi, faqat loyiha/hisobot beradi.
2. **Xabar yuborish yo'q.** `message_drafts` / `reply_drafts` — matn loyihasi, yuborish odam ishi.
3. **Ma'lumot manbai — faqat `mcp__mars_lms__*` tool'lari.** Raqamni taxmin qilish,
   "o'ylab topish" taqiqlanadi. Tool xato bersa — xatoni aytadi, raqam to'qimaydi.
4. **Har bir javobda manba:** qaysi tool, qaysi davr (`month`), qaysi filial.
5. **Shaxsiy ma'lumot (o'quvchi telefoni, qarzi) faqat ish uchun va faqat ichki hisobotda.**
6. **Eskalatsiya:** 403 (rol yetarli emas), takroriy 401, backend 5xx → CTO/CEO ga, taxmin qilmasdan.

## Fayllar

| Papka | Agent | Hisobot beradi | Boshqaradi |
|---|---|---|---|
| `ceo/` | CEO | odam (teamlead) | barcha C-level |
| `coo/` | COO | CEO | attendance/homework/schedule controller |
| `cfo/` | CFO | CEO | debt-collector, cashier-reporter |
| `cto/` | CTO | CEO | mcp-maintainer, dashboard-operator |
| `cmo/` | CMO | CEO | lead-nurturer, growth-analyst |
| `hr/` | HR | CEO | mentor-coach, recruiter |
