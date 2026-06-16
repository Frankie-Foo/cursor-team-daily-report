# Register scheduled task: API + Cloudflare tunnel at logon. ASCII-only.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$script = Join-Path $Root "scripts\run_api_public.ps1"
$taskName = "CursorTeamDailyReport-API-Public"

if (-not (Test-Path $script)) {
    Write-Host "Missing: $script" -ForegroundColor Red
    exit 1
}

$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$script`""

$trigger = New-ScheduledTaskTrigger -AtLogOn

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
    -Description "Cursor team daily report API + public tunnel" -Force | Out-Null

Write-Host "Registered: $taskName" -ForegroundColor Green
Write-Host "Runs at logon. Ensure config/cloudflare-tunnel.yml and .env REPORT_API_URL are set." -ForegroundColor Yellow
