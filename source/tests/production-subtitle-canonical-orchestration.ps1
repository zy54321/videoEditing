#Requires -Version 5.1
<#
.SYNOPSIS
  R1 Closeout — L3 production subtitle route + mandatory canonical gate (E2E).
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$Pass = 0
$Fail = 0

function Assert-True {
    param([bool]$Condition, [string]$Name)
    if ($Condition) { Write-Host "[PASS] $Name" -ForegroundColor Green; $script:Pass++ }
    else { Write-Host "[FAIL] $Name" -ForegroundColor Red; $script:Fail++ }
}

Write-Host '=== R1 Production Canonical Subtitle Orchestration (E2E) ===' -ForegroundColor Cyan

$fixture = Join-Path $PSScriptRoot 'fixtures\r1-subtitle-production-e2e'
$tmp = Join-Path $PSScriptRoot '.tmp-r1-production-e2e'
if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force }
$prod = Join-Path $tmp 'video-workflow\production'
$toolsSrc = Join-Path $Root 'payload\video-workflow\tools'
New-Item -ItemType Directory -Path $prod -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $fixture 'brief.yaml') -Destination (Join-Path $prod 'brief.yaml')
Copy-Item -LiteralPath (Join-Path $fixture 'frozen-script.txt') -Destination (Join-Path $prod 'frozen-script.txt')
Copy-Item -LiteralPath (Join-Path $fixture 'asr-timing-evidence.json') -Destination (Join-Path $prod 'asr-timing-evidence.json')

$toolsDst = Join-Path $tmp 'video-workflow\tools'
Copy-Item -LiteralPath $toolsSrc -Destination $toolsDst -Recurse -Force

$route = Join-Path $toolsDst 'invoke-frozen-script-subtitle-route.ps1'
$rendererGate = Join-Path $toolsDst 'assert-subtitle-renderer-canonical-input.ps1'

& $route -WorkspaceRoot $tmp -NoPause
Assert-True ($LASTEXITCODE -eq 0) 'E2E invoke-frozen-script-subtitle-route exit 0'

$canonical = Join-Path $prod 'canonical-subtitle-cues.json'
$gateResult = Join-Path $prod 'subtitle-canonical-gate-result.json'
Assert-True (Test-Path -LiteralPath $canonical) 'E2E canonical-subtitle-cues.json created'
Assert-True (Test-Path -LiteralPath $gateResult) 'E2E gate result JSON created'

$doc = Get-Content -LiteralPath $canonical -Raw -Encoding UTF8 | ConvertFrom-Json
$flat = -join ($doc.cues | ForEach-Object { $_.text })
$expected = (Get-Content -LiteralPath (Join-Path $prod 'frozen-script.txt') -Raw -Encoding UTF8).Trim().Replace("`r", '').Replace("`n", '')
Assert-True ($flat -eq $expected) 'E2E cue text matches frozen script'
Assert-True ($flat -notmatch '实践') 'E2E no ASR homophone in renderer input'

$gate = Get-Content -LiteralPath $gateResult -Raw -Encoding UTF8 | ConvertFrom-Json
Assert-True ($gate.verdict -eq 'PASS' -and $gate.gate -eq 'SUBTITLE_CANONICAL_AUTHORITY_GATE') 'E2E SUBTITLE_CANONICAL_AUTHORITY_GATE PASS'

& $rendererGate -WorkspaceRoot $tmp
Assert-True ($LASTEXITCODE -eq 0) 'E2E renderer gate PASS when canonical present'

Remove-Item -LiteralPath $canonical -Force
& $rendererGate -WorkspaceRoot $tmp
$rendererBypassExit = $LASTEXITCODE
Assert-True ($rendererBypassExit -eq 3) 'E2E renderer gate FAIL when canonical bypassed'

$l3 = Get-Content (Join-Path $Root 'payload\.cursor\skills\video-production\SKILL.md') -Raw -Encoding UTF8
Assert-True ($l3 -match 'invoke-frozen-script-subtitle-route') 'L3 references production subtitle orchestrator'
Assert-True ($l3 -match 'SUBTITLE_CANONICAL_AUTHORITY_GATE') 'L3 references mandatory gate'
Assert-True ($l3 -match 'assert-subtitle-renderer-canonical-input') 'L3 references renderer fail-closed gate'

Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
exit 0
