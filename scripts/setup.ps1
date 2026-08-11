[CmdletBinding()]
param(
    [switch]$SkipFrontend
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot

function Assert-Succeeded([string]$operation) {
    if ($LASTEXITCODE -ne 0) { throw "$operation failed with exit code $LASTEXITCODE." }
}

Push-Location (Join-Path $projectRoot 'backend')
try {
    if (-not (Test-Path '.venv\Scripts\python.exe')) {
        py -3.12 -m venv .venv
        Assert-Succeeded 'Python environment creation'
    }
    & '.\.venv\Scripts\python.exe' -m pip install -e '.[dev,desktop]'
    Assert-Succeeded 'Backend dependency installation'
    & '.\.venv\Scripts\python.exe' -m alembic upgrade head
    Assert-Succeeded 'Database migration'
}
finally {
    Pop-Location
}

if (-not $SkipFrontend) {
    Push-Location (Join-Path $projectRoot 'frontend')
    try {
        pnpm install --frozen-lockfile
        Assert-Succeeded 'Frontend dependency installation'
    }
    finally {
        Pop-Location
    }
}

Write-Host 'GameDeck setup is complete.' -ForegroundColor Green
Write-Host 'Run .\scripts\seed-demo.ps1 for sample data, then follow the README to start both services.'
