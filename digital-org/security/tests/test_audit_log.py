"""Audit jurnali testlari (fayl tizimi, tarmoqsiz)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from audit_log import read, record  # noqa: E402


def test_record_writes_one_line(tmp_path):
    path = tmp_path / "audit.jsonl"
    entry = record(
        path,
        agent="finance-payroll",
        action="create_payment",
        endpoint="/api/branch/payments",
        method="POST",
        status_code=200,
        task_id="t1",
        branch_id="b1",
        decision="ALLOW",
    )
    assert entry["agent"] == "finance-payroll"
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["task_id"] == "t1"


def test_secrets_redacted(tmp_path):
    path = tmp_path / "audit.jsonl"
    entry = record(
        path,
        agent="ceo-strategist",
        action="login",
        details={"password": "SuperSecret", "token": "abc123", "nested": {"api_key": "k-1"}},
    )
    assert entry["details"]["password"] == "***"
    assert entry["details"]["token"] == "***"
    assert entry["details"]["nested"]["api_key"] == "***"


def test_pii_masked(tmp_path):
    path = tmp_path / "audit.jsonl"
    entry = record(
        path,
        agent="mentor-assistant",
        action="hw_review",
        details={"text": "Ali Valiyev +998901112233 ali@example.com"},
    )
    assert "998901112233" not in entry["details"]["text"]
    assert "ali@example.com" not in entry["details"]["text"]
    assert "+ 998" not in entry["details"]["text"]


def test_long_text_truncated(tmp_path):
    entry = record(tmp_path / "a.jsonl", agent="x", action="y", details={"text": "a" * 900})
    assert len(entry["details"]["text"]) == 500


def test_append_only_and_read_limit(tmp_path):
    path = tmp_path / "audit.jsonl"
    for index in range(5):
        record(path, agent=f"a{index}", action="ping")
    assert len(read(path)) == 5
    latest = read(path, limit=2)
    assert [entry["agent"] for entry in latest] == ["a3", "a4"]


def test_read_missing_file_returns_empty(tmp_path):
    assert read(tmp_path / "yoq.jsonl") == []
