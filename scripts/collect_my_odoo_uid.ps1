# Collect odoo user_id for the current vertu login (ASCII-only for PowerShell encoding)
$ErrorActionPreference = "Stop"
$vertuCli = Join-Path $env:APPDATA "npm\vertu-cli.cmd"
$vertu = Join-Path $env:APPDATA "npm\vertu.cmd"

Write-Host ""
Write-Host "=== Your Odoo user_id ===" -ForegroundColor Cyan
Write-Host ""

$json = $null
if (Test-Path $vertuCli) {
    try {
        $json = & $vertuCli hr +me 2>&1
        if ($LASTEXITCODE -ne 0) { $json = $null }
    } catch { $json = $null }
}
if (-not $json -and (Test-Path $vertu)) {
    $json = & $vertu odoo me 2>&1
}

if (-not $json) {
    Write-Host "Cannot read identity. Run: vertu login  OR  vertu-cli auth login --legacy-odoo-cli" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}

$obj = $json | ConvertFrom-Json
Write-Host "username (Vertu): $($obj.name)"
Write-Host "login:            $($obj.login)"
Write-Host "odoo_user_id:     $($obj.user_id)" -ForegroundColor Green
Write-Host "department:       $($obj.department_name)"
Write-Host ""
Write-Host "Send odoo_user_id to Frank for daily report setup." -ForegroundColor Yellow
Write-Host ""

Read-Host "Press Enter to close"
