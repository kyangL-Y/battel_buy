param(
    [switch]$AllowSecretCapture,
    [string]$ListenHost = '0.0.0.0',
    [int]$Port = 8888
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$captureDir = Join-Path $repoRoot 'tmp\kuailv_capture'
$scriptFile = Join-Path $repoRoot 'tools\kuailv_capture_filter.py'
$stdoutFile = Join-Path $captureDir 'mitmdump.stdout.log'
$stderrFile = Join-Path $captureDir 'mitmdump.stderr.log'
$pidFile = Join-Path $captureDir 'mitmdump.pid'

New-Item -ItemType Directory -Force -Path $captureDir | Out-Null
Set-Content -Path (Join-Path $captureDir 'kuailv_flows.jsonl') -Value '' -Encoding UTF8
Set-Content -Path $stdoutFile -Value '' -Encoding UTF8
Set-Content -Path $stderrFile -Value '' -Encoding UTF8

if (Test-Path $pidFile) {
    $existingPid = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($existingPid) {
        $existingProcess = Get-Process -Id ([int]$existingPid) -ErrorAction SilentlyContinue
        if ($existingProcess) {
            Write-Host "kuailv mitmdump is already running pid=$existingPid"
            exit 0
        }
    }
}

if ($AllowSecretCapture) {
    $secretCaptureDir = Join-Path $repoRoot '.local-secrets\kuailv_capture'
    New-Item -ItemType Directory -Force -Path $secretCaptureDir | Out-Null
    Set-Content -Path (Join-Path $secretCaptureDir 'kuailv_secret_flows.jsonl') -Value '' -Encoding UTF8
    $env:ALLOW_SECRET_CAPTURE = '1'
} else {
    Remove-Item Env:\ALLOW_SECRET_CAPTURE -ErrorAction SilentlyContinue
}

$mitmdump = (Get-Command mitmdump.exe -ErrorAction Stop).Source
$arguments = @(
    '--listen-host', $ListenHost,
    '-p', [string]$Port,
    '-s', $scriptFile,
    '--set', 'flow_detail=1'
)
$process = Start-Process -FilePath $mitmdump `
    -ArgumentList $arguments `
    -WorkingDirectory $repoRoot `
    -RedirectStandardOutput $stdoutFile `
    -RedirectStandardError $stderrFile `
    -PassThru `
    -WindowStyle Hidden
$process.Id | Set-Content -Path $pidFile -Encoding ASCII

Write-Host "kuailv mitmdump started pid=$($process.Id) listen=$ListenHost`:$Port secret_capture=$($AllowSecretCapture.IsPresent)"
Write-Host 'redacted output: tmp\kuailv_capture\kuailv_flows.jsonl'
if ($AllowSecretCapture) {
    Write-Host 'secret output: .local-secrets\kuailv_capture\kuailv_secret_flows.jsonl'
}
