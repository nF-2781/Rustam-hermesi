"""mcp-obsidian-rag — Obsidian vault uchun MCP server (stdio).

Tool'lar
--------
- `vault_search`      — hybrid qidiruv (BM25 + hashed-vector), barcha agentlar.
- `vault_read`        — vault ichidagi `.md` faylni o'qish.
- `vault_append`      — faqat **o'z papkasiga** yozish (path traversal taqiqlangan).
- `vault_lessons_add` — `06_self_improve/lessons_learned.md` ga saboq qo'shish.

Chegaralar
----------
1. `resolve_path()` vault tashqarisiga chiqmaydi (`..`, absolyut yo'l, symlink rad).
2. Har agent faqat `WRITE_SCOPES` dagi papkaga yozadi; boshqasi `WRITE_SCOPE` bilan blok.
3. Yozuv matnida token/parol/API kalit naqshi bo'lsa `SECRET_BLOCKED`.
4. Indeks `pii: none` bo'lmagan faylni umuman olmaydi (`indexer.build_index`).

Ishga tushirish:
    OBSIDIAN_VAULT=C:/…/digital-org/memory/vault \\
    OBSIDIAN_INDEX=C:/…/mcp-servers/obsidian_rag/.index/vault.json \\
    python mcp-servers/obsidian_rag/server.py
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from mcp.server.fastmcp import FastMCP  # noqa: E402

from indexer import build_index, load_index, save_index, search  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
VAULT = Path(os.environ.get("OBSIDIAN_VAULT") or (REPO_ROOT / "digital-org" / "memory" / "vault")).resolve()
INDEX_PATH = Path(os.environ.get("OBSIDIAN_INDEX") or (_HERE / ".index" / "vault.json"))

# Har agent faqat shu papkalarga yozadi (digital-org/memory/README.md bilan bir xil).
WRITE_SCOPES: dict[str, tuple[str, ...]] = {
    "ceo-strategist": ("01_ceo",),
    "academic-manager": ("02_academic",),
    "mentor-assistant": ("02_academic",),
    "tutor-intern": ("02_academic",),
    "branch-manager": ("03_branch",),
    "finance-payroll": ("04_finance",),
    "auditor-security": ("05_audit", "06_self_improve"),
    "orchestrator": (),
    "student-parent": (),
}
SHARED_LESSONS = "06_self_improve/lessons_learned.md"

_SECRET_RE = re.compile(
    r"(password\s*[:=]\s*\S+|token\s*[:=]\s*\S+|api[_-]?key\s*[:=]\s*\S+|"
    r"bearer\s+[A-Za-z0-9._-]{10,}|sk-[A-Za-z0-9]{12,}|-----BEGIN [A-Z ]+PRIVATE KEY-----)",
    re.IGNORECASE,
)

mcp = FastMCP(
    "obsidian-rag",
    instructions=(
        "Obsidian vault (MARS AI OS xotirasi). `vault_search` bilan avval mavjud bilimni qidiring. "
        "`vault_append` faqat o'z papkangizga yozadi; `vault_lessons_add` — umumiy saboqlar fayli. "
        "Maxfiy qiymat (parol, token, API kalit) vault'ga yozilmaydi."
    ),
)


def resolve_path(relative: str) -> Path:
    """Vault ichidagi faylga xavfsiz yo'l. Tashqariga chiqish — ValueError."""
    text = str(relative or "").strip().replace("\\", "/")
    if not text:
        raise ValueError("`path` majburiy (masalan 04_finance/2026-11.md).")
    candidate = Path(text)
    if candidate.is_absolute() or text.startswith("/") or ".." in candidate.parts:
        raise ValueError(f"Yo'l vault ichida bo'lishi kerak, `..` va absolyut yo'l taqiqlangan: {relative}")
    target = (VAULT / candidate).resolve()
    if VAULT != target and VAULT not in target.parents:
        raise ValueError(f"Yo'l vault tashqarisiga chiqadi: {relative}")
    if target.suffix.lower() != ".md":
        raise ValueError("Faqat `.md` fayllar bilan ishlanadi.")
    return target


def _relative(path: Path) -> str:
    return path.resolve().relative_to(VAULT).as_posix()


def _check_scope(agent: str, relative: str) -> None:
    if relative == SHARED_LESSONS:
        return
    scopes = WRITE_SCOPES.get(agent)
    if scopes is None:
        raise PermissionError(f"`{agent}` uchun yozuv papkasi belgilanmagan (WRITE_SCOPES).")
    if not any(relative == scope or relative.startswith(scope + "/") for scope in scopes):
        allowed = ", ".join(scopes) or "yo'q (faqat o'qiydi)"
        raise PermissionError(f"`{agent}` faqat quyidagi papkaga yozadi: {allowed}. So'ralgan: {relative}")


