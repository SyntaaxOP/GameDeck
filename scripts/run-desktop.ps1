[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot

if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    throw 'Rust is required for native desktop development. Install the Tauri Windows prerequisites first.'
}

Push-Location (Join-Path $projectRoot 'frontend')
try {
    pnpm.cmd build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed with exit code $LASTEXITCODE." }
}
finally {
    Pop-Location
}

& (Join-Path $PSScriptRoot 'build-sidecar.ps1')
if ($LASTEXITCODE -ne 0) { throw "Backend sidecar build failed with exit code $LASTEXITCODE." }

cargo run --manifest-path (Join-Path $projectRoot 'src-tauri\Cargo.toml')
if ($LASTEXITCODE -ne 0) { throw "Tauri desktop startup failed with exit code $LASTEXITCODE." }
