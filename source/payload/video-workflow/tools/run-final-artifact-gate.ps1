#Requires -Version 5.1
<#
.SYNOPSIS
  R2 — Post-render: final-artifact-qa.ps1 + FINAL_ARTIFACT_GATE.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspaceRoot,
    [string]$ContractPath = '',
    [string]$VideoPath = '',
    [string]$RunId = '',
    [switch]$SkipAudioLoudness
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$WorkspaceRoot = [System.IO.Path]::GetFullPath($WorkspaceRoot)
$prod = Join-Path $WorkspaceRoot 'video-workflow\production'
$tools = Join-Path $WorkspaceRoot 'video-workflow\tools'
$qaRoot = Join-Path $WorkspaceRoot 'video-workflow\.qa'

if ([string]::IsNullOrWhiteSpace($ContractPath)) {
    $ContractPath = Join-Path $prod 'final-render-contract.json'
}
if ([string]::IsNullOrWhiteSpace($VideoPath)) {
    if (-not (Test-Path -LiteralPath $ContractPath)) {
        throw 'FINAL_RENDER_CONTRACT_MISSING'
    }
    $contractPreview = Get-Content -LiteralPath $ContractPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $VideoPath = [string]$contractPreview.final_artifact_path
}

$qaPs1 = Join-Path $tools 'final-artifact-qa.ps1'
$gatePy = Join-Path $tools 'run-final-artifact-gate.py'
if (-not (Test-Path -LiteralPath $qaPs1)) { throw "MISSING: $qaPs1" }
if (-not (Test-Path -LiteralPath $gatePy)) { throw "MISSING: $gatePy" }

if ([string]::IsNullOrWhiteSpace($RunId)) {
    $RunId = 'final-gate-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
}

$gateResult = Join-Path $prod 'final-artifact-gate-result.json'
$invalid = @{
    gate            = 'FINAL_ARTIFACT_GATE'
    verdict         = 'INVALIDATED'
    status          = 'RUNNING'
    invalidated_at  = (Get-Date).ToString('o')
    final_artifact_path = $VideoPath
} | ConvertTo-Json -Depth 4
Set-Content -LiteralPath $gateResult -Value $invalid -Encoding UTF8

try {
    $qaArgs = @{
        VideoPath = $VideoPath
        QaRoot    = $qaRoot
        RunId     = $RunId
    }
    if ($SkipAudioLoudness) { $qaArgs['SkipAudioLoudness'] = $true }
    $qaOutLines = & $qaPs1 @qaArgs
    $qaReportPath = $qaOutLines | Select-Object -First 1
    if (-not (Test-Path -LiteralPath $qaReportPath)) {
        throw "FINAL_ARTIFACT_QA_REPORT_MISSING: $qaReportPath"
    }

    $workDir = Join-Path $qaRoot $RunId 'subtitle-burnin-frames'
    & python $gatePy --contract $ContractPath --qa-report $qaReportPath --work-dir $workDir --out $gateResult
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'FINAL_ARTIFACT_GATE: FAIL' -ForegroundColor Red
        exit 2
    }

    Write-Host 'FINAL_ARTIFACT_GATE: PASS' -ForegroundColor Green
    Write-Host "PRODUCTION_FINAL_RENDER_PASS: candidate ($VideoPath)"
    exit 0
}
catch {
    $fail = @{
        gate    = 'FINAL_ARTIFACT_GATE'
        verdict = 'FAIL'
        status  = 'ERROR'
        error   = $_.Exception.Message
        failed_at = (Get-Date).ToString('o')
    } | ConvertTo-Json -Depth 4
    Set-Content -LiteralPath $gateResult -Value $fail -Encoding UTF8
    throw
}
