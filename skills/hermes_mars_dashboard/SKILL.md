---
name: hermes-mars-dashboard
description: "Hermes dashboardni Mars loyihasi (MARS IT LMS) kontekstida run qilish, mars_lms MCP serverini tekshirish va nosozliklarni tuzatish — HERMES_HOME tuzog'i, band 9119 port va ishonchli health-check bilan."
version: 1.1.0
author: Rustam
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [hermes, dashboard, mars, lms, mcp, run, verify, windows]
    related_skills: [mars-lms-operations]
---

# Hermes dashboard — Mars loyihasi uchun ishga tushirish

Hermes web dashboardni **Mars** loyihasi (MARS IT LMS: `mars-backend`,
`mcp-servers/mars_lms`, `skills/mars_lms`) kontekstida ko'taradi, `mars_lms` MCP
serveri ulanganini tekshiradi va amalda uchraydigan uchta tuzoqni oldini oladi:

1. `HERMES_HOME` berilmasa — global `~/.hermes` konfiguratsiyasi olinadi;
2. 9119 port odatda Hermes gateway'ning ichki dashboardi tomonidan band;
3. `hermes dashboard --status` ba'zi ishga tushirish usullarida jarayonni
   ko'rsatmaydi — u yagona haqiqat manbai emas.

## 0. Muhim: HERMES_HOME ni har doim bering

`hermes-2.bat` ichida `HERMES_HOME` loyiha papkasiga, `PYTHONPATH` esa
`hermes-agent` ga o'rnatiladi. Python'ni to'g'ridan-to'g'ri chaqirsangiz bu
o'zgaruvchilar **qo'llanmaydi** va Hermes global `~/.hermes` ni oladi. Natijada:

- `config.yaml` dagi `mars_lms` serveri ko'rinmaydi, uning o'rniga global
  konfiguratsiyadagi `mars-lms` topiladi va
  `✗ Connection failed: [WinError 267]` chiqadi;
- `hermes project` buyruqlari global `state.db` ga yozadi, loyihadagi emas;
- dashboard Mars sessiyalari/skillari o'rniga global holatni ko'rsatadi.

Har bir buyruq oldidan (bash) yoki `hermes-2.bat` orqali. **Yo'llar hech qachon
qo'lda yozilmaydi** — repo ildizi aniqlanadi, shuning uchun jamoada repo boshqa
papkaga klonlangan bo'lsa ham ishlaydi:

```bash
REPO="$(git rev-parse --show-toplevel)"     # yoki: REPO="$(pwd)" repo ildizida turgan bo'lsangiz
cd "$REPO"
export HERMES_HOME="$REPO"
export PYTHONPATH="$REPO/hermes-agent"
```

Tekshirish: `hermes project list` Mars'ni ko'rsatishi kerak. Yo'q bo'lsa —
buyruq noto'g'ri `HERMES_HOME` bilan ishlagan.

## 1. Mars loyihasini yaratish / faollashtirish

```bash
hermes project create "Mars" "$REPO" \
  --description "MARS IT LMS — backend, mars_lms MCP server, skills va operatsion zanjirlar" \
  --icon "🔴" --color "#e11d48" --use
```

Mavjud bo'lsa qayta yaratmang, faqat faollashtiring:

```bash
hermes project list        # `*` — aktiv loyiha
hermes project use mars
```

Kutilgan: `* mars   Mars  [1 folder(s)]`.

## 2. MCP serverini tekshirish (dashboarddan oldin)

```bash
hermes mcp test mars_lms
```

Kutilgan: `✓ Connected`, `✓ Tools discovered: 22`.

`Server 'mars_lms' not found ... Available: mars-lms` → 0-qadam bajarilmagan.

## 3. Bo'sh portni aniqlash

9119 ko'pincha Hermes gateway'ning ichki dashboardi tomonidan band bo'ladi
(bunda `hermes dashboard` `BACKEND_PORT_IN_USE port=9119` bilan yiqiladi, lekin
eski server 302 → `/login` qaytaradi). Avval tekshiring:

```bash
netstat -ano | grep ":9119"        # Windows (Git Bash)
```

