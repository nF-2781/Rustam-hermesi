"""MARS LMS — moliya domeni uchun MCP server (stdio).

`digital-org/mcp/servers.json` dagi `mcp-mars-finance` ning ishlaydigan ko'rinishi.
Bitta katta `mars_lms` serveridan farqi: bu yerda **faqat** moliya endpointlari bor
(13 tool), har yozuvchi tool `digital-org/security/security_sandbox.py` dan o'tadi,
CEO uchun server **read-only**.

Qoidalar (majburiy):
- `stdout` faqat JSON-RPC uchun; loglar `stderr` ga.
- Token xotirada (umumiy `lms_client.LMSClient`), diskka yozilmaydi.
- Har javob yagona konvertda: error/status_code/message/endpoint/details.
- `POST /api/payments` (eski) bu serverda umuman yo'q — guardrail ham bloklaydi.

Ishga tushirish (Hermes `config.yaml`):

    command: C:/…/mcp-servers/mars_lms/.venv/Scripts/python.exe
    args:    ["C:/…/mcp-servers/mars_finance/server.py"]
"""

from __future__ import annotations

import functools
import logging
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Optional

_SERVERS_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = _SERVERS_DIR.parent
# Umumiy HTTP klient va endpointlar bitta joyda qoladi (migratsiya qoidasi).
sys.path.insert(0, str(_SERVERS_DIR / "mars_lms"))
sys.path.insert(0, str(_REPO_ROOT / "digital-org" / "security"))

from mcp.server.fastmcp import FastMCP  # noqa: E402

from lms_client import LMSClient, LMSError, envelope  # noqa: E402
from security_sandbox import Decision, check  # noqa: E402

logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("mars_finance.server")

CLIENT = LMSClient()

ALLOWED_AGENTS = {"finance-payroll", "ceo-strategist"}
READ_ONLY_AGENTS = {"ceo-strategist"}

mcp = FastMCP(
    "mars-finance",
    instructions=(
        "MARS LMS moliya domeni: kassa, to'lovlar, xarajatlar, qarzdorlik va oylik. "
        "Avval `finance_login`. Yozuvchi tool'lar (`create_*`, `update_*`, `void_*`, "
        "`set_salary_status`) inson tasdig'ini talab qilishi mumkin: 428 javobi — "
        "amal bajarilmadi, tasdiq so'ralishi kerak; 403 — guardrail blokladi. "
        "Har hisobotda `month` (YYYY-MM) ko'rsatiladi."
    ),
)

# ---------------------------------------------------------------------------
# Yordamchilar
# ---------------------------------------------------------------------------


