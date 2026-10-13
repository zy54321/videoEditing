#Requires -Version 5.1
<#
.SYNOPSIS
  Fail-closed — Production Complete requires FINAL_ARTIFACT_GATE PASS.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspaceRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$WorkspaceRoot = [System.IO.Path]::GetFullPath($WorkspaceRoot)
$gateResult = Join-Path $WorkspaceRoot 'video-workflow\production\final-artifact-gate-result.json'

if (-not (Test-Path -LiteralPath $gateResult)) {
    Write-Host 'PRODUCTION_COMPLETE_BLOCKED: final-artifact-gate-result.json missing' -ForegroundColor Red
    exit 4
}

$gate = Get-Content -LiteralPath $gateResult -Raw -Encoding UTF8 | ConvertFrom-Json
if ($gate.gate -ne 'FINAL_ARTIFACT_GATE' -or $gate.verdict -ne 'PASS') {
    Write-Host 'PRODUCTION_COMPLETE_BLOCKED: FINAL_ARTIFACT_GATE not PASS' -ForegroundColor Red
    exit 4
}

Write-Host 'PRODUCTION_FINAL_RENDER_PASS: gate verified'
exit 0
