#Requires -Version 5.1
<#
.SYNOPSIS
  Final artifact audio QA with optional loudnorm two-pass repair (Step 4A-Repair).
.DESCRIPTION
  Measurement (audio-loudness-qa) and repair (final-audio-loudness-repair) are separate.
  At most one repair attempt, then fail-closed.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$VideoPath,
    [string]$AudioProfilePath = '',
    [string]$WorkDir = '',
    [switch]$PromoteOnPass,
    [string]$PromotedPath = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$wfRoot = Split-Path -Parent $scriptDir
$audioQaCli = Join-Path $scriptDir 'audio-loudness-qa.py'
$repairCli = Join-Path $scriptDir 'final-audio-loudness-repair.py'

if ([string]::IsNullOrWhiteSpace($AudioProfilePath)) {
    $AudioProfilePath = Join-Path $wfRoot 'runtime\narration-short-v1-audio-mix-profile.yaml'
}
if ([string]::IsNullOrWhiteSpace($WorkDir)) {
    $WorkDir = Join-Path $wfRoot '.qa\audio-repair'
}
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null

function Invoke-AudioQaJson {
    param([string]$Path)
    $lines = & python $audioQaCli $Path --profile $AudioProfilePath 2>&1 | ForEach-Object { "$_" }
    $out = ($lines | Out-String).Trim()
    $start = $out.IndexOf('{'); $end = $out.LastIndexOf('}')
    if ($start -lt 0 -or $end -le $start) { throw "AUDIO_QA_PARSE_FAILED: $out" }
    return $out.Substring($start, $end - $start + 1) | ConvertFrom-Json
}

$before = Invoke-AudioQaJson -Path $VideoPath
$report = [ordered]@{
    input = $VideoPath
    before_qa = $before
    repair_attempted = $false
    status = $before.verdict
    ok = [bool]$before.ok
}

if ($before.ok) {
    $report.status = 'NO_REPAIR_REQUIRED'
    $json = $report | ConvertTo-Json -Depth 8
    $outPath = Join-Path $WorkDir 'final-artifact-audio-qa-repair.json'
    $json | Set-Content -LiteralPath $outPath -Encoding UTF8
    Write-Output $outPath
    Write-Output 'NO_REPAIR_REQUIRED'
    exit 0
}

if ($before.verdict -eq 'NO_AUDIO') {
    $report.status = 'BLOCKED'
    $report.ok = $false
    $json = $report | ConvertTo-Json -Depth 8
    $outPath = Join-Path $WorkDir 'final-artifact-audio-qa-repair.json'
    $json | Set-Content -LiteralPath $outPath -Encoding UTF8
    Write-Output $outPath
    Write-Output 'BLOCKED'
    exit 2
}

$repairArgs = @($repairCli, $VideoPath, '--profile', $AudioProfilePath, '--work-dir', $WorkDir)
if ($PromoteOnPass) { $repairArgs += '--promote-on-pass' }
if ($PromotedPath) { $repairArgs += @('--promoted-path', $PromotedPath) }

$repairLines = & python @repairArgs 2>&1 | ForEach-Object { "$_" }
$repairOut = ($repairLines | Out-String).Trim()
$rs = $repairOut.IndexOf('{'); $re = $repairOut.LastIndexOf('}')
if ($rs -lt 0 -or $re -le $rs) { throw "AUDIO_REPAIR_PARSE_FAILED: $repairOut" }
$repair = $repairOut.Substring($rs, $re - $rs + 1) | ConvertFrom-Json

$report.repair_attempted = $true
$report.repair = $repair
$report.after_qa = $repair.after_qa
$report.ok = [bool]$repair.ok
$report.status = [string]$repair.status
$report.attempts = [int]$repair.attempts

$outPath = Join-Path $WorkDir 'final-artifact-audio-qa-repair.json'
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $outPath -Encoding UTF8
Write-Output $outPath
Write-Output $report.status
if (-not $report.ok) { exit 2 }
exit 0
