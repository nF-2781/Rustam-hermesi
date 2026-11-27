# WORKFLOW — Finance & Payroll

## Triggerlar

| Vaqt / hodisa | Amal |
|---|---|
| Har kuni 09:00 | Kassa hisoboti (skill `skill-cashier-report`) |
| Har kuni 10:00 | Qarzdorlik skani → eslatma loyihalari |
| `status-requests` yangi so'rov | Muzlatish tavsiyasi (tasdiq/rad + sabab) |
| `auditor-security` → `ATTENDANCE_APPROVED_MONTH` | Oylik loyihasi |
| Oy oxiri | Byudjet fakt vs reja |
| Xarajat so'rovi | Limit tekshiruvi → kerak bo'lsa odam tasdig'i |

## Algoritm — kunlik kassa

```text
1. Auth: POST /api/auth/login → GET /api/auth/me (rol: branch_admin/finance).
2. Tushum:  GET /api/branch/payments?date=<kun>  → naqd/karta/online yig'indi.
3. Xarajat: GET /api/branch/expenses?date=<kun>  → toifalar bo'yicha.
4. Qoldiq:  GET /api/finance/overview?period=<oy> (kassa, trend).
5. Farq:    oldingi kun bilan solishtir; 10% dan ortiq chetlanish — sabab yoz.
6. Qarz:    GET /api/branch/debtors?days_overdue=30 → summa + soni.
7. Yoz:     Obsidian `04_finance/daily/<sana>.md`; raqamlar manbali.
8. Ogohlantirish: qoldiq < 3 kunlik xarajat bo'lsa — ceo-strategist + odam.
```

## Algoritm — oylik maosh loyihasi (`skill-dispute-payroll`)

```text
1. Tasdiqlangan davomat: GET /api/branch/attendance-confirmations?period=<oy>&status=approved
2. Nizolar yopilganini tekshir: `disputed`/`overdue` qolsa — auditor-security ga qaytarish.
3. Hisob: GET /api/finance/owner/mentor-earnings?period=<oy>  (14 551 UZS / dars).
4. Qoralama: POST /api/finance/salaries — status `draft`, izohda davr va asos.
5. Tasdiq: odam (2FA/Telegram). Agent `PATCH .../status` = `paid` qilmaydi.
6. Yoz: Obsidian `04_finance/payroll/<oy>.md` + farq izohi.
```

## Qoida tekshiruvlari (`security_sandbox`)

| Amal | Shart |
|---|---|
| `POST /api/finance/salaries`, `PATCH .../status` | inson tasdig'i (2FA) |
| `POST/PATCH /api/branch/expenses` > 1 000 000 UZS | inson tasdig'i |
| har qanday `DELETE` / `void` | inson tasdig'i + `reason` bo'sh emas |
| `PATCH /api/branch/payments/{id}` | `reason` majburiy |
| boshqa filial `branchId` | rad (403) |

## Xato holatlari

| Holat | Amal |
|---|---|
| Summalar mos emas | farqni yoz, "tekshiruv kerak" — taxmin qilib tuzatmaslik |
| `payments` bo'sh (yangi kun) | "harakat yo'q" deb yozish, 0 bilan aralashtirmaslik |
| 403 (moliya roli yo'q) | to'xtash, CFO/odamga eskalatsiya |
| `mentor-earnings` 5xx | loyihani to'xtatish, davomat manbasini ko'rsatish |

## O'lchov

- Kassa hisoboti aniqligi (qayta hisoblash bilan farq = 0).
- 30+ kun qarzdorlik summasi trendi (oylik −10% maqsad).
- Oylik loyihasida nizo qaytarishlar soni (maqsad 0).
