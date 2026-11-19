@echo off
setlocal
set "HERMES_HOME=%~dp0"
set "PYTHONPATH=%~dp0hermes-agent"
set "MARS_MCP_PYTHON=%~dp0mcp\mars-lms\.venv\Scripts\python.exe"
"%~dp0runtime\venv\Scripts\python.exe" -m hermes_cli.main %*
endlocal
