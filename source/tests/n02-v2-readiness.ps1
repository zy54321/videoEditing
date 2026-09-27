#Requires -Version 5.1
<#
.SYNOPSIS
  Validates N02 V2 execution readiness contracts for v0.1.1.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$ProjectRoot = Split-Path -Parent $Root
$Payload = Join-Path $Root 'payload'
$Pass = 0
$Fail = 0

function Assert-True {
    param([bool]$Condition, [string]$Name)
    if ($Condition) {
        Write-Host "[PASS] $Name" -ForegroundColor Green
        $script:Pass++
    } else {
        Write-Host "[FAIL] $Name" -ForegroundColor Red
        $script:Fail++
    }
}

Write-Host '=== N02 V2 Readiness Tests ===' -ForegroundColor Cyan
Write-Host ''

$l1 = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\capabilities\davinci-resolve.md'), [System.Text.UTF8Encoding]::new($false))
$l3 = [System.IO.File]::ReadAllText((Join-Path $Payload '.cursor\skills\video-production\SKILL.md'), [System.Text.UTF8Encoding]::new($false))
$l2 = [System.IO.File]::ReadAllText((Join-Path $Payload '.cursor\skills\video-editing\observational-info-short\SKILL.md'), [System.Text.UTF8Encoding]::new($false))
$spike = [System.IO.File]::ReadAllText((Join-Path $ProjectRoot 'validation\capability-spike\STAGE-08A1-n02-v2-execution-readiness.md'), [System.Text.UTF8Encoding]::new($false))
$qaTool = Join-Path $Payload 'video-workflow\tools\final-artifact-qa.ps1'
$version = (Get-Content (Join-Path $Root 'VERSION') -Raw).Trim()

Assert-True ($l1 -match 'N02_V1_CAPABILITY_GATE') 'R01 V1 gate renamed'
Assert-True ($l1 -match 'N02_V2_READINESS_GATE') 'R01 V2 gate exists'
Assert-True ($l1 -notmatch 'N02_CAPABILITY_GATE\s*=\s*PASS' -or $l1 -match 'N02_V1_CAPABILITY_GATE') 'R01 old N02_CAPABILITY_GATE not sole gate'
Assert-True ($l1 -match 'N02_V2_READINESS_GATE\s*=\s*PASS') 'R02 V2 gate PASS documented'

Assert-True ($l1 -match 'subtitle\.line_break_control') 'R03 subtitle capabilities split'
Assert-True ($l1 -match 'subtitle\.safe_text_width') 'R03 safe text width capability'
Assert-True ($l1 -match 'subtitle\.line_break_control[\s\S]{0,80}VERIFIED') 'R04 line-break VERIFIED'
Assert-True ($spike -match 'line_break_control') 'R04 line-break spike evidence'

Assert-True ($l2 -match 'Functional fallback') 'R05 functional layout fallback'
Assert-True ($l1 -match 'subtitle\.visual_style[\s\S]{0,120}UNKNOWN') 'R06 visual_style may be UNKNOWN'

Assert-True ($l1 -match 'Safe Cadence Degradation') 'R07 cadence policy exists'
Assert-True ($l1 -match 'mixed_fps\.interpolation[\s\S]{0,80}UNKNOWN') 'R08 interpolation not required VERIFIED'
Assert-True ($l2 -match 'KEEP.*NORMALIZE.*REPLACE') 'R09 motion risk decisions required'

Assert-True ($l1 -match 'color\.basic[\s\S]{0,80}VERIFIED') 'R10 color.basic VERIFIED for V2'
Assert-True (Test-Path -LiteralPath $qaTool) 'R11 final-artifact-qa helper exists'
Assert-True ($l3 -match 'Post-Render Final Artifact QA') 'R12 subtitle visual QA pipeline in L3'
Assert-True ($l1 -match 'final_render\.black_bar_check[\s\S]{0,80}VERIFIED') 'R13 black-bar pipeline VERIFIED'
Assert-True ($l3 -match 'Pre-Render QA.*Render.*Post-Render') 'R14 post-render ordering explicit'
Assert-True ($version -match '^\d+\.\d+\.\d+(-dev)?$') 'R15 VERSION read from source/VERSION authority'

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -eq 0) { exit 0 }
exit 1
