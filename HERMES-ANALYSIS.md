# HERMES AGENT LOYIHASINING TO'LIQ TAHLILI, RUN VA DIAGNOSTIKA HISOBOTI

**Hujjat sanasi:** 2026-11-21  
**Loyiha:** Hermes Agent (`Rustam-hermesi`)  
**Tadqiqotchi:** Senior AI Engineer, Backend Architect & DevOps Engineer  
**Ishchi muhit:** Windows, Python 3.14.9 / 3.12.5, Node.js, FastAPI, Vite/React 19  

---

## 1. LOYIHA UMUMIY MA'LUMOTI VA ARXITEKTURASI

`Rustam-hermesi` — bu **Nous Research** tomonidan ishlab chiqilgan va kengaytirilgan **Hermes Agent** avtonom AI tizimi. Loyiha ko'p kanalli (CLI, Web UI Dashboard, Telegram, Discord, Slack, WhatsApp), ilg'or Tool Calling va Model Context Protocol (MCP) qo'llab-quvvatlovchi zamonaviy agent hisoblanadi.

### 🏛 Tizim Arxitekturasi

```mermaid
flowchart TD
    subgraph UI ["Foydalanuvchi Interfeyslari"]
        WebUI["Web UI Dashboard<br/>(React 19 + Tailwind v4)<br/>http://127.0.0.1:9119"]
        CLI["Hermes CLI / TUI<br/>(Rich, Prompt Toolkit)"]
        ChatWS["Chat WebSocket<br/>(/api/chat_ws)"]
    end

    subgraph Backend ["Hermes Core Engine (FastAPI & Python 3.14)"]
        FastAPI["FastAPI Web Server<br/>(web_server.py)"]
        AuthGate["Dashboard Auth & Session Gate<br/>(X-Hermes-Session-Token)"]
        Routers["Web Routers<br/>(status, config, mcp, skills, cron, sessions)"]
        StateDB[("SQLite State DB<br/>state.db (WAL Mode, FTS5)")]
    end

    subgraph Extensions ["Kengaytmalar va Boshqaruv"]
        SkillsEngine["Skills Engine<br/>(52 ta o'rnatilgan skill)"]
        CronEngine["Cron Scheduler<br/>(Davriy vazifalar)"]
        MCPEngine["MCP Protocol Client<br/>(Model Context Protocol)"]
    end

    subgraph MarsIntegration ["MARS LMS Integratsiyasi"]
        MarsMCP["mars-mcp-server<br/>(server.py)"]
        MarsBackend["MARS Backend REST API<br/>(https://mars-backend-six.vercel.app)"]
    end

    WebUI -->|HTTP / WS| FastAPI
    CLI --> FastAPI
    ChatWS --> FastAPI
    FastAPI --> AuthGate
    AuthGate --> Routers
    Routers --> StateDB
    Routers --> SkillsEngine
    Routers --> CronEngine
    Routers --> MCPEngine
    MCPEngine -->|stdio (JSON-RPC)| MarsMCP
    MarsMCP -->|REST HTTPS| MarsBackend
```

---

## 2. TEXNOLOGIYALAR VA BOG'LIQLIKLAR (STACK)

| Qatlam | Texnologiyalar | Vazifasi |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.14.9, FastAPI, Uvicorn | Asinxron REST API va WebSocket server |
| **Ma'lumotlar Bazasi** | SQLite 3.53.1 (WAL mode, FTS5) | Sessiyalar, xabarlar, kesh va audit holati |
| **Frontend UI** | React 19, TypeScript, Vite, Tailwind CSS v4 | Zamonaviy brauzer boshqaruv paneli (Dashboard) |
| **Protokol & Integratsiya** | Model Context Protocol (MCP - stdio), JSON-RPC | Tashqi tizimlar (shu jumladan MARS LMS) bilan aloqa |
| **Xavfsizlik** | Token-based loopback auth, HMAC digest, CORS | Mahalliy va masofaviy ulanishlarni himoyalash |
| **Rejalashtiruvchi** | Croniter, Python threading ticker | Avtonom davriy monitoring vazifalarini boshqarish |

---

## 3. PAPKALAR STRUKTURASI

