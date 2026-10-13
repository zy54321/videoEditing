#Requires -Version 5.1
<#
.SYNOPSIS
  R1 Production orchestration — Frozen Script + ASR evidence → Canonical Subtitle Cues + gate.
.DESCRIPTION
  Mandatory path when Brief requires frozen script subtitle authority.
  Writes video-workflow/production/canonical-subtitle-cues.json and gate result.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspaceRoot,
    [string]$BriefPath = '',
    [string]$AsrEvidencePath = '',
    [switch]$NoPause
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$WorkspaceRoot = [System.IO.Path]::GetFullPath($WorkspaceRoot)
$tools = Join-Path $WorkspaceRoot 'video-workflow\tools'
$prod = Join-Path $WorkspaceRoot 'video-workflow\production'

if ([string]::IsNullOrWhiteSpace($BriefPath)) {
    $BriefPath = Join-Path $prod 'brief.yaml'
}
if ([string]::IsNullOrWhiteSpace($AsrEvidencePath)) {
    $AsrEvidencePath = Join-Path $prod 'asr-timing-evidence.json'
}

$buildCli = Join-Path $tools 'build-canonical-subtitle-cues.py'
$gateCli = Join-Path $tools 'validate-canonical-subtitle-authority-gate.py'
$detectPy = @"
import json, sys
from pathlib import Path
sys.path.insert(0, r'$($tools -replace "'","''")\\lib')
from brief_subtitle_authority import load_brief_dict, brief_requires_canonical_subtitle_route
b = load_brief_dict(Path(r'$($BriefPath -replace "'","''")'))
print('REQUIRED' if brief_requires_canonical_subtitle_route(b) else 'SKIP')
"@

$need = & python -c $detectPy 2>&1 | Select-Object -Last 1
if ($need -eq 'SKIP') {
    Write-Host 'FROZEN_SCRIPT_SUBTITLE_ROUTE: SKIP (Brief does not require canonical authority)'
    exit 0
}
if ($need -ne 'REQUIRED') {
    throw "BRIEF_DETECT_FAILED: $need"
}

foreach ($p in @($BriefPath, $AsrEvidencePath, $buildCli, $gateCli)) {
    if (-not (Test-Path -LiteralPath $p)) {
        throw "FROZEN_SCRIPT_SUBTITLE_ROUTE_BLOCKED: missing $p"
    }
}

$canonicalOut = Join-Path $prod 'canonical-subtitle-cues.json'
$gateOut = Join-Path $prod 'subtitle-canonical-gate-result.json'

& python $buildCli --brief $BriefPath --asr $AsrEvidencePath --out $canonicalOut
if ($LASTEXITCODE -ne 0) {
    throw 'CANONICAL_SUBTITLE_BUILD_FAILED'
}

& python $gateCli --canonical $canonicalOut --brief $BriefPath --asr $AsrEvidencePath --out $gateOut
if ($LASTEXITCODE -ne 0) {
    throw 'SUBTITLE_CANONICAL_AUTHORITY_GATE_FAIL'
}

Write-Host 'SUBTITLE_CANONICAL_AUTHORITY_GATE: PASS' -ForegroundColor Green
if (-not $NoPause) { }
exit 0
