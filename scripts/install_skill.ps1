$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Scripts = Join-Path $Root "scripts"
$RepoSkill = Join-Path $Root ".cursor\skills\cursor-daily-report"
$Target = Join-Path $env:USERPROFILE ".cursor\skills\cursor-daily-report"

if (-not (Test-Path $RepoSkill)) {
    throw "Skill not found: $RepoSkill"
}

New-Item -ItemType Directory -Force -Path $Target | Out-Null
Copy-Item -Path (Join-Path $RepoSkill "*") -Destination $Target -Recurse -Force
Write-Host "Skill installed to: $Target"
