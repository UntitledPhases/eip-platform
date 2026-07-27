param(
    [Parameter(Mandatory = $true)]
    [string]$Source,

    [Parameter(Mandatory = $true)]
    [string]$TargetHost,

    [string]$HostKeyAlias = "mirror-host",

    [Parameter(Mandatory = $true)]
    [string]$TargetPath
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
    throw "Source JSON not found: $Source"
}

$sourcePath = (Resolve-Path -LiteralPath $Source).Path
$null = Get-Content -LiteralPath $sourcePath -Raw | ConvertFrom-Json

$targetDir = Split-Path -Parent $TargetPath
$tmpPath = "$TargetPath.tmp.$PID"
$sshOpts = @(
    "-o", "BatchMode=yes",
    "-o", "HostKeyAlias=$HostKeyAlias",
    "-o", "ConnectTimeout=8"
)

ssh @sshOpts $TargetHost "mkdir -p '$targetDir'"
scp @sshOpts $sourcePath "${TargetHost}:$tmpPath"
ssh @sshOpts $TargetHost "python3 -m json.tool '$tmpPath' >/dev/null && mv '$tmpPath' '$TargetPath'"
ssh @sshOpts $TargetHost "curl -fsS --max-time 4 http://127.0.0.1:5000/mirror/api/data >/dev/null"

Write-Host "Pushed mirror data to $TargetHost`:$TargetPath"
