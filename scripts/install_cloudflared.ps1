# Install cloudflared to %LOCALAPPDATA%\cloudflared
$ErrorActionPreference = "Stop"
$dir = Join-Path $env:LOCALAPPDATA "cloudflared"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$dest = Join-Path $dir "cloudflared.exe"
if (-not (Test-Path $dest)) {
    Write-Host "Downloading cloudflared ..."
    Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" `
        -OutFile $dest -UseBasicParsing
}
& $dest --version
Write-Host "Installed: $dest"
