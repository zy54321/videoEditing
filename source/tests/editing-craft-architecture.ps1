#Requires -Version 5.1
<#
.SYNOPSIS
  Validates editing craft knowledge layer and Style-first architecture (Stage 08C).
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

Write-Host '=== Editing Craft Architecture Tests ===' -ForegroundColor Cyan
Write-Host ''

$craftDir = Join-Path $Payload 'video-workflow\knowledge\editing-craft'
$craftFiles = @(
    'README.md',
    'directing-story.md',
    'visual-language.md',
    'editing-rhythm.md',
    'writing-and-picture.md',
    'typography-graphics.md',
    'sound-music.md',
    'color-look-effects.md',
    'aesthetic-qa.md'
)

$utf8 = New-Object System.Text.UTF8Encoding $false
$version = (Get-Content (Join-Path $Root 'VERSION') -Raw).Trim()
$skill = [System.IO.File]::ReadAllText((Join-Path $Payload '.cursor\skills\video-editing\observational-info-short\SKILL.md'), $utf8)
$l3 = [System.IO.File]::ReadAllText((Join-Path $Payload '.cursor\skills\video-production\SKILL.md'), $utf8)
$briefTpl = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\templates\production-brief.yaml'), $utf8)
$briefRef = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\templates\production-brief-reference.md'), $utf8)
$bpTpl = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\templates\edit-blueprint.yaml'), $utf8)
$bpRef = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\templates\edit-blueprint-reference.md'), $utf8)
$craftReadme = [System.IO.File]::ReadAllText((Join-Path $craftDir 'README.md'), $utf8)
$aesthetic = [System.IO.File]::ReadAllText((Join-Path $craftDir 'aesthetic-qa.md'), $utf8)
$styleFirst = [System.IO.File]::ReadAllText((Join-Path $ProjectRoot 'docs\06-style-first-editing.md'), $utf8)
$archDoc = [System.IO.File]::ReadAllText((Join-Path $ProjectRoot 'docs\07-editing-craft-architecture.md'), $utf8)
$buildPolicy = [System.IO.File]::ReadAllText((Join-Path $ProjectRoot 'docs\build-stage-no-production.md'), $utf8)
$styleMd = [System.IO.File]::ReadAllText((Join-Path $Payload '.cursor\skills\video-editing\observational-info-short\references\style.md'), $utf8)

# 1 Knowledge layer exists
Assert-True (Test-Path -LiteralPath $craftDir -PathType Container) 'E01 knowledge layer directory exists'

# 2 eight craft files (+ README)
$allCraft = $true
foreach ($f in $craftFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $craftDir $f))) { $allCraft = $false }
}
Assert-True $allCraft 'E02 all craft knowledge files exist'

# 3 style-first principle (ASCII patterns avoid PS encoding issues)
Assert-True (($styleFirst -match 'primary unit') -and ($archDoc -match 'Primary unit:.*STYLE')) 'E03 style-first principle documented'

# 4 L2 not effect-first
Assert-True (($styleFirst -match 'Not.*first-class L2') -and ($styleFirst -match 'subtitle')) 'E04 L2 not effect-first'

# 5 author intent optional
Assert-True ($briefTpl -match 'author_intent:') 'E05 author_intent in brief template'
Assert-True ($briefTpl -match 'global:\s*null') 'E05 author_intent global optional'

# 6 global/local intent
Assert-True ($briefTpl -match 'local:\s*\[\]') 'E06 local intent array supported'
Assert-True ($briefRef -match 'beat_id') 'E06 local intent beat_id in reference'

# 7 blueprint template
Assert-True (Test-Path -LiteralPath (Join-Path $Payload 'video-workflow\templates\edit-blueprint.yaml')) 'E07 blueprint template exists'

# 8 beat-first
Assert-True (($bpRef -match 'Beat-first') -and ($bpTpl -match 'beats:')) 'E08 blueprint beat-first'

# 9 shot plan optional
Assert-True (($bpTpl -match 'shot_plan:\s*null') -and ($bpRef -match 'Shot Plan')) 'E09 shot plan optional'

# 10 shot expansion conditions
Assert-True ($bpRef -match 'When to expand Shot Plan') 'E10 shot expansion conditions documented'

# 11 blueprint non-blocking default
Assert-True (($bpRef -match 'NON_BLOCKING') -and ($l3 -match 'NON_BLOCKING')) 'E11 blueprint default non-blocking'

# 12 review_before_edit
Assert-True (($briefTpl -match 'review_before_edit') -and ($bpTpl -match 'review_before_edit')) 'E12 review_before_edit support'

