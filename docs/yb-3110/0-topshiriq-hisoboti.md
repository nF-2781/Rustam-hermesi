# YB-3110 — yakuniy hisobot

**Jamoa:** Mars (LMS)
**Team Lead:** Rustam — @rustam106 (CTO, https://github.com/ahshdhdh)
**Topshiruvchi:** @bmt_430
**Muddat:** 24.11.2026, 18:40
**Holat:** barcha bandlar yopilgan, hujjatlar va agent fayllari `origin/rustam` da

---

## 1. Ustoz izohlari (kfc) → qanday yopildi

| # | Izoh | Holat | Qayerda |
|---|---|---|---|
| 1 | Ro'yxatda ismlar | ✅ 7 a'zo: ism + Telegram + GitHub | `2-agent-roster.md` §2 |
| 2 | CEO o'z jamoangdan | ✅ Kamollidin (@k_mukhamedov) — tashqi `@jamkaILZ` butunlay olib tashlandi | `2-agent-roster.md` §1–§2 |
| 3 | GitHub linklar | ✅ har bir a'zo uchun + barcha repolar `nF-2781` | `2-agent-roster.md` §2, `1-lms-context.md` §1 |
| 4 | Frontend manzili | ✅ 8 frontend repo + 8 deploy havolasi | `1-lms-context.md` §1 |
| 5 | Parol almashtirilganini yozish | ✅ yozildi, **parolning o'zi hech qayerda yo'q** | `1-lms-context.md` §4 |
| 6 | CTO `soul.md` + `agents.md` fayl sifatida | ✅ ikkita alohida fayl, repoda commit qilingan | `agents/cto/soul.md`, `agents/cto/agents.md` |

## 2. Jamoa va agentlar (7 kishi — 7 agent)

| # | Ism | Telegram | GitHub | Agent | Lavozim |
|---|---|---|---|---|---|
| 1 | Kamollidin | @k_mukhamedov | https://github.com/MukhamedovK | `mars-ceo` | CEO |
| 2 | Saidabzal | @Saidabza1 | https://github.com/vmio75494-bot | `mars-coo` | COO |
| 3 | Muhammadrizo | @rizo_x7k | https://github.com/rizo04684-sudo | `mars-cfo` | CFO |
| 4 | Rustam | @rustam106 | https://github.com/ahshdhdh | `mars-cto` | CTO |
| 5 | Muhammadsolih | @muhammad_solih13 | https://github.com/muhammadsolihtolqinxojaev13-bot | `mars-cmo` | CMO |
| 6 | Muhammadali (Chihuahua) | Chihuahua | https://github.com/muhammadali850 | `mars-cpo` | CPO |
| 7 | Islom | @vxrnox | https://github.com/muxsimovislom98-sketch | `mars-hr` | HR |

Ierarxiya: **CEO → C-level → sub-agentlar** (sub-agentlar `agents.md` ichida belgilangan).

## 3. CTO fayllari (Rustam)

| Fayl | Mazmuni | Holat |
|---|---|---|
| `agents/cto/soul.md` | agent **kim**: xarakter, ovoz ohangi, javob beradigan savollar, chegaralar, namuna | ✅ yozilgan |
| `agents/cto/agents.md` | agent **nima qiladi**: rol, hisobot zanjiri, sub-agentlar (`mcp-maintainer`, `dashboard-operator`), 7 vazifa, tool'lar, nosozlik zanjiri, nima qilmaydi, chiqish shakli | ✅ yozilgan |

Namuna sifatida yozilgan bu ikki fayl qolgan 6 rol uchun andoza bo'ldi — hammasi bir xil formatda.

## 4. Frontend manzillari

| Repo | Deploy |
|---|---|
| `mars-admin` | https://mars-admin-beta.vercel.app |
| `mars-branch-manager` | https://mars-branch-manager.vercel.app |
| `mars-finance` | https://mars-finance-orpin.vercel.app |
| `mars-intern` | https://mars-intern.vercel.app |
| `mars-mentor` | https://mars-mentor.vercel.app |
| `mars-parent` | https://mars-parent.vercel.app |
| `mars-student` | https://mars-student.vercel.app |
| `mars-tutor` | https://mars-tutor.vercel.app |

Backend: https://mars-backend-six.vercel.app · Swagger: `/api-docs/`

## 5. Parol holati

- LMS owner akkauntining paroli **almashtirildi**.
- Yangi qiymat **faqat lokal `.env`** faylida (`MARS_PHONE` / `MARS_PASSWORD`).
- Parol repo'ga, hujjatga, commitga va chatga **yozilmagan** — `.env` git'ga qo'shilmaydi.

## 6. Tekshirish (takrorlanadigan)

```bash
cd <repo>
bash agents/install.sh --check        # → 7/7 tayyor
hermes mcp test mars_lms              # → 22 tool
hermes -p mars-cto chat               # CTO agenti bilan suhbat
```

## 7. Jamoa uchun bir qatorli ko'rsatma

```bash
git pull && bash agents/install.sh && bash agents/install.sh --check && hermes -p mars-<rol> chat
```

Har bir a'zo o'z papkasini (`agents/<rol>/`) ochib ko'radi; o'zgartirsa — qayta `install.sh`.
