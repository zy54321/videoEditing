#Requires -Version 5.1
<#
.SYNOPSIS
  Fail-closed gate before any subtitle renderer (DRT / ASS) in Frozen Script Production.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspaceRoot,
    [string]$BriefPath = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$WorkspaceRoot = [System.IO.Path]::GetFullPath($WorkspaceRoot)
$tools = Join-Path $WorkspaceRoot 'video-workflow\tools'
$prod = Join-Path $WorkspaceRoot 'video-workflow\production'

if ([string]::IsNullOrWhiteSpace($BriefPath)) {
    $BriefPath = Join-Path $prod 'brief.yaml'
}

$detectPy = @"
import sys
from pathlib import Path
sys.path.insert(0, r'$($tools -replace "'","''")\\lib')
from brief_subtitle_authority import load_brief_dict, brief_requires_canonical_subtitle_route
b = load_brief_dict(Path(r'$($BriefPath -replace "'","''")'))
print('REQUIRED' if brief_requires_canonical_subtitle_route(b) else 'SKIP')
"@

$need = & python -c $detectPy 2>&1 | Select-Object -Last 1
if ($need -eq 'SKIP') {
    Write-Host 'RENDERER_SUBTITLE_GATE: SKIP'
    exit 0
}
if ($need -ne 'REQUIRED') {
    throw "BRIEF_DETECT_FAILED: $need"
}

$canonical = Join-Path $prod 'canonical-subtitle-cues.json'
$gateResult = Join-Path $prod 'subtitle-canonical-gate-result.json'

if (-not (Test-Path -LiteralPath $canonical)) {
    Write-Host 'RENDERER_SUBTITLE_AUTHORITY_BYPASS_BLOCKED: canonical-subtitle-cues.json missing' -ForegroundColor Red
    exit 3
}
if (-not (Test-Path -LiteralPath $gateResult)) {
    Write-Host 'RENDERER_SUBTITLE_AUTHORITY_BYPASS_BLOCKED: subtitle-canonical-gate-result.json missing' -ForegroundColor Red
    exit 3
}

$gate = Get-Content -LiteralPath $gateResult -Raw -Encoding UTF8 | ConvertFrom-Json
if ($gate.verdict -ne 'PASS' -or $gate.gate -ne 'SUBTITLE_CANONICAL_AUTHORITY_GATE') {
    Write-Host 'RENDERER_SUBTITLE_AUTHORITY_BYPASS_BLOCKED: gate not PASS' -ForegroundColor Red
    exit 3
}

Write-Host 'RENDERER_SUBTITLE_GATE: PASS (canonical authority)'
exit 0
