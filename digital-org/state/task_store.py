"""Mars AI OS — State qatlami: A2A vazifalarining holati (SQLite).

Nega kerak: agent javobni 15 daqiqada qaytarmasa yoki inson tasdig'i kutilsa, bu
"yo'qolib ketmasligi" kerak. Holat `tasks` jadvalida saqlanadi, har o'zgarish
`task_events` ga yoziladi — shu bilan zanjir bo'yicha to'liq tarix qoladi.

Holat mashinasi::

    queued ──► running ──► done
      │           ├──► waiting_approval ──► done | failed
      │           ├──► failed ──► queued (qayta urinish)
      └──► blocked ──► queued | failed | expired
    queued | running | waiting_approval ──(muddat)──► expired

Ishlatish::

    from task_store import TaskStore
    store = TaskStore("digital-org/state/tasks.db")
    task = store.create(event_type="GROUP_LAUNCH_ORDER", from_agent="academic-manager",
                        to_agent="branch-manager", requires_approval=False)
    store.transition(task["task_id"], "running", actor="branch-manager")
    store.transition(task["task_id"], "done", actor="branch-manager", note="guruh ochildi")
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

STATUSES = ("queued", "running", "waiting_approval", "done", "failed", "blocked", "expired")
TERMINAL = frozenset({"done", "expired"})

TRANSITIONS: dict[str, frozenset[str]] = {
    "queued": frozenset({"running", "blocked", "expired"}),
    "running": frozenset({"waiting_approval", "done", "failed", "blocked", "expired"}),
    "waiting_approval": frozenset({"done", "failed", "blocked", "expired"}),
    "blocked": frozenset({"queued", "failed", "expired"}),
    "failed": frozenset({"queued"}),
    "done": frozenset(),
    "expired": frozenset(),
}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    task_id           TEXT PRIMARY KEY,
    event_type        TEXT NOT NULL,
    from_agent        TEXT NOT NULL,
    to_agent          TEXT NOT NULL,
    status            TEXT NOT NULL,
    priority          TEXT NOT NULL DEFAULT 'normal',
    payload           TEXT,
    requires_approval INTEGER NOT NULL DEFAULT 0,
    approval_by       TEXT,
    attempts          INTEGER NOT NULL DEFAULT 0,
    last_error        TEXT,
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL,
    expires_at        TEXT
);
CREATE TABLE IF NOT EXISTS task_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id     TEXT NOT NULL,
    at          TEXT NOT NULL,
    from_status TEXT,
    to_status   TEXT NOT NULL,
    actor       TEXT NOT NULL,
    note        TEXT
);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_events_task ON task_events(task_id);
"""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.isoformat(timespec="seconds")


