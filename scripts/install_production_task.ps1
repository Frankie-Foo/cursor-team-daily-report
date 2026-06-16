# Register logon task for production API + tunnel stack. ASCII-only.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$script = Join-Path $Root "scripts\start_production_stack.ps1"
$name = "CursorTeamDailyReport-Production"

$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$script`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings `
    -Description "Cursor team daily report: API + public HTTPS tunnel" -Force | Out-Null

Write-Host "Registered scheduled task: $name" -ForegroundColor Green
Write-Host "Runs at logon. Ensure .env has REPORT_API_URL and CLOUDFLARE_TUNNEL_TOKEN (formal)." -ForegroundColor Yellow
