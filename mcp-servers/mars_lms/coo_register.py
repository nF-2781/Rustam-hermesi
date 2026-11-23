"""COO tool'lari uchun alohida, aniq login qiladigan read-only MCP klienti.

Asosiy 22 tool o'z `CLIENT` sessiyasida ishlaydi; COO auditlari esa shu modulning
o'z `LMSClient` nusxasida ishlaydi. Shu sabab COO tool'laridan oldin `coo_login`
chaqiriladi — token faqat xotirada turadi va hech qachon qaytarilmaydi.
"""

import json
import os
from pathlib import Path

from mcp.types import CallToolResult, TextContent

from coo_tools import register_coo_tools
from scoped_client import DEFAULT_API_URL, LMSClient
from scoped_settings import read_settings


def _result(payload):
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))],
        structuredContent=payload,
        isError=not payload["success"],
    )


def register_coo(mcp):
    api = LMSClient(
        os.environ.get("MARS_API_URL", DEFAULT_API_URL),
        timeout=float(os.environ.get("MARS_API_TIMEOUT_SECONDS", "20")),
    )

    @mcp.tool()
    async def coo_login(phone: str = "", password: str = "", role: str = ""):
        """Authenticate the COO read-only session. Pass both phone and password, or neither to use the server's private .env account. Never returns credentials or the token."""
        if bool(phone) != bool(password):
            return _result(LMSClient.error(400, "Pass both phone and password, or neither"))
        if not phone:
            settings = read_settings(Path(__file__).with_name(".env"))
            phone, password = settings.get("MARS_PHONE", ""), settings.get("MARS_PASSWORD", "")
            role = role or settings.get("MARS_ROLE", "")
        return _result(await api.login(phone, password, role or None))

    register_coo_tools(mcp, api, _result)
