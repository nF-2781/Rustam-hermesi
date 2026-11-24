---
name: hermes-dashboard
description: >-
  Hermes Agent Web Dashboard'ni loyiha bo'yicha mustaqil sozlash, ishga tushirish (run),
  port va API holatini tekshirish (health check) hamda MCP integratsiyasini tekshirish uchun to'liq yo'riqnoma va skill.
---

# Hermes Dashboard — Loyiha: Mars Bo'yicha Ishga Tushirish va Diagnostika Skilli

Ushbu skill **Hermes Agent (Hermes-2)** ni va uning Web UI Dashboard boshqaruv panelini **Mars** loyihasi uchun to'liq sozlash, ishga tushirish (run), to'g'ri ishlashini avtomatlashtirilgan tarzda tekshirish (verify) va `mars-mcp-server` integratsiyasini boshqarish bo'yicha to'liq ish tartibini taqdim etadi.

---

## 🛠 1. Loyihani Sozlash va Muammolarni Tuzatish (Ideal Setup)

Loyiha ilk holatda mustaqil ishlashi uchun barcha zaruriy tuzatishlar avvaldan amalga oshirilgan:

1. **`hermes-2.bat` fayli to'liq tuzatildi:**
   * Bat fayl ichidagi izolyatsiyalangan muhit bog'liqliklari to'g'rilandi.
   * `D:\Desktop\Mars\Rustam-hermesi\hermes-agent\.venv` katalogi venv interpretatoriga ulandi.
2. **Faol loyiha (Project: Mars) ulandi:**
   * Hermes loyihalar tizimida `Mars` ro'yxatdan o'tkazildi va asosiy papka sifatida `D:\Desktop\Mars\Mars` belgilandi.
   * Loyihani tekshirish:
     ```cmd
     hermes-2.bat project list
     # Natija: * mars  Mars  [1 folder(s)]
     ```

---

## 🚀 2. Hermes Dashboard'ni Ishga Tushirish (RUN)

Dashboard'ni **Mars** loyihasi bilan to'liq background rejimida ishga tushirish:

### Standart buyruq:
```powershell
cd "D:\Desktop\Mars\Rustam-hermesi"
.\hermes-2.bat dashboard --port 9119 --host 127.0.0.1 --skip-build --no-open
```

* **Lokal URL:** **`http://127.0.0.1:9119`**
* **Port:** `9119`
* **Xususiyati:** `--skip-build` orqali oldindan yig'ilgan React 19 SPA statik fayllari bir zumda ishga tushadi.

---

## 🔍 3. To'g'ri Ishlayotganini Tekshirish (VERIFY)

Dashboard ishga tushgach, uning to'g'ri va xatosiz ishlayotganini tekshirish bosqichlari:

### 1-qadam: Web UI yuklanishi (HTTP 200 OK)
```powershell
(Invoke-WebRequest -Uri "http://127.0.0.1:9119" -UseBasicParsing).StatusCode
# Chiqish: 200
```

### 2-qadam: Tizim holati (Status API)
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:9119/api/status" -Method Get
```
* `hermes_home`: `D:\Desktop\Mars\Rustam-hermesi`
* `disk.pressure`: `ok`

### 3-qadam: Xavfsizlik Sessiya Tokeni va MCP Testi
Hermes xavfsizlik arxitekturasi bo'yicha loopback so'rovlar uchun sessiya tokeni olinadi va `mars-lms` MCP serveri sinovdan o'tkaziladi:
```powershell
$token = ((Invoke-WebRequest -Uri "http://127.0.0.1:9119" -UseBasicParsing).Content | Select-String -Pattern '__HERMES_SESSION_TOKEN__="([^"]+)"').Matches.Groups[1].Value
$headers = @{ "X-Hermes-Session-Token" = $token }

# mars-lms MCP probe tekshiruvi:
Invoke-RestMethod -Uri "http://127.0.0.1:9119/api/mcp/servers/mars-lms/test" -Headers $headers -Method Post
# Natija: {"ok": true, "tools": [... 11 ta tool ...]}
```

---

## ⚡ 4. Avtomatlashtirilgan Sinov Skripti

Skill to'g'ri ishlashini istalgan vaqtda bitta buyruq bilan avtomatik tekshirish mumkin:

```powershell
python "D:\Desktop\Mars\.agents\skills\hermes-dashboard\scripts\test_skill.py"
```

**Muvaffaqiyatli sinov natijasi:**
```text
==================================================
🚀 HERMES DASHBOARD (LOYIHA: MARS) TESTI BOSHLANDI
==================================================
✅ 1. Web UI Dashboard faol: http://127.0.0.1:9119 (HTTP 200)
✅ 2. Xavfsizlik sessiya tokeni olindi: GsYtJtiWWyHw...
✅ 3. Tizim holati (status):
   • Hermes Home: D:\Desktop\Mars\Rustam-hermesi
   • Disk holati: ok
✅ 4. MCP Server ('mars-lms') faol: 11 ta tool aniqlandi:
   - login
   - branch_me
   - groups
   - students
   - mentors
   - payments
   - finance_overview
   - finance_salaries
   - rooms_availability
   - schedule_conflicts
   - mentor_workload
==================================================
🎉 BARCHA TEKSHIRUVLAR MUVAFFAQIYATLI O'TDI (PASS)
==================================================
```
