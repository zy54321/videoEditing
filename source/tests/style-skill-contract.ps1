#Requires -Version 5.1
<#
.SYNOPSIS
  Validates canonical L2 Style Skill contract (Stage 08D).
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
    if ($Condition) { Write-Host "[PASS] $Name" -ForegroundColor Green; $script:Pass++ }
    else { Write-Host "[FAIL] $Name" -ForegroundColor Red; $script:Fail++ }
}

$utf8 = New-Object System.Text.UTF8Encoding $false
. (Join-Path $PSScriptRoot 'lib\style-profile-schema.ps1')
. (Join-Path $PSScriptRoot 'lib\capability-fallback-contract.ps1')

$vocabText = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\capabilities\logical-capability-vocabulary.yaml'), $utf8)
$vocabStatusMap = Get-VocabularyStatusMap -VocabPath (Join-Path $Payload 'video-workflow\capabilities\logical-capability-vocabulary.yaml')
$vocabIds = [regex]::Matches($vocabText, '(?m)^  ([a-z][a-z0-9_.]+):') | ForEach-Object { $_.Groups[1].Value }
$vocabSet = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach ($id in $vocabIds) { $vocabSet.Add($id) | Out-Null }

$requiredRefSections = @(
    '## Style Goal', '## Inherit from Common Craft', '## Style Defaults', '## Prefer When',
    '## Allow When', '## Avoid When', '## Prohibit', '## Exceptions', '## Trade-offs',
    '## Capability Intent', '## Blueprint Mapping', '## QA Signals', '## Reference Cases'
)
$canonicalRefs = @(
    '01-directing.md', '02-visual-language.md', '03-editing-rhythm.md', '04-typography-graphics.md',
    '05-sound-music.md', '06-color-look-effects.md', '07-taste.md', '08-qa.md'
)
$runtimeLeakPattern = '(?i)(timeline_item|resolve_control|ffmpeg\s|\.py\b|samuelgursky|mcp\.json)'

Write-Host '=== Style Skill Contract Tests ===' -ForegroundColor Cyan
Write-Host ''

$skillsRoot = Join-Path $Payload '.cursor\skills\video-editing'
$styleDirs = Get-ChildItem -LiteralPath $skillsRoot -Directory

