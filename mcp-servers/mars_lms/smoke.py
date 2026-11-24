"""Exercise the actual stdio server; use --fixture for an offline HTTP backend."""

import argparse
import asyncio
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
import tempfile
import threading

from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from scoped_client import DEFAULT_API_URL
from scoped_settings import read_settings

ROOT = Path(__file__).resolve().parent
TOOL_PATHS = {
    "branch_me": "/api/branch/me", "groups": "/api/branch/groups",
    "students": "/students",
    "mentors": "/api/branch/mentors", "payments": "/api/branch/payments",
    "finance_overview": "/api/finance/overview", "finance_salaries": "/api/finance/salaries",
}


@asynccontextmanager
async def connected_client(params):
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            await client.initialize()
            yield client



@contextmanager
def fixture_backend():
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def reply(self, status, body):
            payload = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_POST(self):
            calls.append(("POST", self.path))
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            if self.path == "/api/auth/login" and body.get("phone") == "fixture" and body.get("password") == "fixture":
                self.reply(200, {"success": True, "token": "fixture-memory-token", "role": "admin"})
            else:
                self.reply(401, {"success": False, "message": "Invalid credentials"})

        def do_GET(self):
            calls.append(("GET", self.path))
            if self.headers.get("Authorization") != "Bearer fixture-memory-token":
                self.reply(401, {"success": False, "message": "Bearer token required"})
            elif self.path in TOOL_PATHS.values():
                self.reply(200, {"success": True, "message": "Fixture backend OK", "path": self.path,
                                 "students": [], "analytics": {"topics": []}})
            else:
                self.reply(404, {"success": False, "message": "Route not found"})

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


async def exercise(base_url, phone, password, role=None, tools=None, show=True):
    params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "server.py")],
                                   env={"MARS_API_URL": base_url}, cwd=tempfile.gettempdir())
    results = {}
    async with connected_client(params) as client:
        listed = await client.list_tools()
        expected = {"login", "students", "student_progress", "attendance", "homework", "curriculum", "incoming_requests", "reception_triage"}
        assert {tool.name for tool in listed.tools} >= expected, "Incorrect tool registration"
        if show:
            print(f"Discovered {len(listed.tools)} tools (SDK 1 stdio client)")
        args = {"phone": phone, "password": password}
        if role:
            args["role"] = role
        login = await client.call_tool("login", args)
        results["login"] = login.structuredContent
        if show:
            print(json.dumps({"tool": "login", **results["login"]}, ensure_ascii=False))
        if login.isError:
            return results
        for name in tools or ["students"]:
            reply = await client.call_tool(name, {})
            payload = reply.structuredContent
            results[name] = payload
            if show:
                # Prove the call without dumping real people, payments or salaries.
                print(json.dumps({"tool": name, "success": payload["success"],
                                  "status": payload["status"], "message": payload["message"]}, ensure_ascii=False))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--tool", choices=list(TOOL_PATHS), default="students")
    args = parser.parse_args()
    if args.fixture:
        with fixture_backend() as (base_url, calls):
            replies = asyncio.run(exercise(base_url, "fixture", "fixture", tools=list(TOOL_PATHS)))
            assert all(item["success"] for item in replies.values())
            assert calls == [("POST", "/api/auth/login"), *[("GET", url) for url in TOOL_PATHS.values()]]
            print("PASS: one POST login, seven authenticated GET calls through real stdio MCP (fixture data)")
    else:
        values = read_settings(args.env_file)
        if not values.get("MARS_PHONE") or not values.get("MARS_PASSWORD"):
            parser.error("Set MARS_PHONE and MARS_PASSWORD in the environment or --env-file")
        replies = asyncio.run(exercise(values.get("MARS_API_URL") or DEFAULT_API_URL,
                                        values["MARS_PHONE"], values["MARS_PASSWORD"],
                                        values.get("MARS_ROLE"), [args.tool]))
        if not all(item["success"] for item in replies.values()):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
