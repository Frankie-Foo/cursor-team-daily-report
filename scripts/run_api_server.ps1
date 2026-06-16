# Production API on server (no reload, listen 0.0.0.0). Ops nginx -> this port.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Load-DotEnv {
    $path = Join-Path $Root ".env"
    if (-not (Test-Path $path)) { return @{} }
    $map = @{}
    Get-Content $path | ForEach-Object {
        if ($_ -match '^\s*([^#=]+)=(.*)$') { $map[$matches[1].Trim()] = $matches[2].Trim() }
    }
    return $map
}

$envMap = Load-DotEnv
foreach ($k in $envMap.Keys) { Set-Item -Path "Env:$k" -Value $envMap[$k] }

$port = if ($envMap['API_PORT']) { $envMap['API_PORT'] } else { "8080" }
$hostBind = if ($envMap['API_HOST']) { $envMap['API_HOST'] } else { "0.0.0.0" }

Write-Host "Starting API http://${hostBind}:${port}" -ForegroundColor Cyan
python -m uvicorn api.server:app --host $hostBind --port $port
