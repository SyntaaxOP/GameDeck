[CmdletBinding()]
param(
    [string]$At,
    [string]$DatabaseUrl
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$arguments = @('-m', 'gamedeck.demo')
if ($At) { $arguments += @('--at', $At) }
if ($DatabaseUrl) { $arguments += @('--database-url', $DatabaseUrl) }

Push-Location (Join-Path $projectRoot 'backend')
try {
    if (-not (Test-Path '.venv\Scripts\python.exe')) {
        throw 'Backend environment not found. Run .\scripts\setup.ps1 first.'
    }
    & '.\.venv\Scripts\python.exe' @arguments
    if ($LASTEXITCODE -ne 0) { throw "Demo seed failed with exit code $LASTEXITCODE." }
}
finally {
    Pop-Location
}
