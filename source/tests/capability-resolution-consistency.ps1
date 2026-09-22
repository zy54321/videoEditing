#Requires -Version 5.1
<#
.SYNOPSIS
  Validates Capability Resolution contract wiring (Stage 08D.1).
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

Write-Host '=== Capability Resolution Consistency Tests ===' -ForegroundColor Cyan
Write-Host ''

Assert-True ($l3 -match 'SELECTED') 'CR01 resolution status SELECTED'
Assert-True ($l3 -match 'FALLBACK') 'CR02 resolution status FALLBACK'
Assert-True ($l3 -match 'AVAILABLE_UNVERIFIED') 'CR03 AVAILABLE_UNVERIFIED explicit'
Assert-True ($l3 -match 'must not.*SELECTED') 'CR03b AU must not direct SELECTED'
Assert-True ($l3 -match 'UNSAFE') 'CR04 UNSAFE prohibited'
Assert-True ($resRef -match 'UNSAFE') 'CR04b UNSAFE in state matrix'
Assert-True ($vocab -notmatch 'status:\s+UNAVAILABLE\b') 'CR05 no non-canonical UNAVAILABLE state'
Assert-True ($vocab -match 'canonical_states:') 'CR05b canonical states declared'
Assert-True (($vocab -match 'visual.motion.pan') -and ($vocab -match 'visual.motion.pan[\s\S]{0,80}AVAILABLE_UNVERIFIED')) 'CR06 pan downgraded'
Assert-True ($vocab -match 'audio.music.level_under_voice') 'CR07 level_under_voice logical ID'
Assert-True ($policy -match 'audio.music.level_under_voice') 'CR07b duck fallback to level_under_voice'
Assert-True ($policy -match 'effect_preservation') 'CR08 fallback semantic metadata'
Assert-True ($policy -match 'cannot guarantee 76-78%') 'CR08b pixel width degradation honest'
Assert-True ($resTpl -match 'effect_preservation') 'CR09 resolution records degradation'
Assert-True ($resRef -match 'not an aesthetic score') 'CR10 coverage not aesthetic score'
Assert-True ($l3 -match 'capability-resolution.yaml') 'CR11 L3 runtime resolution path'

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'verify-capability-coverage.ps1') | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'CR12 coverage mechanically verified'

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
exit 0
