$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $repoRoot 'tmp\meicai_capture\mitmdump.pid'

if (Test-Path $pidFile) {
    $mitmPid = [int](Get-Content $pidFile)
    Stop-Process -Id $mitmPid -ErrorAction SilentlyContinue
    Remove-Item $pidFile -ErrorAction SilentlyContinue
}

Write-Host 'meicai mitmdump stopped'
