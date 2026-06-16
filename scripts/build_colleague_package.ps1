$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$PkgRoot = Join-Path $Root "package\colleague\cursor-daily-report"
$Scripts = @(
    "parse_transcripts.py",
    "publish_daily.py",
    "submit_report.py",
    "api_client.py",
    "report_io.py",
    "vertu_client.py",
    "unified_report.py",
    "build_unified_daily.py"
)

New-Item -ItemType Directory -Force -Path "$PkgRoot\scripts", "$PkgRoot\config", "$PkgRoot\api", "$PkgRoot\.tmp" | Out-Null
Set-Content -Path (Join-Path $PkgRoot ".tmp\.gitkeep") -Value "" -Encoding UTF8

foreach ($f in $Scripts) {
    Copy-Item (Join-Path $Root "scripts\$f") (Join-Path $PkgRoot "scripts\$f") -Force
}
Copy-Item (Join-Path $Root "api\schemas.py") (Join-Path $PkgRoot "api\schemas.py") -Force
Copy-Item (Join-Path $Root "api\__init__.py") (Join-Path $PkgRoot "api\__init__.py") -Force -ErrorAction SilentlyContinue

Copy-Item (Join-Path $Root "scripts\publish_today.ps1") (Join-Path $PkgRoot "scripts\publish_today.ps1") -Force
Copy-Item (Join-Path $Root "scripts\run_daily.ps1") (Join-Path $PkgRoot "run_daily.ps1") -Force
Copy-Item (Join-Path $Root "scripts\run_daily.ps1") (Join-Path $PkgRoot "run_unified.ps1") -Force
Copy-Item (Join-Path $Root "scripts\run_daily.ps1") (Join-Path $PkgRoot "run.ps1") -Force
Copy-Item (Join-Path $Root "scripts\install_daily_task.ps1") (Join-Path $PkgRoot "install_daily_task.ps1") -Force
Copy-Item (Join-Path $Root "requirements-colleague.txt") (Join-Path $PkgRoot "requirements.txt") -Force
Copy-Item (Join-Path $Root "config\user.example.json") (Join-Path $PkgRoot "config\user.example.json") -Force
Copy-Item (Join-Path $Root "config\colleague.env.example") (Join-Path $PkgRoot ".env.example") -Force
Copy-Item (Join-Path $Root "scripts\test_api_connection.ps1") (Join-Path $PkgRoot "scripts\test_api_connection.ps1") -Force
Copy-Item (Join-Path $Root "scripts\collect_my_odoo_uid.ps1") (Join-Path $PkgRoot "scripts\collect_my_odoo_uid.ps1") -Force

# 若主管 .env 已配置公网 REPORT_API_URL，写入同事包 .env.example
$envFile = Join-Path $Root ".env"
$pkgEnv = Join-Path $PkgRoot ".env.example"
if ((Test-Path $envFile) -and (Test-Path $pkgEnv)) {
    $apiUrl = ""
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*REPORT_API_URL\s*=\s*(.+)\s*$') {
            $apiUrl = $matches[1].Trim()
        }
    }
    if ($apiUrl -and $apiUrl -notmatch 'YOUR-PUBLIC|10\.100\.') {
        $content = Get-Content $pkgEnv -Raw
        $content = $content -replace 'REPORT_API_URL=.*', "REPORT_API_URL=$apiUrl"
        Set-Content -Path $pkgEnv -Value $content.TrimEnd() -Encoding UTF8
        Write-Host "Injected REPORT_API_URL into package .env.example"
    }
}

$ColleagueDir = Join-Path $Root "package\colleague"
$ZipPath = Join-Path $ColleagueDir "cursor-team-daily-report.zip"
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path $PkgRoot -DestinationPath $ZipPath -Force

Write-Host "Package: $PkgRoot"
Write-Host "Zip: $ZipPath"
