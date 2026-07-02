# Register Cursor team daily report MCP into Cursor (local stdio).
# Merges into existing mcp.json without removing other servers.
# Usage: powershell -ExecutionPolicy Bypass -File mcp/install_mcp.ps1

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Server = Join-Path $Root "mcp\server.py"

if (-not (Test-Path $Server)) {
    throw "Server not found: $Server"
}

$Python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $Python) {
    throw "python not found on PATH"
}

$CursorDir = Join-Path $env:USERPROFILE ".cursor"
$McpJson = Join-Path $CursorDir "mcp.json"
if (-not (Test-Path $CursorDir)) {
    New-Item -ItemType Directory -Force -Path $CursorDir | Out-Null
}

# Read existing mcp.json (PowerShell 5.1 compatible merge)
$servers = @{}
if (Test-Path $McpJson) {
    try {
        $raw = Get-Content $McpJson -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($raw -and $raw.mcpServers) {
            foreach ($prop in $raw.mcpServers.PSObject.Properties) {
                $servers[$prop.Name] = $prop.Value
            }
        }
    } catch {
        Write-Host "Existing mcp.json unreadable, starting fresh."
    }
}

# Backup before writing
if (Test-Path $McpJson) {
    Copy-Item $McpJson "$McpJson.bak" -Force
}

$servers["cursor-team-daily-report"] = @{
    command = $Python
    args    = @($Server)
}

$output = [ordered]@{ mcpServers = $servers }
$output | ConvertTo-Json -Depth 10 | Set-Content -Path $McpJson -Encoding UTF8

Write-Host "MCP config written to: $McpJson"
Write-Host "Server: $Server"
$other = @($servers.Keys | Where-Object { $_ -ne "cursor-team-daily-report" })
if ($other.Count -gt 0) {
    Write-Host "Preserved existing servers: $($other -join ', ')"
}
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Restart Cursor to load the MCP server"
Write-Host "  2. In Cursor Settings -> MCP, confirm cursor-team-daily-report is connected"
Write-Host "  3. Test: ask the agent to call the check_setup tool"
