# PowerShell script: Mars C-level and sub-agent profiles installer
# Usage:
#   .\agents\install.ps1
#   .\agents\install.ps1 -Check

param(
    [switch]$Check
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir

$python = Join-Path $Root "runtime\venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) { throw "Project Python not found: $python" }

$pyScript = Join-Path $ScriptDir "install.py"
if ($Check) {
    & $python $pyScript cfo --check
} else {
    & $python $pyScript cfo
}
exit $LASTEXITCODE
