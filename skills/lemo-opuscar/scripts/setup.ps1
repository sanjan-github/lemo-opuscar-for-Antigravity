# Lemo-Opuscar PowerShell helper: runs setup.sh through Git Bash
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$ErrorActionPreference = "Stop"

# Find Git Bash executable
$bash = $null
if (Get-Command bash.exe -ErrorAction SilentlyContinue) {
    $bash = (Get-Command bash.exe).Source
} elseif (Test-Path "$env:ProgramFiles\Git\bin\bash.exe") {
    $bash = "$env:ProgramFiles\Git\bin\bash.exe"
} elseif (Test-Path "${env:ProgramFiles(x86)}\Git\bin\bash.exe") {
    $bash = "${env:ProgramFiles(x86)}\Git\bin\bash.exe"
} elseif (Test-Path "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe") {
    $bash = "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe"
}

if (-not $bash) {
    Write-Error "Git Bash (bash.exe) not found. Please install Git for Windows."
    exit 1
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$shScript = Join-Path $scriptDir "setup.sh"

# Convert script path to forward slashes for bash
$shScriptPosix = $shScript.Replace('\', '/')

& $bash $shScriptPosix @Arguments
exit $LASTEXITCODE
