#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PY="$ROOT/runtime/venv/bin/python"
[ -x "$PY" ] || PY="$ROOT/runtime/venv/Scripts/python.exe"
[ -x "$PY" ] || { echo "Project runtime Python missing"; exit 1; }
exec "$PY" "$ROOT/skills/hermes_mars_dashboard/dashboard.py" "$@"
