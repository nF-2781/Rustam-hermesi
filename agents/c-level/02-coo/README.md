# MARS COO Hierarchy

```text
CEO — Rustam
└── C-level: mars-coo
    ├── Attendance Sentinel
    ├── Room & Schedule Optimizer
    └── SLA Request Monitor
```

Every role has `agent.md` (contract/workflow) and `soul.md` (identity). This checkout
does not automatically discover these lowercase files as named delegate profiles.
The installer retains `AGENTS.md` and builds native profile `SOUL.md` from both
canonical COO files. This ensures the contract loads even when CWD is the project
root (Hermes discovers AGENTS by CWD, not by profile home). The MCP
`coo_delegation_plan` loads subordinate role text into native `delegate_task`
task contexts. No Hermes core modifications or additional MCP SDK are required.

## Start

From the repository root, install once:

```powershell
.\runtime\venv\Scripts\python.exe agents/c-level/02-coo/install.py
```

Then start the COO profile:

```powershell
.\hermes.bat -p mars-coo chat --skills mars-coo-operations
```

Or open the dashboard at the requested port and select **mars-coo**, then create
a new conversation:

```powershell
.\hermes.bat dashboard --skip-build --port 9120
```

Linux uses `runtime/venv/bin/python agents/c-level/02-coo/install.py` and
`sh hermes.sh -p mars-coo chat --skills mars-coo-operations` after recreating the
single MCP `.venv` for that OS. The installer refuses an existing profile; it does
not clone credentials, alter old profiles, create a CEO, or change sticky default.
It copies only existing model selection. Provider authentication must be available
in this profile; use `hermes.bat -p mars-coo model` if required. No model success
is implied by successful MCP discovery.

## Example Request

Ask for a past reporting period and specify the branch if needed. For a demo:
“Run the COO audit for the selected past week. Use an example 24 elapsed-hour
status-request threshold and 2 consecutive confirmed absences, both unconfirmed
policy. Delegate all three specialist audits, then give one report with limits.”

SLA thresholds and absence rules are not approved company policy until confirmed.
Actual lesson-start punctuality is unavailable in the verified API. Status SLA
monitors frozen-status applications only. This profile exposes six read-only MCP
tools to COO and children; per-role task boundaries are instructions, not separate
security permissions. Terminal/file/web tools are not enabled. No messages,
approvals, schedule edits or recurring jobs are installed.

## Verification

```powershell
.\hermes.bat -p mars-coo skills list
.\hermes.bat -p mars-coo mcp test mars_lms
.\mcp-servers\mars_lms\.venv\Scripts\python.exe -m unittest discover -s mcp-servers/mars_lms -p "test_*.py" -v
```

Raw MCP discovery lists all server tools before profile filtering. Native profile
registration should contain only `login` plus the five `coo_*` tools. See
`api-contracts.md` for actual API evidence and remaining limits.
