"""Obsidian vault uchun RAG indeksatori — tashqi embedding modelisiz.

Nima qiladi
-----------
1. Vault'dagi `.md` fayllarni YAML frontmatter bilan o'qiydi (`pii: none` shart).
2. `##` sarlavhalari bo'yicha chunk'laydi (200–400 token atrofi).
3. Har chunk uchun ikkita ko'rinish yasaydi:
   - **BM25** uchun term-frequency lug'ati (aniq ID, guruh nomi, summa uchun);
   - **hashing-vector** (256 o'lchov, blake2b bilan belgilanadi) — ma'no o'rniga
     so'z birgaligi; tashqi API, kalit va internet kerak emas.
4. Qidiruvda ikkala ball normallashtirilib qo'shiladi (hybrid, 50/50).

Bu "vektor" haqiqiy embedding emas — bu **hashed bag-of-words**. Shuning uchun
natijada `mode: "hashed-bow"` yoziladi; xohlasa, keyinchalik `--embedding-url`
bilan haqiqiy modelga almashtiriladi (interfeys shu faylda).

CLI
---
    python indexer.py build  --vault digital-org/memory/vault --out .index/vault.json
    python indexer.py search "qarzdorlik nazorati" --index .index/vault.json --top 5
    python indexer.py stats  --index .index/vault.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

INDEX_VERSION = 1
VECTOR_DIM = 256
CHUNK_WORDS = 320
BM25_K1 = 1.5
BM25_B = 0.75
HYBRID_BM25_WEIGHT = 0.5

_WORD_RE = re.compile(r"[0-9a-zA-Zʻʼ'‘’_]+", re.UNICODE)
_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


# --- frontmatter -------------------------------------------------------------


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """`---` bilan o'ralgan oddiy YAML'ni o'qiydi (kalit: qiymat)."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    meta: dict[str, Any] = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip().strip('"').strip("'")
        meta[key.strip()] = None if value.lower() in {"null", "~", ""} else value
    return meta, text[match.end():]


# --- tokenlash ---------------------------------------------------------------


def tokenize(text: str) -> list[str]:
    return [word.lower() for word in _WORD_RE.findall(text or "") if len(word) > 1 or word.isdigit()]


def term_frequencies(tokens: Iterable[str]) -> dict[str, int]:
    tf: dict[str, int] = {}
    for token in tokens:
        tf[token] = tf.get(token, 0) + 1
    return tf


def hashed_vector(tf: dict[str, int], idf: dict[str, float], dim: int = VECTOR_DIM) -> list[float]:
    """Hashing trick: har so'z belgilangan o'lchovga tushadi, ishora ham hash'dan."""
    vector = [0.0] * dim
    for token, count in tf.items():
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % dim
        sign = 1.0 if digest[4] & 1 else -1.0
        weight = (1.0 + math.log(count)) * idf.get(token, 1.0)
        vector[index] += sign * weight
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [round(value / norm, 6) for value in vector]


# --- chunking ----------------------------------------------------------------


def chunk_markdown(text: str, path: str, *, max_words: int = CHUNK_WORDS) -> list[dict]:
    """`##` bo'yicha bo'ladi; juda uzun bo'lakni `max_words` da kesadi."""
    sections: list[tuple[str, list[str]]] = []
    heading = Path(path).stem
    buffer: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            sections.append((heading, buffer))
            heading, buffer = line[3:].strip(), []
        else:
            buffer.append(line)
    sections.append((heading, buffer))

    chunks: list[dict] = []
    for heading, lines in sections:
        body = "\n".join(lines).strip()
        if not body and heading == Path(path).stem:
            continue
        words = body.split()
        if len(words) <= max_words:
            parts = [body]
        else:
            parts = [" ".join(words[i: i + max_words]) for i in range(0, len(words), max_words)]
        for index, part in enumerate(parts):
            chunks.append(
                {
                    "path": path,
                    "heading": heading if len(parts) == 1 else f"{heading} ({index + 1})",
                    "text": f"## {heading}\n\n{part}".strip(),
                }
            )
    return chunks


