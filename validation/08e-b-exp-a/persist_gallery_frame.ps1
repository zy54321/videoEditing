#Requires -Version 5.1
<#
.SYNOPSIS
  Helper for A1 frame persistence via gallery_stills (manual MCP step documents paths).

  MCP sequence (Resolve must be on Color page, playhead set on Edit page first):
    1. timeline_markers set_current_timecode
    2. resolve_control open_page color
    3. gallery_stills grab_and_export (cleanup=false)

  Then run this script to copy latest PNG into case evidence path and measure.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SourcePng,
    [Parameter(Mandatory = $true)]
    [string]$CaseId,
    [string]$OutDir = (Join-Path $PSScriptRoot 'renders'),
    [string]$MeasureScript = (Join-Path $PSScriptRoot 'measure_subtitle_width.py')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $SourcePng)) {
    throw "SOURCE_NOT_FOUND: $SourcePng"
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$dest = Join-Path $OutDir "$CaseId.png"
Copy-Item -LiteralPath $SourcePng -Destination $dest -Force

$measureOut = Join-Path $PSScriptRoot "measurements\$CaseId.measurement.json"
New-Item -ItemType Directory -Force -Path (Split-Path $measureOut) | Out-Null
python $MeasureScript $dest --out $measureOut | Write-Host
Write-Host "Saved: $dest"
Write-Host "Measurement: $measureOut"
