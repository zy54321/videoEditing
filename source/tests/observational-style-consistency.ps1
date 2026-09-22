#Requires -Version 5.1
<#
.SYNOPSIS
  Validates observational-info-short Style contract for v0.1.1-dev (Stage 08D canonical).
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

Write-Host '=== Observational Style Consistency Tests ===' -ForegroundColor Cyan
Write-Host ''

$styleRoot = Join-Path $Payload '.cursor\skills\video-editing\observational-info-short'
$skillPath = Join-Path $styleRoot 'SKILL.md'
$refRoot = Join-Path $styleRoot 'references'
$styleDoc = Join-Path $ProjectRoot 'docs\06-style-first-editing.md'
$l3 = Get-Content (Join-Path $Payload '.cursor\skills\video-production\SKILL.md') -Raw -Encoding UTF8
$l1 = Get-Content (Join-Path $Payload 'video-workflow\capabilities\davinci-resolve.md') -Raw -Encoding UTF8
$briefTpl = Get-Content (Join-Path $Payload 'video-workflow\templates\production-brief.yaml') -Raw -Encoding UTF8
$utf8 = New-Object System.Text.UTF8Encoding $false
$skill = [System.IO.File]::ReadAllText($skillPath, $utf8)
$rhythm = [System.IO.File]::ReadAllText((Join-Path $refRoot '03-editing-rhythm.md'), $utf8)
$typo = [System.IO.File]::ReadAllText((Join-Path $refRoot '04-typography-graphics.md'), $utf8)
$colorFx = [System.IO.File]::ReadAllText((Join-Path $refRoot '06-color-look-effects.md'), $utf8)
$qa08 = [System.IO.File]::ReadAllText((Join-Path $refRoot '08-qa.md'), $utf8)
$version = (Get-Content (Join-Path $Root 'VERSION') -Raw).Trim()

Assert-True ($skill -match 'display_name:') 'O01 display_name in SKILL frontmatter'
Assert-True ($skill -match 'Canonical name:') 'O01 canonical name in SKILL'

Assert-True (Test-Path -LiteralPath $styleDoc) 'O02 style-first doc exists'
Assert-True ($skill -match 'Edit Blueprint') 'O02 blueprint required in SKILL'
Assert-True ($l3 -match 'Edit Blueprint') 'O02 blueprint in L3 pipeline'

$refs = @('01-directing.md','02-visual-language.md','03-editing-rhythm.md','04-typography-graphics.md','05-sound-music.md','06-color-look-effects.md','07-taste.md','08-qa.md')
$o3 = $true
foreach ($r in $refs) {
    if (-not (Test-Path (Join-Path $refRoot $r))) { $o3 = $false }
}
Assert-True $o3 'O03 eight canonical reference files present'

Assert-True (Test-Path (Join-Path $styleRoot 'style-profile.yaml')) 'O03b style-profile.yaml present'
Assert-True (Test-Path (Join-Path $styleRoot 'capability-policy.yaml')) 'O03c capability-policy.yaml present'

Assert-True ($briefTpl -match 'creative_direction') 'O04 creative_direction in brief'
Assert-True ($briefTpl -match 'author_intent') 'O04 author_intent in brief'
Assert-True ($skill -match 'Author Intent') 'O04 author intent in SKILL'

Assert-True ($briefTpl -match 'content:\s*[\s\S]*authority:') 'O05 content.authority in brief'

Assert-True ($typo -match 'semantic') 'O06 subtitle semantics in typography ref'

Assert-True ($rhythm -match 'original sound') 'O07 original sound in rhythm ref'

Assert-True ($typo -match '76') 'O08 subtitle target width'
Assert-True ($typo -match 'two lines') 'O08 max two lines'

Assert-True ($rhythm -match 'motion = SKIPPED') 'O09 motion normalization required'

Assert-True ($briefTpl -match 'motion_normalization:\s*true') 'O10 motion_normalization default'

Assert-True ($rhythm -match 'Mixed-fps') 'O11 mixed-fps in rhythm reference'
Assert-True ($l3 -match 'Source FPS Distribution') 'O11 mixed-fps in L3 Analyze'

Assert-True ($skill -match '05-sound-music.md') 'O12 sound reference in SKILL'

Assert-True ($rhythm -match 'Transition') 'O13 transitions in rhythm ref'
Assert-True ($typo -match 'Graphics') 'O14 graphics in typography ref'
Assert-True (Test-Path (Join-Path $refRoot '06-color-look-effects.md')) 'O15 color-look-effects reference exists'
Assert-True ($colorFx -match 'Effects') 'O16 effects in color-look-effects ref'

Assert-True ($l3 -match 'Final Artifact QA') 'O17 Final Artifact QA in L3'
Assert-True ($qa08 -match 'OBS-STYLE-') 'O17 style fidelity QA ids in 08-qa'

Assert-True ($l3 -match 'Timeline State QA') 'O18 timeline QA separated'
Assert-True ($qa08 -match 'not technical') 'O18 08-qa separated from technical QA'

Assert-True ($l1 -match 'subtitle\.line_break_control') 'O19 subtitle.line_break_control capability'
Assert-True ($l1 -match 'N02_V2_READINESS_GATE') 'O19 V2 readiness gate documented'

Assert-True ($version -eq '0.1.1-dev') 'O20 VERSION is 0.1.1-dev'

$styleCompat = [System.IO.File]::ReadAllText((Join-Path $refRoot 'style.md'), $utf8)
Assert-True ($styleCompat -match 'DEPRECATED') 'O21 style.md deprecated pointer only'

Assert-True ($l3 -match 'Aesthetic Decision Priority') 'O22 aesthetic priority in L3'

Assert-True ($l3 -match 'Capability Resolution') 'O23 L3 Capability Resolution'
Assert-True ($skill -match 'Production Brief') 'O24 format authority from Brief not Style'
Assert-True (Test-Path (Join-Path $ProjectRoot 'docs\08-l2-style-contract-aesthetic-intelligence.md')) 'O25 Stage 08D architecture doc'

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
exit 0
