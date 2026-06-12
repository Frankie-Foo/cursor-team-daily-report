$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
python scripts/publish_daily.py --date today --git-push
Write-Host "Done."
