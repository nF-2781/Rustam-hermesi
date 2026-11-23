---
name: hermes-mars-dashboard
description: >-
  Hermes-2 loyihasini ishga tushirish, Hermes Agent Dashboardini "Mars" loyihasi bo'yicha run qilish,
  MARS LMS MCP serverini ulash, GitHubdan yangilanishlarni (pull) olish, HTTP orqali tekshirish,
  jarayonni boshqarish, to'xtatish va qayta ishga tushirish bo'yicha to'liq qo'llanma.
---

# Hermes-2 va Mars Dashboard Ishga Tushirish Qo'llanmasi (Skill)

Ushbu skill **Hermes-2** (`Rustam-hermesi`) loyihasini to'g'ri muhitda ishga tushirish, **Hermes Dashboard**ni **Mars** loyihasi bo'yicha ishga tushirish, **MARS LMS MCP** serverini ulash, HTTP/API orqali uning to'g'ri ishlashini tekshirish hamda to'xtatish/qayta ishga tushirish bo'yicha to'liq va sinalgan amaliy ko'rsatmalarni o'z ichiga oladi.

---

## 1. Talablar (Prerequisites)

1. **Python Muhiti va Paketlar:**
   - Python 3.10+ (tizimda `python.exe` 3.14 mavjud).
   - FastMCP uchun `mcp` ning 1.x versiyasi talab qilinadi (`mcp<2`, masalan `1.30.0`).
   - Kerakli Python kutubxonalari:
     ```powershell
     python -m pip install "mcp<2" rich fastapi uvicorn PyYAML requests pydantic httpx concurrent-log-handler portalocker websockets aiofiles
     ```

2. **Git va Hermes vositalari:**
   - Git yo'li: `C:\Users\user\AppData\Local\hermes\git\cmd\git.exe`
   - Global Hermes vositasi: `C:\Users\user\AppData\Local\hermes\bin\hermes.cmd`
   - Lokal Hermes-2 repozitoriysi: `C:\Users\user\Desktop\Database\Mars\Rustam-hermesi`
   - Boshqaruv skripti: `C:\Users\user\Desktop\Database\Mars\Rustam-hermesi\hermes-2.bat`

3. **Konfiguratsiya va Maxfiy Kalitlar (.env va config.yaml):**
   - Repozitoriyda `.env` va `config.yaml` mavjud bo'lishi kerak.
   - `config.yaml` da `mars_lms` MCP serveri quyidagicha sozlangan bo'lishi shart:
     ```yaml
     mcp_servers:
       mars_lms:
         command: C:/Users/user/AppData/Local/Programs/Python/Python314/python.exe
         args:
           - C:/Users/user/Desktop/Database/Mars/Rustam-hermesi/mcp-servers/mars_lms/server.py
         env:
           PYTHONIOENCODING: utf-8
           PYTHONUNBUFFERED: '1'
         enabled: true
         timeout: 180
         connect_timeout: 60
     ```

---

## 2. GitHub Yangilanishlarini Olish (Git Pull)

Tashkilot: `nF-2781`, Repozitoriy: `Rustam-hermesi` dan eng so'nggi o'zgarishlarni yuklab olish:

```powershell
$git = "C:\Users\user\AppData\Local\hermes\git\cmd\git.exe"
Set-Location "C:\Users\user\Desktop\Database\Mars\Rustam-hermesi"
& $git status
& $git fetch origin
& $git pull origin main
```

*Eslatma: Agar mahalliy `.env` yoki `config.yaml` fayllari bilan to'qnashuv yuzaga kelsa, ularni `.local_backup` ga ko'chirib, keyin `pull` qilinadi va sozlamalar qayta tiklanadi.*

---

## 3. Ishga Tushirish Qadamlari (Step-by-Step Execution)

### 1-qadam: MARS LMS MCP serverini test qilish
Barcha 24 ta MCP instrumentlari to'g'ri ishlashini tekshirish:
```powershell
python "C:\Users\user\Desktop\Database\Mars\Rustam-hermesi\mcp-servers\mars_lms\test_tools.py"
```
Kutilgan natija: `Ran 24 tests in ... OK`.

### 2-qadam: Hermes-2 CLI holatini tekshirish
```powershell
cmd.exe /c "cd /d C:\Users\user\Desktop\Database\Mars\Rustam-hermesi && .\hermes-2.bat status"
```

### 3-qadam: "Mars" loyihasini tekshirish va faollashtirish
```powershell
cmd.exe /c "C:\Users\user\AppData\Local\hermes\bin\hermes.cmd project list"
cmd.exe /c "C:\Users\user\AppData\Local\hermes\bin\hermes.cmd project use mars"
```

### 4-qadam: Hermes Dashboardni "Mars" loyihasi bo'yicha ishga tushirish
Dashboardni 9119-portda fon rejimida ishga tushirish (agar veb UI oldindan qurilgan bo'lsa, `--skip-build` qo'shiladi):
```powershell
cmd.exe /c "cd /d C:\Users\user\Desktop\Database\Mars\Rustam-hermesi && .\hermes-2.bat --in C:\Users\user\Desktop\Database\Mars dashboard --port 9119 --skip-build --no-open"
```
*Parametrlar izohi:*
- `--in C:\Users\user\Desktop\Database\Mars`: Dashboard ishchi katalogini Mars loyihasiga yo'naltiradi.
- `--port 9119`: Standart veb-port.
- `--skip-build`: Web UI dist mavjud bo'lganda tezkor ishga tushiradi (build kutishni chetlab o'tadi).
- `--no-open`: Brauzer oynasini avtomatik ochishni cheklaydi.

