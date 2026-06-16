# Remove API scheduled task.
$ErrorActionPreference = "Stop"
$TaskName = "CursorTeamDailyReport-API-Server"

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) {
    Write-Host "Task not found: $TaskName" -ForegroundColor Yellow
    exit 0
}

Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host "Removed scheduled task: $TaskName" -ForegroundColor Green
