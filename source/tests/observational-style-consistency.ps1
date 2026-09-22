#Requires -Version 5.1
<#
.SYNOPSIS
  Validates observational-info-short Style contract for v0.1.1-dev (architecture-aligned).
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
$refRoot = Join-Path $Payload '.cursor\skills\video-editing\observational-info-short\references'
$qaPath = Join-Path $refRoot 'qa.md'
$editingRef = Join-Path $refRoot 'editing.md'
$typoRef = Join-Path $refRoot 'typography-graphics.md'
$styleDoc = Join-Path $ProjectRoot 'docs\06-style-first-editing.md'
$intakeRule = Get-Content (Join-Path $Payload '.cursor\rules\production-entry-intake.mdc') -Raw -Encoding UTF8
$l3 = Get-Content (Join-Path $Payload '.cursor\skills\video-production\SKILL.md') -Raw -Encoding UTF8
$l1 = Get-Content (Join-Path $Payload 'video-workflow\capabilities\davinci-resolve.md') -Raw -Encoding UTF8
$briefTpl = Get-Content (Join-Path $Payload 'video-workflow\templates\production-brief.yaml') -Raw -Encoding UTF8
$briefRef = Get-Content (Join-Path $Payload 'video-workflow\templates\production-brief-reference.md') -Raw -Encoding UTF8
$utf8 = New-Object System.Text.UTF8Encoding $false
$skill = [System.IO.File]::ReadAllText($skillPath, $utf8)
$qa = [System.IO.File]::ReadAllText($qaPath, $utf8)
$editing = [System.IO.File]::ReadAllText($editingRef, $utf8)
$typo = [System.IO.File]::ReadAllText($typoRef, $utf8)
$colorEffects = [System.IO.File]::ReadAllText((Join-Path $refRoot 'color-effects.md'), $utf8)
$styleFirst = [System.IO.File]::ReadAllText($styleDoc, $utf8)
$version = (Get-Content (Join-Path $Root 'VERSION') -Raw).Trim()

# O01 display name
Assert-True ($skill -match 'display_name:') 'O01 display_name in SKILL frontmatter'
Assert-True ($skill -match 'Canonical name:') 'O01 canonical name in SKILL'

# O02 style-first + blueprint
Assert-True (Test-Path -LiteralPath $styleDoc) 'O02 style-first doc exists'
Assert-True ($skill -match 'Edit Blueprint') 'O02 blueprint required in SKILL'
Assert-True ($l3 -match 'Edit Blueprint') 'O02 blueprint in L3 pipeline'

# O03 reference structure (7 files)
$refs = @('directing.md', 'visual-language.md', 'editing.md', 'typography-graphics.md', 'sound-music.md', 'color-effects.md', 'qa.md')
$o3 = $true
foreach ($r in $refs) {
    if (-not (Test-Path (Join-Path $refRoot $r))) { $o3 = $false }
}
Assert-True $o3 'O03 seven reference files present'

# O04 creative_direction + author_intent
Assert-True ($briefTpl -match 'creative_direction') 'O04 creative_direction in brief'
Assert-True ($briefTpl -match 'author_intent') 'O04 author_intent in brief'
Assert-True ($skill -match 'Author Intent') 'O04 author intent in SKILL'

# O05 content authority
Assert-True ($briefTpl -match 'content:\s*[\s\S]*authority:') 'O05 content.authority in brief'

# O06 subtitle semantics (in typography reference)
Assert-True ($typo -match 'Content vs Presentation') 'O06 subtitle semantics distinction'

# O07 intentional subtitle gap
Assert-True ($editing -match 'Original Sound') 'O07 original sound / gap concept in editing ref'

# O08 subtitle layout
Assert-True ($typo -match '76.?78%') 'O08 subtitle target width'
Assert-True ($typo -match 'max \*\*2 lines\*\*|max \*\*2 lines\*\*') 'O08 max two lines'

# O09 motion strategy
Assert-True (($editing -match 'Motion Strategy') -and ($editing -match 'MUST')) 'O09 Motion Strategy MUST'

# O10 motion_normalization feature
Assert-True ($briefTpl -match 'motion_normalization:\s*true') 'O10 motion_normalization default'

# O11 mixed-fps
Assert-True ($editing -match 'Mixed FPS') 'O11 mixed-fps in editing reference'
Assert-True ($l3 -match 'Source FPS Distribution') 'O11 mixed-fps in L3 Analyze'

# O12 music
Assert-True ($skill -match 'sound-music.md') 'O12 music in reference map'

# O13-16 dimensions via references
Assert-True ($editing -match 'Transition Strategy') 'O13 transitions in editing ref'
Assert-True ($typo -match 'Graphics Strategy') 'O14 graphics in typography ref'
Assert-True ((Join-Path $refRoot 'color-effects.md' | Test-Path)) 'O15 color-effects reference exists'
Assert-True ($colorEffects -match 'Effects Strategy') 'O16 effects in editing/color refs'

# O17 final artifact QA
Assert-True ($l3 -match 'Final Artifact QA') 'O17 Final Artifact QA in L3'
Assert-True ($qa -match 'OBS-QA-FINAL-RENDER') 'O17 style final render QA id'

# O18 timeline vs final
Assert-True ($l3 -match 'Timeline State QA') 'O18 timeline QA separated'
Assert-True ($typo -match 'Timeline subtitle count') 'O18 timeline subtitle not sufficient'

# O19 capability truth
Assert-True ($l1 -match 'subtitle\.line_break_control') 'O19 subtitle.line_break_control capability'
Assert-True ($l1 -match 'N02_V2_READINESS_GATE') 'O19 V2 readiness gate documented'

# O20 version
Assert-True ($version -eq '0.1.1-dev') 'O20 VERSION is 0.1.1-dev'

# O21 deprecated style.md
$styleCompat = [System.IO.File]::ReadAllText((Join-Path $refRoot 'style.md'), $utf8)
Assert-True ($styleCompat -match 'DEPRECATED') 'O21 style.md deprecated pointer only'

# O22 aesthetic priority in L3
Assert-True ($l3 -match 'Aesthetic Decision Priority') 'O22 aesthetic priority in L3'

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
exit 0
