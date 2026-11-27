"""Mars AI OS — Identity + observability: harakat jurnali (JSON Lines).

Har tool chaqiruvi bitta qator bo'lib yoziladi. Qator **kim** (agent, branch),
**nima** (tool, endpoint), **qanday natija** (status, guardrail qarori) va
**qaysi vazifa** (`task_id`) ichida bajarilganini saqlaydi.

Muhim qoidalar:
- maxfiy kalitlar (`password`, `token`, `api_key`…) qiymati `***` bo'ladi;
- telefon/email kabi PII maskalanadi;
- fayl faqat qo'shiladi (append-only), tahrirlanmaydi;
- yozuv muvaffaqiyatsiz bo'lsa ham agent ishi to'xtamaydi (log — yordamchi qatlam).

Ishlatish::

    from audit_log import record
    record("digital-org/state/audit.jsonl", agent="finance-payroll", action="create_payment",
           endpoint="/api/branch/payments", method="POST", status_code=200,
           task_id="…", branch_id="b1", decision="ALLOW")
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

SECRET_KEYS = {
    "password", "token", "access_token", "refresh_token", "secret",
    "api_key", "apikey", "authorization", "cookie", "session",
}
_PHONE_RE = re.compile(r"\+?\d{9,13}")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_MAX_TEXT = 500


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: ("***" if str(key).lower() in SECRET_KEYS else _scrub(item)) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_scrub(item) for item in value]
    if isinstance(value, str):
        masked = _PHONE_RE.sub("***", value)
        masked = _EMAIL_RE.sub("***", masked)
        return masked[:_MAX_TEXT]
    return value


def record(
    path: str | Path,
    *,
    agent: str,
    action: str,
    status_code: int = 200,
    endpoint: str = "",
    method: str = "GET",
    task_id: Optional[str] = None,
    branch_id: Optional[str] = None,
    decision: Optional[str] = None,
    tool: Optional[str] = None,
    details: Optional[dict] = None,
    now: Optional[datetime] = None,
) -> dict:
    """Bitta harakatni jurnalga yozadi va yozilgan yozuvni qaytaradi."""
    moment = now or datetime.now(timezone.utc)
    entry = {
        "ts": moment.isoformat(timespec="seconds"),
        "agent": agent,
        "action": action,
        "tool": tool or action,
        "method": str(method).upper(),
        "endpoint": endpoint,
        "status_code": int(status_code),
        "decision": decision,
        "task_id": task_id,
        "branch_id": branch_id,
        "details": _scrub(details or {}),
    }
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def read(path: str | Path, limit: int = 50) -> list[dict]:
    """Oxirgi `limit` yozuvni qaytaradi (eskidan yangiga)."""
    target = Path(path)
    if not target.exists():
        return []
    lines = target.read_text(encoding="utf-8").splitlines()[-max(1, int(limit)):]
    entries = []
    for line in lines:
        try:
            entries.append(json.loads(line))
        except ValueError:
            continue
    return entries


def main(argv: Optional[list[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = list(argv or sys.argv[1:])
    if not args:
        print("ishlatish: audit_log.py <audit.jsonl> [limit]")
        return 2
    limit = int(args[1]) if len(args) > 1 else 20
    entries = read(args[0], limit)
    for entry in entries:
        print(f"{entry['ts']} {entry['agent']:<18} {entry['method']:<6} {entry['status_code']} "
              f"{entry.get('decision') or '-':<16} {entry['endpoint']}")
    print(f"— {len(entries)} yozuv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
