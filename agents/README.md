# MARS C-Level Agents

The corrected user roster has seven departments. Definitions live only in `agents/c-level`. Historical definitions under references are inactive.

| Profile | Human owner | Source |
|---|---|---|
| mars-ceo | Rustam (Team Lead) | `agents/c-level/01-ceo/soul.md` + `agents.md` |
| mars-coo | Kamollidin | `agents/c-level/02-coo/soul.md` + `agents.md` |
| mars-cfo | Islom | `agents/c-level/03-cfo/soul.md` + `agents.md` |
| mars-cto | Saidabzal | `agents/c-level/04-cto/soul.md` + `agents.md` |
| mars-cmo | Muhammadrizo | `agents/c-level/05-cmo/soul.md` + `agents.md` |
| mars-cpo | Muhammadsolih | `agents/c-level/06-cpo/soul.md` + `agents.md` |
| mars-hr | Muhammadali | `agents/c-level/07-hr/soul.md` + `agents.md` |

## Install and Run

```powershell
runtime/venv/Scripts/python.exe agents/install.py all --sync
runtime/venv/Scripts/python.exe agents/install.py all --check
.\hermes.bat dashboard --port 9120
```

Open http://127.0.0.1:9120 and select a profile. Existing model/auth/history and root credentials are preserved. Seven C-level profiles plus five existing standalone specialists remain.

## Delegation

CEO coordinates COO, CFO, CTO, CMO, CPO and HR, at most three direct departments per batch. COO and CFO each keep three specialists; CPO owns student-progress-auditor and reception-request-router. Native children inherit parent tools. HR and other leaves do not redelegate. See runtime.md for privacy and actual API limitations.
