# YB-3110 — Hermes uchun AI-agentlar ro'yxati

**Muddat:** 19.11.2026, 18:40
**Manba:** mars-backend API (`/api/ai/analytics/*`, `/api/branch/*`, `/api/finance/*`) — `mars-mcp-server` orqali.

> Pastdagi blokni Hermes dashboardidagi jamoaviy suhbatga to'liq nusxalab yuboring.
> Har bir agent uchun 3 majburiy band: **nomi**, **opisaniyasi**, **ish zanjiri**.

---

## NUSXALASH UCHUN MATN

```text
MARS LMS uchun 10 ta AI-agent ro'yxati (YB-3110). Barchasi mars-backend REST API
va mars-mcp-server (stdio MCP) ustida ishlaydi. Autentifikatsiya: POST /api/auth/login
-> Bearer JWT. Har bir agent uchun: nomi, opisaniyasi, ish zanjiri.

1) DAVOMAT QO'RIQCHISI (Attendance Sentinel)
Opisaniya: Har kuni davomatni tekshiradi, 80% dan past guruh va o'quvchilarni topadi,
sababsiz qoldirilgan darslarni aniqlaydi. Muammo: davomat pasayishi o'quvchi ketishiga
olib keladi, lekin mentor buni kech ko'radi.
Ish zanjiri:
 1. GET /api/ai/analytics/attendance-summary?branchId=...&startDate=...&endDate=...
    va GET /api/branch/attendance (tasdiqlanmagan yozuvlar) o'qiladi.
 2. Guruh va o'quvchi kesimida 7/30 kunlik trend hisoblanadi: 80% ostidagilar,
    2+ ketma-ket sababsiz kelmaganlar, mentor tasdiqlamagan davomatlar ajratiladi.
 3. Signal: Hermes gateway orqali Telegram — mentorga shaxsiy xabar (o'z guruhi),
    filial menejeriga kunlik qisqa ro'yxat (guruh, foiz, o'quvchi ismi), 09:00 da.

2) QARZDORLAR KUZATUVCHISI (Debt Collector)
Opisaniya: Qarzdor o'quvchilarni qarz muddati bo'yicha ajratadi va to'lov eslatmasini
bosqichma-bosqich yuboradi. Muammo: qarzlar kech aniqlanadi, kassa qurib qoladi.
Ish zanjiri:
 1. GET /api/ai/analytics/debtors-summary?branchId=...&minDebt=0&page=1&limit=100
    va GET /api/finance/debtors o'qiladi.
 2. Qarz 7/14/30+ kunlik chegaralarga bo'linadi, to'lov tarixi bilan solishtiriladi
    (GET /api/branch/students/:id/payments), takroriy va'da berib to'lamaganlar belgilanadi.
 3. Signal: moliyachiga Telegramda ustuvor ro'yxat; 14+ kunliklar uchun ota-onaga
    GET /api/student-portal/billing havolasi bilan eslatma; 30+ kunliklar adminga
    "bloklash/ muzlatish ko'rib chiqish" kartasi sifatida yuboriladi.

3) MOLIYA SALOMATLIGI AGENTI (Finance Pulse)
Opisaniya: Kunlik daromad/xarajat/sof balansni kuzatadi, reja va o'tgan oyga nisbatan
chetlanishni aytadi. Muammo: filial rahbari moliyaviy holatni faqat oy oxirida biladi.
Ish zanjiri:
 1. GET /api/ai/analytics/finance-summary?branchId=...&month=YYYY-MM
    va GET /api/finance/overview?start_date=...&end_date=... o'qiladi.
 2. Daromad, xarajat, sof balans, to'lov usullari ulushi hisoblanadi; o'tgan oyning
    shu davri va 3 oylik o'rtacha bilan farqi (%) aniqlanadi.
 3. Signal: har kuni 09:00 da filial menejeri va moliyaga Telegram xulosasi;
    sof balans manfiy yoki chetlanish 15% dan oshsa — darhol "ogohlantirish" xabari.

4) O'QUVCHI RISK MENTORI (Student Risk Radar)
Opisaniya: Har bir o'quvchi bo'yicha davomat + baholar + to'lovni birlashtirib
ketish xavfini baholaydi. Muammo: o'quvchi ketishi oldindan sezilmaydi.
Ish zanjiri:
 1. GET /api/ai/analytics/student-performance?studentId=... (yoki groupId=...)
    va GET /api/intern/grades, GET /api/intern/balance o'qiladi.
 2. Risk balli: davomat 40% + baho dinamikasi 40% + to'lov kechikishi 20%;
    yuqori/xavfli o'quvchilar ro'yxati tuziladi va sabab yoziladi.
 3. Signal: mentorga Telegramda "bugun qo'ng'iroq qiling" ro'yxati (ism, sabab,
    tavsiya etilgan harakat); ota-onaga haftalik ijobiy/salbiy trend xulosasi.

5) MENTOR YUKLAMASI AGENTI (Mentor Load Balancer)
Opisaniya: Mentorlar bo'yicha guruhlar, o'quvchilar va dars soatlari yuklamasini
taqqoslaydi. Muammo: bir mentorda 6 guruh, boshqasida 2 — sifat tushadi.
Ish zanjiri:
 1. GET /api/branch/mentors va GET /api/branch/reports/groups o'qiladi.
 2. Har bir mentor uchun guruh/o'quvchi/dars soati hisoblanadi, filial o'rtachasidan
    ±30% chetlanish va bo'sh mentorlar aniqlanadi.
 3. Signal: filial menejeriga haftalik Telegram jadvali + "guruhni ko'chirish"
    tavsiyasi (qaysi guruhni kimga berish).

6) KASSA SMENASI AUDITORI (Cash Shift Auditor)
Opisaniya: Kassa smena hisobotlari va to'lovlar orasidagi farqni topadi.
Muammo: naqd pul kamomadi faqat inventarizatsiyada chiqadi.
Ish zanjiri:
 1. GET /api/finance/cashbox/shift-reports va GET /api/branch/payments
    (status=paid, method=cash) o'qiladi.
 2. Smena bo'yicha kutilgan summa va qayd etilgan summa solishtiriladi;
    1% dan ortiq farq, bekor qilingan (void) to'lovlar va tushum yo'q smenalar belgilanadi.
 3. Signal: auditorga Telegramda farq kartasi (smena, xodim, summa);
    5% dan ortiq farq — darhol filial menejeriga, nusxasi moliyaga.

7) ARIZA/STATUS SLA AGENTI (Status Request SLA)
Opisaniya: O'quvchi status so'rovlarini (muzlatish, chiqish, ko'chirish) vaqt
bo'yicha kuzatadi. Muammo: arizalar 2-3 kun javobsiz qoladi, ota-ona norozi bo'ladi.
Ish zanjiri:
 1. GET /api/branch/status-requests va GET /api/finance/student-status-requests o'qiladi.
 2. Har bir so'rov uchun kutish vaqti hisoblanadi; 24 soatdan oshganlar,
    takroriy so'rovlar va rad etilganlar ajratiladi.
 3. Signal: 24 soatda javobsiz qolgan har bir ariza bo'yicha mas'ul xodimga
    Telegram eslatma; 48 soatdan oshsa filial menejeriga eskalatsiya.

8) XARAJAT ANOMALIYASI AGENTI (Expense Anomaly)
Opisaniya: Xarajatlarni kategoriya bo'yicha 3 oylik o'rtacha bilan solishtiradi va
shubhali sakrashlarni topadi. Muammo: ortiqcha xarajat oy oxirida ko'rinadi.
Ish zanjiri:
 1. GET /api/branch/expenses?from=...&to=... va GET /api/finance/expenses o'qiladi.
 2. Har bir kategoriya bo'yicha o'rtacha, median va dispersiya hisoblanadi;
    2x dan ortiq sakrash, bir kunda takroriy bir xil summalar, chek ilova qilinmagan
    yozuvlar belgilanadi.
 3. Signal: moliya menejeriga Telegramda "tekshiring" kartasi (kategoriya, summa,
    o'rtachadan farq, yozuv ID); tasdiqlanmasa 24 soatdan keyin auditorga.

9) OTA-ONA HAFTALIK DAYJESTI (Parent Digest)
Opisaniya: Har hafta ota-onaga farzandining davomati, bahosi va to'lov qoldig'i
bo'yicha qisqa xulosa yuboradi. Muammo: ota-ona faqat shikoyat bo'lganda xabar oladi.
Ish zanjiri:
 1. GET /api/parent/children/:childId/space va GET /api/student-portal/billing o'qiladi.
 2. Hafta davomida davomat %, o'rtacha baho, topshirilgan vazifalar va to'lov qoldig'i
    hisoblanadi; o'tgan hafta bilan trend aniqlanadi.
 3. Signal: har yakshanba 18:00 da ota-onaga Telegram/SMS dayjest; salbiy trendda
    mentor izohi qo'shiladi va mentorga "qo'ng'iroq qiling" vazifasi yaratiladi.

10) TIZIM SALOMATLIGI AGENTI (SRE Watchdog)
Opisaniya: Backend, MongoDB va API javob vaqtini kuzatadi, uzilishlarni darhol
xabar qiladi. Muammo: nosozlikni foydalanuvchilar birinchi bo'lib sezadi.
Ish zanjiri:
 1. Har 60 sekundda GET /api/health (auth talab qilmaydi) va 3 ta asosiy endpoint
    (GET /api/branch/overview, /api/finance/overview, /api/ai/analytics/attendance-summary)
    chaqiriladi.
 2. HTTP status, javob vaqti (p95) va uptime tekshiriladi; 2 ketma-ket xato,
    5xx, 2 sekunddan ortiq javob yoki Mongo holati "down" bo'lsa — insident.
 3. Signal: devopsga Telegramda insident (endpoint, status, vaqt, oxirgi log);
    5 daqiqada tiklanmasa — qo'ng'iroq (Telegram voice/call) va status sahifasiga yozuv.

Umumiy qoidalar: barcha agentlar filial izolyatsiyasiga rioya qiladi (branchId faqat
tokendagi filial), shaxsiy ma'lumotni ochiq kanalga chiqarmaydi, har bir signalda
manba endpoint va vaqt ko'rsatiladi. Ishga tushirish: Hermes cron (/cron add) yoki
mars-mcp-server tool'lari orqali.
```

---

## Holat

- [x] Freebuff global o'rnatilgan: `freebuff --version` → `0.2.36`
- [x] Freebuff terminalda ishga tushirilgan — isbot: `FREEBUFF-SCREENSHOT.png`
- [ ] Ro'yxat Hermes dashboardiga yuborilishi kerak (yuqoridagi blokni nusxalash)
