# Test connectivity to team daily report API (ASCII-only for PowerShell)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Item -Path "Env:$name" -Value $value
        }
    }
}

$url = $env:REPORT_API_URL
if ([string]::IsNullOrWhiteSpace($url)) {
    Write-Host "REPORT_API_URL not set in .env" -ForegroundColor Red
    exit 1
}

$health = "$($url.TrimEnd('/'))/api/v1/health"
Write-Host ""
Write-Host "Testing: $health" -ForegroundColor Cyan
Write-Host ""

try {
    $resp = Invoke-WebRequest -Uri $health -TimeoutSec 10 -UseBasicParsing
    Write-Host "OK  HTTP $($resp.StatusCode)" -ForegroundColor Green
    Write-Host $resp.Content
    Write-Host ""
    Write-Host "Network OK. You can POST daily reports." -ForegroundColor Green
    exit 0
} catch {
    Write-Host "FAIL  Cannot reach API" -ForegroundColor Red
    Write-Host $_.Exception.Message
    Write-Host ""
    Write-Host "Likely causes:" -ForegroundColor Yellow
    Write-Host "  1. REPORT_API_URL wrong (need public HTTPS from Frank, not 10.100.x.x)"
    Write-Host "  2. API / tunnel not running on Frank's server"
    Write-Host "  3. Typo in .env"
    Write-Host ""
    Write-Host "Ask Frank for the latest public REPORT_API_URL." -ForegroundColor Yellow
    exit 1
}
