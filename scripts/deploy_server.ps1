# One-shot server deploy checklist (Windows). Run ON the server after git clone.
param(
    [string]$PublicUrl = "https://global-pdca.vertu.cn"
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== Cursor Team Daily Report - Server Deploy ===" -ForegroundColor Cyan

if (-not (Test-Path (Join-Path $Root ".env"))) {
    Copy-Item (Join-Path $Root ".env.example") (Join-Path $Root ".env")
    Write-Host "Created .env from example - EDIT DB_PASSWORD and REPORT_API_URL" -ForegroundColor Yellow
}

if (-not (Test-Path (Join-Path $Root "config\api_tokens.json"))) {
    Write-Host "Missing config/api_tokens.json - copy from your laptop" -ForegroundColor Red
    exit 1
}

Write-Host "[1/5] pip install..." -ForegroundColor Cyan
python -m pip install -r requirements.txt

Write-Host "[2/5] set public URL..." -ForegroundColor Cyan
python scripts/set_production_url.py --public-url $PublicUrl.TrimEnd("/")

Write-Host "[3/5] DB schema..." -ForegroundColor Cyan
python scripts/db_schema.py --create-db 2>&1 | Out-Host

Write-Host "[4/5] health check (local)..." -ForegroundColor Cyan
$port = "8080"
if (Test-Path (Join-Path $Root ".env")) {
    Get-Content (Join-Path $Root ".env") | ForEach-Object {
        if ($_ -match '^\s*API_PORT\s*=\s*(.+)\s*$') { $port = $matches[1].Trim() }
    }
}

$job = Start-Job -ScriptBlock {
    param($Root, $port)
    Set-Location $Root
    python -m uvicorn api.server:app --host 127.0.0.1 --port $port
} -ArgumentList $Root, $port
Start-Sleep -Seconds 4
try {
    $h = Invoke-WebRequest -Uri "http://127.0.0.1:${port}/api/v1/health" -UseBasicParsing -TimeoutSec 10
    Write-Host "Local API OK: $($h.Content)" -ForegroundColor Green
} catch {
    Write-Host "Local API failed: $($_.Exception.Message)" -ForegroundColor Red
}
Stop-Job $job -ErrorAction SilentlyContinue
Remove-Job $job -Force -ErrorAction SilentlyContinue

Write-Host "[5/5] rebuild colleague package..." -ForegroundColor Cyan
powershell -File scripts/build_colleague_package.ps1
python scripts/export_member_credentials.py

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Green
Write-Host "1. Ask ops: proxy $PublicUrl -> http://127.0.0.1:${port}"
Write-Host "2. Register auto-start (recommended):" -ForegroundColor Cyan
Write-Host "   powershell -File scripts/install_api_server_task.ps1 -StartNow"
Write-Host "   Or manual: powershell -File scripts/run_api_server.ps1"
Write-Host "3. Verify: curl ${PublicUrl}/api/v1/health"
Write-Host "4. Send zip + member_credentials.md to team"
