#Requires -Version 5.1
<#
.SYNOPSIS
  Batch L1 preflight for Stage 08E-B Experiment A case matrix.
#>
[CmdletBinding()]
param(
    [string]$RootDir,
    [string]$CasesDir,
    [string]$PredictionsDir,
    [string]$PreflightScript
)

if (-not $RootDir) {
    $RootDir = $PSScriptRoot
    if (-not $RootDir) {
        $RootDir = 'E:\01_Work\01_PersonalProjects\011-video-editing-workflow\validation\08e-b-exp-a'
    }
}
if (-not $CasesDir) { $CasesDir = Join-Path $RootDir 'cases' }
if (-not $PredictionsDir) { $PredictionsDir = Join-Path $RootDir 'predictions' }
if (-not $PreflightScript) {
    $repoRoot = (Resolve-Path -LiteralPath (Join-Path $RootDir '..\..')).Path
    $PreflightScript = Join-Path $repoRoot 'source\payload\video-workflow\tools\subtitle-layout-preflight.ps1'
}

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $PreflightScript)) {
    throw "PREFLIGHT_SCRIPT_NOT_FOUND: $PreflightScript"
}
if (-not (Test-Path -LiteralPath $CasesDir)) {
    throw "CASES_DIR_NOT_FOUND: $CasesDir"
}
New-Item -ItemType Directory -Force -Path $PredictionsDir | Out-Null

$requests = Get-ChildItem -LiteralPath $CasesDir -Filter '*.request.json' | Sort-Object Name
if ($requests.Count -eq 0) {
    throw "NO_CASE_REQUESTS: $CasesDir"
}

$summary = @()
foreach ($req in $requests) {
    $caseId = [System.IO.Path]::GetFileNameWithoutExtension($req.Name).Replace('.request', '')
    $out = Join-Path $PredictionsDir "$caseId.prediction.json"
    & $PreflightScript -RequestPath $req.FullName -OutputPath $out | Out-Null
    $pred = Get-Content -LiteralPath $out -Raw | ConvertFrom-Json
    $cue = $pred.cue_results[0]
    $summary += [pscustomobject]@{
        case_id = $caseId
        predicted_width_px = [double]$cue.max_line_width_px
        predicted_frame_ratio = [double]$cue.max_line_width_ratio_frame
        width_band = [string]$cue.width_band
        line_count = [int]$cue.line_count
        status = [string]$cue.status
        split_required = [bool]$cue.split_required
    }
}

$summaryPath = Join-Path $PredictionsDir 'preflight-summary.json'
$summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $summaryPath -Encoding UTF8
Write-Output $summaryPath
$summary | Format-Table -AutoSize
