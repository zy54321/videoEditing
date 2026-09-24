#Requires -Version 5.1
<#
.SYNOPSIS
  Validates Production Continuous Execution contract (post N02 V4 review).
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
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

Write-Host '=== Production Continuous Execution Tests ===' -ForegroundColor Cyan
Write-Host ''

$utf8 = New-Object System.Text.UTF8Encoding $false
$core = [System.IO.File]::ReadAllText((Join-Path $Payload '.cursor\rules\video-workflow-core.mdc'), $utf8)
$intake = [System.IO.File]::ReadAllText((Join-Path $Payload '.cursor\rules\production-entry-intake.mdc'), $utf8)
$l3 = [System.IO.File]::ReadAllText((Join-Path $Payload '.cursor\skills\video-production\SKILL.md'), $utf8)
$review = [System.IO.File]::ReadAllText((Join-Path (Split-Path -Parent $Root) 'validation\first-real-production-review-n02-v4.md'), $utf8)

# Contract presence
Assert-True ($core -match 'Continuous Production Execution') 'CE01 core rule continuous execution section'
Assert-True ($l3 -match 'Continuous Execution Contract') 'CE02 L3 continuous execution contract'
Assert-True ($l3 -match 'CONTINUE_AUTONOMOUSLY') 'CE03 CONTINUE_AUTONOMOUSLY defined'
Assert-True ($l3 -match 'WAIT_FOR_OWNER_CONTINUE') 'CE04 WAIT_FOR_OWNER_CONTINUE forbidden state'
Assert-True ($l3 -match 'Production Authority inherits') 'CE05 authority inheritance documented'

# Case A — normal production must continue autonomously
Assert-True ($l3 -match 'CONTINUE_AUTONOMOUSLY') 'CE-A1 Case A CONTINUE_AUTONOMOUSLY'
Assert-True ($intake -match 'MUST NOT') 'CE-A2 intake MUST NOT gate present'
Assert-True ($intake -match 'OWNER_DECISION_REQUIRED') 'CE-A3 intake pause outcomes aligned'
Assert-True ($core -match 'Continuous Production Execution') 'CE-A4 core continuous execution MUST'

# Case B — blocker
Assert-True ($l3 -match '\| `BLOCKED` \|') 'CE-B1 Case B BLOCKED outcome'
Assert-True ($core -match '`BLOCKED`') 'CE-B2 core BLOCKED pause condition'

# Case C — owner decision
Assert-True ($l3 -match 'OWNER_DECISION_REQUIRED') 'CE-C1 Case C OWNER_DECISION_REQUIRED'
Assert-True ($l3 -match 'Frozen Voice') 'CE-C2 Frozen Voice triggers owner decision'

# Case D — scope boundary
Assert-True ($l3 -match 'AUTHORIZATION_REQUIRED') 'CE-D1 Case D AUTHORIZATION_REQUIRED'

# Case E — progress without pause
Assert-True ($l3 -match 'Progress.*not.*pause' -or $l3 -match 'Progress ≠ pause') 'CE-E1 progress does not equal pause'
Assert-True ($l3 -match 'Forbidden turn endings') 'CE-E2 forbidden turn endings listed'

# Forbidden patterns documented
$forbiddenOk = ($l3 -match 'Forbidden turn endings') -and ($l3 -match 'progress-only checklist')
Assert-True $forbiddenOk 'CE06 forbidden turn-ending patterns documented'

# Inherited actions list
$inheritOk = ($l3 -match 'blueprint') -and ($l3 -match 'render') -and ($l3 -match 'subtitle') -and ($l3 -match 'closeout')
Assert-True $inheritOk 'CE07 inherited action domains listed'

# Review registration
Assert-True ($review -match 'FIRST_REAL_PRODUCTION_E2E') 'CE08 review records E2E gate'
Assert-True ($review -match 'PRODUCTION_CONTINUOUS_EXECUTION') 'CE09 review records continuous execution truth'
Assert-True ($review -match '\*\*FAILED\*\*') 'CE09b review records FAILED status for continuous execution'
Assert-True ($review -match 'checkpointed production runner') 'CE10 checkpoint runner risk registered'

# Audit: no new wait-for-continue in L3 pipeline stages
Assert-True ($l3 -match 'MUST NOT.*WAIT_FOR_OWNER_CONTINUE' -or $l3 -match 'WAIT_FOR_OWNER_CONTINUE') 'CE11 WAIT_FOR_OWNER_CONTINUE contract'
Assert-True ($l3 -match 'checkpointed production runner') 'CE12 runner escalation documented in L3'

# Intake cross-reference after READY
Assert-True ($intake -match 'Continuous Execution Contract') 'CE13 intake references continuous execution contract'

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
exit 0
