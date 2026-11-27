"""`digital-org/mcp/servers.json` ni jonli Swagger (OpenAPI 3) bilan solishtiradi.

Maqsad: "to'qilgan endpoint = 0" da'vosini tekshiriladigan qilish. Registrdagi har bir
`METHOD /path` yozuvi backend spec'ida bor-yo'qligi shu skript bilan aniqlanadi.

Ishlatish::

    # produksiya spec'i bilan
    python digital-org/mcp/verify_registry.py \
        --swagger https://mars-backend-six.vercel.app/swagger.json \
        --report digital-org/mcp/registry_report.json

    # saqlangan nusxa bilan (tarmoqsiz)
    python digital-org/mcp/verify_registry.py --swagger swagger.json

Chiqish kodi: 0 — hammasi topildi, 1 — kamida bitta yozuv spec'da yo'q.

Eslatma: yo'l "shakli" bo'yicha solishtiriladi — `{id}` va `{groupId}` bir xil hisoblanadi,
chunki parametr nomi emas, marshrut tuzilishi muhim.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")
_ENTRY_RE = re.compile(
    r"^((?:GET|POST|PUT|PATCH|DELETE)(?:\s*/\s*(?:GET|POST|PUT|PATCH|DELETE))*)\s+(\S+)$",
    re.IGNORECASE,
)
_PARAM_RE = re.compile(r"\{[^}]+\}")


def normalize_path(path: str) -> str:
    """Parametr nomini birxillashtiradi: `/groups/{groupId}` -> `/groups/{}`."""
    clean = (path or "").split("?", 1)[0].strip()
    clean = _PARAM_RE.sub("{}", clean)
    return clean.rstrip("/") or "/"


def expand_entry(entry: str) -> list[tuple[str, str]]:
    """`POST/PATCH/DELETE /api/branch/groups` -> uchta (method, path) jufti."""
    text = re.sub(r"\s*\([^)]*\)\s*", " ", str(entry or "")).strip()
    match = _ENTRY_RE.match(text)
    if not match:
        return []
    methods = [part.strip().upper() for part in match.group(1).split("/")]
    path = match.group(2)
    return [(method, normalize_path(path)) for method in methods if method in METHODS]


def load_spec(source: str) -> dict:
    if source.startswith(("http://", "https://")):
        request = urllib.request.Request(source, headers={"Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - ochiq spec
            return json.load(response)
    return json.loads(Path(source).read_text(encoding="utf-8"))


def spec_operations(spec: dict) -> set[tuple[str, str]]:
    operations: set[tuple[str, str]] = set()
    for path, item in (spec.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for method in item:
            if method.upper() in METHODS:
                operations.add((method.upper(), normalize_path(path)))
    return operations


def load_registry(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def verify(registry: dict, spec: dict) -> dict:
    operations = spec_operations(spec)
    servers = []
    total = verified = 0
    for server in registry.get("servers") or []:
        entries = []
        missing = []
        seen: set[tuple[str, str]] = set()
        for raw in server.get("endpoints") or []:
            pairs = expand_entry(raw)
            if not pairs:
                missing.append({"entry": raw, "reason": "format o'qilmadi"})
                continue
            for method, path in pairs:
                seen.add((method, path))
        for method, path in sorted(seen):
            total += 1
            ok = (method, path) in operations
            verified += 1 if ok else 0
            entries.append({"method": method, "path": path, "verified": ok})
            if not ok:
                missing.append({"entry": f"{method} {path}", "reason": "spec'da yo'q"})
        servers.append(
            {
                "server": server.get("name"),
                "ops": len(seen),
                "verified": len(seen) - len([e for e in entries if not e["verified"]]),
                "missing": missing,
                "entries": entries,
            }
        )
    return {
        "spec": {
            "title": (spec.get("info") or {}).get("title"),
            "version": (spec.get("info") or {}).get("version"),
            "paths": len(spec.get("paths") or {}),
            "operations": len(operations),
        },
        "registry": {"servers": len(servers), "operations": total, "verified": verified, "missing": total - verified},
        "servers": servers,
    }


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="MCP registrni Swagger bilan solishtirish")
    parser.add_argument("--swagger", required=True, help="URL yoki lokal swagger.json")
    parser.add_argument(
        "--registry",
        default=str(Path(__file__).with_name("servers.json")),
        help="servers.json yo'li",
    )
    parser.add_argument("--report", help="JSON hisobotni shu faylga yozish")
    parser.add_argument("--show-all", action="store_true", help="har server uchun barcha yozuvlarni chiqarish")
    args = parser.parse_args(argv)

    report = verify(load_registry(args.registry), load_spec(args.swagger))
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    spec = report["spec"]
    stats = report["registry"]
    print(f"Spec: {spec['title']} v{spec['version']} — {spec['paths']} path, {spec['operations']} operation")
    print(f"Registr: {stats['servers']} server, {stats['operations']} operation — topildi {stats['verified']}, yo'q {stats['missing']}")
    for server in report["servers"]:
        print(f"\n[{server['server']}] {server['verified']}/{server['ops']}")
        if server["missing"]:
            for item in server["missing"]:
                print(f"  ✗ {item['entry']} — {item['reason']}")
        if args.show_all:
            for entry in server["entries"]:
                mark = "✓" if entry["verified"] else "✗"
                print(f"  {mark} {entry['method']} {entry['path']}")
    if args.report:
        print(f"\nHisobot: {args.report}")
    return 0 if stats["missing"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