foreach ($dir in $styleDirs) {
    $sid = $dir.Name
    $base = $dir.FullName
    $skillMd = Join-Path $base 'SKILL.md'
    $profile = Join-Path $base 'style-profile.yaml'
    $policy = Join-Path $base 'capability-policy.yaml'
    $refDir = Join-Path $base 'references'

    Assert-True (Test-Path $skillMd) "S01 $sid SKILL.md exists"
    Assert-True (Test-Path $profile) "S02 $sid style-profile.yaml exists"
    Assert-True (Test-Path $policy) "S03 $sid capability-policy.yaml exists"

    $skill = [System.IO.File]::ReadAllText($skillMd, $utf8)
    $prof = [System.IO.File]::ReadAllText($profile, $utf8)
    $pol = [System.IO.File]::ReadAllText($policy, $utf8)

    Assert-True ($prof -match 'schema_version:') "S04 $sid profile schema_version"
    Assert-True ($prof -match "style_id:\s*$sid") "S05 $sid profile style_id matches"
    Assert-True ($prof -match 'taste_profile:') "S06 $sid taste_profile present"
    Assert-True ($pol -match 'schema_version:') "S07 $sid policy schema_version"
    Assert-True ($pol -match 'criticality:') "S08 $sid policy criticality present"

    foreach ($ref in $canonicalRefs) {
        $rp = Join-Path $refDir $ref
        Assert-True (Test-Path $rp) "S09 $sid reference $ref exists"
        if (Test-Path $rp) {
            $rt = [System.IO.File]::ReadAllText($rp, $utf8)
            $secOk = $true
            foreach ($sec in $requiredRefSections) {
                if ($rt -notmatch [regex]::Escape($sec)) { $secOk = $false }
            }
            Assert-True $secOk "S10 $sid $ref has decision policy sections"
            Assert-True ($rt -notmatch $runtimeLeakPattern) "S11 $sid $ref no runtime leak"
        }
    }

    Assert-True ($skill -match '07-taste.md') "S12 $sid SKILL loads taste reference"
    Assert-True ($skill -match 'capability-policy.yaml') "S13 $sid SKILL references capability policy"
    Assert-True ($skill -notmatch $runtimeLeakPattern) "S14 $sid SKILL no runtime leak"

    $policyIds = [regex]::Matches($pol, '- ([a-z][a-z0-9_]*\.[a-z0-9_.]+)') | ForEach-Object { $_.Groups[1].Value }
    $policyIds += [regex]::Matches($pol, '(?m)(?:required|preferred|optional|forbidden):\s*\[([^\]]+)\]') | ForEach-Object {
        ($_.Groups[1].Value -split ',\s*') | ForEach-Object { $_.Trim() }
    }
    $invalidIds = @()
    foreach ($capId in $policyIds) {
        if (-not $vocabSet.Contains($capId)) { $invalidIds += $capId }
    }
    Assert-True ($invalidIds.Count -eq 0) "S15 $sid policy IDs in L1 vocabulary ($($invalidIds -join ','))"

    $qa08 = [System.IO.File]::ReadAllText((Join-Path $refDir '08-qa.md'), $utf8)
    Assert-True ($qa08 -match 'Style Fidelity') "S16 $sid 08-qa is Style Fidelity layer"

    $taste = [System.IO.File]::ReadAllText((Join-Path $refDir '07-taste.md'), $utf8)
    Assert-True (($taste -match 'Taste Failure') -and ($taste -match 'Perceptual')) "S17 $sid taste model present"

    $vis = [System.IO.File]::ReadAllText((Join-Path $refDir '02-visual-language.md'), $utf8)
    Assert-True (($vis -match 'Perceptual Effect') -and ($vis -match 'push')) "S18 $sid cinematic language depth"

    $rhythm = [System.IO.File]::ReadAllText((Join-Path $refDir '03-editing-rhythm.md'), $utf8)
    Assert-True (($rhythm -match 'Micro') -and ($rhythm -match 'Macro')) "S19 $sid rhythm model"

    $sound = [System.IO.File]::ReadAllText((Join-Path $refDir '05-sound-music.md'), $utf8)
    Assert-True ($sound -match 'Silence') "S20 $sid sound grammar"

    $typo = [System.IO.File]::ReadAllText((Join-Path $refDir '04-typography-graphics.md'), $utf8)
    Assert-True ($typo -match 'caption-free') "S21 $sid typography grammar"

    $styleMd = Join-Path $refDir 'style.md'
    if (Test-Path $styleMd) {
        $st = [System.IO.File]::ReadAllText($styleMd, $utf8)
        Assert-True ($st -match 'DEPRECATED') "S22 $sid deprecated style.md pointer"
    }

    Assert-True ($skill -match 'Production Brief') "S23 $sid format authority from Brief"
}

$templateDir = Join-Path $Payload 'video-workflow\templates\style-skill'
Assert-True (Test-Path (Join-Path $templateDir 'SKILL.md')) 'S24 canonical style-skill template exists'
Assert-True (Test-Path (Join-Path $templateDir 'style-profile.yaml')) 'S25 template style-profile exists'
Assert-True (Test-Path (Join-Path $templateDir 'capability-policy.yaml')) 'S26 template capability-policy exists'

$l3 = [System.IO.File]::ReadAllText((Join-Path $Payload '.cursor\skills\video-production\SKILL.md'), $utf8)
Assert-True ($l3 -match 'Capability Resolution') 'S27 L3 Capability Resolution stage'
Assert-True ($l3 -match 'logical-capability-vocabulary') 'S28 L3 references L1 vocabulary'

$bp = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\templates\edit-blueprint.yaml'), $utf8)
Assert-True ($bp -match 'capability_requirements') 'S29 blueprint capability_requirements'

