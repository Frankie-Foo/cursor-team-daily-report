$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
python -m uvicorn api.server:app --host 0.0.0.0 --port 8080 --reload
