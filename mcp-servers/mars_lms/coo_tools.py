"""COO tools on the existing FastMCP instance and explicit-login HTTP session."""
import coo_workflows as workflow


def register_coo_tools(mcp, api, result):
    @mcp.tool()
    async def coo_branch_context(branch_id: str | None = None):
        """Read GET /api/branch/me after login; return minimal branch identity and reject mismatched branch scope."""
        return result(await workflow.branch_context(api, branch_id))

    @mcp.tool()
    async def coo_attendance_audit(period_start: str, period_end: str, consecutive_absences: int = 2,
                                   policy_confirmed: bool = False, branch_id: str | None = None, max_pages: int = 10):
        """Read paginated branch attendance for explicit dates. Confirmed attendance only; unknown confirmations never become absences. Actual class start unavailable. Threshold provisional unless confirmed."""
        return result(await workflow.attendance_audit(api, period_start, period_end, consecutive_absences, policy_confirmed, branch_id, max_pages))

    @mcp.tool()
    async def coo_schedule_audit(branch_id: str | None = None, group_limit: int = 100):
        """Read branch group roster/details; detect overlapping room/mentor intervals (not only equal start times). Missing schedule ends/resources stay unknown. No changes applied."""
        return result(await workflow.schedule_audit(api, branch_id, group_limit))

    @mcp.tool()
    async def coo_status_request_sla(sla_hours: float, policy_confirmed: bool = False,
                                      branch_id: str | None = None, max_pages: int = 10):
        """Read all bounded pending /api/branch/status-requests pages and compare elapsed UTC age with explicit SLA hours. Frozen-status applications only; missing timestamps unknown. No approvals/messages."""
        return result(await workflow.status_request_sla(api, sla_hours, policy_confirmed, branch_id, max_pages))

    @mcp.tool()
    async def coo_delegation_plan(period_start: str, period_end: str, sla_hours: float,
                                   consecutive_absences: int = 2, policy_confirmed: bool = False,
                                   branch_id: str | None = None):
        """Build native delegate_task arguments with actual agent.md/soul.md content for three COO children and explicit scope. Preparation only; COO must call delegate_task to execute them."""
        return result(await workflow.delegation_plan(api, period_start, period_end, sla_hours, consecutive_absences, policy_confirmed, branch_id))
