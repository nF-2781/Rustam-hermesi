# YB-3110 — CFO (Bosh Moliya Direktori) Agenti Hujjati

> Integration verification (2026-11-24): the requested commits are imported into
> this checkout. Four finance profiles are installed and visible in the dashboard;
> native MCP login and all seven finance reads returned 200. Current parameters
> and limits are in `agents/c-level/03-cfo/api-contracts.md` and `agents/c-level/03-cfo/README.md`.
> The API table and numeric dialogue below describe the upstream scenario, not a
> newly executed report: current `daily_finance_report` compares months, and no
> `/api/finance/daily` call is made. Model completion/delegation was not run;
> existing Nous authentication currently requires re-login. No cron is installed.

**Jamoa:** Mars (LMS) | **Topshiruvchi:** @bmt_430 | **Muddat:** 24.11.2026, 18:40  
**Mas’ul a’zo:** **Islom Muhsimov** (@vxrnox, GitHub: https://github.com/muxsimovislom98-sketch)  
**Agent profili:** `mars-cfo` | **Lavozim:** CFO (Chief Financial Officer)  
**Bo‘ysunuv va hisobot beradi:** CEO **Rustam** (@rustam106, `mars-ceo`)  

---

## 1. Asosiy Moliyaviy Missiya va Savol

Mars LMS boshqaruv tizimida CFO agenti filiallarning moliyaviy barqarorligi, tushumlar shaffofligi, debitorlik (qarzdorlik) nazorati va kassa hisob-kitoblariga to'liq javobgar hisoblanadi.

> **Asosiy savol:**  
> *"Kassa qoldig'i, kunlik tushum, xarajatlar va qarzdorlik holati qanday? Reja bajarilishi uchun qancha mablag' yetishmayapti?"*

---

## 2. CFO Operatsion Arxitekturasi va Ierarxiyasi

```
                      ┌────────────────────────────┐
                      │ CEO — `mars-ceo`           │
                      │ Rustam (@rustam106)        │
                      └─────────────┬──────────────┘
                                    │
                                    ▼
                      ┌────────────────────────────┐
                      │ CFO — `mars-cfo`           │
                      │ Islom (@vxrnox)            │
                      └─────────────┬──────────────┘
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│ debt-collector   │       │ cashier-reporter │       │  budget-planner  │
│ (Qarzdorlik      │       │ (Kassa qoldig'i  │       │ (Oylik reja va   │
│  nazoratchisi)   │       │  va tushumlar)   │       │  balans prognoz) │
└──────────────────┘       └──────────────────┘       └──────────────────┘
```

---

## 3. 3 ta Ixtisoslashgan Moliya Sub-Agenti

| # | Sub-Agent | Vazifasi va Mas'uliyati | Ishlatadigan API / MCP Vositalari |
|---|---|---|---|
| 1 | **`debt-collector`** | O'quvchilar va guruhlar bo'yicha qarzdorlikni yoshi bo'yicha toifalash (1–7 kun texnik kechikish, 8–14 kun eslatma, 15–30 kun xavf guruhi, 30+ kun kritik qarzdorlik). Eslatma xatlari loyihalarini (`message_drafts`) tayyorlash. | `get_debts`, `debt_control_agent` |
| 2 | **`cashier-reporter`** | Kunlik va haftalik tushumlar, kassa qoldig'i, to'lov usullari (Uzcard, Humo, Naqd) bo'yicha tahliliy hisobot berish, kassa tafovutlarini (kamomad/ortiqcha) aniqlash. | `daily_finance_report`, `get_payments` |
| 3 | **`budget-planner`** | Filial oylik reja ijrosini kuzatish, oylik daromad va xarajat balansini taqqoslash, oyning 10 va 20-kunlarida "Erta ogohlantirish" (Early Warning) prognozini berish. | `get_finance_report`, `daily_finance_report` (compare=true) |

---

## 4. LMS Backend va FastMCP Moliya API Kontraktlari

Barcha amallar **faqat read-only** rejimida va filial konteksti chegarasida ishlaydi:

| Yo'nalish | Endpoint / FastMCP Tool | Kontrakt Shakli | Tavsif |
|---|---|---|---|
| **Qarzdorlik** | `get_debts` (`/finance/debts`) | `{ branch_id, status: "unpaid", days_overdue }` | Muddati o'tgan to'lovlar, o'quvchi ID va qarz miqdori |
| **Kunlik Moliya** | `daily_finance_report` (`/api/finance/daily`) | `{ date, branch_id, compare: true }` | Kunlik tushum, kassa qoldig'i, o'tgan kunga taqqoslash |
| **Umumiy Hisobot** | `get_finance_report` (`/api/finance/overview`) | `{ period: "2026-11", branch_id }` | Oylik tushum, xarajatlar moddasi, sof daromad |
| **To'lovlar Ro'yxati** | `get_payments` (`/api/branch/payments`) | `{ branch_id, method: "all" }` | Uzcard, Humo, Naqd to'lovlar reyestri |

---

## 5. Inson Tasdig'i (HITL) va Xavfsizlik Qoidalari

1. **Pul harakati bo'yicha qat'iy taqiq:**  
   Agent mustaqil pul yechish, to'lovni bekor qilish (refund), qarzni bazadan o'chirish, maosh to'lash yoki chegirma berish huquqiga ega emas. Barcha moliyaviy o'zgartirishlar faqat **CEO (Rustam) va CFO (Islom)** insoniy tasdig'i bilan amalga oshadi.
2. **Shaxsiy ma'lumotlar (PII) himoyasi:**  
   Qarzdorlar ro'yxati yoki hisobotlarda o'quvchilar va ota-onalarning telefon raqamlari doimo maskalanadi: `+998 90 *** ** 45`. Pasport yoki bank rekvizitlari ochiq matnda berilmaydi.
3. **Mijozlarga xabarlar:**  
   Agent mijozlarga to'g'ridan-to'g'ri xabar yubormaydi; faqat loyiha (`message_drafts`) tayyorlaydi. Xabarni yuborish reception yoki admin tasdig'idan keyin amalga oshiriladi.
4. **Boshqa rollar daxlsizligi:**  
   COO (operatsiyalar), CTO (texnika), CMO (marketing), HR (kadrlar) va CPO (mahsulot) sohalariga aralashmaydi.

---

## 6. Jonli Muloqot Namunasi (`hermes -p mars-cfo chat`)

Profil: `mars-cfo` · Mas'ul: Islom Muhsimov · Tizim: Hermes v0.21.2

```bash
$ hermes -p mars-cfo chat -Q -q "Bugungi filial moliyaviy holati va qarzdorliklar qanday?"

Kunlik moliyaviy hisobot va kassa holati (daily_finance_report, noyabr 2026):

| Ko'rsatkich | Qiymat | O'tgan kun / oy | Manba |
|---|---|---|---|
| Kunlik tushum | 24,650,000 UZS | 26,100,000 UZS (-5.5%) | daily_finance_report |
| Oylik jami xarajat | 17,100,000 UZS | 16,400,000 UZS (+4.2%) | get_finance_report |
| Kassa sof qoldig'i | 7,550,000 UZS | 9,700,000 UZS | daily_finance_report |
| Umumiy qarzdorlik | 4,200,000 UZS (18 o'quvchi) | 3,600,000 UZS (15 o'quvchi) | get_debts |

- Kritik qarzdorlik (30+ kun): 1,800,000 UZS (4 nafar o'quvchi). Ushbu o'quvchilar bo'yicha shaxsiy eslatma loyihasi tayyorlandi.
- Oylik reja prognozi: Noyabr rejasini (40,000,000 UZS) yopish uchun qolgan 7 kunda kuniga kamida 2,192,000 UZS tushum talab etiladi.
- Tavsiya: 30+ kunlik 4 nafar qarzdor bo'yicha eslatma xatlarini tasdiqlash uchun ma'muriyatga uzatish; kassa tafovutlari aniqlanmadi (0 UZS).
- Tasdiq talabi: To'lovni kechiktirish yoki chegirma berish faqat CEO (Rustam) tasdig'i bilan hal qilinadi.
```

---

## 7. Repozitoriy va Profil Manbalari

Ushbu CFO arxitekturasi repoda to'liq realizatsiya qilingan:

- **Operatsion Nizom:** [`agents/c-level/03-cfo/agents.md`](https://github.com/nF-2781/Rustam-hermesi/blob/islom/agents/c-level/03-cfo/agents.md)
- **Shaxsiyat va Jonli Muloqot:** [`agents/c-level/03-cfo/soul.md`](https://github.com/nF-2781/Rustam-hermesi/blob/islom/agents/c-level/03-cfo/soul.md)
- **API Kontraktlar:** [`agents/c-level/03-cfo/api-contracts.md`](https://github.com/nF-2781/Rustam-hermesi/blob/islom/agents/c-level/03-cfo/api-contracts.md)
- **Ierarxiya:** [`agents/c-level/03-cfo/hierarchy.json`](https://github.com/nF-2781/Rustam-hermesi/blob/islom/agents/c-level/03-cfo/hierarchy.json)
- **Sub-Agentlar:** [`agents/c-level/03-cfo/sub-agents/`](https://github.com/nF-2781/Rustam-hermesi/blob/islom/agents/c-level/03-cfo/sub-agents/)
- **Hermes Skill:** [`skills/mars-cfo-agent/SKILL.md`](https://github.com/nF-2781/Rustam-hermesi/blob/islom/skills/mars-cfo-agent/SKILL.md)
- **Hermes Profil O'rnatuvchi:** [`agents/install.py`](https://github.com/nF-2781/Rustam-hermesi/blob/islom/agents/install.py)
