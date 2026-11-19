"""MARS LMS backend bilan ishlash uchun HTTP klient.

MCP server (`server.py`) barcha backend so'rovlarini shu klient orqali yuboradi:

- token va sessiya faqat xotirada saqlanadi (diskka yozilmaydi);
- 401 javobida bir marta avtomatik qayta login qilinadi;
- har bir xato agent tushunadigan va tuzatishi mumkin bo'lgan matn bilan qaytadi.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Optional

import httpx

logger = logging.getLogger("mars_lms.client")


def _load_local_dotenv() -> None:
    """Server papkasidagi `.env` faylini o'qiydi (mavjud muhit o'zgaruvchilari ustuvor).

    Hermes MCP serverni o'z jarayoni sifatida ishga tushiradi va config'dagi
    `${env:...}` havolalari har doim ham hal bo'lmaydi; shu sababli maxfiy
    ma'lumotlar server yonidagi `.env` faylda saqlanadi va shu yerda o'qiladi.
    """
    env_path = Path(__file__).with_name(".env")
    if not env_path.exists():
        return
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


_load_local_dotenv()

DEFAULT_TIMEOUT = float(os.environ.get("MARS_TIMEOUT", "30"))
DEFAULT_API_URL = os.environ.get("MARS_API_URL", "https://mars-backend-six.vercel.app")

ENDPOINTS = {
    "login": "/api/auth/login",
    "branch_me": "/api/branch/me",
    "groups": "/api/branch/groups",
    "students": "/api/branch/students",
    "student": "/api/branch/students/{id}",
    "student_payments": "/api/branch/students/{id}/payments",
    "debtors": "/api/branch/debtors",
    "attendance": "/api/branch/attendance",
    "overview": "/api/branch/overview",
    "payments": "/api/branch/payments",
    "expenses": "/api/branch/expenses",
    "mentors": "/api/branch/mentors",
    "status_requests": "/api/branch/status-requests",
    "waitlist": "/api/branch/waitlist",
    "inactive_students": "/api/branch/inactive-students",
    "attendance_risks": "/api/branch/attendance-risks",
    "workload": "/api/branch/workload-planning",
    "reports_groups": "/api/branch/reports/groups",
    "homework": "/homework",
    "finance_overview": "/api/finance/overview",
    "finance_payments": "/api/finance/payments",
}

_ERROR_HINTS = {
    400: "So'rov parametrlari noto'g'ri. Xabar matniga qarab parametrni to'g'rilang va qayta urinib ko'ring.",
    401: "Avtorizatsiya xatosi: token yo'q yoki muddati tugagan. `lms_login` toolini chaqiring; "
         "MARS_PHONE/MARS_PASSWORD to'g'riligini tekshiring.",
    403: "Ruxsat yo'q: bu amal uchun akkaunt roli yetarli emas. Filial administratori (admin) "
         "yoki owner akkaunti bilan urinib ko'ring.",
    404: "Resurs topilmadi: ID yoki sana/oy formati noto'g'ri bo'lishi mumkin. Haqiqiy ID ni "
         "`list_groups` yoki `list_students` orqali oling.",
    409: "Ma'lumot allaqachon mavjud yoki holat to'qnashdi. Ro'yxatni yangilab qayta urinib ko'ring.",
    429: "So'rovlar chegarasi (rate limit). Bir necha soniyadan keyin qayta urinib ko'ring.",
}
_SERVER_HINTS = {
    500: "Backend ichki xatosi. Bir necha daqiqadan keyin qayta urinib ko'ring.",
    502: "Backend vaqtincha javob bermadi (gateway). Qayta urinib ko'ring.",
    503: "Backend xizmati vaqtincha ishlamayapti (ma'lumotlar bazasi ulanishi). Keyinroq urinib ko'ring.",
    504: "Backend javobi kechikdi. `from`/`to` oralig'ini kichraytirib qayta urinib ko'ring.",
}


def envelope(
    error: Optional[str] = None,
    status_code: int = 200,
    message: str = "success",
    endpoint: str = "",
    details: Any = None,
) -> dict:
    """Yagona javob konverti: har bir tool shu shaklda qaytadi."""
    return {
        "error": error,
        "status_code": status_code,
        "message": message,
        "endpoint": endpoint,
        "details": details,
    }


class LMSError(RuntimeError):
    """Backend yoki tarmoq xatosi; `as_envelope()` orqali agentga qaytariladi."""

    def __init__(self, message: str, status_code: int = 0, endpoint: str = "", details: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.endpoint = endpoint
        self.details = details

    def as_envelope(self) -> dict:
        return envelope(
            error=str(self),
            status_code=self.status_code,
            message=str(self),
            endpoint=self.endpoint,
            details=self.details,
        )


def explain_http_error(status: int, endpoint: str, payload: Any) -> str:
    """HTTP holatidan agent uchun harakatga undovchi xabar yasaydi."""
    server_message = ""
    if isinstance(payload, dict):
        server_message = str(payload.get("message") or payload.get("error") or "").strip()
    hint = _ERROR_HINTS.get(status) or _SERVER_HINTS.get(status) or (
        "Backend kutilmagan javob qaytardi. Endpoint va parametrlarni tekshirib qayta urinib ko'ring."
    )
    parts = [f"HTTP {status} — {endpoint}."]
    if server_message:
        parts.append(f"Backend xabari: {server_message}.")
    parts.append(hint)
    return " ".join(parts)


class LMSClient:
    """MARS LMS REST API uchun yupqa klient (sessiya xotirada)."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        phone: Optional[str] = None,
        password: Optional[str] = None,
        role: Optional[str] = None,
        timeout: Optional[float] = None,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.base_url = (base_url or DEFAULT_API_URL).rstrip("/")
        self.phone = phone if phone is not None else os.environ.get("MARS_PHONE", "")
        self.password = password if password is not None else os.environ.get("MARS_PASSWORD", "")
        self.role = role if role is not None else os.environ.get("MARS_ROLE", "admin")
        self.timeout = timeout or DEFAULT_TIMEOUT
        self._transport = transport
        self.token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user: Optional[dict] = None
        self.branch: Optional[dict] = None
        self.authenticated_role: Optional[str] = None

    # --- sessiya -----------------------------------------------------------
    @property
    def is_authenticated(self) -> bool:
        return bool(self.token)

    def session_summary(self) -> dict:
        return {
            "authenticated": self.is_authenticated,
            "role": self.authenticated_role or self.role,
            "user": (self.user or {}).get("fullname") or None,
            "branch": (self.branch or {}).get("name") or None,
            "branch_id": (self.branch or {}).get("_id") or (self.user or {}).get("branch"),
            "base_url": self.base_url,
        }

    def _client(self) -> httpx.Client:
        kwargs: dict = {"timeout": self.timeout, "follow_redirects": True}
        if self._transport is not None:
            kwargs["transport"] = self._transport
        return httpx.Client(**kwargs)

    def login(self, force: bool = False) -> dict:
        """Backendga login qiladi va tokenni xotirada saqlaydi."""
        if self.token and not force:
            return self.session_summary()
        if not self.phone or not self.password:
            raise LMSError(
                "Login ma'lumotlari yo'q: MARS_PHONE va MARS_PASSWORD muhit o'zgaruvchilarini "
                "o'rnating yoki `lms_login` tooliga phone/password bering.",
                endpoint=ENDPOINTS["login"],
            )
        body = {"identifier": self.phone, "password": self.password}
        if self.role:
            body["role"] = self.role
        status, payload = self._raw("POST", ENDPOINTS["login"], body=body)
        if status >= 400:
            raise LMSError(
                explain_http_error(status, ENDPOINTS["login"], payload),
                status_code=status,
                endpoint=ENDPOINTS["login"],
                details=payload,
            )
        self.token = payload.get("accessToken") or payload.get("token")
        self.refresh_token = payload.get("refreshToken")
        self.authenticated_role = payload.get("role") or self.role
        self.user = payload.get("user") or payload.get("admin") or {}
        self.branch = payload.get("branch") or {}
        if not self.token:
            raise LMSError(
                "Login javobida token topilmadi. Backend javobini tekshiring.",
                status_code=status,
                endpoint=ENDPOINTS["login"],
                details=payload,
            )
        if not self.branch:
            self._load_branch_context()
        logger.info("MARS LMS login OK (role=%s)", self.authenticated_role)
        return self.session_summary()

    def _load_branch_context(self) -> None:
        try:
            status, payload = self._raw("GET", ENDPOINTS["branch_me"], token=self.token)
        except LMSError:
            return
        if status < 400 and isinstance(payload, dict):
            self.branch = payload.get("branch") or {}
            self.user = payload.get("admin") or self.user

    def _raw(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        body: Optional[dict] = None,
        token: Optional[str] = None,
    ) -> tuple[int, Any]:
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        url = self.base_url + endpoint
        try:
            with self._client() as client:
                response = client.request(method, url, params=params, json=body, headers=headers)
        except httpx.TimeoutException:
            raise LMSError(
                f"Backend {self.timeout:g} soniyada javob bermadi ({endpoint}). "
                "Keyinroq qayta urinib ko'ring yoki MARS_TIMEOUT ni oshiring.",
                status_code=504,
                endpoint=endpoint,
            )
        except httpx.HTTPError as exc:
            raise LMSError(
                f"Backend bilan aloqa yo'q ({endpoint}): {type(exc).__name__}. "
                "Internet va MARS_API_URL ni tekshiring.",
                status_code=502,
                endpoint=endpoint,
            )
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text[:500]}
        return response.status_code, payload

    def fetch(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        method: str = "GET",
        body: Optional[dict] = None,
    ) -> dict:
        """So'rov yuboradi; xatoda LMSError, muvaffaqiyatda backend payload'ini qaytaradi."""
        if not self.token:
            self.login()
        status, payload = self._raw(method, endpoint, params=params, body=body, token=self.token)
        if status == 401:
            logger.info("401 javobi, bir marta qayta login qilinadi")
            self.login(force=True)
            status, payload = self._raw(method, endpoint, params=params, body=body, token=self.token)
        if status >= 400:
            raise LMSError(
                explain_http_error(status, endpoint, payload),
                status_code=status,
                endpoint=endpoint,
                details=payload,
            )
        if not isinstance(payload, dict):
            payload = {"data": payload}
        return payload

    def get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        return self.fetch(endpoint, params=params)


def make_client(**kwargs: Any) -> LMSClient:
    return LMSClient(**kwargs)
