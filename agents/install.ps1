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

$python = "C:\Users\user\AppData\Local\Programs\Python\Python314\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

$pyScript = Join-Path $ScriptDir "install.py"
if ($Check) {
    & $python $pyScript --check
} else {
    & $python $pyScript
}