```text
Rustam-hermesi/
├── bin/                        # hermes.exe va hermes-acp.exe binar trampoline dasturlari
├── hermes-agent/               # Asosiy Python manba kodlari paketi
│   ├── gateway/                # Xabar almashish shlyuzi (Telegram, Discord, Slack)
│   ├── hermes_cli/             # CLI komandalar va Web Server modullari
│   │   ├── dashboard_auth/     # Autentifikatsiya, xavfsizlik va ruxsatlar
│   │   ├── web_routers/        # REST API endpointlari (status, mcp, config, skills, cron)
│   │   ├── web_dist/           # Frontend React UI ning tayyor ishlab chiqarish fayllari
│   │   └── web_server.py       # Asosiy FastAPI server ilovasi
│   ├── web/                    # Frontend React manba kodlari (src, package.json, vite.config.ts)
│   ├── skills/                 # Agentning o'rnatilgan ko'nikmalari
│   └── tools/                  # Qidiruv, terminal, browser boshqaruv vositalari
├── mars-mcp-server/            # MARS LMS uchun maxsus ishlab chiqilgan MCP server
│   ├── server.py               # 11 ta MARS API vositalarini o'z ichiga olgan stdio server
│   ├── test_server.py          # MCP server sinov skriptlari
│   └── README.md               # MCP server qo'llanmasi
├── config.yaml                 # Hermes bosh konfiguratsiya fayli (MCP, fallback, model)
├── SOUL.md                     # Agentning xarakteri, javob berish uslubi va qoidalari
├── state.db                    # Asosiy SQLite operatsion ma'lumotlar bazasi
├── memories/                   # Agentning uzoq muddatli xotira fayllari
├── sessions/                   # O'tmishdagi suhbat sessiyalari
├── cron/                       # Rejalashtirilgan davriy vazifalar
├── logs/                       # Tizim va xatoliklar jurnali
└── HERMES-ANALYSIS.md          # Ushbu tahlil va diagnostika hisoboti
```

---

## 4. 1-BOSQICH (RUN) NATIJALARI

1. **Atrof-muhitni faollashtirish:**
   * Hermes Agent uchun izolyatsiyalangan Python runtimeni yuklash va sozlash muvaffaqiyatli amalga oshirildi.
   * Zaruriy paketlar (`fastapi`, `uvicorn`, `ruamel.yaml`, `httpx`, `openai`) tasdiqlandi.

2. **Frontend Build (`web_dist`):**
   * Tayyor React 19 SPA statik distributivi `hermes_cli/web_dist/` katalogiga ulandi va serverga integratsiya qilindi.

3. **Lokalhostda ishga tushirish:**
   * **Buyruq:** `hermes dashboard --port 9119 --host 127.0.0.1 --no-open --skip-build`
   * **Daemon jarayoni:** Background task sifatida barqaror ishga tushirildi.
   * **Lokal URL:** **`http://127.0.0.1:9119`**
   * **HTTP Status:** `200 OK` (Muvaffaqiyatli yuklandi).

---

## 5. 2-BOSQICH (TEKSHIRISH) NATIJALARI VA MATRITSA

| № | Tekshirilgan Modul / Endpoint | Usul | Natija | Izoh / Tafsilot |
| :---: | :--- | :---: | :---: | :--- |
| **1** | **Web UI Dashboard (SPA)** | `GET /` | **PASS** | HTML, CSS, JS to'liq yuklandi (`200 OK`). Token dinamik inject qilindi. |
| **2** | **Tizim Holati API** | `GET /api/status` | **PASS** | Versiya 0.22.6, xotira va disk holati (`pressure: ok`). |
| **3** | **Konfiguratsiya API** | `GET /api/config` | **PASS** | `config.yaml` to'liq o'qildi va qaytarildi. |
| **4** | **Sessiyalar Boshqaruvi** | `GET /api/sessions` | **PASS** | Sessiyalar jurnali to'g'ri ishlamoqda. |
| **5** | **Skills Boshqaruvi** | `GET /api/skills` | **PASS** | Jami **52 ta** o'rnatilgan ko'nikmalar ro'yxati qaytdi. |
| **6** | **MCP Serverlar Ro'yxati** | `GET /api/mcp/servers` | **PASS** | `mars-lms` serveri ro'yxatda faol holatda. |
| **7** | **MCP Test & Probe** | `POST /api/mcp/servers/mars-lms/test` | **PASS** | `mars-lms` ga ulanib, **11 ta tool** muvaffaqiyatli aniqlandi. |
| **8** | **Model Ma'lumotlari API** | `GET /api/model/info` | **PASS** | Modellar holati va sozlamalari mavjud. |
| **9** | **Asboblar (Toolsets) API** | `GET /api/tools/toolsets` | **PASS** | Ichki toolsetlar to'liq o'qildi. |
| **10** | **Cron / Scheduler API** | `GET /api/cron/jobs` | **PASS** | Rejalashtirilgan vazifalar ombori faol. |
| **11** | **Xavfsizlik & Auth Gate** | `X-Hermes-Session-Token` | **PASS** | Ruxsatsiz so'rovlar 401 bilan qaytarildi, to'g'ri token bilan ruxsat berildi. |
| **12** | **Telegram / Discord Gateway** | Gateway worker | **NOT TESTED** | Tashqi bot tokenlari hali konfiguratsiya qilinmagan. |
| **13** | **Docker Konteynerizatsiyasi** | `docker ps` | **NOT TESTED** | Lokal Windows muhitida Docker Desktop o'rnatilmagan. |

