@echo off
setlocal
set "HERMES_HOME=%~dp0"
set "PYTHONPATH=%~dp0hermes-agent"
"%~dp0hermes-agent\.venv\Scripts\python.exe" -m hermes_cli.main %*
endlocal
