#!/bin/sh
set -eu

HERMES_HOME=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
PYTHONPATH="$HERMES_HOME/hermes-agent"
MARS_MCP_PYTHON="$HERMES_HOME/mcp/mars-lms/.venv/bin/python"
export HERMES_HOME PYTHONPATH MARS_MCP_PYTHON

exec "$HERMES_HOME/runtime/venv/bin/python" -m hermes_cli.main "$@"
