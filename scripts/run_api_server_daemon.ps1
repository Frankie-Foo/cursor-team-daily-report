# Headless API for scheduled task: load .env, log to file, run uvicorn.
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

function Resolve-PythonExe {
    $pathFile = Join-Path $Root "config\.python_cmd.txt"
    if (Test-Path $pathFile) {
        $saved = (Get-Content $pathFile -Raw).Trim()
        if ($saved -and (Test-Path $saved)) { return $saved }
    }
    return (Get-Command python -ErrorAction Stop).Source
}

$logDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir "api-server.log"

function Write-LogLine {
    param([string]$Message)
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $Message"
    Add-Content -Path $logFile -Value $line -Encoding UTF8
}

try {
    $pythonExe = Resolve-PythonExe
    $envMap = Load-DotEnv
    foreach ($k in $envMap.Keys) { Set-Item -Path "Env:$k" -Value $envMap[$k] }

    $port = if ($envMap['API_PORT']) { $envMap['API_PORT'] } else { "8080" }
    $hostBind = if ($envMap['API_HOST']) { $envMap['API_HOST'] } else { "0.0.0.0" }

    Write-LogLine "python=$pythonExe host=$hostBind port=$port"
    Write-LogLine "Starting uvicorn api.server:app"

    & $pythonExe -m uvicorn api.server:app --host $hostBind --port $port 2>&1 |
        ForEach-Object { Write-LogLine $_ }
} catch {
    Write-LogLine "FATAL: $($_.Exception.Message)"
    exit 1
}
