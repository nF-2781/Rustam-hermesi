@echo off
setlocal
set "HERMES_HOME=%~dp0"
set "PYTHONPATH=%~dp0hermes-agent"
"%~dp0runtime\venv\Scripts\python.exe" -m hermes_cli.main %*
endlocal
