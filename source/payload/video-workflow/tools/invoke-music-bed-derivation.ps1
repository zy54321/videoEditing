#Requires -Version 5.1
<#
.SYNOPSIS
  Measure narration and music, write a derived bed, and fail unless the report is PASS.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspaceRoot,
    [string]$BriefPath = '',
    [switch]$CheckOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$WorkspaceRoot = [System.IO.Path]::GetFullPath($WorkspaceRoot)
$tools = Join-Path $WorkspaceRoot 'video-workflow\tools'
if ([string]::IsNullOrWhiteSpace($BriefPath)) {
    $BriefPath = Join-Path $WorkspaceRoot 'video-workflow\production\brief.yaml'
}
$cli = Join-Path $PSScriptRoot 'ensure-music-bed.py'
if (-not (Test-Path -LiteralPath $cli)) {
    $cli = Join-Path $tools 'ensure-music-bed.py'
}
if (-not (Test-Path -LiteralPath $cli)) {
    throw 'MISSING: ensure-music-bed.py'
}
$profilePath = Join-Path $PSScriptRoot '..\runtime\narration-short-v1-audio-mix-profile.yaml'
if (-not (Test-Path -LiteralPath $profilePath)) {
    $profilePath = Join-Path $WorkspaceRoot 'video-workflow\runtime\narration-short-v1-audio-mix-profile.yaml'
}
$pyArgs = @($cli, '--workspace', $WorkspaceRoot, '--brief', $BriefPath, '--profile', $profilePath)
if ($CheckOnly) { $pyArgs += '--check-only' }
& python @pyArgs
exit $LASTEXITCODE