class TaskStore:
    """A2A vazifalari uchun minimal, lekin qat'iy holat ombori."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(self.path)
        self._db.row_factory = sqlite3.Row
        self._db.executescript(_SCHEMA)
        self._db.commit()

    # --- yozish ---------------------------------------------------------
    def create(
        self,
        *,
        event_type: str,
        from_agent: str,
        to_agent: str,
        payload: Optional[dict] = None,
        priority: str = "normal",
        ttl_minutes: int = 15,
        requires_approval: bool = False,
        task_id: Optional[str] = None,
    ) -> dict:
        if not str(event_type or "").strip():
            raise ValueError("`event_type` majburiy (erkin matn emas, jadval kaliti).")
        for name, value in (("from_agent", from_agent), ("to_agent", to_agent)):
            if not str(value or "").strip():
                raise ValueError(f"`{name}` majburiy.")
        if priority not in {"low", "normal", "high", "critical"}:
            raise ValueError("`priority`: low | normal | high | critical")

        moment = _now()
        identifier = task_id or str(uuid.uuid4())
        self._db.execute(
            "INSERT INTO tasks (task_id, event_type, from_agent, to_agent, status, priority, payload,"
            " requires_approval, created_at, updated_at, expires_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                identifier,
                event_type,
                from_agent,
                to_agent,
                "queued",
                priority,
                json.dumps(payload or {}, ensure_ascii=False),
                1 if requires_approval else 0,
                _iso(moment),
                _iso(moment),
                _iso(moment + timedelta(minutes=max(1, int(ttl_minutes)))),
            ),
        )
        self._event(identifier, None, "queued", from_agent, "vazifa yaratildi")
        self._db.commit()
        return self.get(identifier)  # type: ignore[return-value]

    def transition(
        self,
        task_id: str,
        status: str,
        *,
        actor: str,
        note: str = "",
        error: Optional[str] = None,
    ) -> dict:
        if status not in STATUSES:
            raise ValueError(f"noma'lum holat: {status}. Ruxsat: {', '.join(STATUSES)}")
        current = self.get(task_id)
        if current is None:
            raise KeyError(f"vazifa topilmadi: {task_id}")
        allowed = TRANSITIONS[current["status"]]
        if status not in allowed:
            raise ValueError(
                f"{current['status']} → {status} o'tish taqiqlangan. Ruxsat: "
                f"{', '.join(sorted(allowed)) or 'yoʻq (yakuniy holat)'}"
            )

        moment = _now()
        attempt = 1 if status == "running" else 0
        if status == "waiting_approval":
            self._db.execute(
                "UPDATE tasks SET status = ?, updated_at = ?, attempts = attempts + ?,"
                " last_error = COALESCE(?, last_error), approval_by = NULL WHERE task_id = ?",
                (status, _iso(moment), attempt, error, task_id),
            )
        elif status == "done" and current["status"] == "waiting_approval":
            self._db.execute(
                "UPDATE tasks SET status = ?, updated_at = ?, attempts = attempts + ?,"
                " last_error = COALESCE(?, last_error), approval_by = ? WHERE task_id = ?",
                (status, _iso(moment), attempt, error, actor, task_id),
            )
        else:
            self._db.execute(
                "UPDATE tasks SET status = ?, updated_at = ?, attempts = attempts + ?,"
                " last_error = COALESCE(?, last_error) WHERE task_id = ?",
                (status, _iso(moment), attempt, error, task_id),
            )
        self._event(task_id, current["status"], status, actor, note or error or "")
        self._db.commit()
        return self.get(task_id)  # type: ignore[return-value]

    def approve(self, task_id: str, *, actor: str, note: str = "") -> dict:
        """Inson tasdig'i: `waiting_approval` → `done` (approval_by yoziladi)."""
        current = self.get(task_id)
        if current is None:
            raise KeyError(f"vazifa topilmadi: {task_id}")
        if current["status"] != "waiting_approval":
            raise ValueError(f"tasdiq faqat waiting_approval holatida: hozir {current['status']}")
        result = self.transition(task_id, "done", actor=actor, note=note or "inson tasdig'i")
        return result

    def expire_stale(self, *, now: Optional[datetime] = None) -> list[str]:
        """Muddati o'tgan faol vazifalarni `expired` ga o'tkazadi (orchestrator ishi)."""
        moment = now or _now()
        rows = self._db.execute(
            "SELECT task_id, expires_at FROM tasks WHERE status IN ('queued','running','waiting_approval')"
        ).fetchall()
        expired: list[str] = []
        for row in rows:
            if row["expires_at"] and row["expires_at"] < _iso(moment):
                self.transition(row["task_id"], "expired", actor="orchestrator", note="TTL tugadi")
                expired.append(row["task_id"])
        return expired

    # --- o'qish ---------------------------------------------------------
    def get(self, task_id: str) -> Optional[dict]:
        row = self._db.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        return self._row(row) if row else None

    def list(
        self,
        *,
        status: Optional[str] = None,
        agent: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        query = "SELECT * FROM tasks"
        clauses: list[str] = []
        params: list[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if agent:
            clauses.append("(from_agent = ? OR to_agent = ?)")
            params.extend([agent, agent])
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(max(1, int(limit)))
        return [self._row(row) for row in self._db.execute(query, params).fetchall()]

    def history(self, task_id: str) -> list[dict]:
        rows = self._db.execute(
            "SELECT at, from_status, to_status, actor, note FROM task_events WHERE task_id = ? ORDER BY id",
            (task_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def counts(self) -> dict[str, int]:
        rows = self._db.execute("SELECT status, COUNT(*) AS n FROM tasks GROUP BY status").fetchall()
        return {row["status"]: row["n"] for row in rows}

    def close(self) -> None:
        self._db.close()

    # --- ichki ----------------------------------------------------------
    def _event(self, task_id: str, from_status: Optional[str], to_status: str, actor: str, note: str) -> None:
        self._db.execute(
            "INSERT INTO task_events (task_id, at, from_status, to_status, actor, note) VALUES (?,?,?,?,?,?)",
            (task_id, _iso(_now()), from_status, to_status, actor, note),
        )

    @staticmethod
    def _row(row: sqlite3.Row) -> dict:
        data = dict(row)
        if data.get("payload"):
            try:
                data["payload"] = json.loads(data["payload"])
            except (TypeError, ValueError):
                pass
        data["requires_approval"] = bool(data.get("requires_approval"))
        return data


if __name__ == "__main__":
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    db = sys.argv[1] if len(sys.argv) > 1 else "digital-org/state/tasks.db"
    store = TaskStore(db)
    expired = store.expire_stale()
    print(json.dumps({"db": db, "counts": store.counts(), "expired": expired}, ensure_ascii=False, indent=2))