def _check_secret(content: str) -> None:
    match = _SECRET_RE.search(content or "")
    if match:
        raise PermissionError(f"Matnda maxfiy qiymat naqshi topildi ({match.group(0)[:24]}…) — vault'ga yozilmadi.")


def _ensure_index(force: bool = False) -> dict:
    if not force and INDEX_PATH.exists():
        index = load_index(INDEX_PATH)
        newest = max((p.stat().st_mtime for p in VAULT.rglob("*.md")), default=0)
        built = INDEX_PATH.stat().st_mtime
        if built >= newest:
            return index
    index = build_index(VAULT)
    save_index(index, INDEX_PATH)
    return index


# --- tool'lar ----------------------------------------------------------------


@mcp.tool()
def vault_search(query: str = "", agent: str = "orchestrator", top_k: int = 5) -> dict:
    """Vault bo'yicha hybrid qidiruv (BM25 + hashed-vector).

    Args:
        query: Tabiiy til yoki aniq ID/summa ("qarzdorlik nazorati", "12 551").
        agent: Qidiruvchi agent nomi (audit uchun).
        top_k: Nechta chunk qaytariladi (1-10).
    """
    if not str(query or "").strip():
        return {"error": "`query` bo'sh", "status_code": 400, "message": "Qidiruv matni majburiy.", "endpoint": "vault", "details": None}
    index = _ensure_index()
    results = search(index, query, max(1, min(int(top_k), 10)))
    return {
        "error": None,
        "status_code": 200,
        "message": f"{len(results)} chunk topildi",
        "endpoint": "vault://search",
        "details": {
            "query": query,
            "agent": agent,
            "mode": index.get("mode"),
            "built_at": index.get("built_at"),
            "results": results,
        },
    }


@mcp.tool()
def vault_read(path: str = "") -> dict:
    """Vault ichidagi `.md` faylni o'qiydi.

    Args:
        path: Vault'ga nisbatan yo'l (`04_finance/2026-11.md`).
    """
    try:
        target = resolve_path(path)
    except ValueError as exc:
        return {"error": str(exc), "status_code": 400, "message": str(exc), "endpoint": "vault", "details": None}
    if not target.exists():
        return {"error": "topilmadi", "status_code": 404, "message": f"Fayl yo'q: {path}", "endpoint": "vault", "details": None}
    return {
        "error": None,
        "status_code": 200,
        "message": "ok",
        "endpoint": "vault://read",
        "details": {"path": _relative(target), "content": target.read_text(encoding="utf-8")},
    }


@mcp.tool()
def vault_append(path: str = "", content: str = "", agent: str = "orchestrator") -> dict:
    """Fayl oxiriga yozadi — faqat agentning o'z papkasiga.

    Args:
        path: Vault'ga nisbatan `.md` yo'l.
        content: Qo'shiladigan markdown.
        agent: Yozuvchi agent (WRITE_SCOPES bo'yicha tekshiriladi).
    """
    try:
        target = resolve_path(path)
        relative = _relative(target)
        _check_scope(agent, relative)
        _check_secret(content)
    except (ValueError, PermissionError) as exc:
        return {"error": str(exc), "status_code": 403, "message": str(exc), "endpoint": "vault", "details": None}
    if not str(content or "").strip():
        return {"error": "`content` bo'sh", "status_code": 400, "message": "Yozuv matni bo'sh.", "endpoint": "vault", "details": None}

    target.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with target.open("a", encoding="utf-8") as handle:
        handle.write(f"\n\n<!-- {agent} · {stamp} -->\n{content.rstrip()}\n")
    return {
        "error": None,
        "status_code": 200,
        "message": "yozildi",
        "endpoint": "vault://append",
        "details": {"path": relative, "agent": agent, "bytes": len(content.encode("utf-8"))},
    }


@mcp.tool()
def vault_lessons_add(title: str = "", lesson: str = "", agent: str = "auditor-security") -> dict:
    """`06_self_improve/lessons_learned.md` ga yangi saboq qo'shadi.

    Args:
        title: Qisqa nom ("oylik paid holatida yaratilgan").
        lesson: To'rt qismli yozuv (nima bo'ldi / sabab / qoida / holat).
        agent: Saboqni ochgan agent.
    """
    if not str(title or "").strip() or not str(lesson or "").strip():
        return {"error": "`title`/`lesson` bo'sh", "status_code": 400, "message": "Sarlavha va matn majburiy.", "endpoint": "vault", "details": None}
    try:
        _check_secret(lesson)
    except PermissionError as exc:
        return {"error": str(exc), "status_code": 403, "message": str(exc), "endpoint": "vault", "details": None}
    block = f"## {datetime.now(timezone.utc).date().isoformat()} — {title.strip()}\n\n{lesson.strip()}\n"
    return vault_append(SHARED_LESSONS, block, agent)


if __name__ == "__main__":
    mcp.run()
