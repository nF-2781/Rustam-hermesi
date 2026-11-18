"""MARS LMS stdio MCP server for local Hermes AI employees."""

import json
import logging
import os
from typing import Any

from mcp.server import MCPServer
from mcp.types import CallToolResult, TextContent

from lms_client import DEFAULT_API_URL, LMSClient

logging.basicConfig(level=logging.WARNING)  # stderr; stdout belongs to MCP.
api = LMSClient(os.environ.get("MARS_API_URL", DEFAULT_API_URL),
                timeout=float(os.environ.get("MARS_API_TIMEOUT_SECONDS", "20")))
mcp = MCPServer("mars-lms", instructions=(
    "MARS LMS access for Hermes AI employees. Call login once, then use the GET tools. "
    "The token lives only in this process. Login again after expiry or process restart. "
    "A forbidden response means the account's backend role cannot access that resource."
))
Query = dict[str, str | int | float | bool] | None


def result(payload: dict[str, Any]) -> CallToolResult:
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))],
                          structuredContent=payload, isError=not payload["success"])


@mcp.tool()
async def login(phone: str, password: str, role: str | None = None) -> CallToolResult:
    """POST /api/auth/login. Save the JWT in memory. Omit role for backend role detection."""
    return result(await api.login(phone, password, role))


@mcp.tool()
async def branch_me() -> CallToolResult:
    """GET /api/branch/me using the current in-memory login token."""
    return result(await api.get("/api/branch/me"))


@mcp.tool()
async def groups(query: Query = None) -> CallToolResult:
    """GET /api/branch/groups. Optional backend query filters, such as page or search."""
    return result(await api.get("/api/branch/groups", query))


@mcp.tool()
async def students(query: Query = None) -> CallToolResult:
    """GET /api/branch/students using the current account's backend permissions."""
    return result(await api.get("/api/branch/students", query))


@mcp.tool()
async def mentors(query: Query = None) -> CallToolResult:
    """GET /api/branch/mentors using the saved token."""
    return result(await api.get("/api/branch/mentors", query))


@mcp.tool()
async def payments(query: Query = None) -> CallToolResult:
    """GET /api/branch/payments with optional backend filters."""
    return result(await api.get("/api/branch/payments", query))


@mcp.tool()
async def finance_overview(query: Query = None) -> CallToolResult:
    """GET /api/finance/overview. The backend enforces finance access permissions."""
    return result(await api.get("/api/finance/overview", query))


@mcp.tool()
async def finance_salaries(query: Query = None) -> CallToolResult:
    """GET /api/finance/salaries. The backend enforces finance access permissions."""
    return result(await api.get("/api/finance/salaries", query))


if __name__ == "__main__":
    mcp.run(transport="stdio")
