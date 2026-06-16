# Vertu CLI interactive login (account + password + optional service URL)
# ASCII-only to avoid PowerShell encoding issues on Windows.
$ErrorActionPreference = "Stop"
$vertuCli = Join-Path $env:APPDATA "npm\vertu-cli.cmd"

if (-not (Test-Path $vertuCli)) {
    Write-Host "vertu-cli not found. Run: npm install -g vertu-cli@latest" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}

Write-Host ""
Write-Host "=== Vertu CLI Login ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "If you see ENOTFOUND vps-service.vertu.cn:" -ForegroundColor Yellow
Write-Host "  DNS cannot resolve vps-service. Try company VPN or ask IT for the service URL." -ForegroundColor Yellow
Write-Host ""
Write-Host "Legacy vertu (admin.vertu.cn) may still work: vertu whoami" -ForegroundColor DarkGray
Write-Host ""

$serviceUrl = Read-Host "Service URL [Enter = https://vps-service.vertu.cn]"
if ([string]::IsNullOrWhiteSpace($serviceUrl)) {
    $serviceUrl = "https://vps-service.vertu.cn"
}

& $vertuCli auth login --service-url $serviceUrl --legacy-odoo-cli

Write-Host ""
Read-Host "Press Enter to close"
