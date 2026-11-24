---
name: hermes-mars-dashboard
description: Run and inspect this checkout's Hermes dashboard with the project runtime and verified process ownership.
---
# MARS Hermes Dashboard

## Run

From the repository root:

```powershell
.\hermes.bat dashboard --port 9120
```

Select one of the seven C-level profiles. Synchronize managed contracts with
`runtime/venv/Scripts/python.exe agents/install.py all --sync`; check with `--check`.
The root launcher sets HERMES_HOME and PYTHONPATH from the checkout path.

## Background Lifecycle

```powershell
runtime/venv/Scripts/python.exe skills/hermes_mars_dashboard/dashboard.py start --port 9120
runtime/venv/Scripts/python.exe skills/hermes_mars_dashboard/dashboard.py status --port 9120
runtime/venv/Scripts/python.exe skills/hermes_mars_dashboard/dashboard.py stop
```

The shell wrapper supports the same arguments. Start uses a hidden process on
Windows. Status uses the normal loopback bootstrap and authenticated health API;
no session token is printed or persisted. The helper owns only processes it starts.
Stop checks saved PID/start time, executable, project CWD, module and port before
terminating that process. It never kills candidate-port listeners or unrelated
process trees. An existing healthy dashboard is reused without claiming ownership.

## Limits

Inspect `logs/dashboard-mars.log` for startup errors. Keep credentials in their
existing files; do not print auth.json or .env. Dashboard/API visibility and MCP
discovery do not prove successful model generation. Configure provider login
separately when required. No backend records or external messages are changed.
