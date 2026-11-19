# MARS LMS Local MCP Server

MARS LMS backend tizimi (`https://mars-backend-six.vercel.app`) uchun Python va Model Context Protocol (MCP) asosida yaratilgan lokal server. Ushbu server LLM agentlariga (Antigravity, Claude Desktop, Cursor, Hermes va h.k.) filial va moliya ma'lumotlarini xavfsiz va tezkor o'qish imkonini beradi.

---

## Asosiy Imkoniyatlar

1. **Python + MCP (stdio)**: Rasmiy Model Context Protocol standarti asosida stdin/stdout orqali ishlaydi.
2. **In-Memory JWT Token**: `login` tool chaqirilgandan so'ng olingan JWT token xotirada saqlanadi. Har bir keyingi so'rovda avtomatik ravishda `Authorization: Bearer <token>` headeri qo'shiladi va qayta login qilish talab etilmaydi.
3. **Aniq Xatolik Nazorati**: Backend xatoliklari (401, 403, 404, 500) yoki tarmoq uzilishlari jim yutilmaydi, HTTP status kodi va backend bergan aniq xabar foydalanuvchiga to'liq yetkaziladi.
4. **Demo hisob bilan tayyor integratsiya**: Admin demo hisobi parametr sifatida o'rnatilgan (`998935344549` / `1234`).

---

## Mavjud Tool'lar

| Tool Nomi | REST Endpoint | Tavsif | Parametrlar |
|-----------|---------------|--------|-------------|
| `login` | `POST /api/auth/login` | Tizimga kirish va JWT tokenni xotirada saqlash | `phone` (str), `password` (str), `role` (str, default: 'admin') |
| `branch_me` | `GET /api/branch/me` | Joriy admin va uning filiali ma'lumotlari | — |
| `groups` | `GET /api/branch/groups` | Filialdagi guruhlar ro'yxati | `status` (ixtiyoriy), `search` (ixtiyoriy) |
| `students` | `GET /api/branch/students` | O'quvchilar ro'yxati | `month`, `search`, `page`, `limit` (ixtiyoriy) |
| `mentors` | `GET /api/branch/mentors` | Filial mentorlari ro'yxati | `search` (ixtiyoriy) |
| `payments` | `GET /api/branch/payments` | Filialdagi to'lovlar va kassa holati | `status`, `method`, `page`, `limit` (ixtiyoriy) |
| `finance_overview` | `GET /api/finance/overview` | Filial moliyaviy umumiy hisoboti va KPI | `start_date`, `end_date` (ixtiyoriy) |
| `finance_salaries` | `GET /api/finance/salaries` | Xodimlar oylik maoshlari ro'yxati | `month`, `page`, `limit` (ixtiyoriy) |
| `rooms_availability` | `GET /api/branch/rooms/availability` | 7. Bo'sh xonalar va vaqt slotlari bo'yicha bandlik tahlili | `days`, `time_slot` (ixtiyoriy) |
| `schedule_conflicts` | `GET /api/branch/schedule/conflicts` | 7. Xona va mentorlar jadval to'qnashuvlarini topish | — |
| `mentor_workload` | `GET /api/branch/mentors/workload` | 8. Mentorlar yuklama balansi (kim band, kim bo'sh, tavsiyalar) | `max_groups` (int, default: 3) |

---

## O'rnatish va Ishga Tushirish

### 1. Talablar
- Python 3.10 yoki undan yuqori versiya
- Kerakli paketlarni o'rnatish:
```bash
cd mars-mcp-server
pip install -r requirements.txt
```

### 2. Konfiguratsiya (Ixtiyoriy)
Kerak bo'lsa `.env.example` dan `.env` fayl yarating:
```env
MARS_BASE_URL=https://mars-backend-six.vercel.app
# Oldindan mavjud JWT token (ixtiyoriy):
# MARS_AUTH_TOKEN=
```

---

## Klientlarga Ulash (O'rnatish)

### Antigravity IDE / CLI uchun
Server `C:\Users\User\.gemini\config\mcp_config.json` ga avtomatik tarzda o'rnatildi:
```json
{
  "mcpServers": {
    "mars-lms": {
      "command": "C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
      "args": [
        "D:\\Desktop\\Mars\\mars-mcp-server\\server.py"
      ],
      "env": {
        "MARS_BASE_URL": "https://mars-backend-six.vercel.app"
      }
    }
  }
}
```

### Claude Desktop uchun (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "mars-lms": {
      "command": "python",
      "args": ["D:/Desktop/Mars/mars-mcp-server/server.py"]
    }
  }
}
```

### Hermes Agent uchun (`~/.hermes/config.yaml`)
```yaml
mcp_servers:
  mars-lms:
    command: python
    args: ["D:/Desktop/Mars/mars-mcp-server/server.py"]
    timeout: 30
```

---

## Sinov va Tekshirish

Serverning to'liq ishlashini tekshirish uchun tayyor test skriptlari mavjud:

1. **Barcha 8 ta tool va avtorizatsiyani to'liq tekshirish:**
```bash
python test_server.py
```
Bu test:
- Tokensiz chaqiruvda HTTP 401 qaytishini;
- Noto'g'ri login berilganda backend xatosi to'g'ri ko'rsatilishini;
- Demo hisob bilan login muvaffaqiyatli bajarilishini;
- Xotiradagi token orqali barcha 7 ta GET tool (`branch_me`, `groups`, `students`, `mentors`, `payments`, `finance_overview`, `finance_salaries`) muvaffaqiyatli ma'lumot qaytarishini sinovdan o'tkazadi.

2. **JSON-RPC Stdio Protokolini tekshirish:**
```bash
python test_stdio_protocol.py
```

3. **Serverni stdio rejimida ishga tushirish:**
```bash
python server.py
```

---

## Demo Login Ma'lumotlari
- **Telefon:** `998935344549`
- **Parol:** `1234`
- **Rol:** `admin` (yoki `bm`, `mentor`, `financeManager`, `ceo`)
