#Requires -Version 5.1
<#
.SYNOPSIS
  Validates Capability Resolution contract wiring (Stage 08D).
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$Payload = Join-Path $Root 'payload'
$Pass = 0
$Fail = 0

function Assert-True {
    param([bool]$Condition, [string]$Name)
    if ($Condition) { Write-Host "[PASS] $Name" -ForegroundColor Green; $script:Pass++ }
    else { Write-Host "[FAIL] $Name" -ForegroundColor Red; $script:Fail++ }
}

$utf8 = New-Object System.Text.UTF8Encoding $false
$l3 = [System.IO.File]::ReadAllText((Join-Path $Payload '.cursor\skills\video-production\SKILL.md'), $utf8)
$resTpl = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\templates\capability-resolution-result.yaml'), $utf8)
$resRef = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\templates\capability-resolution-reference.md'), $utf8)
$vocab = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\capabilities\logical-capability-vocabulary.yaml'), $utf8)
$policy = [System.IO.File]::ReadAllText((Join-Path $Payload '.cursor\skills\video-editing\observational-info-short\capability-policy.yaml'), $utf8)
$coverage = [System.IO.File]::ReadAllText((Join-Path $Payload '.cursor\skills\video-editing\observational-info-short\capability-coverage.yaml'), $utf8)

Write-Host '=== Capability Resolution Consistency Tests ===' -ForegroundColor Cyan
Write-Host ''

Assert-True ($l3 -match 'SELECTED') 'CR01 resolution status SELECTED'
Assert-True ($l3 -match 'FALLBACK') 'CR02 resolution status FALLBACK'
Assert-True ($l3 -match 'UNKNOWN') 'CR03 UNKNOWN not treated as VERIFIED'
Assert-True ($l3 -match 'REQUIRED') 'CR04 REQUIRED fail closed'
Assert-True ($resTpl -match 'coverage:') 'CR05 resolution template coverage block'
Assert-True ($resRef -match 'not an aesthetic score') 'CR06 coverage not aesthetic score'
Assert-True (Test-Path (Join-Path $Payload 'video-workflow\capabilities\logical-capability-vocabulary.yaml')) 'CR07 L1 vocabulary file exists'
Assert-True ($vocab -match 'visual.reframe.static') 'CR08 vocabulary includes visual.reframe.static'
Assert-True ($policy -match 'fallback:') 'CR09 observational policy has fallback'
Assert-True ($coverage -match 'NOT an aesthetic score') 'CR10 observational coverage disclaimer'
Assert-True ($l3 -match 'capability-resolution.yaml') 'CR11 L3 runtime resolution path'

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
exit 0
