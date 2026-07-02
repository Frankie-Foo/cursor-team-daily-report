# Push Gary/Henry (or all) tokens to remote API via admin endpoint + DB sync.
param(
    [string[]]$Users = @("Gary", "Henry")
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== Push tokens to server ===" -ForegroundColor Cyan

$userList = $Users -join " "
& python scripts/sync_tokens_to_db.py --users $userList.Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries)
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$py = @'
import json, os, sys
import requests
from pathlib import Path
sys.path.insert(0, "scripts")
from report_io import load_env
load_env()
root = Path(".")
all_tokens = json.loads((root / "config/api_tokens.json").read_text(encoding="utf-8"))["tokens"]
users = [u.strip() for u in sys.argv[1].split(",") if u.strip()] if len(sys.argv) > 1 and sys.argv[1] else []
selected = {u: all_tokens[u] for u in users if u in all_tokens} if users else all_tokens
base = os.getenv("REPORT_API_URL", "").rstrip("/")
frank = all_tokens.get("Frank", "")
if not base or not frank:
    raise SystemExit("Missing REPORT_API_URL or Frank token")
url = base + "/api/v1/admin/tokens/sync"
r = requests.post(url, headers={"Authorization": "Bearer " + frank}, json={"tokens": selected}, timeout=30)
print("HTTP", r.status_code)
print(r.text)
sys.exit(0 if r.status_code == 200 else 1)
'@

$userArg = ($Users -join ",")
python -c $py $userArg
if ($LASTEXITCODE -eq 0) {
    Write-Host "Remote API token sync OK" -ForegroundColor Green
    exit 0
}

Write-Host ""
Write-Host "Admin API not on server yet. Tokens synced to PostgreSQL api_tokens table." -ForegroundColor Yellow
Write-Host "Ask ops: git pull && docker compose up -d --build" -ForegroundColor Yellow
Write-Host "Or docker cp config/api_tokens.json cursor-team-daily-report-api:/app/config/api_tokens.json" -ForegroundColor Yellow
exit 1
