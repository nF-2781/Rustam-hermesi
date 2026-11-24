"""MCP server uchun haqiqiy stdio test klienti (Anthropic Phase 4).

Bu skript serverni alohida jarayon sifatida ishga tushiradi va MCP protokoli
orqali tool'larni ro'yxatlaydi hamda jonli backend bilan tekshiradi.

Ishga tushirish:
    .venv/Scripts/python.exe test_client.py            # to'liq (jonli backend)
    .venv/Scripts/python.exe test_client.py --no-live  # faqat tools/list
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable
SERVER = os.path.join(HERE, "server.py")

EXPECTED_AGENTS = {
    "debt_control_agent",
    "attendance_control_agent",
    "homework_control_agent",
    "daily_finance_report",
    "new_student_followup",
    "pending_approvals_digest",
    "room_schedule_assistant",
    "mentor_workload_analysis",
    "student_progress_audit",
    "reception_router",
}

failures: list[str] = []


def body_of(result) -> dict:
    """Tool natijasini structuredContent yoki JSON matnidan oladi."""
    if getattr(result, "structuredContent", None):
        return result.structuredContent
    for item in getattr(result, "content", []) or []:
        text = getattr(item, "text", None)
        if text:
            try:
                return json.loads(text)
            except ValueError:
                continue
    return {}


def check(condition: bool, message: str) -> None:
    if condition:
        print(f"PASS  {message}")
    else:
        failures.append(message)
        print(f"FAIL  {message}")


async def main() -> int:
    live = "--no-live" not in sys.argv
    env = {
        **os.environ,
        "MARS_API_URL": os.environ.get("MARS_API_URL", "https://mars-backend-six.vercel.app"),
        "PYTHONIOENCODING": "utf-8",
    }
    params = StdioServerParameters(command=PYTHON, args=[SERVER], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            print(f"tools: {len(names)}")
            check(EXPECTED_AGENTS.issubset(names), "10 ta workflow-agent tool ro'yxatga olindi")
            check({"lms_login", "lms_context", "get_debts", "list_groups"} <= names, "yordamchi tool'lar mavjud")
            check(len(names) == 43, "barcha 43 ta birlashtirilgan tool mavjud")

            if not live:
                return 1 if failures else 0

            payload = await session.call_tool("lms_login", {})
            data = body_of(payload)
            check(not data.get("error"), f"lms_login muvaffaqiyatli ({data.get('message')})")

            for tool_name, arguments in (
                ("debt_control_agent", {}),
                ("attendance_control_agent", {"consecutive_misses": 2}),
                ("homework_control_agent", {"only_overdue": True}),
                ("daily_finance_report", {}),
                ("new_student_followup", {"days": 30}),
                ("pending_approvals_digest", {}),
                ("room_schedule_assistant", {}),
                ("mentor_workload_analysis", {}),
                ("student_progress_audit", {}),
                ("reception_router", {}),
            ):
                result = await session.call_tool(tool_name, arguments)
                body = body_of(result)
                ok = body.get("error") is None and isinstance(body.get("details"), dict)
                details = body.get("details") or {}
                summary = details.get("summary") or details.get("counts") or details.get("pagination") or {}
                check(ok, f"{tool_name} -> {body.get('message')} {summary}")

            bad = await session.call_tool("get_debts", {"month": "not-a-month"})
            bad_body = body_of(bad)
            check(bad_body.get("status_code") == 400, "noto'g'ri oy formati 400 bilan rad etildi")

            missing = await session.call_tool("get_student_progress", {"student_id": "000000000000000000000000"})
            missing_body = body_of(missing)
            check(bool(missing_body.get("error")), "mavjud bo'lmagan o'quvchi uchun aniq xato qaytdi")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
