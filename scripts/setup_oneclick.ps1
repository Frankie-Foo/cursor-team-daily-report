# One-click colleague setup: deps + config + skill + API test + schedule.
param(
    [string]$CursorWorkspace = "",
    [switch]$SkipTask,
    [switch]$SkipDryRun
)
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

function Write-Step($n, $total, $msg) {
    Write-Host "[$n/$total] $msg" -ForegroundColor Cyan
}

function Resolve-Python {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $cmd) {
        throw "未找到 Python。请先安装 Python 3.10+ 并勾选 Add to PATH。"
    }
    return $cmd.Source
}

function Load-Json($path) {
    if (-not (Test-Path $path)) { return $null }
    return Get-Content $path -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Test-VertuReady {
    try {
        $null = & python -c @"
import sys
sys.path.insert(0, r'$Root\scripts')
from vertu_client import fetch_vertu_daily_summary
print('ok')
"@ 2>$null
        return $true
    } catch {
        return $false
    }
}

Write-Host ""
Write-Host "=== Cursor 统一日报 · 一键安装 ===" -ForegroundColor Green
Write-Host "目录: $Root"
Write-Host ""

$credPath = Join-Path $Root "config\setup.credentials.json"
$creds = Load-Json $credPath
if (-not $creds) {
    Write-Host "缺少个人配置 config/setup.credentials.json" -ForegroundColor Red
    Write-Host "请向 Frank 索取「个人安装包」，不要下通用 zip。" -ForegroundColor Yellow
    Read-Host "按 Enter 退出"
    exit 1
}

$python = Resolve-Python
$total = 8

Write-Step 1 $total "安装 Python 依赖..."
& $python -m pip install -q -r (Join-Path $Root "requirements.txt")

Write-Step 2 $total "写入 .env 与 user.json..."
$envLines = @(
    "REPORT_API_URL=$($creds.report_api_url.TrimEnd('/'))",
    "REPORT_API_TOKEN=$($creds.report_api_token)",
    "CURSOR_REPORT_USER=$($creds.username)"
)
Set-Content -Path (Join-Path $Root ".env") -Value ($envLines -join "`n") -Encoding UTF8

$workspace = $CursorWorkspace.Trim()
if (-not $workspace -and $creds.cursor_workspace) {
    $workspace = [string]$creds.cursor_workspace
}
while (-not $workspace) {
    Write-Host ""
    Write-Host "请输入你日常用 Cursor 打开的项目文件夹路径（不是本日报文件夹）" -ForegroundColor Yellow
    Write-Host "示例: D:/经销商PDCA  或  D:/my-project" -ForegroundColor DarkGray
    $workspace = (Read-Host "cursor_workspace").Trim()
}
if (-not (Test-Path $workspace)) {
    Write-Host "警告: 路径不存在，仍将写入配置，请稍后改 config/user.json" -ForegroundColor Yellow
}

$userObj = @{
    username       = [string]$creds.username
    display_name   = [string]$creds.display_name
    odoo_user_id   = [int]$creds.odoo_user_id
    timezone       = "Asia/Shanghai"
    cursor_workspace = ($workspace -replace '\\', '/')
}
New-Item -ItemType Directory -Force -Path (Join-Path $Root "config") | Out-Null
$userObj | ConvertTo-Json | Set-Content -Path (Join-Path $Root "config\user.json") -Encoding UTF8

Write-Step 3 $total "安装 Cursor Skill..."
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root "install_skill.ps1")

Write-Step 4 $total "检查 API 连通性..."
$testScript = Join-Path $Root "scripts\test_api_connection.ps1"
if (Test-Path $testScript) {
    try {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $testScript
    } catch {
        Write-Host "API 暂不可达（可能运维还在部署）。Skill 已装好，API 通后再试 run_daily.ps1" -ForegroundColor Yellow
    }
} else {
    Write-Host "跳过 API 测试（脚本缺失）" -ForegroundColor Yellow
}

Write-Step 5 $total "检查 Vertu CLI..."
$vertuCmd = Get-Command vertu -ErrorAction SilentlyContinue
if (-not $vertuCmd) {
    $vertuCmd = Get-Command "$env:APPDATA\npm\vertu.cmd" -ErrorAction SilentlyContinue
}
if (-not $vertuCmd) {
    Write-Host "未安装 vertu CLI。请运行: npm install -g @vertu-tech/vps-cli" -ForegroundColor Yellow
    Write-Host "安装后执行: vertu login" -ForegroundColor Yellow
} else {
    try {
        & $vertuCmd.Source whoami 2>&1 | Out-Host
    } catch {
        Write-Host "vertu 未登录。请运行: vertu login" -ForegroundColor Yellow
    }
}

if (-not $SkipDryRun) {
    Write-Step 6 $total "试跑日报（dry-run，不提交）..."
    Set-Location $Root
    try {
        & $python (Join-Path $Root "scripts\build_unified_daily.py") --date today --dry-run 2>&1 | Select-Object -Last 8 | Out-Host
    } catch {
        Write-Host "试跑失败（常见原因: vertu 未登录）。登录后运行: powershell -File run_daily.ps1" -ForegroundColor Yellow
    }
} else {
    Write-Step 6 $total "跳过试跑"
}

if (-not $SkipTask) {
    Write-Step 7 $total "注册工作日 17:30 自动 POST..."
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root "install_daily_task.ps1")
} else {
    Write-Step 7 $total "跳过计划任务"
}

$installMcp = Join-Path $Root "mcp\install_mcp.ps1"
if (Test-Path $installMcp) {
    Write-Step 8 $total "安装 Cursor MCP（在 Cursor 里一句话发日报）..."
    & powershell -NoProfile -ExecutionPolicy Bypass -File $installMcp
} else {
    Write-Step 8 $total "跳过 MCP 安装（包内无 mcp 目录）"
}

Write-Host ""
Write-Host "=== 安装完成 ===" -ForegroundColor Green
Write-Host "用户: $($creds.username) / $($creds.display_name)"
Write-Host "手动发日报: powershell -File run_daily.ps1"
Write-Host "在 Cursor 里发日报: 直接说「总结我今天在 Cursor 里的工作并提交日报」"
Write-Host "定时: 工作日 17:30 自动 POST（已注册 Windows 计划任务）"
Write-Host "Skill 目录: $env:USERPROFILE\.cursor\skills\cursor-daily-report"
Write-Host ""
Write-Host "注意: 请重启 Cursor 让 MCP 生效。" -ForegroundColor Yellow
Write-Host ""
Read-Host "按 Enter 关闭"
