$ErrorActionPreference = "Stop"
# 注册 Windows 计划任务：工作日 17:30 自动 POST 统一日报
# 用法: powershell -ExecutionPolicy Bypass -File install_daily_task.ps1

$Root = $PSScriptRoot
$Runner = Join-Path $Root "run_daily.ps1"
$TaskName = "Cursor统一日报-自动POST"

if (-not (Test-Path $Runner)) {
    throw "找不到 $Runner"
}

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`"" `
    -WorkingDirectory $Root

$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday -At "17:30"

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Vertu+Vemory+Cursor 统一日报，POST 到团队 API" `
    -Force | Out-Null

Write-Host "已注册计划任务: $TaskName"
Write-Host "时间: 工作日 17:30"
Write-Host "命令: $Runner"
Write-Host ""
Write-Host "手动试跑: powershell -File run_daily.ps1"
