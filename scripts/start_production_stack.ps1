# Start API + Cloudflare tunnel (production). ASCII-only.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$LogDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Load-DotEnv {
    $path = Join-Path $Root ".env"
    if (-not (Test-Path $path)) { return @{} }
    $map = @{}
    Get-Content $path | ForEach-Object {
        if ($_ -match '^\s*([^#=]+)=(.*)$') { $map[$matches[1].Trim()] = $matches[2].Trim() }
    }
    return $map
}

function Find-Cloudflared {
    foreach ($p in @(
        (Get-Command cloudflared -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source),
        (Join-Path $env:LOCALAPPDATA "cloudflared\cloudflared.exe")
    )) {
        if ($p -and (Test-Path $p)) { return $p }
    }
    return $null
}

$envMap = Load-DotEnv
$port = if ($envMap['API_PORT']) { $envMap['API_PORT'] } else { "8080" }
$hostBind = if ($envMap['API_HOST']) { $envMap['API_HOST'] } else { "127.0.0.1" }
$token = $envMap['CLOUDFLARE_TUNNEL_TOKEN']
$config = if ($envMap['CLOUDFLARE_TUNNEL_CONFIG']) { $envMap['CLOUDFLARE_TUNNEL_CONFIG'] } else { Join-Path $Root "config\cloudflare-tunnel.yml" }
$cf = Find-Cloudflared

if (-not $cf) {
    Write-Error "cloudflared missing. Run scripts/install_cloudflared.ps1"
}

# Stop stale processes on same port (optional)
Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

Write-Host "[1/2] API http://${hostBind}:${port}" -ForegroundColor Cyan
Start-Process -FilePath "python" -ArgumentList "-m","uvicorn","api.server:app","--host",$hostBind,"--port",$port `
    -WorkingDirectory $Root -WindowStyle Hidden | Out-Null
Start-Sleep -Seconds 3

Write-Host "[2/2] Cloudflare tunnel" -ForegroundColor Cyan
if ($token) {
    Write-Host "Mode: named tunnel (token)" -ForegroundColor Green
    Write-Host "Public: $($envMap['REPORT_API_URL'])" -ForegroundColor Green
    & $cf tunnel run --token $token 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "tunnel.log")
} elseif (Test-Path $config) {
    Write-Host "Mode: named tunnel (config)" -ForegroundColor Green
    & $cf tunnel --config $config run 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "tunnel.log")
} else {
    Write-Host "Mode: quick tunnel (NOT for long-term production)" -ForegroundColor Yellow
    & $cf tunnel --url "http://${hostBind}:${port}" 2>&1 | Tee-Object -FilePath (Join-Path $LogDir "tunnel.log")
}