# 13 seven style reference files
$refFiles = @('directing.md', 'visual-language.md', 'editing.md', 'typography-graphics.md', 'sound-music.md', 'color-effects.md', 'qa.md')
$refsOk = $true
$refRoot = Join-Path $Payload '.cursor\skills\video-editing\observational-info-short\references'
foreach ($r in $refFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $refRoot $r))) { $refsOk = $false }
}
Assert-True $refsOk 'E13 all seven style reference files exist'

# 14 SKILL load order
Assert-True ($skill -match 'Reference Loading Order') 'E14 SKILL references load order defined'

# 15 aesthetic hierarchy (all four levels explicit)
Assert-True ($aesthetic -match 'STRUCTURAL_INVARIANT') 'E15a STRUCTURAL_INVARIANT documented'
Assert-True ($aesthetic -match 'REVIEWED_INVARIANT') 'E15b REVIEWED_INVARIANT documented'
Assert-True ($aesthetic -match 'CRAFT_DEFAULT') 'E15c CRAFT_DEFAULT documented'
Assert-True ($aesthetic -match 'TASTE_OPTION') 'E15d TASTE_OPTION documented'

# 16 craft vs style separation — all topic files (README may use contrast example)
$styleIds = @('observational-info-short', 'lifestyle-vlog', 'news-explainer', 'documentary-short')
$topicFiles = $craftFiles | Where-Object { $_ -ne 'README.md' }
$craftLeakFree = $true
foreach ($tf in $topicFiles) {
    $content = [System.IO.File]::ReadAllText((Join-Path $craftDir $tf), $utf8)
    foreach ($sid in $styleIds) {
        if ($content -match $sid) { $craftLeakFree = $false }
    }
}
Assert-True (($craftReadme -match 'cannot override Style') -and $craftLeakFree) 'E16 craft topic files free of Style authority leak'

# 17 no runtime actions in blueprint
Assert-True (($bpRef -notmatch 'timeline_item') -and ($bpTpl -notmatch 'MCP')) 'E17 runtime actions absent from blueprint template'

# 18 build-stage no-production policy
Assert-True (($buildPolicy -match 'BUILD_STAGE_NO_PRODUCTION') -and ($archDoc -match 'Build vs Production')) 'E18 build-stage no-production policy exists'

# 19 version
Assert-True ($version -eq '0.1.1-dev') 'E19 VERSION is 0.1.1-dev'

# deprecated style.md pointer
Assert-True ($styleMd -match 'DEPRECATED') 'E20 style.md deprecated compatibility pointer'

# 21 L3 pipeline and execution continuity both require Edit Blueprint
$pipelineSection = ($l3 -split '## Production Pipeline', 2)[1]
$continuitySection = ($l3 -split '## Execution Continuity', 2)[1]
Assert-True (($pipelineSection -match 'Generate Edit Blueprint') -and ($continuitySection -match 'Generate Edit Blueprint')) 'E21 L3 flows include Edit Blueprint'
Assert-True ($continuitySection -match 'Analyze must not bypass Edit Blueprint') 'E21 Execution Continuity blocks Blueprint bypass'

# 22 Owner Author Intent authority / provenance
Assert-True ($briefRef -match 'Sole Owner Author Intent authority') 'E22 brief declares sole Owner Author Intent authority'
Assert-True ($briefRef -match 'remains absent') 'E22 Owner Author Intent absent state explicit'
Assert-True ($l3 -match 'Owner Author Intent remains absent') 'E22 L3 does not infer Owner Author Intent'
Assert-True ($bpRef -match 'Brief wins') 'E22 Blueprint defers to Brief on conflict'

# 23 manifest Stage 08C components
$manifestTpl = [System.IO.File]::ReadAllText((Join-Path $Root 'manifest.template.json'), $utf8)
$manifestObj = $manifestTpl | ConvertFrom-Json
$manifestOk = ($manifestObj.components.templates -contains 'edit-blueprint') -and
    ($manifestObj.components.knowledge -contains 'editing-craft')
Assert-True $manifestOk 'E23 manifest lists edit-blueprint and editing-craft'

# 24 build required payload aligned with installer ProductFiles
$buildScript = [System.IO.File]::ReadAllText((Join-Path $Root 'build\build-release.ps1'), $utf8)
$installerScript = [System.IO.File]::ReadAllText((Join-Path $Root 'installer\init-video-workflow.ps1'), $utf8)
Assert-True ($buildScript -match 'Get-InstallerProductFiles') 'E24 build uses installer ProductFiles preflight'
Assert-True ($installerScript -match 'edit-blueprint.yaml') 'E24 installer ProductFiles includes blueprint template'
Assert-True ($installerScript -match 'editing-craft\\README.md') 'E24 installer ProductFiles includes craft knowledge'

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
exit 0
