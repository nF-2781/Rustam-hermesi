"""Mars AI OS — 2-qavat himoya: hard guardrail (MCP tool chaqirilishidan oldin).

`.md` fayldagi qoida — model uchun chiziq; bu modul esa **kod**: `if/else` devor.
Agent tool chaqirishdan oldin `check()` (yoki `enforce()`) ni o'tkazadi.

Qamralgan qoidalar
------------------
1. `PROMPT_INJECTION`  — foydalanuvchi matnidagi buyruqni `<user_data>` ga ajratadi va
   `grade`/`payment` turidagi amalni bloklaydi.
2. `LEGACY_ENDPOINT`   — eski `POST /api/payments` (bloklangan) o'tmaydi.
3. `ABAC_BRANCH`       — boshqa filial resursiga yozish rad etiladi.
4. `REASON_REQUIRED`   — pul yozuvini o'zgartirishda `reason` bo'sh bo'lmaydi.
5. `HUMAN_APPROVAL`    — oylik, `paid`, katta xarajat, `DELETE`/`void` — inson tasdig'i.
6. `CANCEL_WINDOW`     — darsga 1 soatdan kam qolganda bronni bekor qilib bo'lmaydi.

Ishlatish::

    from security_sandbox import check, enforce, GuardrailDenied

    d = check("finance-payroll", "POST", "/api/finance/salaries", {"amount": 4_500_000})
    if not d.allowed:
        ...  # d.requires_approval -> odamga yuboriladi, bajarilmaydi

CLI (qo'lda sinash)::

    echo '{"agent":"auditor","method":"DELETE","path":"/api/branch/groups/1","args":{}}' \\
      | python digital-org/security/security_sandbox.py
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Optional

# --- siyosat (konfiguratsiya) ------------------------------------------------

MONEY_APPROVAL_LIMIT = 1_000_000  # UZS — bundan yuqori xarajat inson tasdig'i bilan
CANCEL_WINDOW = timedelta(hours=1)  # darsga qolgan minimal vaqt

SECRET_KEYS = ("password", "token", "access_token", "refresh_token", "secret", "api_key")
TEXT_KEYS = ("content", "text", "feedback", "comment", "answer", "message",
             "homework_text", "submission", "review")

INJECTION_PATTERNS = (
    r"ignore\s+(all\s+)?previous",
    r"forget\s+(all\s+)?(previous\s+)?(rules|instructions)",
    r"oldingi\s+qoidalarni\s+unut",
    r"qoidalarni\s+unut",
    r"system\s*prompt",
    r"tizim\s+prompt",
    r"sen\s+endi\b",
    r"acting\s+as",
    r"\b100\s*ball\b",
    r"give\s+me\s+(a\s+)?(full|100)",
)

MONEY_WRITE_PATH = re.compile(
    r"^/api/(finance|branch)/(salaries|payments|expenses|debtors)(/|$)"
)
SALARY_STATUS_PATH = re.compile(r"^/api/finance/salaries/[^/]+/status$")
EXTRA_LESSON_CANCEL = re.compile(r"^/students/me/extra-lessons/[^/]+/book$")
TUTOR_BOOKING = re.compile(r"^/api/tutor-bookings/[^/]+$")


# --- natija ------------------------------------------------------------------


@dataclass(frozen=True)
class Decision:
    """Bitta tool chaqiruvi uchun qaror."""

    allowed: bool
    rule: str
    reason: str
    requires_approval: bool = False
    sanitized_args: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "rule": self.rule,
            "reason": self.reason,
            "requires_approval": self.requires_approval,
            "sanitized_args": self.sanitized_args,
        }


class GuardrailDenied(PermissionError):
    """`enforce()` uchun: qoida bajarilishni to'xtatdi."""

    def __init__(self, decision: Decision):
        self.decision = decision
        super().__init__(f"{decision.rule}: {decision.reason}")


# --- yordamchi ---------------------------------------------------------------


def _clean_path(path: str) -> str:
    return (path or "").split("?", 1)[0].split("#", 1)[0].rstrip("/") or "/"


def _redact(args: Mapping[str, Any]) -> dict:
    out: dict[str, Any] = {}
    for key, value in args.items():
        out[key] = "***" if key.lower() in SECRET_KEYS else value
    return out


def wrap_user_data(text: str) -> str:
    """Foydalanuvchi matnini chegaralaydi — model uchun bu ma'lumot, ko'rsatma emas."""
    if not isinstance(text, str):
        return text
    safe = text.replace("</user_data>", "<\\/user_data>")
    return f"<user_data>{safe}</user_data>"


def detect_injection(text: str) -> Optional[str]:
    if not isinstance(text, str):
        return None
    low = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, low):
            return pattern
    return None


