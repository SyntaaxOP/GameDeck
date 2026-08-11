[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $projectRoot 'backend'
$target = 'x86_64-pc-windows-msvc'
$output = Join-Path $projectRoot 'src-tauri\binaries'
New-Item -ItemType Directory -Force -Path $output | Out-Null
Push-Location $backend
try {
    & '.\.venv\Scripts\python.exe' -m PyInstaller --noconfirm --clean --onefile --name "gamedeck-api-$target" --paths src --add-data "alembic.ini;." --add-data "migrations;migrations" --collect-all gamedeck src\gamedeck\sidecar.py --distpath $output
    if ($LASTEXITCODE -ne 0) { throw "Sidecar build failed with exit code $LASTEXITCODE." }
}
finally { Pop-Location }
