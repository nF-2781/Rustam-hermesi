"""`mcp-obsidian-rag` testlari: indeks, hybrid qidiruv, papka chegarasi, secret filtr.

Ishga tushirish:
    ./mcp-servers/mars_lms/.venv/Scripts/python.exe -m pytest mcp-servers/obsidian_rag/tests -q
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_PKG = _HERE.parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


indexer = _load("obsidian_rag_indexer", _PKG / "indexer.py")

DOC_PII_NONE = """---
path: 04_finance/kassa.md
agent: finance-payroll
pii: none
---

## Kassa tartibi

Kunlik kassa yopilishi 20:00 da. Qarzdorlik nazorati har kuni 09:00 da boshlanadi.
Qarzdorlik summasi 12 551 000 UZS bo'lsa, filial administratoriga xabar beriladi.

## Maosh

Oylik loyihasi faqat `draft` holatida yaratiladi; `paid` — inson tasdig'i bilan.
"""

DOC_PII_FORBIDDEN = """---
path: 02_academic/mini.md
pii: contains
---

## O'quvchi

Ali Valiyev, telefon 998901112233, qarzdorlik nazorati.
"""

DOC_NO_FRONTMATTER = """## Izoh

Bu faylda metadata yo'q, shuning uchun indeksga tushmaydi.
"""


@pytest.fixture()
def vault(tmp_path: Path) -> Path:
    (tmp_path / "04_finance").mkdir()
    (tmp_path / "02_academic").mkdir()
    (tmp_path / "04_finance" / "kassa.md").write_text(DOC_PII_NONE, encoding="utf-8")
    (tmp_path / "02_academic" / "mini.md").write_text(DOC_PII_FORBIDDEN, encoding="utf-8")
    (tmp_path / "notes.md").write_text(DOC_NO_FRONTMATTER, encoding="utf-8")
    return tmp_path


# --- indeksator --------------------------------------------------------------


def test_frontmatter_parsed():
    meta, body = indexer.parse_frontmatter(DOC_PII_NONE)
    assert meta["agent"] == "finance-payroll"
    assert meta["pii"] == "none"
    assert body.startswith("## Kassa tartibi")


def test_chunking_splits_by_heading():
    _, body = indexer.parse_frontmatter(DOC_PII_NONE)
    chunks = indexer.chunk_markdown(body, "04_finance/kassa.md")
    headings = [chunk["heading"] for chunk in chunks]
    assert headings == ["Kassa tartibi", "Maosh"]
    assert all(chunk["path"] == "04_finance/kassa.md" for chunk in chunks)


def test_only_pii_none_indexed(vault):
    index = indexer.build_index(vault)
    paths = {chunk["path"] for chunk in index["chunks"]}
    assert paths == {"04_finance/kassa.md"}
    skipped = {item["path"] for item in index["skipped"]}
    assert skipped == {"02_academic/mini.md", "notes.md"}


def test_vector_is_normalized(vault):
    index = indexer.build_index(vault)
    for chunk in index["chunks"]:
        norm = sum(value * value for value in chunk["vector"]) ** 0.5
        assert abs(norm - 1.0) < 1e-3
        assert len(chunk["vector"]) == indexer.VECTOR_DIM


def test_search_finds_finance_chunk(vault):
    index = indexer.build_index(vault)
    results = indexer.search(index, "qarzdorlik nazorati", top_k=3)
    assert results
    assert results[0]["path"] == "04_finance/kassa.md"
    assert results[0]["bm25"] > 0
    assert results[0]["score"] > 0


def test_search_exact_number_uses_bm25(vault):
    index = indexer.build_index(vault)
    results = indexer.search(index, "12 551 000 UZS", top_k=3)
    assert results
    assert "12 551 000" in results[0]["text"]


def test_search_empty_query_returns_nothing(vault):
    index = indexer.build_index(vault)
    assert indexer.search(index, "   ") == []


def test_index_roundtrip(tmp_path, vault):
    index = indexer.build_index(vault)
    path = indexer.save_index(index, tmp_path / "idx" / "vault.json")
    loaded = indexer.load_index(path)
    assert loaded["mode"] == "hashed-bow"
    assert len(loaded["chunks"]) == len(index["chunks"])


# --- server chegaralari ------------------------------------------------------


@pytest.fixture()
def rag(vault, monkeypatch):
    module = _load("obsidian_rag_server", _PKG / "server.py")
    monkeypatch.setattr(module, "VAULT", vault.resolve())
    monkeypatch.setattr(module, "INDEX_PATH", vault.resolve() / ".index" / "vault.json")
    return module


def test_search_tool_returns_envelope(rag):
    result = rag.vault_search("qarzdorlik", agent="finance-payroll")
    assert result["status_code"] == 200
    assert result["details"]["results"]


def test_read_rejects_path_traversal(rag):
    result = rag.vault_read("../../config.yaml")
    assert result["status_code"] == 400


def test_read_rejects_non_markdown(rag):
    assert rag.vault_read("notes.txt")["status_code"] == 400


def test_append_outside_scope_blocked(rag):
    result = rag.vault_append("03_branch/kunlik.md", "matn", agent="finance-payroll")
    assert result["status_code"] == 403
    assert not (rag.VAULT / "03_branch" / "kunlik.md").exists()


def test_append_inside_scope_allowed(rag):
    result = rag.vault_append("04_finance/kunlik.md", "- kassa yopildi", agent="finance-payroll")
    assert result["status_code"] == 200
    content = (rag.VAULT / "04_finance" / "kunlik.md").read_text(encoding="utf-8")
    assert "kassa yopildi" in content
    assert "finance-payroll" in content


def test_read_only_agent_cannot_write(rag):
    result = rag.vault_append("01_ceo/brifing.md", "matn", agent="orchestrator")
    assert result["status_code"] == 403


def test_secret_blocked(rag):
    result = rag.vault_append("04_finance/kunlik.md", "password: SuperSecret123", agent="finance-payroll")
    assert result["status_code"] == 403
    assert not (rag.VAULT / "04_finance" / "kunlik.md").exists()


def test_lessons_add_appends_shared_file(rag):
    result = rag.vault_lessons_add("test saboq", "### holat\n- **Nima bo'ldi:** test", agent="auditor-security")
    assert result["status_code"] == 200
    content = (rag.VAULT / "06_self_improve" / "lessons_learned.md").read_text(encoding="utf-8")
    assert "test saboq" in content
