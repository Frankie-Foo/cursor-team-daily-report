# Show API scheduled task and local health check.
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$TaskName = "CursorTeamDailyReport-API-Server"
$port = "8080"
$envFile = Join-Path $Root ".env"

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*API_PORT\s*=\s*(.+)\s*$') { $port = $matches[1].Trim() }
    }
}

Write-Host "=== Task: $TaskName ===" -ForegroundColor Cyan
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($task) {
    $info = Get-ScheduledTaskInfo -TaskName $TaskName
    Write-Host "State:       $($task.State)"
    Write-Host "Last run:    $($info.LastRunTime)"
    Write-Host "Last result: $($info.LastTaskResult)"
    Write-Host "Next run:    $($info.NextRunTime)"
} else {
    Write-Host "Not registered. Run scripts/install_api_server_task.ps1 as Admin." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Health http://127.0.0.1:${port}/api/v1/health ===" -ForegroundColor Cyan
try {
    $h = Invoke-WebRequest -Uri "http://127.0.0.1:${port}/api/v1/health" -UseBasicParsing -TimeoutSec 5
    Write-Host $h.Content -ForegroundColor Green
} catch {
    Write-Host "Not responding: $($_.Exception.Message)" -ForegroundColor Red
}

$logFile = Join-Path $Root "logs\api-server.log"
if (Test-Path $logFile) {
    Write-Host ""
    Write-Host "=== Last 8 log lines ===" -ForegroundColor Cyan
    Get-Content $logFile -Tail 8
}
