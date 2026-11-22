"""Small HTTP adapter. Authentication belongs to this process, not a file."""

import asyncio
from typing import Any

import httpx

DEFAULT_API_URL = "https://mars-backend-six.vercel.app"


class LMSClient:
    def __init__(self, base_url: str = DEFAULT_API_URL, timeout: float = 20,
                 transport: httpx.AsyncBaseTransport | None = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.transport = transport
        self.token: str | None = None
        self._lock = asyncio.Lock()

    @staticmethod
    def error(status: int | None, message: str, source: str = "mcp") -> dict[str, Any]:
        return {"success": False, "status": status, "message": message, "source": source}

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport,
                                         follow_redirects=False) as client:
                response = await client.request(method, self.base_url + path,
                                                headers=headers, **kwargs)
        except httpx.TimeoutException:
            return self.error(None, f"Backend request timed out after {self.timeout:g}s", "network")
        except httpx.RequestError as exc:
            return self.error(None, f"{type(exc).__name__}: {exc}", "network")

        if response.status_code == 401:
            self.token = None
        try:
            body = response.json() if response.content else None
        except ValueError:
            return self.error(response.status_code,
                              response.text[:1000] or "Backend returned a non-JSON response", "backend")
        success = response.is_success and not (isinstance(body, dict) and body.get("success") is False)
        message = body.get("message") if isinstance(body, dict) else None
        if not message:
            message = "OK" if success else (response.reason_phrase or "Backend request failed")
        return {"success": success, "status": response.status_code, "message": str(message),
                "source": "backend", "data": body}

    async def login(self, phone: str, password: str, role: str | None = None) -> dict[str, Any]:
        async with self._lock:
            # A failed account switch must not leave the previous user's token active.
            self.token = None
            if not phone.strip() or not password:
                return self.error(400, "phone and password are required")
            payload = {"phone": phone.strip(), "password": password}
            if role and role.strip():
                payload["role"] = role.strip()
            result = await self._request("POST", "/api/auth/login", json=payload)
            body = result.get("data")
            if not result["success"]:
                # Do not return a login response containing incidental auth fields.
                return {key: value for key, value in result.items() if key != "data"}
            token = body.get("token") if isinstance(body, dict) else None
            if not isinstance(token, str) or not token.strip():
                return self.error(result["status"], "Login response did not contain a token", "backend")
            self.token = token
            return {"success": True, "status": result["status"], "message": "Logged in; token stored in memory",
                    "source": "backend", "role": body.get("role", role)}

    async def get(self, path: str, query: dict[str, Any] | None = None) -> dict[str, Any]:
        async with self._lock:
            if not self.token:
                return self.error(401, "Login required. Call login(phone, password, role) first.")
            return await self._request("GET", path, params=query)
