# YB-3110 — 2-topshiriq: Agentlar taqsimoti (kim — qaysi agent)

**Jamoa:** Mars | **Topshiruvchi:** @bmt_430 | **Muddat:** bugun 21:30
**Team Lead:** Rustam (@rustam106) — CTO

Har bir a'zoga bitta agent: jamoa **7 kishi**, agent ham **7 ta**.
Ierarxiya: **CEO → C-level → sub-agentlar**. Sub-agentlar keyingi darsda to'ldiriladi,
lekin har bir `agents.md` da ularning joyi allaqachon belgilangan.

## 1. Ierarxiya sxemasi

```
                     ┌────────────────────────────┐
                     │ CEO — `mars-ceo`           │
                     │ Kamollidin (@k_mukhamedov) │
                     └─────────────┬──────────────┘
   ┌──────────┬──────────┬─────────┼─────────┬──────────┬──────────┐
   ▼          ▼          ▼         ▼         ▼          ▼
  COO        CFO        CTO       CMO       CPO        HR
```

## 2. Kim — qaysi agent

| # | A'zo | Telegram | GitHub | Agent (profil) | Lavozim | Asosiy savol |
|---|---|---|---|---|---|---|
| 1 | Kamollidin | @k_mukhamedov | https://github.com/MukhamedovK | `mars-ceo` | **CEO** | "Filial bugun qanday ishlayapti va nima qilish kerak?" |
| 2 | Saidabzal | @Saidabza1 | https://github.com/vmio75494-bot | `mars-coo` | COO | "Operatsiya: davomat, uy vazifasi, jadval, tasdiqlar" |
| 3 | Muhammadrizo | @rizo_x7k | https://github.com/rizo04684-sudo | `mars-cfo` | CFO | "Pul: tushum, qarzdorlik, xarajat, qoldiq" |
| 4 | Rustam | @rustam106 | https://github.com/ahshdhdh | `mars-cto` | CTO | "Platforma (MCP, backend, dashboard, agentlar) sog'lommi?" |
| 5 | Muhammadsolih | @muhammad_solih13 | https://github.com/muhammadsolihtolqinxojaev13-bot | `mars-cmo` | CMO | "O'sish: yangi o'quvchi, waitlist, murojaatlar" |
| 6 | Muhammadali | — | https://github.com/muhammadali850 | `mars-cpo` | CPO | "Mahsulot: o'quvchi tajribasi, sifat, takliflar" |
| 7 | Islom | @vxrnox | https://github.com/muxsimovislom98-sketch | `mars-hr` | HR | "Odamlar: mentor yuklamasi, sifat, onboarding" |

## 3. Har bir agentning fayllari

```
agents/
  README.md          — ierarxiya, ishga tushirish qoidasi
  ceo/soul.md  ceo/agents.md      ← skelet (Kamollidin to'ldiradi)
  coo/soul.md  coo/agents.md      ← skelet (Saidabzal to'ldiradi)
  cfo/soul.md  cfo/agents.md      ← skelet (Muhammadrizo to'ldiradi)
  cto/soul.md  cto/agents.md      ← to'liq yozilgan (Rustam)
  cmo/soul.md  cmo/agents.md      ← skelet (Muhammadsolih to'ldiradi)
  cpo/soul.md  cpo/agents.md      ← skelet (Muhammadali to'ldiradi)
  hr/soul.md   hr/agents.md       ← skelet (Islom to'ldiradi)
  install.sh         — soul.md + agents.md → Hermes profil SOUL.md
```

- `soul.md` — agent **kim**: xarakter, til, ohang, nimaga javob beradi, chegaralari.
- `agents.md` — agent **nima qiladi**: vazifalar, hisobot zanjiri, boshqaradigan
  sub-agentlar, ishlatadigan API/MCP tool'lar, ish zanjiri, **nima qilmaydi**.

> **Vazifa taqsimoti:** har bir a'zo **o'z** agentining `soul.md` va `agents.md` faylini
> o'zi yozadi. Namuna va to'ldirilgan holat — `agents/cto/` (CTO: Rustam).

## 4. Hisobot zanjiri (rasmiy)

```
sub-agent  →  C-level  →  CEO (Kamollidin)  →  odam (teamlead)
                          ↘  CTO (Rustam, texnik tasdiq: platforma o'zgarishlari)
Har qanday moliyaviy yoki tashqi ta'sirli amal → inson tasdig'i (CEO emas, ODAM)
```

## 5. Ishga tushirish (har bir a'zo o'z agenti bilan)

```bash
cd <repo>                                     # repo ildizi
bash agents/install.sh                        # 7 profilni yaratadi (bir marta)
bash agents/install.sh --check                # 7/7 tayyorligini ko'rsatadi
hermes -p mars-cfo chat                       # o'z agentingiz bilan suhbat
```

Profil yaratilgach `profiles/mars-cfo/` (yoki `~/.hermes/profiles/mars-cfo/`) ichida
o'z `SOUL.md`, `config.yaml`, `.env`, sessiyalari bo'ladi — boshqa agentlarnikiga aralashmaydi.

## 6. Tekshirish uchun topshiriladigan narsa

1. shu fayl (2-topshiriq) — kim qaysi agent;
2. `agents/*/soul.md` va `agents/*/agents.md` (7 ta agent);
3. `bash agents/install.sh --check` chiqishi (7/7 tayyor);
4. bitta agent bilan qilingan jonli suhvat namunasi (`mars-cto chat` → platforma holati).