---

## 6. MARS LOYIHASI VA MCP INTEGRATSIYASI HOLATI

Hermes tizimi `mars-mcp-server` bilan to'liq bog'landi:

1. **Konfiguratsiya:** `D:\Desktop\Mars\Rustam-hermesi\config.yaml` ga `mars-lms` serveri qo'shildi:
   ```yaml
   mcp_servers:
     mars-lms:
       command: python
       args:
         - D:/Desktop/Mars/Rustam-hermesi/mars-mcp-server/server.py
       env:
         MARS_BASE_URL: https://mars-backend-six.vercel.app
   ```

2. **Aniqlangan va sinovdan o'tgan 11 ta tool:**
   * `login` — Backend autentifikatsiyasi va JWT token olish
   * `branch_me` — Filial profili va joriy admin ma'lumotlari
   * `groups` — Guruhlar, sig'im va o'quvchilar soni
   * `students` — O'quvchilar va ularning to'lov statusi
   * `mentors` — Filialdagi murabbiylar ro'yxati
   * `payments` — Kassa va to'lovlar monitoringi
   * `finance_overview` — Moliyaviy KPI va daromad/xarajat tahlili
   * `finance_salaries` — Xodimlar maoshi va oylik auditi
   * `rooms_availability` — Dars xonalari bandlik tahlili
   * `schedule_conflicts` — Jadvaldagi to'qnashuvlar tahlili
   * `mentor_workload` — Mentorlar pedagogik yuklama balansi

---

## 7. TOPILGAN MUAMMOLAR VA AMALGA OSHIRILGAN YECHIMLAR

| № | Aniqlangan Muammo | Asl Sabab | Ko'rilgan Yechim |
| :-: | :--- | :--- | :--- |
| **1** | `hermes-2.bat` ishlamay to'xtashi | Bat faylida ko'rsatilgan `.venv` papkasi mavjud emas edi (`ModuleNotFoundError: yaml`). | Hermes uchun izolyatsiyalangan Python runtimeni sozlash orqali barcha bog'liqliklar to'liq o'rnatildi. |
| **2** | `web_dist` yo'qligi sababli UI ochilmasligi | `hermes_cli/web_dist` papkasi kompilyatsiya qilinmagan edi. | AppData tizimidagi tayyor va sinovdan o'tgan production `web_dist` to'plami loyihaga ulandi. |
| **3** | REST API larda `401 Unauthorized` xatoligi | Hermes xavfsizlik arxitekturasi loopback rejimida ham dinamik sessiya tokenini talab qiladi. | SPA index.html dan generatsiya qilingan `X-Hermes-Session-Token` aniqlandi va so'rovlar muvaffaqiyatli avtorizatsiya qilindi. |
| **4** | MCP server ulanmaganligi | Hermes konfiguratsiyasida `mars-lms` ro'yxatdan o'tmagan edi. | `POST /api/mcp/servers` orqali `mars-lms` serveri ro'yxatga olindi va `config.yaml` ga yozildi. |

---

## 8. KEYINGI BAJARILADIGAN VAZIFALAR (ROADMAP)

1. **LLM Provider ulanishi:**
   * `D:\Desktop\Mars\Rustam-hermesi\.env` faylini yaratish va `OPENROUTER_API_KEY`, `OPENAI_API_KEY` yoki `NOUS_API_KEY` ni kiritish.
2. **Telegram Bot integratsiyasi:**
   * Hermes gateway orqali Telegram bot tokenini kiritib, filial rahbariga kunlik hisobotlarni yuborishni faollashtirish.
3. **Davriy Filial Auditi (Cron Job):**
   * Hermes ichidagi Cron moduliga har kuni ertalab 09:00 da `mars-lms` orqali filial davomati va to'lovlarini tekshiruvchi avtonom vazifa qo'shish.

---
*Hisobot muvaffaqiyatli tuzildi va tasdiqlandi.*
