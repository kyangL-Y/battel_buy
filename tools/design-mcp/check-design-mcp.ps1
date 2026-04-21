param()

$checks = @()

function Add-Check {
    param(
        [string]$Name,
        [string]$Status,
        [string]$Details
    )

    $script:checks += [PSCustomObject]@{
        Name = $Name
        Status = $Status
        Details = $Details
    }
}

$codexConfig = 'C:/Users/LBQ/.codex/config.toml'
$codexConfigContent = ''
$figmaToken = [Environment]::GetEnvironmentVariable('FIGMA_OAUTH_TOKEN', 'Process')
if (-not $figmaToken) { $figmaToken = [Environment]::GetEnvironmentVariable('FIGMA_OAUTH_TOKEN', 'User') }
if (-not $figmaToken) { $figmaToken = [Environment]::GetEnvironmentVariable('FIGMA_OAUTH_TOKEN', 'Machine') }

$stitchApiKey = [Environment]::GetEnvironmentVariable('STITCH_API_KEY', 'Process')
if (-not $stitchApiKey) { $stitchApiKey = [Environment]::GetEnvironmentVariable('STITCH_API_KEY', 'User') }
if (-not $stitchApiKey) { $stitchApiKey = [Environment]::GetEnvironmentVariable('STITCH_API_KEY', 'Machine') }

$stitchAccessToken = [Environment]::GetEnvironmentVariable('STITCH_ACCESS_TOKEN', 'Process')
if (-not $stitchAccessToken) { $stitchAccessToken = [Environment]::GetEnvironmentVariable('STITCH_ACCESS_TOKEN', 'User') }
if (-not $stitchAccessToken) { $stitchAccessToken = [Environment]::GetEnvironmentVariable('STITCH_ACCESS_TOKEN', 'Machine') }

$gcpProject = [Environment]::GetEnvironmentVariable('GOOGLE_CLOUD_PROJECT', 'Process')
if (-not $gcpProject) { $gcpProject = [Environment]::GetEnvironmentVariable('GOOGLE_CLOUD_PROJECT', 'User') }
if (-not $gcpProject) { $gcpProject = [Environment]::GetEnvironmentVariable('GOOGLE_CLOUD_PROJECT', 'Machine') }

if (Test-Path $codexConfig) {
    Add-Check -Name "Codex config" -Status "ok" -Details $codexConfig
    $codexConfigContent = Get-Content -Raw -Encoding UTF8 $codexConfig
}
else {
    Add-Check -Name "Codex config" -Status "missing" -Details "~/.codex/config.toml not found"
}

if ($figmaToken) {
    Add-Check -Name "Figma token" -Status "ok" -Details "FIGMA_OAUTH_TOKEN is set"
}
else {
    Add-Check -Name "Figma token" -Status "missing" -Details "FIGMA_OAUTH_TOKEN is missing"
}

$figmaConfigured = $codexConfigContent -match "(?m)^\[mcp_servers\.figma\]$"
if ($figmaToken -and $figmaConfigured) {
    Add-Check -Name "Figma config state" -Status "ok" -Details "Figma MCP is enabled"
}
elseif ($figmaToken) {
    Add-Check -Name "Figma config state" -Status "manual" -Details "FIGMA_OAUTH_TOKEN exists, but Figma MCP is not enabled; run apply-codex-mcp.ps1"
}
elseif ($figmaConfigured) {
    Add-Check -Name "Figma config state" -Status "warning" -Details "Figma MCP is enabled without credentials; run apply-codex-mcp.ps1 to remove it"
}
else {
    Add-Check -Name "Figma config state" -Status "ok" -Details "Figma MCP is disabled because credentials are missing"
}

if ($stitchApiKey) {
    Add-Check -Name "Stitch auth" -Status "ok" -Details "STITCH_API_KEY is set"
}
elseif ($stitchAccessToken -and $gcpProject) {
    Add-Check -Name "Stitch auth" -Status "ok" -Details "STITCH_ACCESS_TOKEN and GOOGLE_CLOUD_PROJECT are set"
}
else {
    Add-Check -Name "Stitch auth" -Status "missing" -Details "Missing STITCH_API_KEY, or missing STITCH_ACCESS_TOKEN plus GOOGLE_CLOUD_PROJECT"
}

$stitchConfigured = $codexConfigContent -match "(?m)^\[mcp_servers\.stitch\]$"
$stitchReady = [bool]$stitchApiKey -or ([bool]$stitchAccessToken -and [bool]$gcpProject)
if ($stitchReady -and $stitchConfigured) {
    Add-Check -Name "Stitch config state" -Status "ok" -Details "Stitch MCP is enabled"
}
elseif ($stitchReady) {
    Add-Check -Name "Stitch config state" -Status "manual" -Details "Stitch credentials exist, but Stitch MCP is not enabled; run apply-codex-mcp.ps1"
}
elseif ($stitchConfigured) {
    Add-Check -Name "Stitch config state" -Status "warning" -Details "Stitch MCP is enabled without credentials; run apply-codex-mcp.ps1 to remove it"
}
else {
    Add-Check -Name "Stitch config state" -Status "ok" -Details "Stitch MCP is disabled because credentials are missing"
}

if (Test-Path 'E:/battel/tools/design-mcp/node_modules/@google/stitch-sdk') {
    Add-Check -Name "Stitch proxy deps" -Status "ok" -Details "@google/stitch-sdk is installed"
}
else {
    Add-Check -Name "Stitch proxy deps" -Status "missing" -Details "Run npm install in tools/design-mcp/"
}

Add-Check -Name "Pencil runtime" -Status "manual" -Details "Pencil must be installed and running, then verify it manually in Codex /mcp."

$checks | Format-Table -AutoSize
