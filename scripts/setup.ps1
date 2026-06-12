$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "Cursor team daily report setup"

$EnvFile = Join-Path $Root ".env"
$EnvExample = Join-Path $Root ".env.example"
$UserFile = Join-Path $Root "config/user.json"
$UserExample = Join-Path $Root "config/user.example.json"

if (-not (Test-Path $EnvFile)) {
    Copy-Item $EnvExample $EnvFile
    Write-Host "Created .env - fill DB_PASSWORD and CURSOR_REPORT_USER"
}

if (-not (Test-Path $UserFile)) {
    Copy-Item $UserExample $UserFile
    Write-Host "Created config/user.json - fill username"
}

pip install -r (Join-Path $Root "requirements.txt")
python (Join-Path $Root "scripts/db_schema.py") --create-db

Write-Host "Done. Test: python scripts/publish_daily.py --date today --skip-db"
