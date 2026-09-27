#Requires -Version 5.1
<#
.SYNOPSIS
  Step 5 disposable Resolve probe orchestrator (Route A checkpoint).
.DESCRIPTION
  Requires Resolve running. If gold standard not captured, stops with OWNER_MANUAL_GOLD_STANDARD_REQUIRED.
#>
[CmdletBinding()]
param(
    [string]$ProjectName = '_mcp_VEW-Native-Subtitle-Readability-Unblock',
    [string]$BaselineDrt = '',
    [string]$StyledDrt = '',
    [string]$EvidenceRoot = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$wfRoot = Split-Path -Parent $scriptDir
$payloadRoot = Split-Path -Parent $wfRoot
$sourceRoot = Split-Path -Parent $payloadRoot
$repoRoot = Split-Path -Parent $sourceRoot
$templateDir = Join-Path $wfRoot 'runtime\native-drt-subtitle-stroke-template'
$captureCli = Join-Path $scriptDir 'native-drt-subtitle-stroke-capture.py'

if ([string]::IsNullOrWhiteSpace($EvidenceRoot)) {
    $EvidenceRoot = Join-Path $repoRoot 'validation\native-subtitle-readability-unblock'
}
New-Item -ItemType Directory -Force -Path $EvidenceRoot | Out-Null

$statusPath = Join-Path $EvidenceRoot 'probe-status.json'

if ([string]::IsNullOrWhiteSpace($BaselineDrt) -or [string]::IsNullOrWhiteSpace($StyledDrt)) {
    @{
        status = 'OWNER_MANUAL_GOLD_STANDARD_REQUIRED'
        project = $ProjectName
        required_owner_action = 'In disposable Resolve project, set Native Subtitle track: white text + black outer stroke, then export/save baseline vs styled DRT pair.'
        next_command = "native-drt-subtitle-stroke-capture.py <baseline.drt> <styled.drt>"
    } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $statusPath -Encoding UTF8
    Write-Output $statusPath
    Write-Output 'OWNER_MANUAL_GOLD_STANDARD_REQUIRED'
    exit 3
}

$lines = & python $captureCli $BaselineDrt $StyledDrt --template-dir $templateDir 2>&1 | ForEach-Object { "$_" }
$out = ($lines | Out-String).Trim()
$start = $out.IndexOf('{'); $end = $out.LastIndexOf('}')
if ($start -lt 0 -or $end -le $start) { throw "CAPTURE_PARSE_FAILED: $out" }
$capture = $out.Substring($start, $end - $start + 1) | ConvertFrom-Json
$report = [ordered]@{
    status = if ($capture.template_valid) { 'TEMPLATE_CAPTURED' } else { 'CAPTURE_INVALID' }
    capture = $capture
    evidence_root = $EvidenceRoot
}
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statusPath -Encoding UTF8
Write-Output $statusPath
Write-Output $report.status
if (-not $capture.template_valid) { exit 2 }
exit 0
