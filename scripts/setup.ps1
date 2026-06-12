$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "=== Cursor Team Daily Report Setup ==="

$EnvFile = Join-Path $Root ".env"
$EnvExample = Join-Path $Root ".env.example"
$UserFile = Join-Path $Root "config/user.json"
$UserExample = Join-Path $Root "config/user.example.json"

if (-not (Test-Path $EnvFile)) {
    Copy-Item $EnvExample $EnvFile
    Write-Host "[1/4] Created .env - ask Frank for DB_PASSWORD"
} else {
    Write-Host "[1/4] .env exists"
}

if (-not (Test-Path $UserFile)) {
    Copy-Item $UserExample $UserFile
    Write-Host "[2/4] Created config/user.json - edit username and cursor_workspace"
} else {
    Write-Host "[2/4] config/user.json exists"
}

Write-Host "[3/4] Installing Python packages..."
pip install -r (Join-Path $Root "requirements.txt")

Write-Host "[4/4] DB schema (safe to re-run)..."
python (Join-Path $Root "scripts/db_schema.py") --create-db

Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Edit config/user.json"
Write-Host "  2. Edit .env with DB password from Frank"
Write-Host "  3. powershell -File scripts/install_skill.ps1"
Write-Host "  4. python scripts/publish_daily.py --date today --git-push"
