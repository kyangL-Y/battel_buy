$ErrorActionPreference = 'Stop'

$root = 'E:/battel/tmp/liancai_capture'
New-Item -ItemType Directory -Force -Path $root | Out-Null

$pidFile = Join-Path $root 'mitmdump.pid'
$stdoutFile = Join-Path $root 'mitmdump.stdout.log'
$stderrFile = Join-Path $root 'mitmdump.stderr.log'
$scriptFile = 'E:/battel/tools/liancai_capture_filter.py'

if (Test-Path $pidFile) {
    $existingPid = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($existingPid) {
        $proc = Get-Process -Id ([int]$existingPid) -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Output "mitmdump is already running with PID $existingPid"
            exit 0
        }
    }
}

$proc = Start-Process -FilePath 'mitmdump' `
    -ArgumentList @('--listen-host', '0.0.0.0', '--listen-port', '8080', '-s', $scriptFile) `
    -WindowStyle Hidden `
    -RedirectStandardOutput $stdoutFile `
    -RedirectStandardError $stderrFile `
    -PassThru

Set-Content -Path $pidFile -Value $proc.Id -Encoding UTF8
Write-Output "started mitmdump pid=$($proc.Id) listen=0.0.0.0:8080"
