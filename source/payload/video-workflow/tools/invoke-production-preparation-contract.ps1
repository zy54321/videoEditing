#Requires -Version 5.1
<#
.SYNOPSIS
  PREPARATION closeout — deterministic Brief → final-render-contract + render-prep verdict.
.DESCRIPTION
  Runs at PREPARATION_GATE boundary (after Brief save). Does not replace U3 FINAL_ARTIFACT_GATE.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspaceRoot,
    [string]$BriefPath = '',
    [switch]$NoWrite
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$WorkspaceRoot = [System.IO.Path]::GetFullPath($WorkspaceRoot)
$prod = Join-Path $WorkspaceRoot 'video-workflow\production'
$tools = Join-Path $WorkspaceRoot 'video-workflow\tools'
$buildCli = Join-Path $tools 'build-final-render-contract-from-brief.py'

if ([string]::IsNullOrWhiteSpace($BriefPath)) {
    $BriefPath = Join-Path $prod 'brief.yaml'
}
if (-not (Test-Path -LiteralPath $BriefPath)) {
    Write-Host 'RENDER_PREPARATION_CONTRACT_BLOCKED: brief.yaml missing' -ForegroundColor Red
    exit 4
}
if (-not (Test-Path -LiteralPath $buildCli)) {
    throw "MISSING: $buildCli"
}

$contractPath = Join-Path $prod 'final-render-contract.json'
$resultPath = Join-Path $prod 'preparation-contract-result.json'
$args = @(
    $buildCli,
    '--brief', $BriefPath,
    '--workspace', $WorkspaceRoot,
    '--json'
)
if (-not $NoWrite) {
    $args += @('--out', $contractPath, '--force')
} else {
    $args += '--dry-run'
}

$stdout = (& python @args 2>$null | Out-String).Trim()
$code = $LASTEXITCODE
if (-not $stdout) { throw 'Empty output from build-final-render-contract-from-brief.py' }
$payload = $stdout | ConvertFrom-Json
$status = [string]$payload.status

$renderPrep = switch ($status) {
    'CONTRACT_READY' { 'PASS' }
    'INCOMPLETE' { 'PENDING' }
    default { 'FAIL' }
}

$gateVerdict = switch ($renderPrep) {
    'PASS' { 'PASS' }
    'PENDING' { 'PENDING' }
    default { 'FAIL' }
}

$doc = @{
    gate                          = 'RENDER_PREPARATION_CONTRACT'
    contract_preparation_status   = $status
    render_preparation_contract   = $renderPrep
    final_delivery_gate_status    = 'NOT_RUN'
    final_delivery_gate_note      = 'U3 closeout not invoked; CONTRACT_READY is not FINAL_ARTIFACT_GATE PASS'
    verdict                       = $gateVerdict
    build_exit_code               = $code
    errors                        = @($payload.errors)
    final_artifact_path           = $payload.final_artifact_path
    contract_path                 = if ($status -eq 'CONTRACT_READY' -and -not $NoWrite) { $contractPath } else { $null }
    completed_at                  = (Get-Date).ToString('o')
}
$doc | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $resultPath -Encoding UTF8

if ($status -eq 'BLOCKED') {
    Write-Host "RENDER_PREPARATION_CONTRACT: FAIL ($($payload.errors -join '; '))" -ForegroundColor Red
    exit 1
}
if ($status -eq 'INCOMPLETE') {
    Write-Host 'RENDER_PREPARATION_CONTRACT: PENDING (contract not deliverable yet)' -ForegroundColor Yellow
    exit 2
}
if (-not $NoWrite -and -not (Test-Path -LiteralPath $contractPath)) {
    Write-Host 'RENDER_PREPARATION_CONTRACT_BLOCKED: contract file missing after build' -ForegroundColor Red
    exit 4
}

Write-Host 'RENDER_PREPARATION_CONTRACT: PASS (CONTRACT_READY)' -ForegroundColor Green
exit 0
