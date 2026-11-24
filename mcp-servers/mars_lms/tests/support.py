"""Test yordamchisi: haqiqiy stdio MCP serverga ulanadigan klient."""

from contextlib import asynccontextmanager

from mcp import ClientSession
from mcp.client.stdio import stdio_client


@asynccontextmanager
async def connected_client(params):
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            await client.initialize()
            yield client
