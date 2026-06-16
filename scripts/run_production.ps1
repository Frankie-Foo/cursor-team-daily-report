# Production: API + Cloudflare Tunnel (token or config). ASCII-only.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Load-DotEnv {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return @{} }
    $map = @{}
    Get-Content $Path | ForEach-Object {
        if ($_ -match '^\s*([^#=]+)=(.*)$') {
            $map[$matches[1].Trim()] = $matches[2].Trim()
        }
    }
    return $map
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

$envMap = Load-DotEnv (Join-Path $Root ".env")
foreach ($k in $envMap.Keys) { Set-Item -Path "Env:$k" -Value $envMap[$k] }

$port = if ($envMap['API_PORT']) { $envMap['API_PORT'] } else { "8080" }
$hostBind = if ($envMap['API_HOST']) { $envMap['API_HOST'] } else { "127.0.0.1" }
$token = $envMap['CLOUDFLARE_TUNNEL_TOKEN']
if (-not $token) { $token = $env:CLOUDFLARE_TUNNEL_TOKEN }

$cf = Find-Cloudflared
if (-not $cf) {
    Write-Host "cloudflared not found. Run scripts/install_cloudflared.ps1" -ForegroundColor Red
    exit 1
}

if (-not $envMap['REPORT_API_URL'] -or $envMap['REPORT_API_URL'] -match 'YOUR-PUBLIC|10\.100\.') {
    Write-Host "Set REPORT_API_URL in .env to your public HTTPS URL first." -ForegroundColor Red
    Write-Host "See docs/公网部署-正式版.md" -ForegroundColor Yellow
    exit 1
}

Write-Host "Starting API ${hostBind}:${port} ..." -ForegroundColor Cyan
$apiProc = Start-Process -FilePath "python" `
    -ArgumentList "-m", "uvicorn", "api.server:app", "--host", $hostBind, "--port", $port `
    -WorkingDirectory $Root -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 3
try {
    $h = Invoke-WebRequest -Uri "http://${hostBind}:${port}/api/v1/health" -TimeoutSec 10 -UseBasicParsing
    Write-Host "API OK: $($h.Content)" -ForegroundColor Green
} catch {
    Write-Host "API health check failed: $($_.Exception.Message)" -ForegroundColor Red
    Stop-Process -Id $apiProc.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

Write-Host "Public URL: $($envMap['REPORT_API_URL'])" -ForegroundColor Green
Write-Host "Starting Cloudflare tunnel ..." -ForegroundColor Cyan

$config = $envMap['CLOUDFLARE_TUNNEL_CONFIG']
if (-not $config) { $config = Join-Path $Root "config\cloudflare-tunnel.yml" }

try {
    if ($token) {
        & $cf tunnel run --token $token
    } elseif (Test-Path $config) {
        & $cf tunnel --config $config run
    } else {
        Write-Host "Missing CLOUDFLARE_TUNNEL_TOKEN or config/cloudflare-tunnel.yml" -ForegroundColor Red
        Stop-Process -Id $apiProc.Id -Force -ErrorAction SilentlyContinue
        exit 1
    }
} finally {
    Stop-Process -Id $apiProc.Id -Force -ErrorAction SilentlyContinue
}
