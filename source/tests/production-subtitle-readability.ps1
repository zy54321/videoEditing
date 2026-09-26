#Requires -Version 5.1
<#
.SYNOPSIS
  Production Repair Step 2 — Native DRT subtitle readability profile & truth regression.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$Payload = Join-Path $Root 'payload'
$RepoRoot = Split-Path -Parent $Root
$Pass = 0
$Fail = 0

function Assert-True {
    param([bool]$Condition, [string]$Name)
    if ($Condition) { Write-Host "[PASS] $Name" -ForegroundColor Green; $script:Pass++ }
    else { Write-Host "[FAIL] $Name" -ForegroundColor Red; $script:Fail++ }
}

Write-Host '=== Production Subtitle Readability Tests ===' -ForegroundColor Cyan
Write-Host ''

$utf8 = New-Object System.Text.UTF8Encoding $false
$profilePath = Join-Path $Payload 'video-workflow\runtime\native-drt-subtitle-readability-profile.yaml'
$refPath = Join-Path $Payload 'video-workflow\templates\native-drt-subtitle-readability-reference.md'
$l1 = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\capabilities\davinci-resolve.md'), $utf8)
$vocab = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\capabilities\logical-capability-vocabulary.yaml'), $utf8)
$l3 = [System.IO.File]::ReadAllText((Join-Path $Payload '.cursor\skills\video-production\SKILL.md'), $utf8)
$textplusProfile = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\runtime\textplus-production-profile.yaml'), $utf8)
$closeout = Join-Path $RepoRoot 'validation\production-repair-step2-subtitle-stroke-closeout.md'

# 1 — Profile contract
Assert-True (Test-Path $profilePath) 'R01 profile file exists'
$profile = [System.IO.File]::ReadAllText($profilePath, $utf8)
Assert-True ($profile -match 'profile_id:\s*native-drt-subtitle-readability-v1') 'R02 profile_id'
Assert-True ($profile -match 'route:\s*native_drt_subtitles') 'R03 route frozen'
Assert-True ($profile -match 'color:\s*white') 'R04 foreground white'
Assert-True ($profile -match 'outline:[\s\S]{0,120}enabled:\s*true') 'R05 outline enabled default'
Assert-True ($profile -match 'color:\s*black') 'R06 outline black'
Assert-True ($profile -match 'stroke_automation:\s*VERIFIED') 'R07 stroke automation VERIFIED truth'
Assert-True ($profile -match 'textplus_overlay') 'R08 profile forbids Text+ overlay default'

# 2 — Reference doc
Assert-True (Test-Path $refPath) 'R09 reference doc exists'
$ref = [System.IO.File]::ReadAllText($refPath, $utf8)
Assert-True ($ref -match 'AVAILABLE_MANUAL') 'R10 manual UI stroke documented'
Assert-True ($ref -match 'BLOCKED') 'R11 automation BLOCKED documented'

# 3 — L1 capability truth
Assert-True ($l1 -match 'subtitle\.render\.readability_stroke') 'R12 L1 readability_stroke capability present'
Assert-True ($l1 -match 'subtitle\.render\.readability_stroke[\s\S]{0,160}VERIFIED') 'R13 readability_stroke VERIFIED'
Assert-True ($l1 -match 'native_drt_subtitles[\s\S]{0,120}VERIFIED') 'R14 native_drt_subtitles still VERIFIED'
Assert-True ($l1 -match 'subtitle\.line_break_control[\s\S]{0,120}VERIFIED') 'R15 semantic/line-break regression'
Assert-True ($l1 -match 'subtitle\.safe_text_width[\s\S]{0,120}AVAILABLE_UNVERIFIED') 'R16 safe_text_width / pixel_width unchanged'
Assert-True ($l1 -match 'subtitle\.keyword_emphasis[\s\S]{0,160}AVAILABLE_UNVERIFIED') 'R17 keyword emphasis unchanged'

# 4 — Vocabulary
Assert-True ($vocab -match 'subtitle\.render\.readability_stroke:') 'R18 vocab readability_stroke entry'
Assert-True ($vocab -match 'subtitle\.render\.readability_stroke:[\s\S]{0,120}status:\s*VERIFIED') 'R19 vocab status VERIFIED'
Assert-True ($vocab -match 'subtitle\.style\.keyword_emphasis:[\s\S]{0,160}status:\s*AVAILABLE_UNVERIFIED') 'R20 vocab keyword emphasis unchanged'
Assert-True ($vocab -match 'subtitle\.layout\.pixel_width:[\s\S]{0,160}status:\s*AVAILABLE_UNVERIFIED') 'R21 vocab pixel_width unchanged'
Assert-True ($vocab -match 'subtitle\.segment\.semantic:[\s\S]{0,120}status:\s*VERIFIED') 'R22 semantic segmentation regression'

# 5 — Text+ production truth not upgraded
Assert-True ($textplusProfile -match 'stroke_px:\s*0') 'R23 Text+ stroke_px still 0'
Assert-True ($l1 -match 'textplus_styledtextcls_import_comp[\s\S]{0,80}VERIFIED \(isolated\)') 'R24 Text+ isolated truth preserved'

# 6 — L3 wiring
Assert-True ($l3 -match 'native-drt-subtitle-readability-profile\.yaml') 'R25 L3 references readability profile'
Assert-True ($l3 -match 'subtitle\.render\.readability_stroke') 'R26 L3 documents readability capability'
Assert-True ($l3 -match 'subtitle\.render\.readability_stroke[\s\S]{0,100}VERIFIED') 'R27 L3 stroke capability VERIFIED'

# 7 — Closeout artifact
Assert-True (Test-Path $closeout) 'R28 closeout doc exists'

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
