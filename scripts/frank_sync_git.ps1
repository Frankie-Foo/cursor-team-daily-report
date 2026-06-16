$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
python scripts/export_db_to_git.py --date today --push
Write-Host "Done."
