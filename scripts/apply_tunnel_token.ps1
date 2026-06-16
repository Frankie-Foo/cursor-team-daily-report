# Paste Cloudflare Tunnel Token into .env and restart stack. ASCII-only.
param(
    [Parameter(Mandatory = $true)]
    [string]$PublicUrl,
    [Parameter(Mandatory = $true)]
    [string]$TunnelToken
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
python scripts/set_production_url.py --public-url $PublicUrl --tunnel-token $TunnelToken
Write-Host ""
Write-Host "Updated .env. Restart stack:" -ForegroundColor Green
Write-Host "  powershell -File scripts/start_production_stack.ps1" -ForegroundColor Cyan
Write-Host "Then rebuild package:" -ForegroundColor Green
Write-Host "  powershell -File scripts/build_colleague_package.ps1" -ForegroundColor Cyan
Write-Host "  python scripts/export_member_credentials.py" -ForegroundColor Cyan