# --- indeks qurish -----------------------------------------------------------


def iter_markdown(vault: Path) -> Iterable[Path]:
    for path in sorted(vault.rglob("*.md")):
        if any(part.startswith(".") for part in path.relative_to(vault).parts):
            continue
        yield path


def build_index(vault: str | Path, *, require_pii_none: bool = True) -> dict:
    """Vault'dan indeks yasaydi. `pii: none` bo'lmagan fayl indeksga tushmaydi."""
    vault_path = Path(vault).resolve()
    if not vault_path.is_dir():
        raise ValueError(f"Vault papkasi topilmadi: {vault_path}")

    raw_chunks: list[dict] = []
    skipped: list[dict] = []
    for file_path in iter_markdown(vault_path):
        relative = file_path.relative_to(vault_path).as_posix()
        try:
            text = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            skipped.append({"path": relative, "reason": f"o'qib bo'lmadi: {exc}"})
            continue
        meta, body = parse_frontmatter(text)
        pii = str(meta.get("pii") or "").strip().lower()
        if require_pii_none and pii != "none":
            skipped.append({"path": relative, "reason": f"pii={pii or 'yoʻq'} (indeksga faqat pii: none)"})
            continue
        for chunk in chunk_markdown(body, relative):
            chunk.update({"pii": pii or "none", "agent": meta.get("agent"), "period": meta.get("period")})
            raw_chunks.append(chunk)

    if not raw_chunks:
        return {
            "version": INDEX_VERSION,
            "mode": "hashed-bow",
            "dim": VECTOR_DIM,
            "vault": vault_path.as_posix(),
            "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "documents": 0,
            "chunks": [],
            "skipped": skipped,
        }

    # idf butun korpus bo'yicha
    df: dict[str, int] = {}
    for chunk in raw_chunks:
        chunk["tf"] = term_frequencies(tokenize(chunk["text"]))
        chunk["length"] = sum(chunk["tf"].values())
        for token in chunk["tf"]:
            df[token] = df.get(token, 0) + 1
    total = len(raw_chunks)
    idf = {token: math.log(1 + (total - count + 0.5) / (count + 0.5)) for token, count in df.items()}

    for chunk in raw_chunks:
        chunk["vector"] = hashed_vector(chunk["tf"], idf)

    return {
        "version": INDEX_VERSION,
        "mode": "hashed-bow",
        "dim": VECTOR_DIM,
        "vault": vault_path.as_posix(),
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "documents": len({chunk["path"] for chunk in raw_chunks}),
        "avg_length": round(sum(chunk["length"] for chunk in raw_chunks) / total, 2),
        "chunks": raw_chunks,
        "skipped": skipped,
    }


# --- qidiruv -----------------------------------------------------------------


def _bm25_scores(index: dict, query_tokens: list[str]) -> dict[int, float]:
    chunks = index["chunks"]
    total = len(chunks) or 1
    avg_length = index.get("avg_length") or (sum(c["length"] for c in chunks) / total if chunks else 0) or 1
    df: dict[str, int] = {}
    for chunk in chunks:
        for token in chunk["tf"]:
            df[token] = df.get(token, 0) + 1
    scores: dict[int, float] = {}
    for position, chunk in enumerate(chunks):
        score = 0.0
        for token in query_tokens:
            freq = chunk["tf"].get(token, 0)
            if not freq:
                continue
            idf = math.log(1 + (total - df.get(token, 0) + 0.5) / (df.get(token, 0) + 0.5))
            denominator = freq + BM25_K1 * (1 - BM25_B + BM25_B * chunk["length"] / avg_length)
            score += idf * freq * (BM25_K1 + 1) / denominator
        if score:
            scores[position] = score
    return scores


