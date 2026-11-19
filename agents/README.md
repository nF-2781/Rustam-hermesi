# MARS Hermes Agents

Two isolated, project-local Hermes profiles use the existing MARS Python MCP
package and the deployed backend `https://mars-backend-six.vercel.app`.
The original `mcp/mars-lms/server.py` and default profile are preserved. The agent
profiles use `mcp/mars-lms/agents_server.py`, which reuses the existing authenticated
HTTP client and adds bounded workflow tools. Each process owns its login token.

## Start

Run from the project root in PowerShell:

```powershell
.\hermes.bat -p student-progress-auditor chat --skills mars-student-progress-auditor
.\hermes.bat -p reception-request-router chat --skills mars-reception-request-router
```

Linux/macOS uses the project wrapper:

```bash
sh hermes.sh -p student-progress-auditor chat --skills mars-student-progress-auditor
sh hermes.sh -p reception-request-router chat --skills mars-reception-request-router
```

Select a profile in the dashboard profile picker to use its SOUL/skill and MCP
configuration. Start a new conversation after switching profile/configuration.

**Model setup is still required.** At installation neither new profile had a
selected model. Run these interactive wizards before attempting LLM work:

```powershell
.\hermes.bat -p student-progress-auditor model
.\hermes.bat -p reception-request-router model
```

No model credentials were copied between profiles. MCP login is separate from LLM
authentication: `login()` reads the authorized local `mcp/mars-lms/.env.local`
without showing credentials to the agent. For production use role-appropriate
accounts; the bundled local account is shared unless explicit credentials are
provided to login. Do not put credentials in skills, SOUL or reports.

## Tools and Verified Contracts

| Tool | Actual source / behavior |
|---|---|
| `login` | POST `/api/auth/login`, token kept only in MCP memory |
| `students` | GET `/students`, returns a minimal authorized roster |
| `attendance` | GET `/attendance/group/:groupId` |
| `homework` | GET `/homework/group/:groupId`, does not auto-create assignments |
| `student_progress` | Verifies student in the authorized roster, then computes current-group attendance and normalized homework grades from the above GETs |
| `curriculum` | GET `/api/branch/curriculum-topic-analytics`, admin/bm only; aggregate context rather than individual proof |
| `incoming_requests` | Explicit capability 501 for backend ingestion; accepts manual `{id,text}` arrays |
| `reception_triage` | Proposed categories/roles/draft replies for supplied messages; never forwards/sends |

Auditor registration includes six domain tools: login, students, attendance,
homework, student_progress, curriculum. Reception registration includes three:
login, incoming_requests, reception_triage. Hermes utility resources/prompts are
disabled. These tool filters and profiles are not an OS sandbox.

The user-provided `/student-progress`, `/curriculum`, `/branch-manager/requests`,
`/issues` and their `/api/...` variants were checked against the deployed backend:
all returned 404. They were not found in the inspected local backend or frontend
route registries either. `/api/branch/status-requests` exists but represents only
frozen-status applications; it is not a generic reception inbox. No verified
general request assignment/dispatch endpoint was found. Automatic reception
ingestion and forwarding remain blocked on a real inbox/dispatch contract.

## Example Requests

Auditor (after confirming a cohort and period):

```text
2026-11-01 dan 2026-11-19 gacha tanlangan guruh o‘quvchilarini tekshir.
Avval mezonlarni ko‘rsat; tasdiqlanmaguncha xulosani namuna deb belgilagin.
Mentor uchun dalillar, noma’lum ma’lumotlar va individual yordam rejasini ber.
```

Reception:

```text
Murojaatlarni tasnifla va administratorga yo‘naltirish taklifini ber. Yuborma.
[{"id":"r1","text":"Dars jadvalini bilmoqchiman"},
 {"id":"r2","text":"To‘lovim ko‘rinmayapti"}]
```

Example thresholds are 80% attendance with at least three observed lessons,
60% normalized graded homework and two missing group submissions. They are
**unapproved examples**, not the center's policy. Missing grades/attendance remain
unknown; current-group assignments may predate enrollment. No transfer/exam
completeness is claimed. Curriculum defect/resolved labels are backend heuristics
and require human review. The reception classifier uses multilingual keyword
suggestions; ambiguous messages go to administrator clarification.

Only consistent `confirmed/approved` present and `rejected/not_needed` absent
attendance records contribute to percentages. Pending, disputed, missing or
inconsistent confirmation states stay unknown. Attendance uses the backend's
Tashkent `day` field where available, otherwise the ISO date prefix.

## Install on Another Machine

Rebuild the host and MCP virtual environments as described in the MCP README.
From this project root, using the host environment:

```powershell
.\runtime\venv\Scripts\python.exe agents/install.py
```

```bash
runtime/venv/bin/python agents/install.py
```

The installer creates only missing named profiles, refuses existing targets,
copies no credentials and does not create global aliases or change sticky default.
Run it on the target OS; it selects `Scripts/python.exe` or `bin/python` and uses
the launcher's `${PYTHONPATH}` to resolve this checkout independently of profile
home. Keep using the project launcher. If profiles were copied to another OS,
back up their user data and reconcile their MCP command paths before use; existing
profiles are never overwritten automatically.

## Checks and Limits

```powershell
.\mcp\mars-lms\.venv\Scripts\python.exe -m unittest discover -s mcp/mars-lms/tests -v
.\hermes.bat -p student-progress-auditor mcp test mars-lms
.\hermes.bat -p reception-request-router mcp test mars-lms
.\hermes.bat -p student-progress-auditor skills list
.\hermes.bat -p reception-request-router skills list
```

`mcp test` reports the eight tools advertised by the companion server before
profile registration filters; native registry verification confirms the six/three
tools actually registered for these profiles. Fixtures cover no-login, scoped
student access, denied requests, normalization, missing evidence, ambiguous
requests and no delivery. Live probes log only status/schema facts; they do not
persist student records. No LLM-generated report, Linux deployment, scheduled run
or messaging delivery has been tested. No cron, gateway, Telegram/email sender or
backend writes were installed. Stop using a profile to disable it; any later
profile deletion must preserve the user's data and credentials.
