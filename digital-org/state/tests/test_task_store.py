"""State qatlami testlari (SQLite, tarmoqsiz)."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from task_store import TaskStore  # noqa: E402


@pytest.fixture()
def store():
    db = TaskStore(":memory:")
    yield db
    db.close()


def _create(store, **kwargs):
    params = dict(
        event_type="GROUP_LAUNCH_ORDER",
        from_agent="academic-manager",
        to_agent="branch-manager",
    )
    params.update(kwargs)
    return store.create(**params)


def test_create_starts_queued(store):
    task = _create(store)
    assert task["status"] == "queued"
    assert task["attempts"] == 0
    assert store.history(task["task_id"])[0]["to_status"] == "queued"


def test_requires_event_type(store):
    with pytest.raises(ValueError):
        store.create(event_type="", from_agent="a", to_agent="b")


def test_valid_transition_chain(store):
    task = _create(store)
    tid = task["task_id"]
    assert store.transition(tid, "running", actor="branch-manager")["status"] == "running"
    assert store.transition(tid, "done", actor="branch-manager", note="guruh ochildi")["status"] == "done"
    assert [row["to_status"] for row in store.history(tid)] == ["queued", "running", "done"]


def test_invalid_transition_rejected(store):
    task = _create(store)
    with pytest.raises(ValueError):
        store.transition(task["task_id"], "done", actor="branch-manager")  # queued → done yo'q


def test_done_is_terminal(store):
    task = _create(store)
    store.transition(task["task_id"], "running", actor="x")
    store.transition(task["task_id"], "done", actor="x")
    with pytest.raises(ValueError):
        store.transition(task["task_id"], "running", actor="x")


def test_unknown_task_raises(store):
    with pytest.raises(KeyError):
        store.transition("yoq", "running", actor="x")


def test_approval_flow(store):
    task = _create(store, requires_approval=True)
    store.transition(task["task_id"], "running", actor="finance-payroll")
    store.transition(task["task_id"], "waiting_approval", actor="finance-payroll")
    approved = store.approve(task["task_id"], actor="human:CFO")
    assert approved["status"] == "done"
    assert approved["approval_by"] == "human:CFO"


def test_approve_requires_waiting_status(store):
    task = _create(store)
    with pytest.raises(ValueError):
        store.approve(task["task_id"], actor="human:CFO")


def test_failed_can_retry(store):
    task = _create(store)
    store.transition(task["task_id"], "running", actor="x")
    store.transition(task["task_id"], "failed", actor="x", error="502")
    retried = store.transition(task["task_id"], "queued", actor="orchestrator", note="qayta urinish")
    assert retried["status"] == "queued"
    assert retried["last_error"] == "502"


def test_expire_stale_marks_overdue(store):
    task = _create(store, ttl_minutes=1)
    later = datetime.now(timezone.utc) + timedelta(minutes=5)
    expired = store.expire_stale(now=later)
    assert expired == [task["task_id"]]
    assert store.get(task["task_id"])["status"] == "expired"


def test_expire_stale_ignores_fresh(store):
    _create(store, ttl_minutes=30)
    assert store.expire_stale() == []


def test_list_and_counts(store):
    a = _create(store)
    _create(store, event_type="PAYMENT_DUE", from_agent="finance-payroll", to_agent="student-parent")
    store.transition(a["task_id"], "running", actor="branch-manager")
    assert len(store.list()) == 2
    assert len(store.list(status="running")) == 1
    assert len(store.list(agent="student-parent")) == 1
    assert store.counts()["running"] == 1


def test_persists_after_reopen(tmp_path):
    path = tmp_path / "tasks.db"
    first = TaskStore(path)
    task = _create(first)
    first.transition(task["task_id"], "running", actor="branch-manager")
    first.close()

    second = TaskStore(path)
    restored = second.get(task["task_id"])
    assert restored["status"] == "running"
    assert len(second.history(task["task_id"])) == 2
    second.close()


def test_payload_roundtrip(store):
    task = _create(store, payload={"ids": ["wl_101"], "numbers": {"waitlist": 12}})
    assert task["payload"]["numbers"]["waitlist"] == 12


def test_priority_validated(store):
    with pytest.raises(ValueError):
        _create(store, priority="tez")
