# MARS CFO Dashboard Integration

Imported from Islom's commits `5fca699` and `1ea5755` using cherry-pick provenance.
The shared installer conflict was resolved by preserving the pre-existing auditor
and reception installer, then adding a CFO-specific entry point.

## Profiles

| Profile | Role | MCP tools |
| --- | --- | --- |
| `mars-cfo` | Islom, CFO reporting to CEO Rustam | 8 finance tools plus native delegation |
| `debt-collector` | Debts and reminder drafts | lms_login, get_debts, debt_control_agent |
| `cashier-reporter` | Payment/finance reporting | lms_login, daily_finance_report, get_payments |
| `budget-planner` | Monthly overview and qualified projections | lms_login, get_finance_report, daily_finance_report, lms_context |

The CFO creates three native leaf tasks from the actual subordinate definitions
embedded in its generated SOUL. Standalone specialist dashboard profiles are also
available. No separate per-child permissions are implied for native delegates:
they inherit the CFO's8-tool whitelist, while standalone profiles have3/3/4.

## Install and Run

From this repository root:

```powershell
.\runtime\venv\Scripts\python.exe agents/install.py cfo
.\runtime\venv\Scripts\python.exe agents/install.py cfo --check
.\hermes.bat dashboard --skip-build --port 9120
```

The installation command runs once and refuses to overwrite existing CFO profiles.
`-Check` is read-only. In the dashboard, select **mars-cfo** and start a new chat.
Example: ask for the selected month YYYY-MM and request debt, payment and financial
overview summaries with sources and limitations. The native delegation task template
uses USER_CONFIRMED_MONTH, which CFO replaces with that month before dispatch.

CLI alternative:

```powershell
.\hermes.bat -p mars-cfo chat --skills mars-cfo-agent
.\hermes.bat -p mars-cfo mcp test mars_lms
```

Profiles copy only the existing model selection. Provider credentials are not copied;
configure model authentication for a profile if needed using
`.\hermes.bat -p mars-cfo model`. Successful MCP discovery does not prove successful
model generation. Backend credentials remain in the single MCP `.env`.

## Compatibility and Limits

No additional MCP tools, SDK or server were needed. Existing COO and auditor/reception
profiles are preserved. Runtime contract and current API definitions are documented
in `runtime.md` and `api-contracts.md`. Native identity loads the adapted source SOUL
and actual child packets under the context budget; static numeric dialogue examples
are excluded. Profile AGENTS is retained as reference because dashboard CWD does not
automatically load it.

This checkout's daily_finance_report compares months, not days. Budget targets and
actual counted cash are not supplied by these tools. Financial projections must be
labelled assumptions; no messages, financial writes or cron are installed. Student
contact details must not appear in outputs. Upstream examples are illustrative.
