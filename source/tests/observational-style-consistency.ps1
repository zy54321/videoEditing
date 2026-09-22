#Requires -Version 5.1
<#
.SYNOPSIS
  Validates observational-info-short Style-first contract for v0.1.1-dev.
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

$skillPath = Join-Path $Payload '.cursor\skills\video-editing\observational-info-short\SKILL.md'
$qaPath = Join-Path $Payload '.cursor\skills\video-editing\observational-info-short\references\qa.md'
$styleDoc = Join-Path $ProjectRoot 'docs\06-style-first-editing.md'
$intakeRule = Get-Content (Join-Path $Payload '.cursor\rules\production-entry-intake.mdc') -Raw -Encoding UTF8
$l3 = Get-Content (Join-Path $Payload '.cursor\skills\video-production\SKILL.md') -Raw -Encoding UTF8
$l1 = Get-Content (Join-Path $Payload 'video-workflow\capabilities\davinci-resolve.md') -Raw -Encoding UTF8
$briefTpl = Get-Content (Join-Path $Payload 'video-workflow\templates\production-brief.yaml') -Raw -Encoding UTF8
$briefRef = Get-Content (Join-Path $Payload 'video-workflow\templates\production-brief-reference.md') -Raw -Encoding UTF8
$utf8 = New-Object System.Text.UTF8Encoding $false
$skill = [System.IO.File]::ReadAllText($skillPath, $utf8)
$qa = [System.IO.File]::ReadAllText($qaPath, $utf8)
$styleFirst = [System.IO.File]::ReadAllText($styleDoc, $utf8)
$version = (Get-Content (Join-Path $Root 'VERSION') -Raw).Trim()

# 1 canonical display name
Assert-True ($skill -match 'display_name:') 'O01 display_name in SKILL frontmatter'
Assert-True ($skill -match 'Canonical display name:') 'O01 canonical display name label in SKILL'

# 2 Style-first principle
Assert-True (Test-Path -LiteralPath $styleDoc) 'O02 style-first doc exists'
Assert-True (($styleFirst -match 'WHAT / WHEN / WHY') -or ($skill -match 'WHAT / WHEN / WHY')) 'O02 Style authority WHAT/WHEN/WHY'

# 3 seventeen dimensions
$dims = @(
    'Style Identity', 'Narrative Grammar', 'Pacing', 'Shot Grammar', 'Source Selection',
    'Motion Strategy', 'Framing Strategy', 'Transition Strategy', 'Subtitle Strategy',
    'Voice Treatment', 'Music Strategy', 'Sound Design', 'Graphics', 'Color', 'Effects Strategy',
    'Ending Strategy', 'Style QA'
)
$o3 = $true
foreach ($d in $dims) {
    if ($skill -notmatch $d) { $o3 = $false }
}
Assert-True $o3 'O03 all 17 Style dimensions referenced'

# 4 creative_direction
Assert-True ($briefTpl -match 'creative_direction') 'O04 creative_direction in brief template'
Assert-True ($briefRef -match 'editing\.creative_direction') 'O04 creative_direction in brief reference'
Assert-True ($intakeRule -match 'Creative Direction') 'O04 creative direction in intake rule'

# 5 content authority
Assert-True ($briefTpl -match 'content:\s*[\s\S]*authority:') 'O05 content.authority in brief'
Assert-True ($intakeRule -match 'Content Authority') 'O05 content authority in intake'

# 6 subtitle semantics vs timing
Assert-True ($skill -match 'Content Semantics vs Presentation') 'O06 subtitle semantics distinction'
Assert-True ($styleFirst -match 'Content vs Presentation') 'O06 in style-first doc'

# 7 intentional subtitle gap
Assert-True ($skill -match 'Intentional Subtitle Gap') 'O07 intentional subtitle gap allowed'

# 8 subtitle layout
Assert-True ($skill -match '80.?86%') 'O08 subtitle layout safe width'
Assert-True ($skill -match 'max \*\*2 lines\*\*|max \*\*2 lines\*\*|2 lines') 'O08 max two lines'

# 9 motion strategy
Assert-True (($skill -match 'Motion Normalization') -and ($skill -match 'MUST')) 'O09 Motion Strategy MUST normalization'

# 10 motion normalization MUST in features
Assert-True ($briefTpl -match 'motion_normalization:\s*true') 'O10 motion_normalization feature default'

# 11 mixed-fps
Assert-True ($skill -match 'Source FPS Distribution') 'O11 mixed-fps analysis in L2'
Assert-True ($l3 -match 'Source FPS Distribution') 'O11 mixed-fps in L3 Analyze'

# 12 music multi-section
Assert-True ($skill -match 'Narrative turn') 'O12 music section roles'
Assert-True ($skill -match 'second track') 'O12 multiple music allowed'

# 13 voice treatment
Assert-True ($skill -match 'Voice Treatment') 'O13 Voice Treatment section'

# 14 sound design
Assert-True ($skill -match 'Sound Design') 'O14 Sound Design section'

# 15 color look
Assert-True ($skill -match 'Color / Look Strategy') 'O15 Color Look section'

# 16 effects
Assert-True ($skill -match 'Effects Strategy') 'O16 Effects Strategy section'

# 17 final artifact QA
Assert-True ($l3 -match 'Final Artifact QA') 'O17 Final Artifact QA in L3'
Assert-True ($qa -match 'OBS-QA-FINAL-RENDER') 'O17 style final render QA id'

# 18 timeline vs final
Assert-True ($l3 -match 'Timeline State QA') 'O18 timeline QA separated'
Assert-True ($skill -match 'Timeline subtitle count') 'O18 timeline subtitle not sufficient'

# 19 capability truth
Assert-True ($l1 -match 'subtitle\.line_break_control') 'O19 subtitle.line_break_control capability'
Assert-True ($l1 -match 'subtitle\.visual_style') 'O19 subtitle.visual_style capability'
Assert-True ($l1 -match 'N02_V2_READINESS_GATE') 'O19 V2 readiness gate documented'
Assert-True (($l1 -match 'subtitle\.create') -and ($l1 -match 'visual_style')) 'O19 capability truth explicit'

# 20 version
Assert-True ($version -eq '0.1.1-dev') 'O20 VERSION is 0.1.1-dev'

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
exit 0
