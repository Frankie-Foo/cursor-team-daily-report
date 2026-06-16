# Start FastAPI + Cloudflare Tunnel for public HTTPS POST. ASCII-only.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Load-DotEnv {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }
    Get-Content $Path | ForEach-Object {
        if ($_ -match '^\s*([^#=]+)=(.*)$') {
            Set-Item -Path "Env:$($matches[1].Trim())" -Value $matches[2].Trim()
        }
    }
}

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

Load-DotEnv (Join-Path $Root ".env")

$port = $env:API_PORT
if ([string]::IsNullOrWhiteSpace($port)) { $port = "8080" }
$hostBind = $env:API_HOST
if ([string]::IsNullOrWhiteSpace($hostBind)) { $hostBind = "127.0.0.1" }

$cf = Find-Cloudflared
if (-not $cf) {
    Write-Host "cloudflared not found. Run: winget install Cloudflare.cloudflared" -ForegroundColor Red
    exit 1
}

$tunnelConfig = $env:CLOUDFLARE_TUNNEL_CONFIG
if ([string]::IsNullOrWhiteSpace($tunnelConfig)) {
    $tunnelConfig = Join-Path $Root "config\cloudflare-tunnel.yml"
}

Write-Host "Starting API on ${hostBind}:${port} ..." -ForegroundColor Cyan
$apiJob = Start-Job -ScriptBlock {
    param($RootPath, $Bind, $PortNum)
    Set-Location $RootPath
    python -m uvicorn api.server:app --host $Bind --port $PortNum
} -ArgumentList $Root, $hostBind, $port

Start-Sleep -Seconds 3

try {
    $health = Invoke-WebRequest -Uri "http://${hostBind}:${port}/api/v1/health" -TimeoutSec 10 -UseBasicParsing
    Write-Host "API OK: $($health.Content)" -ForegroundColor Green
} catch {
    Write-Host "API not ready yet, tunnel will still start..." -ForegroundColor Yellow
}

Write-Host ""
if (Test-Path $tunnelConfig) {
    Write-Host "Named tunnel: $tunnelConfig" -ForegroundColor Cyan
    Write-Host "Public URL should be REPORT_API_URL in .env" -ForegroundColor Green
    & $cf tunnel --config $tunnelConfig run
} else {
    Write-Host "No config/cloudflare-tunnel.yml - using quick tunnel (URL changes each run)" -ForegroundColor Yellow
    Write-Host "For fixed URL see docs/公网部署指南.md" -ForegroundColor Yellow
    & $cf tunnel --url "http://${hostBind}:${port}"
}

Stop-Job $apiJob -ErrorAction SilentlyContinue
Remove-Job $apiJob -Force -ErrorAction SilentlyContinue
