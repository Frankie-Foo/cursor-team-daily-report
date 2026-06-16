# Build offline server deploy zip (no git clone required on server).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$OutDir = Join-Path $Root "package\server\cursor-team-daily-report"
$ZipPath = Join-Path $Root "package\server\cursor-team-daily-report-server.zip"

$RequiredSecrets = @(
    ".env",
    "config\api_tokens.json",
    "config\odoo_user_ids.json"
)

foreach ($rel in $RequiredSecrets) {
    $full = Join-Path $Root $rel
    if (-not (Test-Path $full)) {
        Write-Host "Missing required file: $rel" -ForegroundColor Red
        Write-Host "Create it on your laptop before packing for ops." -ForegroundColor Yellow
        exit 1
    }
}

if (Test-Path $OutDir) { Remove-Item $OutDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path "$OutDir\api", "$OutDir\scripts", "$OutDir\config" | Out-Null

Copy-Item (Join-Path $Root "api\*") (Join-Path $OutDir "api\") -Recurse -Force
Copy-Item (Join-Path $Root "requirements.txt") (Join-Path $OutDir "requirements.txt") -Force
Copy-Item (Join-Path $Root ".env.example") (Join-Path $OutDir ".env.example") -Force
Copy-Item (Join-Path $Root ".env") (Join-Path $OutDir ".env") -Force

$Scripts = @(
    "deploy_server.ps1",
    "deploy_server.sh",
    "run_api_server.ps1",
    "run_api_server_daemon.ps1",
    "install_api_server_task.ps1",
    "uninstall_api_server_task.ps1",
    "status_api_server_task.ps1",
    "db_schema.py",
    "set_production_url.py",
    "install_production_task.ps1"
)
foreach ($name in $Scripts) {
    $src = Join-Path $Root "scripts\$name"
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $OutDir "scripts\$name") -Force
    }
}

$ConfigFiles = @(
    "api_tokens.json",
    "odoo_user_ids.json",
    "org.json",
    "team.json",
    "nginx-global-pdca.example.conf"
)
foreach ($name in $ConfigFiles) {
    $src = Join-Path $Root "config\$name"
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $OutDir "config\$name") -Force
    }
}

$opsReadme = @"
Cursor Team Daily Report - 服务器离线部署包
==========================================

仓库为私有，运维无需 git clone。解压后按下面步骤执行即可。

1) 解压到固定目录，例如:
   D:\apps\cursor-team-daily-report

2) Windows 服务器一键部署:
   cd D:\apps\cursor-team-daily-report
   powershell -File scripts\deploy_server.ps1 -PublicUrl https://global-pdca.vertu.cn

3) 注册开机自启 (管理员 PowerShell):
   powershell -File scripts\install_api_server_task.ps1 -StartNow

   或临时手动:
   powershell -File scripts\run_api_server.ps1

4) Nginx 反代 (发给运维):
   https://global-pdca.vertu.cn  ->  http://127.0.0.1:8080
   参考 config\nginx-global-pdca.example.conf

5) 验证:
   curl https://global-pdca.vertu.cn/api/v1/health
   期望: {"status":"ok","service":"cursor-team-daily-report"}

说明:
- 本 zip 已含 .env 与 Token 配置，请勿转发给无关人员。
- 更新版本时由 Frank 重新打包并私发给运维。
"@
Set-Content -Path (Join-Path $OutDir "OPS_README.txt") -Value $opsReadme.TrimEnd() -Encoding UTF8
Compress-Archive -Path $OutDir -DestinationPath $ZipPath -Force

Write-Host "Server package dir: $OutDir" -ForegroundColor Green
Write-Host "Server deploy zip:  $ZipPath" -ForegroundColor Green
Write-Host "Send this zip to ops privately (WeChat / RDP / shared drive)." -ForegroundColor Cyan