def _parse_dt(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _scan_payload(args: Mapping[str, Any]) -> tuple[Optional[str], dict]:
    """Matn maydonlarini tekshiradi; topilsa pattern nomini va xavfsiz nusxani qaytaradi."""
    cleaned = _redact(args)
    for key, value in args.items():
        if key.lower() in TEXT_KEYS or (isinstance(value, str) and len(value) > 80):
            hit = detect_injection(value) if isinstance(value, str) else None
            if hit:
                cleaned[key] = wrap_user_data(value)
                return hit, cleaned
    return None, cleaned


def _requires_reason(method: str, path: str) -> bool:
    # O'quvchining o'z bronini bekor qilishi alohida qoida bilan boshqariladi (CANCEL_WINDOW),
    # moliyaviy tuzatish emas — undan `reason` talab qilinmaydi.
    if EXTRA_LESSON_CANCEL.match(path) or TUTOR_BOOKING.match(path):
        return False
    if method == "DELETE":
        return True
    if path.endswith("/void"):
        return True
    if method in ("PATCH", "PUT") and re.match(r"^/api/(branch|finance)/(payments|expenses)/[^/]+$", path):
        return True
    return False


# --- asosiy tekshiruv --------------------------------------------------------


def check(
    agent: str,
    method: str,
    path: str,
    args: Optional[Mapping[str, Any]] = None,
    *,
    actor_branch: Optional[str] = None,
    resource_branch: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Decision:
    """Bitta chaqiruvni tekshiradi (tarmoqqa chiqmaydi, holat saqlamaydi)."""
    method = (method or "GET").upper()
    path = _clean_path(path)
    raw_args = dict(args or {})
    now = now or datetime.now(timezone.utc)

    # 1) Prompt injection: matn ichidagi buyruq
    hit, cleaned = _scan_payload(raw_args)
    if hit:
        return Decision(
            allowed=False,
            rule="PROMPT_INJECTION",
            reason=(
                "foydalanuvchi matnida buyruq naqshi topildi "
                f"({hit}); matn <user_data> ga ajratildi, grade/payment amali bloklandi"
            ),
            sanitized_args=cleaned,
        )

    # 2) Bloklangan eski endpoint
    if method != "GET" and (path == "/api/payments" or path.startswith("/api/payments/")):
        return Decision(
            allowed=False,
            rule="LEGACY_ENDPOINT",
            reason="eski /api/payments yozuvi bloklangan; /api/finance/payments yoki /api/branch/payments ishlatiladi",
            sanitized_args=cleaned,
        )

    # 3) ABAC: filial chegarasi
    if (
        resource_branch
        and actor_branch
        and str(resource_branch) != str(actor_branch)
        and method != "GET"
    ):
        return Decision(
            allowed=False,
            rule="ABAC_BRANCH",
            reason=f"agent filiali {actor_branch} ≠ resurs filiali {resource_branch}",
            sanitized_args=cleaned,
        )

    # 4) Bronni bekor qilish oynasi
    if method == "DELETE" and (EXTRA_LESSON_CANCEL.match(path) or TUTOR_BOOKING.match(path)):
        scheduled = _parse_dt(cleaned.get("scheduled_at") or cleaned.get("starts_at"))
        if scheduled is None:
            return Decision(
                allowed=False,
                rule="CANCEL_WINDOW",
                reason="dars vaqti (scheduled_at) berilmagan — qoidani tekshirib bo'lmaydi",
                sanitized_args=cleaned,
            )
        left = scheduled - now
        if left < CANCEL_WINDOW:
            return Decision(
                allowed=False,
                rule="CANCEL_WINDOW",
                reason=f"darsga {int(left.total_seconds() // 60)} daqiqa qoldi (< 60) — bekor qilib bo'lmaydi",
                sanitized_args=cleaned,
            )

    # 5) Pul yozuvida sabab majburiy
    if _requires_reason(method, path):
        reason = str(cleaned.get("reason") or "").strip()
        if not reason:
            return Decision(
                allowed=False,
                rule="REASON_REQUIRED",
                reason=f"{method} {path} uchun `reason` bo'sh — sababsiz o'zgartirish bloklandi",
                sanitized_args=cleaned,
            )

    # 6) Inson tasdig'i (Human-in-the-Loop)
    approval_reason: Optional[str] = None
    if method == "POST" and path == "/api/finance/salaries":
        approval_reason = "oylik loyihasi yaratish — rahbar tasdig'i (2FA)"
    elif method == "PATCH" and SALARY_STATUS_PATH.match(path) and str(cleaned.get("status", "")).lower() == "paid":
        approval_reason = "oylikni `paid` qilish — rahbar tasdig'i (2FA)"
    elif method in ("POST", "PUT", "PATCH") and re.match(r"^/api/(finance|branch)/expenses(/|$)", path):
        amount = cleaned.get("amount")
        if isinstance(amount, (int, float)) and amount > MONEY_APPROVAL_LIMIT:
            approval_reason = f"xarajat {amount:,} UZS > {MONEY_APPROVAL_LIMIT:,} — rahbar tasdig'i"
    self_service_cancel = bool(EXTRA_LESSON_CANCEL.match(path) or TUTOR_BOOKING.match(path))
    if (method == "DELETE" and not self_service_cancel) or path.endswith("/void"):
        approval_reason = approval_reason or f"{method} {path} — qaytarilmas amal, inson tasdig'i"

    if approval_reason:
        return Decision(
            allowed=False,
            rule="HUMAN_APPROVAL",
            reason=approval_reason,
            requires_approval=True,
            sanitized_args=cleaned,
        )

    return Decision(
        allowed=True,
        rule="ALLOW",
        reason=f"{agent}: {method} {path} — qoida buzilmadi",
        sanitized_args=cleaned,
    )


def enforce(*args: Any, **kwargs: Any) -> Decision:
    """`check()` natijasi ruxsat bermasa `GuardrailDenied` ko'taradi."""
    decision = check(*args, **kwargs)
    if not decision.allowed:
        raise GuardrailDenied(decision)
    return decision


# --- CLI ---------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> int:
    # Windows konsoli cp1251 bo'lsa "—" kabi belgilar buziladi — chiqishni UTF-8 ga o'tkazamiz.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    payload = json.load(sys.stdin)
    decision = check(
        payload.get("agent", "unknown"),
        payload.get("method", "GET"),
        payload.get("path", "/"),
        payload.get("args") or {},
        actor_branch=payload.get("actor_branch"),
        resource_branch=payload.get("resource_branch"),
    )
    print(json.dumps(decision.as_dict(), ensure_ascii=False, indent=2))
    return 0 if decision.allowed else 2


if __name__ == "__main__":
    raise SystemExit(main())