- **Bo'sh** → 9119 da ishlatish mumkin;
- **Band** → 9120 yoki boshqa bo'sh portni oling, yoki `--port 0` (OS bo'sh port
  beradi; haqiqiy portni log'dagi `HERMES_DASHBOARD_READY port=NNNN` qatoridan
  oling). Band portni egallagan jarayonni o'ldirmang — bu gateway bo'lishi mumkin.

## 4. Dashboardni ishga tushirish

**Eng tez yo'l — tayyor skript** (bo'sh portni o'zi tanlaydi, tayyor bo'lishini
kutadi va health-check qiladi; 2–5 daqiqalik build ham shu yerda):

```bash
bash skills/hermes_mars_dashboard/run_mars_dashboard.sh          # start
bash skills/hermes_mars_dashboard/run_mars_dashboard.sh status   # holat
bash skills/hermes_mars_dashboard/run_mars_dashboard.sh stop     # to'xtatish
```

Skript chiqishi: `✓ Dashboard tayyor: http://127.0.0.1:9120` + `/api/status`
qiymati. Agar dashboard allaqachon ishlayotgan bo'lsa, qayta ko'tarmaydi.
PID `logs/.mars-dashboard.pid` ga yoziladi — `stop` faqat shu jarayonni
o'chiradi (gateway'ga tegmaydi).

Qo'lda ishga tushirish kerak bo'lsa:

```bash
hermes dashboard --port 9120 --no-open --skip-build > logs/dashboard-mars.log 2>&1 &
```

