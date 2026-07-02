$ErrorActionPreference = "Stop"
# 每日定时提交日报：有 odoo_user_id 走统一日报(Vertu+Vemory+Cursor)，否则回退 Cursor-only。
$Root = $PSScriptRoot
if (-not (Test-Path (Join-Path $Root "scripts\build_unified_daily.py"))) {
    $Root = Split-Path -Parent $PSScriptRoot
}
Set-Location $Root

# 读 user.json 的 odoo_user_id
$uid = 0
$userJson = Join-Path $Root "config\user.json"
if (Test-Path $userJson) {
    try {
        $profile = Get-Content $userJson -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($profile.odoo_user_id) { $uid = [int]$profile.odoo_user_id }
    } catch {}
}

if ($uid -gt 0) {
    python scripts/build_unified_daily.py --date today --api-only
} else {
    # 无 uid：只提交 Cursor 工作日报（不依赖 Vertu）
    python scripts/publish_daily.py --date today --api-only
}
