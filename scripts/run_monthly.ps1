$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Scripts = Join-Path $Root "scripts"

Write-Host "Monthly rollup + git sync"
python (Join-Path $Scripts "aggregate_weekly.py") --date today --write-db
python (Join-Path $Scripts "aggregate_monthly.py") --write-db
$Month = Get-Date -Format "yyyy-MM"
python (Join-Path $Scripts "git_sync.py") --message "chore: monthly rollup $Month"
Write-Host "Done."
