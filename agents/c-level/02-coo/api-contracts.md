# COO API Contracts

## Sources

Checked on 2026-11-22 against deployed
`https://mars-backend-six.vercel.app/api-docs.json` (HTTP 200), the Swagger UI's
underlying OpenAPI source. The browser reader could not render `/api-docs`.
Cross-checked source in `C:/Users/Asus/Desktop/MARS-LMS/mars-backend/src`:
`router/branchAdmin.router.js`, `router/branchAdminExtra.router.js`,
`models/attendance.models.js`, `models/studentStatusRequest.model.js`,
`models/group.models.js`. Credentials stay in `mcp-servers/mars_lms/.env`.

## Read Contracts

| Endpoint | Usage and limits |
| --- | --- |
| POST `/api/auth/login` | Explicit MCP `login`; token in memory, never returned |
| GET `/api/branch/me` | Establish account's branch; reject a requested different branch |
| GET `/api/branch/groups` | Current branch roster; list does not expose room assignment |
| GET `/api/branch/groups/{id}` | Branch-scoped group detail includes room/schedule; student fields are discarded |
| GET `/api/branch/attendance` | Paginated attendance, group/student/date filters; no actual class-start event |
| GET `/api/branch/status-requests` | Paginated frozen-status applications; status pending/approved/rejected; not a generic inbox |
| GET `/api/branch/workload-planning` | Existing `get_room_plan` uses this planning estimate; not proof of room availability |

Authenticated live checks returned 200 for branch identity, groups, attendance,
pending status requests and workload planning. Native Hermes calls to all five
new COO tools also returned 200, including scoped group detail reads. The plan's
three role packets passed the current native delegate_task schema/normalizer and
output-schema validation; actual LLM child execution was not run. No approval or mutation
route is exposed to COO. Source GET `/api/branch/attendance-risks` performs a scan
with persistence in this backend, so it is deliberately excluded.

## Evidence Rules

- `date` on attendance is not actual lesson start. Punctuality is unavailable.
- Pending/disputed/missing/inconsistent confirmations are unknown, not absences.
- Explicit weekly schedule start/end is required; interval overlap, not equal start,
  establishes a planned collision. Missing rooms/mentors or end times stay unknown.
- SLA uses pending `createdAt`, server UTC and a required elapsed-hour threshold.
  Business-hour calendars and official thresholds are not assumed.
- Pagination caps, duplicate records, malformed shapes and API failures remain visible.
- Branch admin/bm account scope is not company-wide authorization.

## Newly Added Tools

`coo_branch_context`, `coo_attendance_audit`, `coo_schedule_audit`,
`coo_status_request_sla`, `coo_delegation_plan`. The last tool prepares role context;
native Hermes `delegate_task` actually launches the three children.
