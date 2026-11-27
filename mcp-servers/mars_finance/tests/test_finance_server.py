"""`mcp-mars-finance` serverining guardrail/RBAC testlari (tarmoqsiz).

Ishga tushirish:
    ./mcp-servers/mars_lms/.venv/Scripts/python.exe -m pytest mcp-servers/mars_finance/tests -q
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import httpx
import pytest

_HERE = Path(__file__).resolve().parent
_SERVER_PATH = _HERE.parent / "server.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


server = _load("mars_finance_server", _SERVER_PATH)


class MockBackend:
    """Moliya endpointlarini taqlid qiladi; chaqiruvlarni yozib boradi."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        self.calls.append((request.method, path))
        if path == "/api/auth/login":
            return httpx.Response(200, json={"accessToken": "tok", "role": "admin"})
        if path == "/api/branch/overview":
            return httpx.Response(200, json={"overview": {"income": 10_000_000, "expense": 4_000_000}})
        if path == "/api/finance/overview":
            return httpx.Response(200, json={"overview": {"netProfit": 6_000_000}})
        return httpx.Response(200, json={"ok": True, "path": path})


@pytest.fixture()
def backend(monkeypatch):
    fake = MockBackend()
    client = server.LMSClient(
        base_url="https://mock.local",
        phone="998900000000",
        password="x",
        transport=httpx.MockTransport(fake.handler),
    )
    client.token = "tok"
    client.authenticated_role = "admin"
    client.branch = {"_id": "b1", "name": "Chilonzor"}
    client.user = {"branch": "b1"}
    monkeypatch.setattr(server, "CLIENT", client)
    return fake


# --- RBAC -------------------------------------------------------------------


def test_read_tool_allowed_for_finance(backend):
    result = server.list_payments(agent="finance-payroll", limit=10)
    assert result["status_code"] == 200
    assert ("GET", "/api/branch/payments") in backend.calls


def test_ceo_can_read(backend):
    result = server.list_debtors(agent="ceo-strategist", month="2026-11")
    assert result["status_code"] == 200
    assert result["endpoint"] == "/api/branch/debtors"


def test_ceo_cannot_write(backend):
    result = server.create_payment(agent="ceo-strategist", student_id="s1", amount=100_000)
    assert result["status_code"] == 403
    assert result["details"]["guardrail"]["rule"] == "RBAC_READ_ONLY"
    assert backend.calls == []  # tarmoqqa chiqmadi


def test_unknown_agent_blocked(backend):
    result = server.list_payments(agent="mentor-assistant")
    assert result["status_code"] == 403
    assert result["details"]["guardrail"]["rule"] == "RBAC_AGENT"


def test_abac_blocks_foreign_branch_read(backend):
    result = server.list_payments(agent="finance-payroll", branch_id="b2")
    assert result["status_code"] == 403
    assert result["details"]["guardrail"]["rule"] == "ABAC_BRANCH"
    assert backend.calls == []


# --- Yozuvchi tool'lar -------------------------------------------------------


def test_create_payment_allowed(backend):
    result = server.create_payment(student_id="s1", amount=800_000, month="2026-11", reason="kassa")
    assert result["status_code"] == 200
    assert ("POST", "/api/branch/payments") in backend.calls


def test_payment_amount_must_be_positive(backend):
    result = server.create_payment(student_id="s1", amount=0)
    assert result["status_code"] == 400
    assert backend.calls == []


def test_payment_requires_student_id(backend):
    result = server.create_payment(student_id="", amount=1000)
    assert result["status_code"] == 400


def test_update_payment_without_reason_blocked(backend):
    result = server.update_payment(payment_id="p1", status="confirmed")
    assert result["status_code"] == 403
    assert result["details"]["guardrail"]["rule"] == "REASON_REQUIRED"
    assert backend.calls == []


def test_update_payment_with_reason_allowed(backend):
    result = server.update_payment(payment_id="p1", status="confirmed", reason="bank cheki")
    assert result["status_code"] == 200
    assert ("PATCH", "/api/branch/payments/p1") in backend.calls


def test_void_payment_needs_approval(backend):
    result = server.void_payment(payment_id="p1", reason="xato kiritilgan")
    assert result["status_code"] == 428
    assert result["details"]["guardrail"]["rule"] == "HUMAN_APPROVAL"
    assert result["details"]["requires_approval"] is True
    assert backend.calls == []


def test_void_payment_without_reason_is_blocked_first(backend):
    result = server.void_payment(payment_id="p1")
    assert result["status_code"] == 403
    assert result["details"]["guardrail"]["rule"] == "REASON_REQUIRED"


def test_small_expense_allowed(backend):
    result = server.create_expense(amount=250_000, category="arenda", month="2026-11")
    assert result["status_code"] == 200
    assert ("POST", "/api/branch/expenses") in backend.calls


def test_large_expense_needs_approval(backend):
    result = server.create_expense(amount=1_500_000, category="arenda")
    assert result["status_code"] == 428
    assert result["details"]["guardrail"]["rule"] == "HUMAN_APPROVAL"
    assert backend.calls == []


def test_salary_draft_needs_approval(backend):
    result = server.create_salary_draft(mentor_id="m1", month="2026-11", amount=4_500_000)
    assert result["status_code"] == 428
    assert result["details"]["guardrail"]["rule"] == "HUMAN_APPROVAL"


def test_salary_status_review_allowed_but_paid_needs_approval(backend):
    allowed = server.set_salary_status(salary_id="sal1", status="review")
    assert allowed["status_code"] == 200
    blocked = server.set_salary_status(salary_id="sal1", status="paid")
    assert blocked["status_code"] == 428
    assert blocked["details"]["guardrail"]["rule"] == "HUMAN_APPROVAL"


def test_invalid_salary_status_rejected(backend):
    result = server.set_salary_status(salary_id="sal1", status="done")
    assert result["status_code"] == 400


def test_overview_sums_income_and_expense(backend):
    result = server.finance_overview(agent="ceo-strategist", month="2026-11")
    assert result["status_code"] == 200
    assert result["details"]["balance"] == 6_000_000


def test_no_tool_touches_legacy_payments_endpoint(backend):
    server.list_payments()
    server.create_payment(student_id="s1", amount=1000)
    server.update_payment(payment_id="p1", status="confirmed", reason="tuzatish")
    assert all(path != "/api/payments" for _, path in backend.calls)
