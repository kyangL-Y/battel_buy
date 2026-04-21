param()

$codexConfig = 'C:/Users/LBQ/.codex/config.toml'
$backupPath = 'C:/Users/LBQ/.codex/config.toml.design-mcp.bak'

function Get-EnvValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $processValue = [Environment]::GetEnvironmentVariable($Name, 'Process')
    if ($processValue) { return $processValue }

    $userValue = [Environment]::GetEnvironmentVariable($Name, 'User')
    if ($userValue) { return $userValue }

    return [Environment]::GetEnvironmentVariable($Name, 'Machine')
}

function Remove-McpBlock {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Content,
        [Parameter(Mandatory = $true)]
        [string]$ServerName
    )

    $pattern = "(?ms)\r?\n?\[mcp_servers\.$([Regex]::Escape($ServerName))\]\r?\n.*?(?=(\r?\n\[)|\z)"
    return [Regex]::Replace($Content, $pattern, '')
}

function Set-McpBlock {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Content,
        [Parameter(Mandatory = $true)]
        [string]$ServerName,
        [Parameter(Mandatory = $true)]
        [string]$Block
    )

    $updatedContent = Remove-McpBlock -Content $Content -ServerName $ServerName
    $trimmedContent = $updatedContent.TrimEnd("`r", "`n")
    if (-not $trimmedContent) {
        return $Block.Trim()
    }

    return $trimmedContent + "`r`n`r`n" + $Block.Trim() + "`r`n"
}

if (-not (Test-Path $codexConfig)) {
    throw "Codex config not found: $codexConfig"
}

$figmaEnabled = [bool](Get-EnvValue -Name 'FIGMA_OAUTH_TOKEN')
$stitchEnabled = [bool](Get-EnvValue -Name 'STITCH_API_KEY') -or (
    [bool](Get-EnvValue -Name 'STITCH_ACCESS_TOKEN') -and
    [bool](Get-EnvValue -Name 'GOOGLE_CLOUD_PROJECT')
)

$figmaBlock = @"
[mcp_servers.figma]
url = "https://mcp.figma.com/mcp"
bearer_token_env_var = "FIGMA_OAUTH_TOKEN"
http_headers = { "X-Figma-Region" = "us-east-1" }
startup_timeout_sec = 20
tool_timeout_sec = 120
"@

$stitchBlock = @"
[mcp_servers.stitch]
type = "stdio"
command = "node"
args = ["E:\\battel\\tools\\design-mcp\\stitch-proxy.mjs"]
startup_timeout_sec = 20
tool_timeout_sec = 120
"@

Copy-Item -LiteralPath $codexConfig -Destination $backupPath -Force

$content = Get-Content -Raw -Encoding UTF8 $codexConfig

if ($content -notmatch '(?m)^\[features\]$' -and $content -notmatch '(?m)^rmcp_client\s*=') {
    $content = $content.TrimEnd("`r", "`n") + "`r`n`r`n[features]`r`nrmcp_client = true`r`n"
}

$actions = @()

if ($figmaEnabled) {
    $content = Set-McpBlock -Content $content -ServerName 'figma' -Block $figmaBlock
    $actions += 'figma=enabled'
}
else {
    $content = Remove-McpBlock -Content $content -ServerName 'figma'
    $actions += 'figma=disabled(missing FIGMA_OAUTH_TOKEN)'
}

if ($stitchEnabled) {
    $content = Set-McpBlock -Content $content -ServerName 'stitch' -Block $stitchBlock
    $actions += 'stitch=enabled'
}
else {
    $content = Remove-McpBlock -Content $content -ServerName 'stitch'
    $actions += 'stitch=disabled(missing Stitch credentials)'
}

$normalizedContent = ($content.TrimEnd("`r", "`n") + "`r`n")
Set-Content -LiteralPath $codexConfig -Value $normalizedContent -Encoding UTF8

[PSCustomObject]@{
    config = $codexConfig
    backup = $backupPath
    actions = $actions
} | ConvertTo-Json -Depth 3
