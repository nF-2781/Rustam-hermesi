# MARS C-Level Agents

Canonical definitions live only in `agents/c-level`. Historical source copies under `references` are not active agents.

| Role | Owner/contact | Definition |
|---|---|---|
| mars-ceo — Chief Executive Officer | @rustam106 | `agents/c-level/01-ceo/soul.md` + `agents.md` |
| mars-coo — Chief Operating Officer | @jamkaILZ | `agents/c-level/02-coo/soul.md` + `agents.md` |
| mars-cfo — Chief Financial Officer | @vxrnox | `agents/c-level/03-cfo/soul.md` + `agents.md` |
| mars-cto — Chief Technology Officer | Hacker | `agents/c-level/04-cto/soul.md` + `agents.md` |
| mars-cmo — Chief Marketing Officer | @Saidabza1 | `agents/c-level/05-cmo/soul.md` + `agents.md` |
| mars-chro — Chief Human Resources and Education Quality Officer | @rizo_x7k | `agents/c-level/06-chro/soul.md` + `agents.md` |
| mars-cso — Chief Student Success Officer | @k_mukhamedov | `agents/c-level/07-cso/soul.md` + `agents.md` |
| mars-head-reception — Head of Reception | @muhammad_solih13 | `agents/c-level/08-head-reception/soul.md` + `agents.md` |
| mars-chief-audit — Chief Audit Officer | Unassigned | `agents/c-level/09-chief-audit/soul.md` + `agents.md` |

## Install and Run

From the repository root:

```powershell
runtime/venv/Scripts/python.exe agents/install.py all --sync
runtime/venv/Scripts/python.exe agents/install.py all --check
.\hermes.bat dashboard --port 9120
```

Open http://127.0.0.1:9120 and select a profile. Existing model settings, auth and profile history are preserved. New profiles copy only non-secret model selection. Authenticate the configured model provider separately if required.

## Delegation

The registry records eight COO/CFO/CSO/Reception specialists; five retain standalone profiles. CEO uses batches of at most three direct departments. Native delegation inherits parent tools, so specialist tool lists are instructions rather than separate authorization. Shared runtime contracts and actual source identities are embedded in each delegated context. No automatic notifications or schedules are installed.
