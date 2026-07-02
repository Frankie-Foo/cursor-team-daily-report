# Build per-person colleague zips (pre-filled credentials). Frank only.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$CredFile = Join-Path $Root "config\member_credentials.json"
$PkgTemplate = Join-Path $Root "package\colleague\cursor-daily-report"
$OutBase = Join-Path $Root "package\colleague\personal"

if (-not (Test-Path $CredFile)) {
    Write-Host "Run first: python scripts/export_member_credentials.py" -ForegroundColor Red
    exit 1
}

& powershell -File (Join-Path $Root "scripts\build_colleague_package.ps1")

$creds = Get-Content $CredFile -Raw -Encoding UTF8 | ConvertFrom-Json
New-Item -ItemType Directory -Force -Path $OutBase | Out-Null

foreach ($member in $creds.members) {
    if (-not $member.api_token) {
        Write-Host "Skip $($member.username): missing api_token" -ForegroundColor Yellow
        continue
    }
    $uid = 0
    if ($member.odoo_user_id) { $uid = [int]$member.odoo_user_id }

    $personDir = Join-Path $OutBase $member.username
    $personPkg = Join-Path $personDir "cursor-daily-report"
    if (Test-Path $personDir) { Remove-Item $personDir -Recurse -Force }
    Copy-Item $PkgTemplate $personPkg -Recurse -Force

    $setupCred = @{
        username         = $member.username
        display_name     = $member.display_name
        odoo_user_id     = $uid
        cursor_workspace = ""
        report_api_url   = $creds.report_api_url
        report_api_token = $member.api_token
    }
    New-Item -ItemType Directory -Force -Path (Join-Path $personPkg "config") | Out-Null
    $setupCred | ConvertTo-Json | Set-Content (Join-Path $personPkg "config\setup.credentials.json") -Encoding UTF8

    Copy-Item (Join-Path $Root "scripts\setup_oneclick.ps1") (Join-Path $personPkg "setup_oneclick.ps1") -Force
    Copy-Item (Join-Path $Root "scripts\SETUP.bat") (Join-Path $personPkg "SETUP.bat") -Force
    $guide = Get-ChildItem (Join-Path $Root "package\colleague") -Filter "*.md" |
        Where-Object { $_.Name -ne "cursor-team-daily-report.zip" } |
        Select-Object -First 1
    if ($guide) {
        Copy-Item $guide.FullName (Join-Path $personPkg "使用说明.md") -Force
    }

    $zipPath = Join-Path $personDir "cursor-daily-report-$($member.username).zip"
    if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
    Compress-Archive -Path $personPkg -DestinationPath $zipPath -Force
    Write-Host "Built: $zipPath" -ForegroundColor Green
}

Write-Host ""
Write-Host "Send each person their zip +: 解压后双击 SETUP.bat，只需填 Cursor 项目路径" -ForegroundColor Cyan
