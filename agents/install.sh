#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/runtime/venv/bin/python"
[ -x "$PY" ] || PY="$ROOT/runtime/venv/Scripts/python.exe"
[ -x "$PY" ] || { echo "Project runtime Python missing"; exit 1; }
if [ "${1:-}" = "--check" ]; then
  exec "$PY" "$ROOT/agents/install.py" all --check
fi
exec "$PY" "$ROOT/agents/install.py" all --sync
