# 仅汇总当天 Cursor 对话，写入 daily/<user>/YYYY-MM-DD.md（不 POST API）
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
if (-not (Test-Path (Join-Path $Root "scripts\publish_daily.py"))) {
    $Root = Split-Path -Parent $PSScriptRoot
}
Set-Location $Root
python scripts/publish_daily.py --date today --skip-db