---

## 4. Tekshirish (Verification Checklist)

Dashboard to'liq va xatosiz ishlayotganini 4 ta bosqichda tekshiring:

### 1. Port va Jarayon Holati (Port & Process Check)
```powershell
netstat -ano | findstr "9119"
```
**To'g'ri natija belgisi:**
```
TCP    127.0.0.1:9119         0.0.0.0:0              LISTENING       <PID>
```

### 2. Dashboard Salomatlik Tekshiruvi (Health Check)
```powershell
curl.exe -s http://127.0.0.1:9119/api/health
```
**To'g'ri natija belgisi:**
```json
{"ok":true,"version":"0.21.2","auth_required":false}
```

### 3. Veb Interfeys Sarlavhasi (HTML Title)
```powershell
curl.exe -s http://127.0.0.1:9119/ | Select-String -Pattern "<title>(.*?)</title>"
```
**To'g'ri natija belgisi:**
```html
<title>Hermes Agent - Dashboard</title>
```

### 4. Mars Loyihasi Ochilganini Tasdiqlash (Workspace Verification)
Dashboard sessiya tokeni orqali faol loyihani tekshirish:
```powershell
$html = curl.exe -s http://127.0.0.1:9119/
if ($html -match '__HERMES_SESSION_TOKEN__\s*=\s*"([^"]+)"') {
    $tok = $matches[1]
    $tree = curl.exe -s -H "Authorization: Bearer $tok" http://127.0.0.1:9119/api/profiles/projects/tree | ConvertFrom-Json
    $mars = $tree.projects | Where-Object { $_.label -eq "Mars" }
    Write-Output "Loyiha nomi: $($mars.label)"
    Write-Output "Yo'l: $($mars.path)"
}
```
**To'g'ri natija belgisi:**
```
Loyiha nomi: Mars
Yo'l: C:\Users\user\Desktop\Database\Mars
```

---

## 5. Keng Tarqalgan Xatolar va Mukammal Yechimlari

| № | Uchragan Haqiqiy Xato | Sababi | Mukammal Yechim |
|---|-----------------------|--------|-----------------|
| 1 | `git : The term 'git' is not recognized` | Git global tizim `PATH` o'zgaruvchisida yo'q. | `C:\Users\user\AppData\Local\hermes\git\cmd\git.exe` to'liq yo'lini ishlatish yoki uni `$env:PATH` ga qo'shish. |
| 2 | `error: The following untracked working tree files would be overwritten by merge: .env, config.yaml` | Mahalliy fayllar masofaviy repozitoriy fayllari bilan to'qnash kelgan. | Mahalliy fayllarni zaxiralash (`.local_backup`), `git pull` qilish va zarur sozlamalarni qayta tiklash. |
| 3 | `ModuleNotFoundError: No module named 'mcp.server.fastmcp'` | `pip install mcp` v2.x ni o'rnatgan, unda `FastMCP` boshqa nomga o'zgartirilgan. | FastMCP 1.x versiyasini o'rnatish: `python -m pip install "mcp<2"`. |
| 4 | `ModuleNotFoundError: No module named 'concurrent_log_handler'` | Hermes 0.21.2 log yuritish moduli uchun paket o'rnatilmagan. | `python -m pip install concurrent-log-handler portalocker` o'rnatish. |
| 5 | `config.yaml` dagi noto'g'ri yo'l (`C:/Users/user/Documents/Hermes-2/...`) | Repozitoriyda boshqa mashinadagi yo'l yozilgan. | Yo'llarni joriy mashina yo'liga to'g'rilash: `C:/Users/user/Desktop/Database/Mars/Rustam-hermesi/mcp-servers/mars_lms/server.py`. |
| 6 | `Port 9119 on 127.0.0.1 is already in use` | Oldingi dashboard jarayoni fonda ishlab turibdi. | Jarayonni to'xtatish: `hermes dashboard --stop` yoki tegishli PID ni to'xtatish. |
| 7 | `The system cannot find the path specified` (`hermes-2.bat` da) | `hermes-2.bat` mavjud bo'lmagan `.venv\Scripts\python.exe` ga murojaat qilgan. | `hermes-2.bat` ichida `.venv` yo'q bo'lsa tizim `python.exe` siga o'tadigan tekshiruv shartini qo'shish. |

---

## 6. To'xtatish va Qayta Ishga Tushirish (Lifecycle Management)

### Dashboardni To'xtatish (Stop):
```powershell
cmd.exe /c "C:\Users\user\AppData\Local\hermes\bin\hermes.cmd dashboard --stop"
```
*Holatni tasdiqlash:*
```powershell
cmd.exe /c "C:\Users\user\AppData\Local\hermes\bin\hermes.cmd dashboard --status"
```
Kutilgan javob: `No hermes dashboard or serve processes running.`

### Dashboardni Qayta Ishga Tushirish (Restart):
```powershell
cmd.exe /c "cd /d C:\Users\user\Desktop\Database\Mars\Rustam-hermesi && .\hermes-2.bat --in C:\Users\user\Desktop\Database\Mars dashboard --port 9119 --skip-build --no-open"
```

### Holatni Qayta Tekshirish:
```powershell
Start-Sleep -Seconds 2
curl.exe -s http://127.0.0.1:9119/api/health
```
Natija: `{"ok":true,"version":"0.21.2","auth_required":false}`
