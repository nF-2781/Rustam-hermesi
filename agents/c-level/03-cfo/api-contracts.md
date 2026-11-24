# CFO API Contracts

## Checked Implementation

The backend is an Express service, with OpenAPI at
`https://mars-backend-six.vercel.app/api-docs.json`. This integration follows the
actual existing `mcp-servers/mars_lms/server.py` and `lms_client.py` contracts, not
unverified route names in illustrative upstream reports. Credentials are read
privately from `mcp-servers/mars_lms/.env`; no account secrets are copied to profiles.

| Tool | Parameters used | Actual backend reads / result |
| --- | --- | --- |
| `lms_login` | No arguments by default | POST `/api/auth/login`; in-memory session summary |
| `lms_context` | None | `/api/branch/overview`, `/api/branch/groups`; session/branch context |
| `get_debts` | `month`, `status`, `search`, `limit` | `/api/branch/debtors`; `details.debtors`, total_remaining, counts, pagination |
| `debt_control_agent` | `month`, `min_days_overdue`, `limit` | `/api/branch/debtors`; report and reminder drafts |
| `get_payments` | `month`, `page`, `limit` | `/api/branch/payments`; `details.payments` and pagination |
| `get_finance_report` | `month` | `/api/branch/overview?month=...` and `/api/finance/overview`; `details.branch` and `details.finance` |
| `daily_finance_report` | `month`, `compare` | Same overview reads plus previous branch month when compare=true |
| `list_students` | `search`, `group_id`, `only_debtors`, `limit`, `offset` | `/api/branch/students`; selected student records and pagination |

## Evidence and Limits

- Current tools do not call `/finance/debts` or `/api/finance/daily`.
- Workflow responses use `error/status_code/message/endpoint/details`. Inspect error
  before using details; do not treat failures or absent fields as zero.
- `daily_finance_report` is a monthly snapshot/comparison despite its name. Its
  computed income-expense balance is not verified cash-on-hand or a reconciled till.
- The branch overview accepts month. Finance overview is fetched without month;
  establish its period and scope before combining figures or claiming comparisons.
- Payment methods are cash/card/transfer unless actual records provide finer labels.
- Budget target, period and projection assumptions must be supplied explicitly.
  No authoritative budget plan endpoint or completed forecast is implied.
- Follow available pagination and report caps/incomplete coverage. Source branch
  authorization does not establish company-wide visibility.
- Raw tools may return phone/name fields. Agent reports and delegated summaries
  must omit these and use internal student IDs. No automatic PII masking is claimed.
- No write, payment/refund, salary, approval or message-sending tool is exposed to
  these profiles. Proposed timetable rows do not install recurring jobs.

## Runtime Integration

`agents/c-level/03-cfo/install.py` creates only `mars-cfo`, `debt-collector`,
`cashier-reporter` and `budget-planner`, using one existing MCP SDK/environment.
The CFO's generated SOUL embeds supported native delegation tasks and actual child
role text. Shared finance whitelist8 for native delegates; standalone specialists
have minimal toolsets3/3/4. See `README.md` for current setup and verification.
