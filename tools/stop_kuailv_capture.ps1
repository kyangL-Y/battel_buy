$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $repoRoot 'tmp\kuailv_capture\mitmdump.pid'

if (!(Test-Path $pidFile)) {
    Write-Host 'kuailv mitmdump pid file not found'
    exit 0
}

$pidValue = Get-Content $pidFile -ErrorAction SilentlyContinue
if ($pidValue) {
    $captureProcess = Get-Process -Id ([int]$pidValue) -ErrorAction SilentlyContinue
    if ($captureProcess) {
        Stop-Process -Id $captureProcess.Id -Force
        Write-Host "stopped kuailv mitmdump pid=$pidValue"
    } else {
        Write-Host "kuailv mitmdump process $pidValue not running"
    }
}

Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
