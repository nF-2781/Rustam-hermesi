# YB-3110 — 2-topshiriq: Agentlar taqsimoti (kim — qaysi agent)

**Jamoa:** Mars | **Topshiruvchi:** @bmt_430 | **Muddat:** 24.11.2026, 18:40
**Team Lead:** Rustam (@rustam106) — CEO agenti (`mars-ceo`)
**Holat:** 2-topshiriq tayyor — 7 a'zo, 7 agent; barcha `soul.md` + `agents.md` yozilgan va repo'da

Har bir a'zoga bitta agent: jamoa **7 kishi**, agent ham **7 ta**.
Ierarxiya: **CEO → C-level → sub-agentlar**. Sub-agentlar keyingi darsda to'ldiriladi,
lekin har bir `agents.md` da ularning joyi allaqachon belgilangan.

## 1. Ierarxiya sxemasi

```
                     ┌────────────────────────────┐
                     │ CEO — `mars-ceo`           │
                     │ Rustam (@rustam106)        │
                     └─────────────┬──────────────┘
   ┌──────────┬──────────┬─────────┼─────────┬──────────┬──────────┐
   ▼          ▼          ▼         ▼         ▼          ▼
  COO        CFO        CTO       CMO       CPO        HR
```

## 2. Kim — qaysi agent

**Tartib — yuqoridan pastga:** 1 — eng yuqori (CEO), 7 — eng past (HR).

| # | A'zo | Telegram | GitHub | Agent (profil) | Lavozim | Asosiy savol |
|---|---|---|---|---|---|---|
| 1 | Rustam | @rustam106 | https://github.com/ahshdhdh | `mars-ceo` | **CEO** | "Filial bugun qanday ishlayapti va nima qilish kerak?" |
| 2 | Kamollidin | @k_mukhamedov | https://github.com/MukhamedovK | `mars-coo` | COO | "Operatsiya: davomat, uy vazifasi, jadval, tasdiqlar" |
| 3 | Islom | @vxrnox | https://github.com/muxsimovislom98-sketch | `mars-cfo` | CFO | "Pul: tushum, qarzdorlik, xarajat, qoldiq" |
| 4 | Saidabzal | @Saidabza1 | https://github.com/vmio75494-bot | `mars-cto` | CTO | "Platforma (MCP, backend, dashboard, agentlar) sog'lommi?" |
| 5 | Muhammadrizo | @rizo_x7k | https://github.com/rizo04684-sudo | `mars-cmo` | CMO | "O'sish: yangi o'quvchi, waitlist, murojaatlar" |
| 6 | Muhammadsolih | @muhammad_solih13 | https://github.com/muhammadsolihtolqinxojaev13-bot | `mars-cpo` | CPO | "Mahsulot: o'quvchi tajribasi, sifat, takliflar" |
| 7 | Muhammadali "Chihuahua" | Chihuahua | https://github.com/muhammadali850 | `mars-hr` | HR | "Odamlar: mentor yuklamasi, sifat, onboarding" |

> **CEO — o'z jamoamizdan:** Rustam (@rustam106, https://github.com/ahshdhdh) — Team Lead.
> Boshqa jamoadan olingan `@jamkaILZ` bu hujjatdan butunlay olib tashlandi.
> **Ismlar + Telegram + GitHub** — yuqoridagi jadvalning 2–4-ustunlari.
> **Frontend manzillari** — `1-lms-context.md` §1 (8 repo + 8 deploy havolasi).
> **Parol holati** — almashtirildi; yangi qiymat repo'ga, hujjatga va chatga yozilmagan (`1-lms-context.md` §4).

## 3. Har bir agentning fayllari

```
agents/
  README.md          — ierarxiya, ishga tushirish qoidasi
  ceo/soul.md  ceo/agents.md      ← yozilgan (Rustam)
  coo/soul.md  coo/agents.md      ← yozilgan (Kamollidin)
  cfo/soul.md  cfo/agents.md      ← yozilgan (Islom)
  cto/soul.md  cto/agents.md      ← yozilgan (Saidabzal; mazmun — Rustam namunasi)
  cmo/soul.md  cmo/agents.md      ← yozilgan (Muhammadrizo)
  cpo/soul.md  cpo/agents.md      ← yozilgan (Muhammadsolih)
  hr/soul.md   hr/agents.md       ← yozilgan (Muhammadali / Chihuahua)
  install.sh         — soul.md + agents.md → Hermes profil SOUL.md
```

- `soul.md` — agent **kim**: xarakter, til, ohang, nimaga javob beradi, chegaralari.
- `agents.md` — agent **nima qiladi**: vazifalar, hisobot zanjiri, boshqaradigan
  sub-agentlar, ishlatadigan API/MCP tool'lar, ish zanjiri, **nima qilmaydi**.

> **Holat:** 7 agentning hammasi yozilgan (Rustam — namuna sifatida). Har bir a'zo
> `git pull` qiladi, o'z papkasini (`agents/<rol>/`) ochib ko'radi, kerak bo'lsa tahrirlaydi
> va `bash agents/install.sh` bilan profilini yangilaydi.

## 4. Hisobot zanjiri (rasmiy)

```
sub-agent  →  C-level  →  CEO (Rustam)  →  odam (topshiruvchi)
                          ↘  CTO (Saidabzal, texnik tasdiq: platforma o'zgarishlari)
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
4. bitta agent bilan qilingan jonli suhbat namunasi (`hermes -p mars-cto chat` → agent o'zini va chegaralarini tanishtirdi) — to'liq matn `0-topshiriq-hisoboti.md` §7 da.
