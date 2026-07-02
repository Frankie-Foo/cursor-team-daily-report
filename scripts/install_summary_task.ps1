# 注册 Windows 计划任务：工作日 17:30 自动生成本地 Cursor 当日总结（按会话分类）
# 用法: powershell -ExecutionPolicy Bypass -File scripts/install_summary_task.ps1

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Runner = Join-Path $Root "run_cursor_summary_local.ps1"
$TaskName = "Cursor当日工作总结"

if (-not (Test-Path $Runner)) {
    throw "找不到 $Runner"
}

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`"" `
    -WorkingDirectory $Root

# 工作日 17:30（下午 5:30）
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
    -Description "汇总当天 Cursor 所有对话会话，分类写入 daily/<user>/ 本地 Markdown" `
    -Force | Out-Null

Write-Host "已注册计划任务: $TaskName"
Write-Host "时间: 工作日 17:30"
Write-Host "输出: $Root\daily\用户名\YYYY-MM-DD.md"
Write-Host ""
Write-Host '手动试跑: powershell -File run_cursor_summary_local.ps1'
