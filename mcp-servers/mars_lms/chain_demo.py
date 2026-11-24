"""MARS LMS ish zanjirini MCP orqali yurgizadigan demo (uyga vazifa, 3-qism).

Zanjir: lms_login -> lms_context -> get_debts -> get_payments ->
debt_control_agent -> daily_finance_report

Ishga tushirish:
    .venv/Scripts/python.exe chain_demo.py
    .venv/Scripts/python.exe chain_demo.py --month 2026-11 --local
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# lms_client `.env` faylini o'qiydi va DEFAULT_API_URL ni hal qiladi.
# Shu sababli backend manzili faqat bitta joyda (`.env`) sozlanadi.
from lms_client import DEFAULT_API_URL

# Windows konsoli (CP866/CP1251) UTF-8 o'rniga o'z kodlashini ishlatib matnni buzadi.
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable
SERVER = os.path.join(HERE, "server.py")
REPORT = os.path.join(HERE, "chain_report.md")


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


def arg_value(flag: str, default: str) -> str:
    if flag in sys.argv:
        index = sys.argv.index(flag)
        if index + 1 < len(sys.argv):
            return sys.argv[index + 1]
    return default


async def main() -> int:
    month = arg_value("--month", datetime.now(timezone.utc).strftime("%Y-%m"))
    base_url = "http://localhost:7000" if "--local" in sys.argv else DEFAULT_API_URL
    env = {**os.environ, "MARS_API_URL": base_url, "PYTHONIOENCODING": "utf-8"}

    params = StdioServerParameters(command=PYTHON, args=[SERVER], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(f"tools: {len(tools.tools)} | backend: {base_url} | month: {month}")

            steps: list[tuple[str, dict, dict]] = []

            async def run(tool: str, arguments: dict) -> dict:
                result = await session.call_tool(tool, arguments)
                body = body_of(result)
                if body.get("error"):
                    print(f"FAIL  {tool}: {body.get('message')}")
                else:
                    print(f"OK    {tool}: {body.get('message')} ({body.get('endpoint')})")
                steps.append((tool, arguments, body))
                return body

            await run("lms_login", {})
            context = await run("lms_context", {})
            debts = await run("get_debts", {"month": month})
            payments = await run("get_payments", {"month": month})
            reminders = await run("debt_control_agent", {"month": month})
            finance = await run("daily_finance_report", {"month": month})

            if any(body.get("error") for _, _, body in steps):
                print("chain FAILED — yuqoridagi xatoni tuzating")
                return 1

            ctx = context.get("details") or {}
            # lms_context raqamlarni details.counts ichida qaytaradi, details'ning o'zida emas.
            counts = ctx.get("counts") or {}
            debt_details = debts.get("details") or {}
            pay_details = payments.get("details") or {}
            fin_details = finance.get("details") or {}
            drafts = (reminders.get("details") or {}).get("message_drafts") or []

            lines = [
                f"## MARS LMS — kunlik holat ({datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC})",
                "",
                f"- Backend: `{base_url}` | Oy: `{month}`",
                f"- Guruhlar: {counts.get('groups', 0)} | "
                f"Faol o'quvchilar: {counts.get('active_students', 0)} | "
                f"To'lamaganlar: {counts.get('unpaid_students', 0)}",
                f"- Qarzdorlar: {len(debt_details.get('debtors') or [])} ta",
                # Ikkala raqam ham har xil manbadan: ro'yxat hisob oyi (month), KPI to'langan sana (paidAt) bo'yicha.
                f"- Tushumlar (hisob oyi bo'yicha ro'yxat): {len(pay_details.get('payments') or [])} ta",
                f"- Moliyaviy KPI (to'langan sana bo'yicha): {json.dumps(fin_details.get('kpi') or {}, ensure_ascii=False)}",
                f"- Eslatma loyihalari: {len(drafts)} ta (yuborilmagan)",
                "",
                "### Zanjir qadamlari",
            ]
            for tool, arguments, body in steps:
                args = ", ".join(f"{k}={v}" for k, v in arguments.items()) or "-"
                lines.append(f"1. `{tool}` ({args}) → {body.get('status_code')} {body.get('message')}")

            for index, draft in enumerate(drafts[:5], start=1):
                text = draft if isinstance(draft, str) else draft.get("text") or json.dumps(draft, ensure_ascii=False)
                lines.append(f"{index}. {text}")

            with open(REPORT, "w", encoding="utf-8") as handle:
                handle.write("\n".join(lines) + "\n")

            print(f"chain OK — {len(steps)} qadam, hisobot: {REPORT}")
            return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
