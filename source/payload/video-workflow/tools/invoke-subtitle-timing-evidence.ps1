#Requires -Version 5.1
<#
.SYNOPSIS
  Ensure word-level subtitle timing evidence exists before Canonical build.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspaceRoot,
    [string]$BriefPath = '',
    [string]$ScriptPath = '',
    [string]$VoiceAudioPath = '',
    [string]$ResolveTranscriptionPath = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$WorkspaceRoot = [System.IO.Path]::GetFullPath($WorkspaceRoot)
$prod = Join-Path $WorkspaceRoot 'video-workflow\production'
$tools = Join-Path $WorkspaceRoot 'video-workflow\tools'
if ([string]::IsNullOrWhiteSpace($BriefPath)) {
    $BriefPath = Join-Path $prod 'brief.yaml'
}
$cli = Join-Path $PSScriptRoot 'acquire-subtitle-timing-evidence.py'
if (-not (Test-Path -LiteralPath $cli)) {
    $cli = Join-Path $tools 'acquire-subtitle-timing-evidence.py'
}
if (-not (Test-Path -LiteralPath $cli)) {
    throw "MISSING: acquire-subtitle-timing-evidence.py"
}

$evidence = Join-Path $prod 'asr-timing-evidence.json'
$binding = Join-Path $prod 'subtitle-timing-binding.json'
$report = Join-Path $prod 'subtitle-timing-quality-report.json'
$args = @(
    $cli,
    '--evidence', $evidence,
    '--binding', $binding,
    '--report', $report
)
if (-not [string]::IsNullOrWhiteSpace($ScriptPath)) { $args += @('--script', $ScriptPath) }
if (-not [string]::IsNullOrWhiteSpace($VoiceAudioPath)) { $args += @('--voice-audio', $VoiceAudioPath) }
if (-not [string]::IsNullOrWhiteSpace($ResolveTranscriptionPath)) {
    $args += @('--resolve-transcription', $ResolveTranscriptionPath)
}
$stdout = & python @args
if ($LASTEXITCODE -ne 0) {
    Write-Host "SUBTITLE_TIMING_EVIDENCE: BLOCKED $stdout" -ForegroundColor Red
    exit 4
}
Write-Host "SUBTITLE_TIMING_EVIDENCE: $stdout"
exit 0
