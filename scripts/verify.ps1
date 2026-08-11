[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot

function Assert-Succeeded([string]$operation) {
    if ($LASTEXITCODE -ne 0) { throw "$operation failed with exit code $LASTEXITCODE." }
}

Push-Location (Join-Path $projectRoot 'backend')
try {
    & '.\.venv\Scripts\python.exe' -m pytest
    Assert-Succeeded 'Backend tests'
    & '.\.venv\Scripts\python.exe' -m alembic upgrade head
    Assert-Succeeded 'Database migration'
    & '.\.venv\Scripts\python.exe' -m alembic check
    Assert-Succeeded 'Migration consistency check'
}
finally {
    Pop-Location
}

Push-Location (Join-Path $projectRoot 'frontend')
try {
    pnpm lint
    Assert-Succeeded 'Frontend lint'
    pnpm build
    Assert-Succeeded 'Frontend production build'
}
finally {
    Pop-Location
}

$frontendRoot = Join-Path $projectRoot 'frontend'
if ($frontendRoot.Contains('#')) {
    $temporaryRoot = Join-Path ([IO.Path]::GetTempPath()) "gamedeck-frontend-tests-$PID"
    $resolvedTempParent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    $resolvedTemporaryRoot = [IO.Path]::GetFullPath($temporaryRoot)
    if (-not $resolvedTemporaryRoot.StartsWith($resolvedTempParent) -or
        -not (Split-Path $resolvedTemporaryRoot -Leaf).StartsWith('gamedeck-frontend-tests-')) {
        throw "Refusing unsafe temporary path: $resolvedTemporaryRoot"
    }
    if (Test-Path $resolvedTemporaryRoot) {
        throw "Temporary test path already exists: $resolvedTemporaryRoot"
    }
    New-Item -ItemType Directory -Path $resolvedTemporaryRoot | Out-Null
    try {
        robocopy $frontendRoot $resolvedTemporaryRoot /E /XD node_modules dist | Out-Null
        if ($LASTEXITCODE -gt 7) { throw "Frontend copy failed with exit code $LASTEXITCODE" }
        Push-Location $resolvedTemporaryRoot
        try {
            pnpm install --frozen-lockfile
            Assert-Succeeded 'Temporary frontend dependency installation'
            pnpm test
            Assert-Succeeded 'Frontend tests'
        }
        finally {
            Pop-Location
        }
    }
    finally {
        if (Test-Path $resolvedTemporaryRoot) {
            Remove-Item -LiteralPath $resolvedTemporaryRoot -Recurse -Force
        }
    }
}
else {
    Push-Location $frontendRoot
    try {
        pnpm test
        Assert-Succeeded 'Frontend tests'
    }
    finally { Pop-Location }
}

Write-Host 'All GameDeck checks passed.' -ForegroundColor Green
