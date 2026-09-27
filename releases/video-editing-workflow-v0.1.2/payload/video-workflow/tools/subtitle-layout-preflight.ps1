#Requires -Version 5.1
<#
.SYNOPSIS
  Deterministic subtitle layout preflight — L1 measurement / wrap / split detection.
.DESCRIPTION
  Uses System.Drawing text measurement. Does NOT write to Resolve / Timeline.
  Preflight PASS != Final Artifact PASS (renderer parity unvalidated).
.PARAMETER RequestPath
  Path to subtitle-layout-request.json
.PARAMETER OutputPath
  Path to write subtitle-layout-result.json
.PARAMETER FontPolicy
  allow_fallback | fail_closed
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RequestPath,
    [Parameter(Mandatory = $true)]
    [string]$OutputPath,
    [ValidateSet('allow_fallback', 'fail_closed')]
    [string]$FontPolicy = 'allow_fallback'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$enginePath = Join-Path $PSScriptRoot 'lib\subtitle-layout-engine.ps1'
. $enginePath

if (-not (Test-Path -LiteralPath $RequestPath)) {
    throw "REQUEST_NOT_FOUND: $RequestPath"
}

$json = [System.IO.File]::ReadAllText($RequestPath, (New-Object System.Text.UTF8Encoding $false))
$request = $json | ConvertFrom-Json

if ([int]$request.schema_version -ne 1) {
    throw "UNSUPPORTED_SCHEMA_VERSION: $($request.schema_version)"
}

$result = Invoke-SubtitleLayoutPreflight -Request $request -FontPolicy $FontPolicy
$outJson = $result | ConvertTo-Json -Depth 12
$utf8 = New-Object System.Text.UTF8Encoding $false
$outDir = Split-Path -Parent $OutputPath
if ($outDir -and -not (Test-Path -LiteralPath $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}
[System.IO.File]::WriteAllText($OutputPath, $outJson, $utf8)
Write-Output $OutputPath
