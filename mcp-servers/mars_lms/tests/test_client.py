import sys
from pathlib import Path
import unittest

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scoped_client import LMSClient
from smoke import TOOL_PATHS, exercise, fixture_backend
from mcp import StdioServerParameters
from smoke import connected_client


class HTTPTests(unittest.IsolatedAsyncioTestCase):
    async def test_login_then_reuse_bearer_without_role(self):
        requests = []

        def respond(request):
            requests.append(request)
            if request.method == "POST":
                self.assertNotIn(b'"role"', request.content)
                self.assertNotIn("Authorization", request.headers)
                return httpx.Response(200, json={"token": "test-token", "role": "admin"})
            self.assertEqual(request.headers["Authorization"], "Bearer test-token")
            return httpx.Response(200, json={"success": True, "items": []})

        api = LMSClient(transport=httpx.MockTransport(respond))
        self.assertTrue((await api.login("fixture", "password"))["success"])
        self.assertTrue((await api.get("/api/branch/groups", {"page": 2}))["success"])
        self.assertTrue((await api.get("/api/branch/students"))["success"])
        self.assertEqual([r.method for r in requests], ["POST", "GET", "GET"])
        self.assertEqual(requests[1].url.params["page"], "2")

    async def test_missing_login_does_not_call_network(self):
        def unexpected(_request):
            self.fail("Unauthenticated request reached the network")
        result = await LMSClient(transport=httpx.MockTransport(unexpected)).get("/api/branch/me")
        self.assertEqual(result["status"], 401)
        self.assertEqual(result["source"], "mcp")

    async def test_expired_token_cleared_and_backend_status_preserved(self):
        api = LMSClient(transport=httpx.MockTransport(lambda _: httpx.Response(401, json={"message": "Expired"})))
        api.token = "expired"
        result = await api.get("/api/branch/me")
        self.assertEqual((result["status"], result["message"]), (401, "Expired"))
        self.assertIsNone(api.token)

    async def test_failed_account_switch_clears_previous_login(self):
        api = LMSClient(transport=httpx.MockTransport(lambda _: httpx.Response(401, json={"message": "Bad password"})))
        api.token = "previous-account"
        result = await api.login("fixture", "wrong", "admin")
        self.assertFalse(result["success"])
        self.assertIsNone(api.token)

    async def test_login_without_token_is_not_success(self):
        api = LMSClient(transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"success": True})))
        result = await api.login("fixture", "password")
        self.assertFalse(result["success"])
        self.assertEqual(result["status"], 200)
        self.assertIn("token", result["message"])

    async def test_http_errors_and_non_json_are_visible(self):
        for status in (403, 404, 429, 500):
            api = LMSClient(transport=httpx.MockTransport(lambda _, s=status: httpx.Response(s, json={"message": "Backend says no"})))
            api.token = "token"
            result = await api.get("/api/branch/groups")
            self.assertEqual((result["status"], result["message"]), (status, "Backend says no"))
            self.assertFalse(result["success"])
        api = LMSClient(transport=httpx.MockTransport(lambda _: httpx.Response(502, text="Deployment unavailable")))
        api.token = "token"
        self.assertEqual((await api.get("/api/branch/me"))["message"], "Deployment unavailable")

    async def test_timeout_reports_no_invented_http_status(self):
        def timeout(request):
            raise httpx.ReadTimeout("Timeout", request=request)
        api = LMSClient(transport=httpx.MockTransport(timeout))
        api.token = "token"
        result = await api.get("/api/branch/me")
        self.assertIsNone(result["status"])
        self.assertEqual(result["source"], "network")
        self.assertIn("timed out", result["message"])

    async def test_stdio_scoped_reads_on_unified_sdk(self):
        with fixture_backend() as (url, calls):
            replies = await exercise(url, "fixture", "fixture", tools=list(TOOL_PATHS), show=False)
            self.assertTrue(all(reply["success"] for reply in replies.values()))
            self.assertEqual(len(calls), 8)
            self.assertEqual(calls[0], ("POST", "/api/auth/login"))
            self.assertEqual(calls[1:], [("GET", path) for path in TOOL_PATHS.values()])

    async def test_stdio_errors_are_marked_and_failed_switch_drops_token(self):
        server = Path(__file__).resolve().parents[1] / "server.py"
        with fixture_backend() as (url, calls):
            params = StdioServerParameters(command=sys.executable, args=[str(server)], env={"MARS_API_URL": url})
            async with connected_client(params) as client:
                missing = await client.call_tool("students", {})
                self.assertTrue(missing.isError)
                self.assertEqual(missing.structuredContent["status"], 401)
                self.assertEqual(calls, [])
                valid = await client.call_tool("login", {"phone": "fixture", "password": "fixture"})
                self.assertFalse(valid.isError)
                invalid = await client.call_tool("login", {"phone": "fixture", "password": "wrong"})
                self.assertTrue(invalid.isError)
                self.assertEqual(invalid.structuredContent["status"], 401)
                denied = await client.call_tool("students", {})
                self.assertTrue(denied.isError)
                self.assertEqual(denied.structuredContent["source"], "mcp")
                self.assertEqual([method for method, _ in calls], ["POST", "POST"])


if __name__ == "__main__":
    unittest.main()
