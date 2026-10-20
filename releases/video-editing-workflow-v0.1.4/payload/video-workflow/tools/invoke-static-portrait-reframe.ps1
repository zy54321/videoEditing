#Requires -Version 5.1
<#
.SYNOPSIS
  R3 production orchestration — timeline probe → static-portrait-reframe plan (optional Resolve apply).
.DESCRIPTION
  Policy: static-portrait-reframe.v1 (zoom-only cover). Replaces ad-hoc crop+zoom bulk scripts.
  Probe JSON: MCP timeline.probe_timeline_structure export → video-workflow/production/timeline-probe.json
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspaceRoot,
    [string]$ProbePath = '',
    [string]$PlanPath = '',
    [string]$ExpectedTimeline = '',
    [switch]$Apply,
    [string]$McpRoot = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$WorkspaceRoot = [System.IO.Path]::GetFullPath($WorkspaceRoot)
$tools = Join-Path $WorkspaceRoot 'video-workflow\tools'
$prod = Join-Path $WorkspaceRoot 'video-workflow\production'

if ([string]::IsNullOrWhiteSpace($ProbePath)) {
    $ProbePath = Join-Path $prod 'timeline-probe.json'
}
if ([string]::IsNullOrWhiteSpace($PlanPath)) {
    $PlanPath = Join-Path $prod 'static-portrait-reframe-plan.json'
}

$buildCli = Join-Path $tools 'build-static-portrait-reframe-plan.py'
$applyCli = Join-Path $tools 'apply-static-portrait-reframe-bulk.py'

foreach ($p in @($ProbePath, $buildCli)) {
    if (-not (Test-Path -LiteralPath $p)) {
        throw "STATIC_PORTRAIT_REFRAME_BLOCKED: missing $p"
    }
}

& python $buildCli --probe $ProbePath --out $PlanPath
if ($LASTEXITCODE -ne 0) {
    throw 'STATIC_PORTRAIT_REFRAME_PLAN_FAILED'
}

$plan = Get-Content -LiteralPath $PlanPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($plan.status -ne 'OK') {
    throw "STATIC_PORTRAIT_REFRAME_PLAN_STATUS: $($plan.status)"
}

Write-Host "STATIC_PORTRAIT_REFRAME_PLAN: OK shots=$($plan.shot_count) policy=$($plan.policy_id)" -ForegroundColor Green

if (-not $Apply) {
    Write-Host 'STATIC_PORTRAIT_REFRAME_APPLY: SKIPPED (pass -Apply to write Resolve transforms)'
    exit 0
}

if (-not (Test-Path -LiteralPath $applyCli)) {
    throw "MISSING: $applyCli"
}

$applyArgs = @('--plan', $PlanPath, '--result-out', (Join-Path $prod 'static-portrait-reframe-apply-result.json'))
if ($ExpectedTimeline) { $applyArgs += @('--expected-timeline', $ExpectedTimeline) }
elseif ($plan.timeline_name) { $applyArgs += @('--expected-timeline', [string]$plan.timeline_name) }
if ($McpRoot) { $applyArgs += @('--mcp-root', $McpRoot) }

& python $applyCli @applyArgs
if ($LASTEXITCODE -ne 0) {
    throw 'STATIC_PORTRAIT_REFRAME_APPLY_FAILED'
}

Write-Host 'STATIC_PORTRAIT_REFRAME_APPLY: OK' -ForegroundColor Green
exit 0
