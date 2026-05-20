$ErrorActionPreference = 'Stop'

$pidFile = 'E:/battel/tmp/liancai_capture/mitmdump.pid'
if (!(Test-Path $pidFile)) {
    Write-Output 'mitmdump pid file not found'
    exit 0
}

$pidValue = Get-Content $pidFile -ErrorAction SilentlyContinue
if ($pidValue) {
    $proc = Get-Process -Id ([int]$pidValue) -ErrorAction SilentlyContinue
    if ($proc) {
        Stop-Process -Id $proc.Id -Force
        Write-Output "stopped mitmdump pid=$pidValue"
    } else {
        Write-Output "process $pidValue not running"
    }
}

Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
