# YB-3110 — 2-topshiriq: Agentlar taqsimoti (kim — qaysi agent)

**Jamoa:** Mars | **Topshiruvchi:** @bmt_430 | **Muddat:** bugun 21:30

Har bir a'zoga bitta agent. Ierarxiya: **CEO → C-level → sub-agentlar**.
Hozirgi bosqichda asosiy kuch — rahbariyat (C-level). Sub-agentlar keyingi darsda
to'ldiriladi, lekin har bir `agents.md` da ularning joyi va vazifasi allaqachon belgilangan.

## 1. Ierarxiya sxemasi

```
                         ┌──────────────────┐
                         │  CEO (mars-ceo)  │  ← @jamkaILZ
                         └────────┬─────────┘
        ┌───────────────┬────────┼────────┬───────────────┐
        ▼               ▼        ▼        ▼               ▼
   ┌─────────┐   ┌──────────┐ ┌──────┐ ┌──────┐   ┌──────────┐
   │   COO   │   │   CFO    │ │ CTO  │ │ CMO  │   │    HR    │
   └────┬────┘   └────┬─────┘ └──┬───┘ └──┬───┘   └────┬─────┘
        │             │          │        │            │
   attendance-    debt-      mcp-     lead-        mentor-
   controller     collector  maintainer nurturer    coach
   homework-      cashier-   dashboard- growth-     recruiter
   controller     reporter   operator  analyst     onboarding-
   schedule-                                        buddy
   planner
```

## 2. Kim — qaysi agent

| # | A'zo | Agent (profil) | Lavozim | Asosiy savol |
|---|---|---|---|---|
| 1 | @jamkaILZ | `mars-ceo` | CEO | "Filial bugun qanday ishlayapti va nima qilish kerak?" |
| 2 | @rustam106 | `mars-cto` | CTO | "Platforma (MCP, backend, dashboard, agentlar) sog'lommi?" |
| 3 | _(to'ldirilsin)_ | `mars-coo` | COO | "Operatsiya: davomat, uy vazifasi, jadval, tasdiqlar" |
| 4 | _(to'ldirilsin)_ | `mars-cfo` | CFO | "Pul: tushum, qarzdorlik, xarajat, qoldiq" |
| 5 | _(to'ldirilsin)_ | `mars-cmo` | CMO | "O'sish: yangi o'quvchi, waitlist, murojaatlar" |
| 6 | _(to'ldirilsin)_ | `mars-hr` | HR | "Odamlar: mentor yuklamasi, sifat, onboarding" |

> **Muhim:** 3–6 qatorlardagi ismlar teamlead tomonidan to'ldiriladi va @bmt_430 ga
> yuboriladi. Jamoa 6 kishidan kam bo'lsa, `mars-hr` va `mars-cmo` ni bitta a'zoga
> birlashtirish mumkin (CEO qarori bilan), lekin **CEO va CTO majburiy**.

## 3. Har bir agentning fayllari

```
agents/
  README.md          — ierarxiya, ishga tushirish qoidasi
  ceo/soul.md  ceo/agents.md
  coo/soul.md  coo/agents.md
  cfo/soul.md  cfo/agents.md
  cto/soul.md  cto/agents.md
  cmo/soul.md  cmo/agents.md
  hr/soul.md   hr/agents.md
  install.sh         — fayllardan Hermes profil yasaydi (soul.md + agents.md → SOUL.md)
```

- `soul.md` — agent **kim**: xarakter, til, ohang, nimaga javob beradi, chegaralari.
- `agents.md` — agent **nima qiladi**: vazifalar, hisobot zanjiri, boshqaradigan
  sub-agentlar, ishlatadigan API/MCP tool'lar, ish zanjiri, **nima qilmaydi**.

## 4. Hisobot zanjiri (rasmiy)

```
sub-agent  →  C-level  →  CEO  →  @jamkaILZ (inson, teamlead)
                        ↘  @rustam106 (texnik tasdiq: platforma o'zgarishlari)
Har qanday moliyaviy yoki tashqi ta'sirli amal → inson tasdig'i (CEO emas, ODAM)
```

## 5. Ishga tushirish (har bir a'zo o'z agenti bilan)

```bash
cd <repo>                                     # repo ildizi
bash agents/install.sh                        # 6 profilni yaratadi (bir marta)
hermes -p mars-cfo chat                       # yoki: mars-cfo chat (alias)
```

Profil yaratilgach `~/.hermes/profiles/mars-cfo/` ichida o'z `SOUL.md`, `config.yaml`,
`.env`, sessiyalari bo'ladi — boshqa agentlarnikiga aralashmaydi.

## 6. Tekshirish uchun topshiriladigan narsa

1. shu fayl (2-topshiriq) — kim qaysi agent;
2. `agents/*/soul.md` va `agents/*/agents.md`;
3. `hermes profile list` chiqishi (6 profil ko'rinadi);
4. bitta agent bilan qilingan jonli suhbat namunasi (`mars-cfo chat` → qarzdorlik hisoboti).
