# mcp-mars-finance — moliya domeni MCP serveri

`digital-org/mcp/servers.json` dagi `mcp-mars-finance` registrining **ishlaydigan kodi**.
Bitta katta `mars_lms` serveridan ajratilgan birinchi domen: moliya endpointlari boshqa
agentlarga umuman ko'rinmaydi, har yozuvchi tool kod darajasidagi guardrail'dan o'tadi.

```text
Hermes (finance-payroll | ceo-strategist)
   └──stdio──> mcp-servers/mars_finance/server.py
                  ├── lms_client.LMSClient      (umumiy HTTP klient, token xotirada)
                  └── security_sandbox.check()  (RBAC → ABAC → hard guardrail)
```

## Nima uchun alohida server

| Sabab | Natija |
|---|---|
| Kontekst iqtisodi | mentorga moliya tool'i ko'rinmaydi (13 tool o'rniga 0) |
| RBAC | `ceo-strategist` faqat o'qiydi; yozuv — `finance-payroll` ishi |
| Guardrail bir joyda | pul amallari `security_sandbox.py` dan o'tmasdan bajarilmaydi |
| Orqaga qaytish | `mcp-servers/mars_lms` o'chirilmagan, ikkisi parallel ishlaydi |

## Tool'lar (13)

| Tool | Metod · endpoint | Guardrail |
|---|---|---|
| `finance_login` | `POST /api/auth/login` | — |
| `finance_overview` | `GET /api/branch/overview` + `/api/finance/overview` | ABAC |
| `list_payments` | `GET /api/branch/payments` | ABAC |
| `list_expenses` | `GET /api/branch/expenses` | ABAC |
| `list_debtors` | `GET /api/branch/debtors` | `month` majburiy, ABAC |
| `list_salaries` | `GET /api/finance/salaries` | ABAC |
| `mentor_earnings` | `GET /api/finance/owner/mentor-earnings` | ABAC |
| `create_payment` | `POST /api/branch/payments` | summa > 0 |
| `update_payment` | `PATCH /api/branch/payments/{id}` | `REASON_REQUIRED` |
| `void_payment` | `POST /api/branch/payments/{id}/void` | `REASON_REQUIRED` + `HUMAN_APPROVAL` |
| `create_expense` | `POST /api/branch/expenses` | > 1 000 000 UZS → `HUMAN_APPROVAL` |
| `create_salary_draft` | `POST /api/finance/salaries` | har doim `HUMAN_APPROVAL` |
| `set_salary_status` | `PATCH /api/finance/salaries/{id}/status` | `paid` → `HUMAN_APPROVAL` |

Eski `POST /api/payments` bu serverda **yo'q**; guardrail ham uni `LEGACY_ENDPOINT`
bilan bloklaydi.

## Javob konverti

```json
{"error": null, "status_code": 200, "message": "success", "endpoint": "/api/branch/payments", "details": {}}
```

| status_code | Ma'nosi | Agent nima qiladi |
|---|---|---|
| `200` | bajarildi | natijani hisobotga qo'shadi |
| `400` | parametr xatosi | parametrni tuzatib qayta chaqiradi |
| `403` | `RBAC_AGENT` / `RBAC_READ_ONLY` / `ABAC_BRANCH` / `REASON_REQUIRED` / `LEGACY_ENDPOINT` | to'xtaydi, odamga aytadi |
| `428` | `HUMAN_APPROVAL` — amal **bajarilmadi** | taklif/hisobot beradi, tasdiq so'raydi |
| `5xx` | backend xatosi | eskalatsiya (Auditor + CTO) |

`428` muhim: bu "yumshoq ruxsat" emas. Tool hech narsa yozmaydi, faqat to'xtaydi.

## Ishga tushirish

```bash
# 1. Testlar (mock backend, tarmoqsiz)
./mcp-servers/mars_lms/.venv/Scripts/python.exe -m pytest mcp-servers/mars_finance/tests -q

# 2. Qo'lda stdio tekshiruvi
./mcp-servers/mars_lms/.venv/Scripts/python.exe mcp-servers/mars_finance/server.py
```

Hermes `config.yaml` ga qo'shish (mars_lms bilan bir xil venv ishlatiladi):

```yaml
mcp_servers:
  mars_finance:
    command: C:/Users/user/Documents/Hermes-2/mcp-servers/mars_lms/.venv/Scripts/python.exe
    args: [C:/Users/user/Documents/Hermes-2/mcp-servers/mars_finance/server.py]
    env:
      PYTHONIOENCODING: utf-8
      PYTHONUNBUFFERED: '1'
    enabled: true
    timeout: 180
```

Server `mcp-servers/mars_lms/.env` ni o'qiydi (parol chatga ham, git'ga ham chiqmaydi).

## Holat (halol)

- Guardrail/RBAC yo'li **mock backend** bilan 19 testda tekshirilgan.
- Jonli backend bilan to'liq oqim (login → to'lov → tasdiq) hali sinalmagan: buning uchun
  haqiqiy akkaunt va tasdiqlash oynasi kerak.
- `GET` endpointlar `mars_lms/server.py` da allaqachon ishlagan; bu serverda ular
  qayta yozilmadi, umumiy `lms_client` orqali chaqiriladi.
- Keyingi server: `mcp-mars-branch` (eng katta endpoint guruhi).
