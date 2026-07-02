# Build minimal zip for ops: update api_tokens.json on running server container.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$OutDir = Join-Path $Root "package\server\token-update"
$ZipPath = Join-Path $Root "package\server\api_tokens-update.zip"

New-Item -ItemType Directory -Force -Path (Join-Path $OutDir "config") | Out-Null
Copy-Item (Join-Path $Root "config\api_tokens.json") (Join-Path $OutDir "config\api_tokens.json") -Force

$readme = @"
API Token 热更新包
==================

在服务器上（Docker 部署）：

  docker cp config/api_tokens.json cursor-team-daily-report-api:/app/config/api_tokens.json

无需重启容器，下一次 POST 即生效。

验证 Henry：
  curl -H "Authorization: Bearer <Henry Token>" https://global-pdca.vertu.cn/api/v1/health
"@
Set-Content -Path (Join-Path $OutDir "OPS_README.txt") -Value $readme.TrimEnd() -Encoding UTF8

if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path $OutDir -DestinationPath $ZipPath -Force
Write-Host "Built: $ZipPath" -ForegroundColor Green
