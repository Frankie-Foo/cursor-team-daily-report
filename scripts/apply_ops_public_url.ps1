# Apply ops-provided fixed public API URL and rebuild colleague package. ASCII-only.
param(
    [Parameter(Mandatory = $true)]
    [string]$PublicUrl
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$url = $PublicUrl.Trim().TrimEnd("/")
if ($url -notmatch "^https://") {
    Write-Host "Public URL must start with https://" -ForegroundColor Red
    exit 1
}

python scripts/set_production_url.py --public-url $url

Write-Host ""
Write-Host "Updated .env REPORT_API_URL=$url" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Ask ops to proxy $url -> http://127.0.0.1:8080 (or your API server:8080)"
Write-Host "  2. Verify: curl $url/api/v1/health"
Write-Host "  3. Rebuild package:"
Write-Host "       powershell -File scripts/build_colleague_package.ps1"
Write-Host "       python scripts/export_member_credentials.py"
Write-Host "  4. Notify team to update REPORT_API_URL in .env"

powershell -File scripts/build_colleague_package.ps1
python scripts/export_member_credentials.py

Write-Host ""
Write-Host "Done. See config/member_credentials.md for per-person messages." -ForegroundColor Green
