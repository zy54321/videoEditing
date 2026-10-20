#Requires -Version 5.1
<#
.SYNOPSIS
  Opt-in external ASS deliver — R1 canonical cues → ASS → libass burn-in (post clean master).
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspaceRoot,
    [string]$ContractPath = '',
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$WorkspaceRoot = [System.IO.Path]::GetFullPath($WorkspaceRoot)
$tools = Join-Path $WorkspaceRoot 'video-workflow\tools'
$prod = Join-Path $WorkspaceRoot 'video-workflow\production'

if ([string]::IsNullOrWhiteSpace($ContractPath)) {
    $ContractPath = Join-Path $prod 'final-render-contract.json'
}
if (-not (Test-Path -LiteralPath $ContractPath)) {
    throw 'EXTERNAL_ASS_ROUTE_BLOCKED: final-render-contract.json missing'
}

$contract = Get-Content -LiteralPath $ContractPath -Raw -Encoding UTF8 | ConvertFrom-Json
$route = [string]$contract.renderer_route
$mat = [string]$contract.subtitle_materialization

if ($route -ne 'external_ass' -and $mat -ne 'external_ass_burnin') {
    Write-Host 'EXTERNAL_ASS_DELIVER_ROUTE: SKIP (contract is not external_ass)'
    exit 0
}

$canonical = if ($contract.PSObject.Properties['canonical_subtitle_cues_path']) { [string]$contract.canonical_subtitle_cues_path } else { '' }
$clean = if ($contract.PSObject.Properties['clean_master_path']) { [string]$contract.clean_master_path } else { '' }
$final = if ($contract.PSObject.Properties['final_artifact_path']) { [string]$contract.final_artifact_path } else { '' }
$ass = if ($contract.PSObject.Properties['ass_path']) { [string]$contract.ass_path } else { '' }

if ([string]::IsNullOrWhiteSpace($canonical)) {
    $canonical = Join-Path $prod 'canonical-subtitle-cues.json'
}
if ([string]::IsNullOrWhiteSpace($ass)) {
    $ass = Join-Path $prod 'external-deliver.ass'
}

foreach ($p in @($canonical, $clean)) {
    if (-not (Test-Path -LiteralPath $p)) {
        throw "EXTERNAL_ASS_ROUTE_BLOCKED: missing $p"
    }
}
if ([string]::IsNullOrWhiteSpace($final)) {
    throw 'EXTERNAL_ASS_ROUTE_BLOCKED: final_artifact_path empty in contract'
}

$toAss = Join-Path $tools 'canonical-to-external-ass.py'
$burn = Join-Path $tools 'external-ass-burnin.py'
foreach ($p in @($toAss, $burn)) {
    if (-not (Test-Path -LiteralPath $p)) { throw "MISSING: $p" }
}

$manifest = Join-Path $prod 'external-ass-materialization.json'
& python $toAss --canonical $canonical --out $ass --manifest $manifest
if ($LASTEXITCODE -ne 0) { throw 'CANONICAL_TO_EXTERNAL_ASS_FAILED' }

$finalPath = [System.IO.Path]::GetFullPath($final)
$finalDir = Split-Path -Parent $finalPath
if (-not (Test-Path -LiteralPath $finalDir)) {
    New-Item -ItemType Directory -Path $finalDir -Force | Out-Null
}

$inter = Join-Path $prod '_external_ass_burnin_intermediate.mp4'
if ((Test-Path -LiteralPath $finalPath) -and -not $Force) {
    throw "EXTERNAL_ASS_ROUTE_BLOCKED: final exists (use -Force for new version): $finalPath"
}

& python $burn --clean-master $clean --ass $ass --out $inter
if ($LASTEXITCODE -ne 0) { throw 'EXTERNAL_ASS_BURNIN_FAILED' }
if (-not (Test-Path -LiteralPath $inter)) { throw 'EXTERNAL_ASS_BURNIN_OUTPUT_MISSING' }

if (Test-Path -LiteralPath $finalPath) { Remove-Item -LiteralPath $finalPath -Force }
Move-Item -LiteralPath $inter -Destination $finalPath -Force

$result = @{
    route               = 'external_ass'
    policy              = 'astra-external-ass-n02prod-v1'
    canonical_path      = $canonical
    ass_path            = $ass
    clean_master_path   = $clean
    final_artifact_path = $finalPath
    materialization_manifest = $manifest
    status              = 'OK'
    completed_at        = (Get-Date).ToString('o')
}
$resultPath = Join-Path $prod 'external-ass-deliver-result.json'
$result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $resultPath -Encoding UTF8

Write-Host "EXTERNAL_ASS_DELIVER_ROUTE: OK -> $finalPath" -ForegroundColor Green
exit 0