def tool_guard(func):
    """Kutilmagan xatoni ham yagona konvertga aylantiradi."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except LMSError as exc:
            return exc.as_envelope()
        except ValueError as exc:
            return envelope(error=str(exc), status_code=400, message=str(exc), endpoint="local")
        except Exception as exc:  # noqa: BLE001 - agentga aniq xabar muhim
            logger.exception("tool xatosi: %s", func.__name__)
            return envelope(
                error=f"Kutilmagan server xatosi: {type(exc).__name__}: {exc}",
                status_code=500,
                message="Tool ichida kutilmagan xato. Parametrlarni tekshirib qayta urinib ko'ring.",
                endpoint="local",
            )

    return wrapper


def _month_or_default(month: Optional[str]) -> str:
    from datetime import date

    if not month:
        return date.today().strftime("%Y-%m")
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", str(month)):
        raise ValueError("`month` YYYY-MM formatida bo'lishi kerak (masalan 2026-11).")
    return str(month)


def _actor_branch() -> str:
    return str((CLIENT.branch or {}).get("_id") or (CLIENT.user or {}).get("branch") or "")


def _guard(
    agent: str,
    method: str,
    path: str,
    args: Optional[Mapping[str, Any]] = None,
    *,
    branch_id: Optional[str] = None,
    write: bool = False,
) -> Decision:
    """RBAC → ABAC → hard guardrail. Tarmoqqa chiqmaydi."""
    payload = dict(args or {})
    if agent not in ALLOWED_AGENTS:
        return Decision(
            allowed=False,
            rule="RBAC_AGENT",
            reason=f"`{agent}` mcp-mars-finance ga ulanmagan (rbac_matrix.json → mcp_servers)",
            sanitized_args=payload,
        )
    if write and agent in READ_ONLY_AGENTS:
        return Decision(
            allowed=False,
            rule="RBAC_READ_ONLY",
            reason=f"`{agent}` bu serverda faqat o'qiydi; yozuv finance-payroll ishi",
            sanitized_args=payload,
        )
    actor_branch = _actor_branch()
    if branch_id and actor_branch and str(branch_id) != actor_branch:
        return Decision(
            allowed=False,
            rule="ABAC_BRANCH",
            reason=f"agent filiali {actor_branch} ≠ so'ralgan filial {branch_id}",
            sanitized_args=payload,
        )
    return check(
        agent,
        method,
        path,
        payload,
        actor_branch=actor_branch or None,
        resource_branch=str(branch_id) if branch_id else None,
    )


def _blocked(decision: Decision, endpoint: str) -> dict:
    if decision.requires_approval:
        return envelope(
            error=f"HUMAN_APPROVAL: {decision.reason}",
            status_code=428,
            message=(
                "Amal bajarilmadi: inson tasdig'i kerak. Agent faqat taklif/hisobot beradi; "
                "tasdiqlangandan keyin amal qayta chaqiriladi."
            ),
            endpoint=endpoint,
            details={"guardrail": decision.as_dict(), "requires_approval": True},
        )
    return envelope(
        error=f"{decision.rule}: {decision.reason}",
        status_code=403,
        message="Amal guardrail tomonidan bloklandi.",
        endpoint=endpoint,
        details={"guardrail": decision.as_dict(), "requires_approval": False},
    )


def _run(
    agent: str,
    method: str,
    path: str,
    *,
    endpoint: Optional[str] = None,
    params: Optional[dict] = None,
    body: Optional[dict] = None,
    branch_id: Optional[str] = None,
    args: Optional[Mapping[str, Any]] = None,
    write: bool = False,
    message: str = "success",
) -> dict:
    decision = _guard(agent, method, path, args, branch_id=branch_id, write=write)
    if not decision.allowed:
        return _blocked(decision, endpoint or path)
    payload = CLIENT.fetch(endpoint or path, params=params, method=method, body=body)
    return envelope(message=message, endpoint=endpoint or path, details=payload)


def _require(value: Any, name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"`{name}` majburiy.")
    return text


def _positive(value: Any, name: str = "amount") -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"`{name}` son bo'lishi kerak.")
    if number <= 0:
        raise ValueError(f"`{name}` 0 dan katta bo'lishi kerak.")
    return number


# ---------------------------------------------------------------------------
# Sessiya
# ---------------------------------------------------------------------------


@mcp.tool()
@tool_guard
def finance_login(phone: str = "", password: str = "", role: str = "", force: bool = False) -> dict:
    """Moliya serveri uchun sessiya ochadi (token xotirada qoladi).

    Args:
        phone: Telefon (bo'sh bo'lsa MARS_PHONE).
        password: Parol (bo'sh bo'lsa MARS_PASSWORD; chatga yozilmaydi).
        role: Akkaunt roli (admin, bm, owner…).
        force: True bo'lsa mavjud sessiya tashlanadi.
    """
    if phone:
        CLIENT.phone = phone
    if password:
        CLIENT.password = password
    if role:
        CLIENT.role = role
    if force:
        CLIENT.token = None
    summary = CLIENT.login(force=force)
    return envelope(
        message=f"Sessiya tayyor: {summary.get('user') or summary.get('role')}",
        endpoint="/api/auth/login",
        details=summary,
    )


# ---------------------------------------------------------------------------
# O'qish tool'lari (finance-payroll + ceo-strategist)
# ---------------------------------------------------------------------------


@mcp.tool()
@tool_guard
def finance_overview(agent: str = "finance-payroll", month: str = "", branch_id: str = "") -> dict:
    """Filial moliyasi va tizim moliyasi umumiy ko'rsatkichlari.

    Args:
        agent: `finance-payroll` yoki `ceo-strategist` (CEO — faqat o'qish).
        month: Oy `YYYY-MM`; bo'sh bo'lsa joriy oy.
        branch_id: Boshqa filialni so'rash — ABAC bloklaydi.
    """
    month_value = _month_or_default(month or None)
    decision = _guard(agent, "GET", "/api/branch/overview", {"month": month_value}, branch_id=branch_id or None)
    if not decision.allowed:
        return _blocked(decision, "/api/branch/overview")
    branch = CLIENT.get("/api/branch/overview", {"month": month_value}).get("overview") or {}
    treasury = CLIENT.get("/api/finance/overview").get("overview") or {}
    balance = float(branch.get("income") or 0) - float(branch.get("expense") or 0)
    return envelope(
        message=f"Moliya ko'rsatkichlari: {month_value}",
        endpoint="/api/branch/overview",
        details={"month": month_value, "branch": branch, "treasury": treasury, "balance": balance},
    )


@mcp.tool()
@tool_guard
def list_payments(
    agent: str = "finance-payroll",
    page: int = 1,
    limit: int = 20,
    month: str = "",
    branch_id: str = "",
) -> dict:
    """To'lovlar ro'yxati (o'quvchi, summa, usul, holat, sana).

    Args:
        agent: Ruxsatli agent nomi.
        page: Sahifa (1 dan).
        limit: Sahifadagi yozuvlar (1-100).
        month: Oy `YYYY-MM` filtri.
        branch_id: Filial tekshiruvi (ABAC).
    """
    params: dict = {"page": max(1, int(page)), "limit": max(1, min(int(limit), 100))}
    if month:
        params["month"] = _month_or_default(month)
    return _run(
        agent,
        "GET",
        "/api/branch/payments",
        params=params,
        branch_id=branch_id or None,
        message="To'lovlar ro'yxati",
    )


@mcp.tool()
@tool_guard
def list_expenses(agent: str = "finance-payroll", month: str = "", limit: int = 50, branch_id: str = "") -> dict:
    """Filial xarajatlari ro'yxati.

    Args:
        agent: Ruxsatli agent nomi.
        month: Oy `YYYY-MM`.
        limit: Maksimal yozuvlar (1-100).
        branch_id: Filial tekshiruvi (ABAC).
    """
    params: dict = {"page": 1, "limit": max(1, min(int(limit), 100))}
    if month:
        params["month"] = _month_or_default(month)
    return _run(
        agent,
        "GET",
        "/api/branch/expenses",
        params=params,
        branch_id=branch_id or None,
        message="Xarajatlar ro'yxati",
    )


@mcp.tool()
@tool_guard
def list_debtors(
    agent: str = "finance-payroll",
    month: str = "",
    status: str = "",
    search: str = "",
    limit: int = 50,
    branch_id: str = "",
) -> dict:
    """Qarzdorlar: summa, kechikish kunlari, guruh.

    Args:
        agent: Ruxsatli agent nomi.
        month: Oy `YYYY-MM` (majburiy — davrsiz hisobot yo'q).
        status: `overdue` yoki `unpaid`.
        search: Ism/telefon/guruh filtri.
        limit: Maksimal yozuvlar.
        branch_id: Filial tekshiruvi (ABAC).
    """
    params: dict = {"month": _month_or_default(month or None), "limit": max(1, min(int(limit), 100))}
    if status:
        params["status"] = status
    if search:
        params["search"] = search
    return _run(
        agent,
        "GET",
        "/api/branch/debtors",
        params=params,
        branch_id=branch_id or None,
        message="Qarzdorlar ro'yxati",
    )


@mcp.tool()
@tool_guard
def list_salaries(agent: str = "finance-payroll", month: str = "", branch_id: str = "") -> dict:
    """Oylik loyihalari ro'yxati (holat: draft / review / paid).

    Args:
        agent: Ruxsatli agent nomi.
        month: Oy `YYYY-MM`.
        branch_id: Filial tekshiruvi (ABAC).
    """
    params = {"month": _month_or_default(month or None)}
    return _run(
        agent,
        "GET",
        "/api/finance/salaries",
        params=params,
        branch_id=branch_id or None,
        message="Oylik ro'yxati",
    )


@mcp.tool()
@tool_guard
def mentor_earnings(agent: str = "ceo-strategist", period: str = "", branch_id: str = "") -> dict:
    """Mentor daromadlari (owner ko'rinishi) — oylik hisoblash uchun manba.

    Args:
        agent: `ceo-strategist` (standart) yoki `finance-payroll`.
        period: Davr `YYYY-MM`; bo'sh bo'lsa joriy oy.
        branch_id: Filial tekshiruvi (ABAC).
    """
    params = {"period": _month_or_default(period or None)}
    return _run(
        agent,
        "GET",
        "/api/finance/owner/mentor-earnings",
        params=params,
        branch_id=branch_id or None,
        message="Mentor daromadlari",
    )


# ---------------------------------------------------------------------------
# Yozuvchi tool'lar (faqat finance-payroll; guardrail majburiy)
# ---------------------------------------------------------------------------


@mcp.tool()
@tool_guard
def create_payment(
    student_id: str = "",
    amount: float = 0,
    method: str = "cash",
    month: str = "",
    reason: str = "",
    agent: str = "finance-payroll",
    branch_id: str = "",
) -> dict:
    """To'lovni qabul qilish (`POST /api/branch/payments`).

    Pul yozuvi: `amount` 0 dan katta, `student_id` majburiy. `reason` ixtiyoriy,
    lekin keyingi tuzatishlar uchun yozib qo'yish tavsiya etiladi.

    Args:
        student_id: O'quvchi ID.
        amount: Summa (UZS).
        method: `cash`, `card`, `transfer`…
        month: Qaysi oy uchun `YYYY-MM`.
        reason: Izoh (kassa izohi).
        agent: `finance-payroll` (CEO yozmaydi).
        branch_id: Filial (ABAC).
    """
    amount_value = _positive(amount)
    body = {
        "student": _require(student_id, "student_id"),
        "amount": amount_value,
        "method": method or "cash",
        "month": _month_or_default(month or None),
    }
    if reason:
        body["reason"] = reason
    return _run(
        agent,
        "POST",
        "/api/branch/payments",
        endpoint="/api/branch/payments",
        body=body,
        args={"amount": amount_value, "reason": reason},
        branch_id=branch_id or None,
        write=True,
        message="To'lov qabul qilindi",
    )


@mcp.tool()
@tool_guard
def update_payment(
    payment_id: str = "",
    status: str = "",
    amount: float = 0,
    reason: str = "",
    agent: str = "finance-payroll",
    branch_id: str = "",
) -> dict:
    """To'lovni tuzatish (`PATCH /api/branch/payments/{id}`) — `reason` majburiy.

    Args:
        payment_id: To'lov ID.
        status: Yangi holat (ixtiyoriy).
        amount: Yangi summa (ixtiyoriy, 0 = o'zgartirilmaydi).
        reason: Tuzatish sababi — bo'sh bo'lsa guardrail bloklaydi.
        agent: `finance-payroll`.
        branch_id: Filial (ABAC).
    """
    payment = _require(payment_id, "payment_id")
    body: dict = {}
    if status:
        body["status"] = status
    if amount:
        body["amount"] = _positive(amount)
    if not body:
        raise ValueError("O'zgartirish uchun kamida `status` yoki `amount` bering.")
    body["reason"] = reason
    return _run(
        agent,
        "PATCH",
        f"/api/branch/payments/{payment}",
        body=body,
        args={"reason": reason, "status": status, "amount": amount},
        branch_id=branch_id or None,
        write=True,
        message="To'lov tuzatildi",
    )


@mcp.tool()
@tool_guard
def void_payment(
    payment_id: str = "",
    reason: str = "",
    agent: str = "finance-payroll",
    branch_id: str = "",
) -> dict:
    """To'lovni bekor qilish (`POST /api/branch/payments/{id}/void`).

    Qaytarilmas amal: har doim inson tasdig'i (`HUMAN_APPROVAL`, 428) va `reason`.
    Sababsiz chaqiruv `REASON_REQUIRED` bilan bloklanadi.

    Args:
        payment_id: To'lov ID.
        reason: Bekor qilish sababi (majburiy).
        agent: `finance-payroll`.
        branch_id: Filial (ABAC).
    """
    payment = _require(payment_id, "payment_id")
    return _run(
        agent,
        "POST",
        f"/api/branch/payments/{payment}/void",
        body={"reason": reason},
        args={"reason": reason},
        branch_id=branch_id or None,
        write=True,
        message="To'lov bekor qilindi",
    )


@mcp.tool()
@tool_guard
def create_expense(
    amount: float = 0,
    category: str = "",
    description: str = "",
    month: str = "",
    agent: str = "finance-payroll",
    branch_id: str = "",
) -> dict:
    """Xarajat kiritish (`POST /api/branch/expenses`).

    1 000 000 UZS dan yuqori xarajat `HUMAN_APPROVAL` (428) bilan to'xtaydi.

    Args:
        amount: Summa (UZS).
        category: Toifa (`arenda`, `oylik`, `marketing`…).
        description: Izoh.
        month: Oy `YYYY-MM`.
        agent: `finance-payroll`.
        branch_id: Filial (ABAC).
    """
    amount_value = _positive(amount)
    body = {
        "amount": amount_value,
        "category": _require(category, "category"),
        "month": _month_or_default(month or None),
    }
    if description:
        body["description"] = description
    return _run(
        agent,
        "POST",
        "/api/branch/expenses",
        body=body,
        args={"amount": amount_value, "description": description},
        branch_id=branch_id or None,
        write=True,
        message="Xarajat kiritildi",
    )


@mcp.tool()
@tool_guard
def create_salary_draft(
    mentor_id: str = "",
    month: str = "",
    amount: float = 0,
    agent: str = "finance-payroll",
    branch_id: str = "",
) -> dict:
    """Oylik loyihasini yaratish (`POST /api/finance/salaries`).

    Har doim `HUMAN_APPROVAL` (428): agent loyiha tayyorlaydi, odam 2FA bilan tasdiqlaydi.

    Args:
        mentor_id: Mentor ID.
        month: Oy `YYYY-MM`.
        amount: Hisoblangan summa.
        agent: `finance-payroll`.
        branch_id: Filial (ABAC).
    """
    amount_value = _positive(amount)
    body = {"mentor": _require(mentor_id, "mentor_id"), "month": _month_or_default(month or None), "amount": amount_value}
    return _run(
        agent,
        "POST",
        "/api/finance/salaries",
        body=body,
        args={"amount": amount_value},
        branch_id=branch_id or None,
        write=True,
        message="Oylik loyihasi yaratildi",
    )


@mcp.tool()
@tool_guard
def set_salary_status(
    salary_id: str = "",
    status: str = "draft",
    agent: str = "finance-payroll",
    branch_id: str = "",
) -> dict:
    """Oylik holatini o'zgartirish (`PATCH /api/finance/salaries/{id}/status`).

    `draft` / `review` — ruxsat; `paid` — faqat inson tasdig'i bilan (428).

    Args:
        salary_id: Oylik yozuvi ID.
        status: `draft`, `review` yoki `paid`.
        agent: `finance-payroll`.
        branch_id: Filial (ABAC).
    """
    salary = _require(salary_id, "salary_id")
    status_value = _require(status, "status").lower()
    if status_value not in {"draft", "review", "paid"}:
        raise ValueError("`status` faqat draft, review yoki paid bo'lishi mumkin.")
    return _run(
        agent,
        "PATCH",
        f"/api/finance/salaries/{salary}/status",
        body={"status": status_value},
        args={"status": status_value},
        branch_id=branch_id or None,
        write=True,
        message=f"Oylik holati: {status_value}",
    )


if __name__ == "__main__":
    mcp.run()
