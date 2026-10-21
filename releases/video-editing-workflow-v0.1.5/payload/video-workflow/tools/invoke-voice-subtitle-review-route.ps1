#Requires -Version 5.1
<#
.SYNOPSIS
  U1 — Voice subtitle text review route (deterministic + safe degradation).
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
$prod = Join-Path $WorkspaceRoot 'video-workflow\production'
$tools = Join-Path $WorkspaceRoot 'video-workflow\tools'

if ([string]::IsNullOrWhiteSpace($BriefPath)) {
    $BriefPath = Join-Path $prod 'brief.yaml'
}

$cli = Join-Path $tools 'run-voice-subtitle-review.py'
if (-not (Test-Path -LiteralPath $cli)) { throw "MISSING: $cli" }

$stdout = (& python $cli --workspace $WorkspaceRoot --brief $BriefPath --json 2>$null | Out-String).Trim()
if (-not $stdout) { throw 'Empty review output' }
$payload = $stdout | ConvertFrom-Json
$status = [string]$payload.status

if ($status -eq 'NOT_APPLICABLE') {
    Write-Host 'VOICE_SUBTITLE_REVIEW: SKIP'
    exit 0
}
if ($status -eq 'BLOCKED') {
    Write-Host "VOICE_SUBTITLE_REVIEW: BLOCKED ($($payload.anomalies.Count) anomalies)" -ForegroundColor Red
    exit 1
}
if ($status -eq 'NEEDS_OWNER_REVIEW') {
    Write-Host 'VOICE_SUBTITLE_REVIEW: NEEDS_OWNER_REVIEW' -ForegroundColor Yellow
    exit 2
}
if ($status -eq 'AUTO_ACCEPTED') {
    Write-Host 'VOICE_SUBTITLE_REVIEW: AUTO_ACCEPTED (unexpected in repo runtime)' -ForegroundColor Yellow
    exit 2
}
Write-Host "VOICE_SUBTITLE_REVIEW: $status"
exit 0
