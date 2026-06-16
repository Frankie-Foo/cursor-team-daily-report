# Quick public HTTPS tunnel (URL changes on each restart). ASCII-only.
$ErrorActionPreference = "Stop"

function Find-Cloudflared {
    $cmd = Get-Command cloudflared -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    foreach ($p in @(
        (Join-Path $env:LOCALAPPDATA "cloudflared\cloudflared.exe"),
        (Join-Path $env:ProgramFiles "cloudflared\cloudflared.exe")
    )) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

$cf = Find-Cloudflared
if (-not $cf) {
    Write-Host "cloudflared not found." -ForegroundColor Red
    Write-Host "Install: winget install Cloudflare.cloudflared" -ForegroundColor Yellow
    Write-Host "Then re-run this script." -ForegroundColor Yellow
    exit 1
}

$port = $env:API_PORT
if ([string]::IsNullOrWhiteSpace($port)) { $port = "8080" }

Write-Host ""
Write-Host "Starting quick tunnel -> http://127.0.0.1:$port" -ForegroundColor Cyan
Write-Host "Make sure API is running: scripts/run_api.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "When URL appears, set in .env:" -ForegroundColor Green
Write-Host "  REPORT_API_URL=https://xxxx.trycloudflare.com" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkGray
Write-Host ""

& $cf tunnel --url "http://127.0.0.1:$port"
