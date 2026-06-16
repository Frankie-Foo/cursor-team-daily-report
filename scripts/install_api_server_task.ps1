# Register Windows scheduled task: API starts at boot (SYSTEM) + at logon.
param(
    [switch]$StartNow
)
$ErrorActionPreference = "Stop"

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Admin)) {
    Write-Host "Run PowerShell as Administrator." -ForegroundColor Red
    exit 1
}

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$TaskName = "CursorTeamDailyReport-API-Server"
$daemonScript = Join-Path $Root "scripts\run_api_server_daemon.ps1"

if (-not (Test-Path (Join-Path $Root ".env"))) {
    Write-Host "Missing .env - copy from Frank before installing task." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $daemonScript)) {
    Write-Host "Missing: $daemonScript" -ForegroundColor Red
    exit 1
}

$pythonExe = (Get-Command python -ErrorAction Stop).Source
$configDir = Join-Path $Root "config"
New-Item -ItemType Directory -Force -Path $configDir | Out-Null
Set-Content -Path (Join-Path $configDir ".python_cmd.txt") -Value $pythonExe -Encoding ASCII
Write-Host "Saved python path: $pythonExe" -ForegroundColor Cyan

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$daemonScript`"" `
    -WorkingDirectory $Root

$triggerBoot = New-ScheduledTaskTrigger -AtStartup
$triggerLogon = New-ScheduledTaskTrigger -AtLogOn

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Days 365)

$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger @($triggerBoot, $triggerLogon) `
    -Settings $settings `
    -Principal $principal `
    -Description "Cursor team daily report FastAPI (uvicorn on port 8080)" `
    -Force | Out-Null

Write-Host "Registered scheduled task: $TaskName" -ForegroundColor Green
Write-Host "  Triggers: At system startup + At logon" -ForegroundColor Gray
Write-Host "  Run as:   SYSTEM" -ForegroundColor Gray
Write-Host "  Logs:     $Root\logs\api-server.log" -ForegroundColor Gray
Write-Host ""
Write-Host "Tip: run deploy_server.ps1 once as Admin so pip packages are system-wide." -ForegroundColor Yellow

if ($StartNow) {
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 4
    $port = "8080"
    Get-Content (Join-Path $Root ".env") | ForEach-Object {
        if ($_ -match '^\s*API_PORT\s*=\s*(.+)\s*$') { $port = $matches[1].Trim() }
    }
    try {
        $h = Invoke-WebRequest -Uri "http://127.0.0.1:${port}/api/v1/health" -UseBasicParsing -TimeoutSec 10
        Write-Host "Health OK: $($h.Content)" -ForegroundColor Green
    } catch {
        Write-Host "Health check failed - see logs\api-server.log" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Manage:" -ForegroundColor Cyan
Write-Host "  Start:   Start-ScheduledTask -TaskName $TaskName"
Write-Host "  Stop:    Stop-ScheduledTask -TaskName $TaskName"
Write-Host "  Remove:  powershell -File scripts\uninstall_api_server_task.ps1"