**Windows'da `&` bilan ko'tarmang** — terminal/oyna yopilganda jarayon o'ladi
(SIGHUP). Skript buni o'zi hal qiladi: `hermes-2.bat` ni **alohida oynada**
ishga tushiradi (`start "Hermes Mars Dashboard" /min cmd /c ...`), shuning uchun
terminal yopilsa ham dashboard ishlab turadi. Start ~15–20s (jarayon ko'tarilishi),
skript stdio'ni uzadi va chaqiruvchi terminalni bloklamaydi. Qo'lda
kerak bo'lsa:

```bat
cd /d %REPO%
start "Hermes Mars Dashboard" /min hermes-2.bat dashboard --port 9120 --no-open --skip-build
```
(Log faylga yo'naltirilsa: `hermes-2.bat dashboard --port 9120 --no-open > logs\dashboard-mars.log 2>&1`.)

- `--no-open` — brauzerni avtomatik ochmaydi (skript uchun).
- **Birinchi** ishga tushishda web UI avtomatik build qilinadi
  (`npm install` + `tsc -b && vite build`, 2–5 daqiqa). Build chiqishi
  `hermes-agent/hermes_cli/web_dist` ga yoziladi (`web/dist` emas).
- Keyingi safar `--skip-build` qo'shing — server darhol ko'tariladi.
- Tayyor bo'lganda log'da:

```text
→ Skipping web UI build (--skip-build); using dist at ...\hermes_cli\web_dist
HERMES_DASHBOARD_READY port=9120
  Hermes Web UI → http://127.0.0.1:9120
```

Dashboard loyiha `state.db`, sessiyalar, skillar, Model/Keys/Cron sahifalari va
`config.yaml` ni shu `HERMES_HOME` doirasida ko'rsatadi.

## 5. To'g'ri ishga tushganini tekshirish (ishonchli usul)

**`hermes dashboard --status` ga yolg'iz tayanmang** — Windows'da bash orqali
ko'tarilgan server uchun u `No hermes dashboard or serve processes running`
deb noto'g'ri javob berishi mumkin (kuzatilgan). Uch mustaqil dalil ishlating:

```bash
# 1) port haqiqatan tinglayapti va PID ma'lum
netstat -ano | grep ":9120"

# 2) HTTP 200 (Mars dashboardi; gateway'ning 9119 dagisi 302 → /login beradi)
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:9120/
# kutilgan: 200

# 3) backend tirik va versiya ko'rinadi
curl -s http://127.0.0.1:9120/api/status | head -c 300
# kutilgan: {"version":"0.21.2",...,"auth_required":false,...}

# 4) log'da tayyorlik qatori
grep HERMES_DASHBOARD_READY logs/dashboard-mars.log
```

Jarayon PID/port `logs/.mars-dashboard.pid` va `logs/.mars-dashboard.port` ga
yoziladi (PID — portni tinglayotgan haqiqiy python jarayoni).

`/api/status` — auth talab qilmaydigan yagona ishonchli probe. `/api/sessions`,
`/api/projects` kabi yo'llar `{"detail":"Unauthorized"}` qaytarishi normal
(brauzer cookie'si kerak), bu server o'lmaganini bildirmaydi.

Brauzerda <http://127.0.0.1:9120> ni ochib, yuqoridagi loyiha nomi va
sessiyalar Mars kontekstida ekanini vizual tekshiring.

## 6. To'xtatish

```bash
bash skills/hermes_mars_dashboard/run_mars_dashboard.sh stop   # faqat skript ko'targan jarayon
hermes dashboard --stop                                        # barcha dashboard/serve jarayonlari
```

Topilmasa, `netstat -ano | grep ":9120"` dagi PID ni ishlating
(`taskkill //PID <pid> //F`). Nom bo'yicha (`taskkill /IM node.exe`,
`pkill -f hermes`) o'ldirmang — gateway va boshqa Hermes jarayonlari ham
o'chadi.

## Nosozliklar jadvali

| Belgi | Sabab | Yechim |
|---|---|---|
| `Available: mars-lms`, `WinError 267` | `HERMES_HOME` berilmagan | 0-qadam: `HERMES_HOME` + `PYTHONPATH` |
| `hermes project list` bo'sh / Mars yo'q | buyruq global home'ga yozgan | 0-qadam bilan qayta yaratish |
| `BACKEND_PORT_IN_USE port=9119` | gateway'ning ichki dashboardi | bo'sh port (9120) yoki `--port 0` |
| `hermes dashboard --status` "running emas" deydi, lekin sayt ochiladi | PID-skaner chetlab o'tgan (bash/wrapper) | netstat + curl + log bo'yicha tekshirish |
| HTTP 302 → `/login` | auth gate yoqilgan (gateway yoki OAuth) | Mars serverini alohida portda ko'tarish yoki `hermes dashboard register` |
| Log'da `npm`/`vite` xatosi | `node`/`npm` yo'q yoki `web/node_modules` buzilgan | `cd hermes-agent/web && npm install && npm run build`, keyin `--skip-build` |
| Dashboardda MCP tool'lari yo'q | sessiya eski | yangi sessiya yoki `/reload-mcp` |

## Tekshirilgan natija (2026-11-21)

- `hermes project list` → `* mars  Mars  [1 folder(s)]`
- `hermes mcp test mars_lms` → connected, 22 tool
- `hermes dashboard --port 9120 --skip-build` → `HERMES_DASHBOARD_READY port=9120`,
  `GET /` → 200, `/api/status` → `version 0.21.2`, `auth_required:false`
- `run_mars_dashboard.sh start` (Windows, hermes-2.bat alohida oynada) → 17.6s,
  `port=9120`, PID faylda, skript chiqqandan keyin ham `GET /` → 200
- `run_mars_dashboard.sh stop` → `✓ To'xtatildi (port 9120, PID ...)`, port bo'shadi
- Skill yo'llari repo-nisbiy: boshqa papkaga klonlangan repoda ham mutlaq yo'l yo'q

## Qoidalar

- Buyruqlarni **loyiha ildizidan** bering — `config.yaml`, `state.db` va
  skillar shu yerda.
- Dashboardni `0.0.0.0` ga ochmang: lokal uchun `127.0.0.1` yetarli, tashqi bind
  auth provayderini talab qiladi. `--insecure` endi auth'ni o'chirmaydi.
- Dashboard Mars ma'lumotlarini **o'qiydi**; to'lov/qarz bo'yicha pul
  operatsiyalari faqat inson tasdig'i bilan (`mars-lms-operations` skilliga
  qarang).