def _cosine_scores(index: dict, query_tokens: list[str]) -> dict[int, float]:
    chunks = index["chunks"]
    df: dict[str, int] = {}
    for chunk in chunks:
        for token in chunk["tf"]:
            df[token] = df.get(token, 0) + 1
    total = len(chunks) or 1
    idf = {token: math.log(1 + (total - count + 0.5) / (count + 0.5)) for token, count in df.items()}
    query_vector = hashed_vector(term_frequencies(query_tokens), idf, index.get("dim", VECTOR_DIM))
    scores: dict[int, float] = {}
    for position, chunk in enumerate(chunks):
        score = sum(a * b for a, b in zip(query_vector, chunk["vector"]))
        if score > 0:
            scores[position] = score
    return scores


def _normalize(scores: dict[int, float]) -> dict[int, float]:
    if not scores:
        return {}
    top = max(scores.values()) or 1.0
    return {key: value / top for key, value in scores.items()}


def search(index: dict, query: str, top_k: int = 5) -> list[dict]:
    """Hybrid qidiruv: BM25 (0.5) + hashed-vector (0.5), normallashtirilgan."""
    tokens = tokenize(query)
    if not tokens or not index.get("chunks"):
        return []
    bm25 = _normalize(_bm25_scores(index, tokens))
    cosine = _normalize(_cosine_scores(index, tokens))
    combined: dict[int, float] = {}
    for position in set(bm25) | set(cosine):
        combined[position] = (
            HYBRID_BM25_WEIGHT * bm25.get(position, 0.0)
            + (1 - HYBRID_BM25_WEIGHT) * cosine.get(position, 0.0)
        )
    ranked = sorted(combined.items(), key=lambda item: -item[1])[: max(1, int(top_k))]
    results = []
    for position, score in ranked:
        chunk = index["chunks"][position]
        results.append(
            {
                "path": chunk["path"],
                "heading": chunk["heading"],
                "text": chunk["text"][:1200],
                "score": round(score, 4),
                "bm25": round(bm25.get(position, 0.0), 4),
                "vector": round(cosine.get(position, 0.0), 4),
                "pii": chunk.get("pii"),
            }
        )
    return results


# --- fayl operatsiyalari -----------------------------------------------------


def save_index(index: dict, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    return target


def load_index(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


# --- CLI ---------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="indexer", description="Obsidian vault RAG indeksatori")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="indeksni qurish")
    build.add_argument("--vault", required=True)
    build.add_argument("--out", required=True)
    build.add_argument("--allow-unknown-pii", action="store_true", help="pii: none bo'lmasa ham indeksga oladi (tavsiya etilmaydi)")

    query = sub.add_parser("search", help="indeksdan qidirish")
    query.add_argument("text")
    query.add_argument("--index", required=True)
    query.add_argument("--top", type=int, default=5)

    stats = sub.add_parser("stats", help="indeks haqida qisqa ma'lumot")
    stats.add_argument("--index", required=True)

    args = parser.parse_args(argv)

    if args.command == "build":
        index = build_index(args.vault, require_pii_none=not args.allow_unknown_pii)
        target = save_index(index, args.out)
        print(f"indeks: {target} · hujjat: {index['documents']} · chunk: {len(index['chunks'])} · o'tkazib yuborildi: {len(index['skipped'])}")
        return 0

    index = load_index(args.index)
    if args.command == "stats":
        print(json.dumps({key: index.get(key) for key in ("version", "mode", "dim", "vault", "built_at", "documents", "avg_length")} | {"chunks": len(index.get("chunks") or []), "skipped": len(index.get("skipped") or [])}, ensure_ascii=False, indent=2))
        return 0

    results = search(index, args.text, args.top)
    if not results:
        print("natija yo'q")
        return 0
    for item in results:
        print(f"[{item['score']}] {item['path']} — {item['heading']}")
        print("   " + " ".join(item["text"].split())[:300])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
