"""Scoped progress/reception tools registered on the shared MCP server."""
import json
import os
from pathlib import Path

from mcp.types import CallToolResult, TextContent
from scoped_client import DEFAULT_API_URL, LMSClient
from scoped_settings import read_settings
import agent_workflows as workflow


def result(payload):
    return CallToolResult(content=[TextContent(type='text', text=json.dumps(payload, ensure_ascii=False))],
                          structuredContent=payload, isError=not payload['success'])


def register_profile_tools(mcp):
    api = LMSClient(os.environ.get('MARS_API_URL', DEFAULT_API_URL),
                    timeout=float(os.environ.get('MARS_API_TIMEOUT_SECONDS', '20')))

    @mcp.tool()
    async def branch_me():
        """GET /api/branch/me after explicit login; retained original read tool."""
        return result(await api.get('/api/branch/me'))

    @mcp.tool()
    async def groups(query: dict[str, str | int | float | bool] | None = None):
        """GET /api/branch/groups after explicit login, with optional backend filters."""
        return result(await api.get('/api/branch/groups', query))

    @mcp.tool()
    async def mentors(query: dict[str, str | int | float | bool] | None = None):
        """GET /api/branch/mentors after explicit login, with optional backend filters."""
        return result(await api.get('/api/branch/mentors', query))

    @mcp.tool()
    async def payments(query: dict[str, str | int | float | bool] | None = None):
        """GET /api/branch/payments after explicit login, with optional backend filters."""
        return result(await api.get('/api/branch/payments', query))

    @mcp.tool()
    async def finance_overview(query: dict[str, str | int | float | bool] | None = None):
        """GET /api/finance/overview; the backend enforces finance permissions."""
        return result(await api.get('/api/finance/overview', query))

    @mcp.tool()
    async def finance_salaries(query: dict[str, str | int | float | bool] | None = None):
        """GET /api/finance/salaries; the backend enforces finance permissions."""
        return result(await api.get('/api/finance/salaries', query))

    @mcp.tool()
    async def login(phone: str | None = None, password: str | None = None, role: str | None = None):
        """Authenticate with explicit credentials or the authorized local .env account. Never returns credentials/token. Pass both phone and password, or neither."""
        if (phone is None) != (password is None):
            return result(LMSClient.error(400, 'Pass both phone and password, or neither'))
        if phone is None:
            settings = read_settings(Path(__file__).with_name('.env'))
            phone, password = settings.get('MARS_PHONE', ''), settings.get('MARS_PASSWORD', '')
            role = settings.get('MARS_ROLE')
        return result(await api.login(phone, password, role))

    @mcp.tool()
    async def students():
        """List minimal authorized students from verified GET /students; omit phones and financial fields."""
        return result(await workflow.roster(api))

    @mcp.tool()
    async def attendance(group_id: str):
        """GET /attendance/group/{group_id}. Backend enforces group scope; workflow fields only."""
        return result(await workflow.group_records(api, 'attendance', group_id))

    @mcp.tool()
    async def homework(group_id: str):
        """GET /homework/group/{group_id}. Read existing assignments without generating homework."""
        return result(await workflow.group_records(api, 'homework', group_id))

    @mcp.tool()
    async def student_progress(student_id: str, period_start: str, period_end: str,
                               criteria: dict | None = None, criteria_confirmed: bool = False):
        """Audit authorized student's current-group attendance and homework for YYYY-MM-DD period. Missing data stays unknown; normalize grades by maxScore. Default thresholds are unconfirmed examples."""
        return result(await workflow.student_progress(api, student_id, period_start, period_end, criteria, criteria_confirmed))

    @mcp.tool()
    async def curriculum(fail_threshold_percent: int = 40, score_threshold: int = 60, cross_group_threshold: int = 2):
        """GET /api/branch/curriculum-topic-analytics (admin/bm). Branch topic aggregates, NOT individual student progress. Backend causal labels/resolved statuses are heuristics requiring mentor review."""
        if (not 1 <= fail_threshold_percent <= 100 or not 1 <= score_threshold <= 100
                or not 1 <= cross_group_threshold <= 100):
            return result(LMSClient.error(400, 'Percent thresholds must be 1..100; group threshold 1..100'))
        reply = await api.get('/api/branch/curriculum-topic-analytics', {
            'failThresholdPercent': fail_threshold_percent, 'scoreThreshold': score_threshold,
            'crossGroupThreshold': cross_group_threshold})
        if reply['success']:
            reply['limitations'] = ['Branch aggregates are not individual diagnoses.',
                                    'Systemic-flaw labels are backend heuristics, not proven causes.',
                                    'Resolved status may be automatic, not human-confirmed.']
        return result(reply)

    @mcp.tool()
    async def incoming_requests(requests: list[dict[str, str]] | None = None):
        """Without input return explicit 501: no verified generic backend inbox. With [{id,text}] ingest manual messages; never substitute frozen-status requests."""
        return result(workflow.incoming_requests(requests))

    @mcp.tool()
    async def reception_triage(requests: list[dict[str, str]], responsible_roles: dict[str, str] | None = None):
        """Suggest payment/schedule/education/technical/other categories, responsible roles and draft replies. Flag ambiguity. Never send or assign anything."""
        return result(workflow.reception_triage(requests, responsible_roles))

