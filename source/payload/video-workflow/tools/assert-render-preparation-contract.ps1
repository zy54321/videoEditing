#Requires -Version 5.1
<#
.SYNOPSIS
  Fail-closed before render — requires CONTRACT_READY + on-disk contract matching Brief.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspaceRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$WorkspaceRoot = [System.IO.Path]::GetFullPath($WorkspaceRoot)
$prod = Join-Path $WorkspaceRoot 'video-workflow\production'
$resultPath = Join-Path $prod 'preparation-contract-result.json'
$contractPath = Join-Path $prod 'final-render-contract.json'
$briefPath = Join-Path $prod 'brief.yaml'

if (-not (Test-Path -LiteralPath $resultPath)) {
    Write-Host 'RENDER_PREP_ASSERT_BLOCKED: preparation-contract-result.json missing (run invoke-production-preparation-contract.ps1)' -ForegroundColor Red
    exit 4
}
$result = Get-Content -LiteralPath $resultPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($result.gate -ne 'RENDER_PREPARATION_CONTRACT') {
    Write-Host 'RENDER_PREP_ASSERT_BLOCKED: wrong gate id' -ForegroundColor Red
    exit 4
}
if ($result.render_preparation_contract -ne 'PASS') {
    Write-Host "RENDER_PREP_ASSERT_BLOCKED: render_preparation_contract=$($result.render_preparation_contract)" -ForegroundColor Red
    exit 4
}
if ($result.contract_preparation_status -ne 'CONTRACT_READY') {
    Write-Host 'RENDER_PREP_ASSERT_BLOCKED: not CONTRACT_READY' -ForegroundColor Red
    exit 4
}
if ($result.final_delivery_gate_status -ne 'NOT_RUN') {
    Write-Host 'RENDER_PREP_ASSERT_BLOCKED: unexpected final_delivery_gate_status' -ForegroundColor Red
    exit 4
}
if (-not (Test-Path -LiteralPath $contractPath)) {
    Write-Host 'RENDER_PREP_ASSERT_BLOCKED: final-render-contract.json missing' -ForegroundColor Red
    exit 4
}

$tools = Join-Path $WorkspaceRoot 'video-workflow\tools'
$validatePy = @"
import sys
from pathlib import Path
sys.path.insert(0, r'$($tools -replace "'","''")\\lib')
from brief_final_render_contract import load_brief_yaml, validate_contract_matches_brief
from final_render_contract import load_final_render_contract
ws = Path(r'$($WorkspaceRoot -replace "'","''")')
brief = load_brief_yaml(ws / 'video-workflow/production/brief.yaml')
c = load_final_render_contract(ws / 'video-workflow/production/final-render-contract.json')
errs = validate_contract_matches_brief(brief, c, workspace_root=ws, brief_dir=ws/'video-workflow/production')
from brief_final_render_contract import validate_render_preparation_canonical_binding
errs.extend(validate_render_preparation_canonical_binding(ws, ws/'video-workflow/production/brief.yaml'))
if errs:
    print(';'.join(errs))
    sys.exit(4)
print('OK')
sys.exit(0)
"@
$out = & python -c $validatePy 2>&1 | Select-Object -Last 1
if ($LASTEXITCODE -ne 0) {
    Write-Host "RENDER_PREP_ASSERT_BLOCKED: $out" -ForegroundColor Red
    exit 4
}

$musicCli = Join-Path $tools 'invoke-music-bed-derivation.ps1'
if (Test-Path -LiteralPath $musicCli) {
    & $musicCli -WorkspaceRoot $WorkspaceRoot -BriefPath $briefPath -CheckOnly | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'RENDER_PREP_ASSERT_BLOCKED: MUSIC_BED_STALE_OR_FAILED' -ForegroundColor Red
        exit 4
    }
}

Write-Host 'RENDER_PREPARATION_CONTRACT_ASSERT: PASS'
exit 0