# Canonical template full contract (Stage 08D.1)
$templateRefDir = Join-Path $templateDir 'references'
$obsPolicy = [System.IO.File]::ReadAllText((Join-Path $Payload '.cursor\skills\video-editing\observational-info-short\capability-policy.yaml'), $utf8)
foreach ($ref in $canonicalRefs) {
    Assert-True (Test-Path (Join-Path $templateRefDir $ref)) "S30 template reference $ref exists"
    if (Test-Path (Join-Path $templateRefDir $ref)) {
        $trt = [System.IO.File]::ReadAllText((Join-Path $templateRefDir $ref), $utf8)
        $tsecOk = $true
        foreach ($sec in $requiredRefSections) {
            if ($trt -notmatch [regex]::Escape($sec)) { $tsecOk = $false }
        }
        Assert-True $tsecOk "S31 template $ref section structure"
        Assert-True ($trt -notmatch 'observational-info-short') "S32 template $ref no style-specific content"
    }
}

$schemaPath = Join-Path $Payload 'video-workflow\templates\style-profile-schema.yaml'
Assert-True (Test-Path $schemaPath) 'S33 style-profile-schema exists'
$profileSchema = Read-StyleProfileSchema -SchemaPath $schemaPath

# Validate all formal Style profiles against schema authority
foreach ($dir in $styleDirs) {
    $sid = $dir.Name
    $profPath = Join-Path $dir.FullName 'style-profile.yaml'
    $profErrors = @(Test-StyleProfileAgainstSchema -ProfilePath $profPath -Schema $profileSchema -Label $sid)
    Assert-True ($profErrors.Count -eq 0) "S34 $sid style-profile conforms to schema ($($profErrors -join '; '))"
}

$templateProfilePath = Join-Path $templateDir 'style-profile.yaml'
$templateProfErrors = @(Test-StyleProfileAgainstSchema -ProfilePath $templateProfilePath -Schema $profileSchema -Label 'canonical-template')
Assert-True ($templateProfErrors.Count -eq 0) "S34b canonical template style-profile conforms to schema ($($templateProfErrors -join '; '))"

# Per-entry fallback contract on all formal Styles
foreach ($dir in $styleDirs) {
    $sid = $dir.Name
    $polPath = Join-Path $dir.FullName 'capability-policy.yaml'
    $fbResult = Test-FallbackContract -PolicyPath $polPath -VocabMap $vocabStatusMap -Label $sid
    $fbErrors = @($fbResult.Errors)
    Assert-True ($fbErrors.Count -eq 0) "S34c $sid fallback per-entry contract ($($fbErrors -join '; '))"
}

# Vocabulary canonical states only
$badStates = @([regex]::Matches($vocabText, 'status: ([A-Z_]+)') | ForEach-Object { $_.Groups[1].Value } | Where-Object { $_ -notin @('VERIFIED','AVAILABLE_UNVERIFIED','UNKNOWN','FAILED','UNSAFE','DEFERRED') })
Assert-True ($badStates.Count -eq 0) 'S35 vocabulary uses canonical states only'

# Policy criticality values
$critOk = $true
foreach ($dir in $styleDirs) {
    $polText = [System.IO.File]::ReadAllText((Join-Path $dir.FullName 'capability-policy.yaml'), $utf8)
    if ($polText -match 'criticality:\s*(?!REQUIRED|PREFERRED|OPTIONAL)\w+') { $critOk = $false }
}
Assert-True $critOk 'S36 policy criticality legal values'

# Canonical template encoding: no known mojibake (U+9225 garbled em-dash, U+FFFD replacement)
$mojibakeChars = @([char]0x9225, [char]0xFFFD)
foreach ($ref in $canonicalRefs) {
    $trp = Join-Path $templateRefDir $ref
    if (Test-Path $trp) {
        $trt = [System.IO.File]::ReadAllText($trp, $utf8)
        $hasMojibake = $false
        foreach ($mc in $mojibakeChars) {
            if ($trt.IndexOf($mc) -ge 0) { $hasMojibake = $true }
        }
        Assert-True (-not $hasMojibake) "S37 template $ref no mojibake"
    }
}

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'verify-capability-coverage.ps1') | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'S38 coverage snapshot matches policy+vocabulary'

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
exit 0
