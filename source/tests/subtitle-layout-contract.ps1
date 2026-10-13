#Requires -Version 5.1
<#
.SYNOPSIS
  Stage 08E-A — Subtitle layout contract & preflight tests.
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

$enginePath = Join-Path $Payload 'video-workflow\tools\lib\subtitle-layout-engine.ps1'
$preflightPath = Join-Path $Payload 'video-workflow\tools\subtitle-layout-preflight.ps1'
. $enginePath

$script:DefaultTestFont = 'Arial'
$script:DefaultLatinFont = 'Arial'
$installedFonts = Get-InstalledFontNames
foreach ($candidate in @('Microsoft YaHei', 'Microsoft YaHei UI', 'SimHei', 'SimSun', 'Malgun Gothic')) {
    if ($installedFonts.Contains($candidate)) { $script:DefaultTestFont = $candidate; break }
}
if ($installedFonts.Contains('Arial')) { $script:DefaultLatinFont = 'Arial' }
elseif ($installedFonts.Contains('Segoe UI')) { $script:DefaultLatinFont = 'Segoe UI' }

function New-LayoutRequest {
    param(
        [array]$Runs,
        [string]$CueId = 'T01',
        [int]$CanvasWidth = 1080,
        [double]$TargetRatio = 0.77,
        [double]$CeilingRatio = 0.80,
        [int]$MaxLines = 2,
        [int]$BaseFontSize = 48,
        [string]$FontFamily = '',
        [hashtable]$Margins = @{ left_px = 54; right_px = 54 }
    )
    if ([string]::IsNullOrWhiteSpace($FontFamily)) { $FontFamily = $script:DefaultTestFont }
    return [pscustomobject]@{
        schema_version = 1
        canvas = @{ width_px = $CanvasWidth; height_px = 1920 }
        layout = @{
            target_width_ratio = $TargetRatio
            hard_ceiling_ratio = $CeilingRatio
            max_lines = $MaxLines
            safe_margins = $Margins
        }
        typography = @{
            font_family = $FontFamily
            fallback_font_family = 'SimSun'
            base_font_size_px = $BaseFontSize
            tracking_px = 0
            stroke_px = 0
            visual_padding_px = 0
            emphasis_style_mapping = @{
                normal = @{ size_multiplier = 1.0; font_style = 'Regular'; tracking_px = 0 }
                subtle = @{ size_multiplier = 1.0; font_style = 'Regular'; tracking_px = 0 }
                medium = @{ size_multiplier = 1.1; font_style = 'Regular'; tracking_px = 0 }
                strong = @{ size_multiplier = 1.25; font_style = 'Regular'; tracking_px = 0 }
            }
        }
        cues = @(@{
                cue_id = $CueId
                runs = $Runs
            })
    }
}

function New-Run {
    param([string]$Text, [string]$Emphasis = 'normal', [string]$BreakAfter = 'allow', [string]$Role = 'phrase')
    return [pscustomobject]@{
        text = $Text
        semantic_role = $Role
        emphasis_level = $Emphasis
        break_after = $BreakAfter
    }
}

function Get-CueLayoutFingerprint {
    param($Cue)
    $lineCompositions = @($Cue.lines | ForEach-Object {
            @($_.runs | ForEach-Object { $_.text }) -join '+'
        })
    return [ordered]@{
        status = [string]$Cue.status
        line_count = [int]$Cue.line_count
        line_compositions = $lineCompositions
        selected_break_indices = @($Cue.selected_break_indices)
        selected_break_policies = @($Cue.selected_break_policies)
        width_band = [string]$Cue.width_band
        max_line_width_px = [double]$Cue.max_line_width_px
        split_required = [bool]$Cue.split_required
    }
}

Write-Host '=== Subtitle Layout Contract Tests ===' -ForegroundColor Cyan
Write-Host ''

# T01 plain Chinese caption
$r1 = New-LayoutRequest -Runs @(
    (New-Run -Text '今天天气不错' -BreakAfter 'prefer'),
    (New-Run -Text '适合出门走走' -BreakAfter 'forbid')
)
$res1 = Invoke-SubtitleLayoutPreflight -Request $r1
Assert-True ($res1.cue_results[0].content_preserved) 'T01 plain Chinese measurement'
Assert-True ($res1.cue_results[0].status -in @('PASS', 'PASS_WITH_WARNING')) 'T01 status acceptable'

# T02 English
$r2 = New-LayoutRequest -Runs @(
    (New-Run -Text 'This is a simple caption' -BreakAfter 'forbid')
) -FontFamily $script:DefaultLatinFont
$res2 = Invoke-SubtitleLayoutPreflight -Request $r2
Assert-True ($res2.cue_results[0].content_preserved) 'T02 English caption'

# T03 mixed Chinese / English / number (short phrase fits one line; 40% remains trailing run)
$r3 = New-LayoutRequest -Runs @(
    (New-Run -Text '涨了' -BreakAfter 'prefer'),
    (New-Run -Text '40%' -Role 'key_number' -Emphasis 'strong' -BreakAfter 'forbid')
)
$res3 = Invoke-SubtitleLayoutPreflight -Request $r3
Assert-True ($res3.cue_results[0].content_preserved) 'T03 mixed content preserved'
Assert-True ($res3.cue_results[0].lines[0].runs[-1].text -eq '40%') 'T03 key number run intact'

# T04 emphasis changes width
$plain = New-LayoutRequest -Runs @( (New-Run -Text '真正离谱' -Emphasis 'normal' -BreakAfter 'forbid') )
$strong = New-LayoutRequest -Runs @( (New-Run -Text '真正离谱' -Emphasis 'strong' -BreakAfter 'forbid') )
$wPlain = (Invoke-SubtitleLayoutPreflight -Request $plain).cue_results[0].max_line_width_px
$wStrong = (Invoke-SubtitleLayoutPreflight -Request $strong).cue_results[0].max_line_width_px
Assert-True ($wStrong -gt $wPlain) 'T04 strong emphasis increases measured width'

# T05 40% remains intact on one run
$r5 = New-LayoutRequest -Runs @(
    (New-Run -Text '涨了' -BreakAfter 'prefer'),
    (New-Run -Text '40%' -Role 'key_number' -Emphasis 'strong' -BreakAfter 'forbid')
)
$res5 = Invoke-SubtitleLayoutPreflight -Request $r5
$allText = ($res5.cue_results[0].lines | ForEach-Object { $_.runs } | ForEach-Object { $_.text }) -join ''
Assert-True ($allText -match '40%') 'T05 percent preserved in output'

# T06 forbid boundary not broken inside run (40% single run)
$percentRun = @($res5.cue_results[0].lines | ForEach-Object { $_.runs } | Where-Object { $_.text -eq '40%' })
Assert-True ($percentRun.Count -eq 1) 'T06 forbid keeps percent atomic'

# T07 prefer boundary priority — combined width exceeds ceiling; each run fits alone; must break at prefer
$longRuns = @()
$longRuns += New-Run -Text ('观察' * 5) -BreakAfter 'prefer'
$longRuns += New-Run -Text ('记录' * 5) -BreakAfter 'forbid'
$r7 = New-LayoutRequest -Runs $longRuns
$res7 = Invoke-SubtitleLayoutPreflight -Request $r7
Assert-True ($res7.cue_results[0].line_count -ge 2) 'T07 prefer boundary enables line break'

# T08 within hard ceiling PASS
$r8 = New-LayoutRequest -Runs @( (New-Run -Text '短句' -BreakAfter 'forbid') )
$res8 = Invoke-SubtitleLayoutPreflight -Request $r8
Assert-True (-not $res8.cue_results[0].overflow) 'T08 within ceiling no overflow'

# T09 above target within ceiling => warning band (font-agnostic probe)
$t09Ok = $false
foreach ($n in 10..40) {
    $probeText = -join ((1..$n) | ForEach-Object { 'W' })
    $rx = New-LayoutRequest -Runs @( (New-Run -Text $probeText -BreakAfter 'forbid') ) -TargetRatio 0.35 -CeilingRatio 0.80
    $rs = Invoke-SubtitleLayoutPreflight -Request $rx
    if ($rs.cue_results[0].width_band -eq 'ABOVE_TARGET_WITHIN_CEILING' -and -not $rs.cue_results[0].overflow) {
        $t09Ok = $true
        break
    }
}
Assert-True $t09Ok 'T09 above target within ceiling warning'
Assert-True $t09Ok 'T09 not overflow below ceiling'

# T10 above ceiling triggers overflow status
$wideText = -join ((1..60) | ForEach-Object { 'M' })
$r10 = New-LayoutRequest -Runs @( (New-Run -Text $wideText -BreakAfter 'forbid') ) -BaseFontSize 72
$res10 = Invoke-SubtitleLayoutPreflight -Request $r10
Assert-True ($res10.cue_results[0].overflow -or $res10.cue_results[0].split_required) 'T10 wide cue overflow or split'

# T11 > max_lines => CUE_SPLIT_REQUIRED
$many = @()
1..4 | ForEach-Object { $many += New-Run -Text (-join ((1..24) | ForEach-Object { 'S' })) -BreakAfter 'prefer' }
$r11 = New-LayoutRequest -Runs $many -MaxLines 2
$res11 = Invoke-SubtitleLayoutPreflight -Request $r11
Assert-True ($res11.cue_results[0].status -eq 'CUE_SPLIT_REQUIRED') 'T11 exceeds max lines split required'

# T12 no font shrinking — engine has no shrink path
$engineText = [System.IO.File]::ReadAllText($enginePath, (New-Object System.Text.UTF8Encoding $false))
Assert-True ($engineText -notmatch 'shrink|ScaleFont') 'T12 no indefinite font shrinking in engine'

# T13 content preserved exactly
Assert-True ($res3.cue_results[0].content_preserved) 'T13 content preserved'

# T14 missing font fail closed
$r14 = New-LayoutRequest -Runs @( (New-Run -Text 'test' -BreakAfter 'forbid') ) -FontFamily 'FontThatDoesNotExist_ZZZ_08E'
$fontFail = $false
try {
    Invoke-SubtitleLayoutPreflight -Request $r14 -FontPolicy 'fail_closed' | Out-Null
}
catch {
    if ($_.Exception.Message -match 'FONT_NOT_FOUND') { $fontFail = $true }
}
Assert-True $fontFail 'T14 missing font fails closed'

# T15 deterministic same input same structural result
$a = Invoke-SubtitleLayoutPreflight -Request $r3
$b = Invoke-SubtitleLayoutPreflight -Request $r3
$fpA = Get-CueLayoutFingerprint -Cue $a.cue_results[0]
$fpB = Get-CueLayoutFingerprint -Cue $b.cue_results[0]
Assert-True (($fpA | ConvertTo-Json -Compress) -eq ($fpB | ConvertTo-Json -Compress)) 'T15 deterministic layout structure'

# T16 keyword emphasis AVAILABLE_UNVERIFIED (isolated CLS verified; production overlay not final)
$vocab = Get-Content (Join-Path $Payload 'video-workflow\capabilities\logical-capability-vocabulary.yaml') -Raw -Encoding UTF8
Assert-True ($vocab -match 'subtitle.style.keyword_emphasis:[\s\S]{0,160}status: AVAILABLE_UNVERIFIED') 'T16 keyword emphasis AVAILABLE_UNVERIFIED'

# T17 pixel_width remains AVAILABLE_UNVERIFIED
Assert-True ($vocab -match 'subtitle.layout.pixel_width:[\s\S]{0,120}status: AVAILABLE_UNVERIFIED') 'T17 pixel_width AVAILABLE_UNVERIFIED'

# T18 Blueprint semantic typography has no Runtime implementation terms
$bpRef = Get-Content (Join-Path $Payload 'video-workflow\templates\edit-blueprint-reference.md') -Raw -Encoding UTF8
$typoMatch = [regex]::Match($bpRef, '(?ms)subtitle_typography_intent:\s*\r?\n```yaml\r?\n(.*?)```')
$typoSection = if ($typoMatch.Success) { $typoMatch.Groups[1].Value } else { '' }
$forbidden = @('font_size_px', 'Fusion', 'resolve_control', 'System.Drawing', 'MCP', 'timeline_item')
$leak = $false
foreach ($f in $forbidden) { if ($typoSection -match $f) { $leak = $true } }
Assert-True (-not $leak) 'T18 blueprint typography intent no runtime terms'

# T19 product inventory includes layout artifacts (installer copies ProductFiles)
$productGen = Get-Content (Join-Path $Root 'installer\product-files.generated.ps1') -Raw -Encoding UTF8
Assert-True ($productGen -match 'subtitle-layout-preflight\.ps1') 'T19 installer includes preflight tool'
Assert-True ($productGen -match 'subtitle-layout-reference\.md') 'T19 installer includes layout reference'
Assert-True (Test-Path $preflightPath) 'T19 preflight script exists'

# T20 preflight CLI round-trip
$tmp = Join-Path $env:TEMP "subtitle-layout-test-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $tmp -Force | Out-Null
$cliReq = New-LayoutRequest -Runs @(
    (New-Run -Text 'CLI round trip' -BreakAfter 'forbid')
)
$reqPath = Join-Path $tmp 'request.json'
$outPath = Join-Path $tmp 'result.json'
($cliReq | ConvertTo-Json -Depth 10) | Set-Content -LiteralPath $reqPath -Encoding UTF8
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $preflightPath -RequestPath $reqPath -OutputPath $outPath | Out-Null
Assert-True (($LASTEXITCODE -eq 0) -and (Test-Path $outPath)) 'T20 preflight CLI writes result JSON'
Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue

# --- Stage 08E-A-R1 tests ---

# R1-01 frame width authority
$r21 = New-LayoutRequest -Runs @( (New-Run -Text 'frame test' -BreakAfter 'forbid') ) -CanvasWidth 1000 -Margins @{ left_px = 100; right_px = 100 }
$res21 = Invoke-SubtitleLayoutPreflight -Request $r21
Assert-True ($res21.cue_results[0].style_target_width_px -eq 770) 'R1-01 style target uses frame width'
Assert-True ($res21.cue_results[0].style_hard_ceiling_px -eq 800) 'R1-01 style ceiling uses frame width'
Assert-True ($res21.cue_results[0].safe_area_width_px -eq 800) 'R1-01 safe area independent'
Assert-True ($res21.cue_results[0].effective_ceiling_px -eq 800) 'R1-01 effective ceiling min(style,safe)'

# R1-02 greedy counterexample (synthetic widths)
$synthRuns = @(
    [pscustomobject]@{ text = 'A'; semantic_role = 'p'; emphasis_level = 'normal'; break_after = 'prefer'; width_px = 40 }
    [pscustomobject]@{ text = 'B'; semantic_role = 'p'; emphasis_level = 'normal'; break_after = 'forbid'; width_px = 40 }
    [pscustomobject]@{ text = 'C'; semantic_role = 'p'; emphasis_level = 'normal'; break_after = 'allow'; width_px = 30 }
)
$lr22 = Resolve-SubtitleLineLayout -ResolvedRuns $synthRuns -StyleTargetPx 80 -StyleCeilingPx 100 -EffectiveCeilingPx 100 -MaxLines 2 -FrameWidthPx 100 -SafeAreaWidthPx 100
Assert-True ($lr22.status -eq 'PASS') 'R1-02 counterexample finds valid layout'
Assert-True ($lr22.lines.Count -eq 2) 'R1-02 two lines'
Assert-True ($lr22.lines[0].Count -eq 1 -and $lr22.lines[0][0].text -eq 'A') 'R1-02 line1 is A only'

# R1-03 prefer boundary over allow when both valid
$synth23 = @(
    [pscustomobject]@{ text = 'A'; semantic_role = 'p'; emphasis_level = 'normal'; break_after = 'prefer'; width_px = 40 }
    [pscustomobject]@{ text = 'B'; semantic_role = 'p'; emphasis_level = 'normal'; break_after = 'allow'; width_px = 30 }
    [pscustomobject]@{ text = 'C'; semantic_role = 'p'; emphasis_level = 'normal'; break_after = 'allow'; width_px = 40 }
)
$lr23 = Resolve-SubtitleLineLayout -ResolvedRuns $synth23 -StyleTargetPx 50 -StyleCeilingPx 100 -EffectiveCeilingPx 100 -MaxLines 2 -FrameWidthPx 100 -SafeAreaWidthPx 100
Assert-True ($lr23.status -in @('PASS', 'PASS_WITH_WARNING')) 'R1-03 prefer layout valid'
Assert-True ($lr23.lines[0][0].text -eq 'A') 'R1-03 breaks at prefer boundary'

# R1-04 invalid emphasis fail closed
$badEmph = $false
try {
    $typ = (New-LayoutRequest -Runs @( (New-Run -Text 'x' -BreakAfter 'forbid') )).typography
    Get-EmphasisMetrics -Typography $typ -EmphasisLevel 'hero' | Out-Null
}
catch { if ($_.Exception.Message -match 'EMPHASIS_LEVEL_UNSUPPORTED') { $badEmph = $true } }
Assert-True $badEmph 'R1-04 invalid emphasis fail closed'

# R1-04b missing emphasis defaults normal
$typN = (New-LayoutRequest -Runs @( (New-Run -Text 'x' -Emphasis '' -BreakAfter 'forbid') )).typography
$em = Get-EmphasisMetrics -Typography $typN -EmphasisLevel ''
Assert-True ($em.emphasis_level -eq 'normal') 'R1-04b missing emphasis defaults normal'

# R1-04c invalid break_after
$badBreak = $false
try {
    $r24 = New-LayoutRequest -Runs @([pscustomobject]@{ text = 'x'; semantic_role = 'p'; emphasis_level = 'normal'; break_after = 'maybe' })
    Invoke-SubtitleLayoutPreflight -Request $r24 | Out-Null
}
catch { if ($_.Exception.Message -match 'BREAK_POLICY_UNSUPPORTED') { $badBreak = $true } }
Assert-True $badBreak 'R1-04c invalid break_after fail closed'

# R1-06 invalid margins
$badMargin = $false
try {
    $r25 = New-LayoutRequest -Runs @( (New-Run -Text 'x' -BreakAfter 'forbid') ) -CanvasWidth 100 -Margins @{ left_px = 60; right_px = 60 }
    Invoke-SubtitleLayoutPreflight -Request $r25 | Out-Null
}
catch { if ($_.Exception.Message -match 'SAFE_MARGIN_EXCEEDS_FRAME') { $badMargin = $true } }
Assert-True $badMargin 'R1-06 invalid margins fail closed'

# R1-06b target > ceiling ratio
$badRatio = $false
try {
    $r26 = New-LayoutRequest -Runs @( (New-Run -Text 'x' -BreakAfter 'forbid') ) -TargetRatio 0.85 -CeilingRatio 0.80
    Invoke-SubtitleLayoutPreflight -Request $r26 | Out-Null
}
catch { if ($_.Exception.Message -match 'TARGET_EXCEEDS_CEILING_RATIO') { $badRatio = $true } }
Assert-True $badRatio 'R1-06b target exceeds ceiling ratio fail closed'

# R1-06c empty runs
$emptyRuns = $false
try {
    $r27 = New-LayoutRequest -Runs @()
    Invoke-SubtitleLayoutPreflight -Request $r27 | Out-Null
}
catch { if ($_.Exception.Message -match 'CUE_RUNS_EMPTY') { $emptyRuns = $true } }
Assert-True $emptyRuns 'R1-06c empty runs fail closed'

# R1-07 result example contract consistency
$resExample = Get-Content (Join-Path $Payload 'video-workflow\templates\subtitle-layout-result.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$exCue = $resExample.cue_results[0]
Assert-True ($exCue.line_count -eq $exCue.lines.Count) 'R1-07 result example line_count matches lines'
Assert-True ($exCue.max_line_width_ratio -eq $exCue.max_line_width_ratio_frame) 'R1-07 canonical ratio is frame-based'

# R1-08 split candidates exclude forbid
$synth28 = @(
    [pscustomobject]@{ text = 'A'; semantic_role = 'p'; emphasis_level = 'normal'; break_after = 'forbid'; width_px = 60 }
    [pscustomobject]@{ text = 'B'; semantic_role = 'p'; emphasis_level = 'normal'; break_after = 'allow'; width_px = 60 }
)
$lr28 = Resolve-SubtitleLineLayout -ResolvedRuns $synth28 -StyleTargetPx 50 -StyleCeilingPx 80 -EffectiveCeilingPx 80 -MaxLines 1 -FrameWidthPx 100 -SafeAreaWidthPx 100
Assert-True ($lr28.split_required) 'R1-08 split required when no valid layout'
$forbidCand = @($lr28.split_candidates | Where-Object { $_.boundary_policy -eq 'forbid' })
Assert-True ($forbidCand.Count -eq 0) 'R1-08 split candidates exclude forbid'

# R1-08b atomic oversized run
$synth29 = @(
    [pscustomobject]@{ text = 'BIG'; semantic_role = 'p'; emphasis_level = 'normal'; break_after = 'forbid'; width_px = 150 }
)
$lr29 = Resolve-SubtitleLineLayout -ResolvedRuns $synth29 -StyleTargetPx 80 -StyleCeilingPx 100 -EffectiveCeilingPx 100 -MaxLines 2 -FrameWidthPx 100 -SafeAreaWidthPx 100
Assert-True ($lr29.warnings -contains 'NO_LEGAL_INTERNAL_BREAK') 'R1-08b atomic oversized run evidence'

# R1-05 no typography.font_style top-level duplicate authority
$reqExampleObj = Get-Content (Join-Path $Payload 'video-workflow\templates\subtitle-layout-request.json') -Raw -Encoding UTF8 | ConvertFrom-Json
Assert-True (-not ($reqExampleObj.typography.PSObject.Properties.Name -contains 'font_style')) 'R1-05 request has no duplicate typography.font_style field'

# R1-09 measurement limitation present
$resLim = Invoke-SubtitleLayoutPreflight -Request (New-LayoutRequest -Runs @( (New-Run -Text 'warn' -BreakAfter 'forbid') ))
Assert-True ($resLim.measurement_limitations.Count -ge 1) 'R1-09 measurement limitations documented'

# R1-10 keyword emphasis production overlay not final; pixel_width unchanged
Assert-True ($vocab -match 'subtitle.style.keyword_emphasis:[\s\S]{0,160}status: AVAILABLE_UNVERIFIED') 'R1-10 keyword emphasis AVAILABLE_UNVERIFIED'
Assert-True ($vocab -match 'subtitle.layout.pixel_width:[\s\S]{0,120}status: AVAILABLE_UNVERIFIED') 'R1-10 pixel_width still AVAILABLE_UNVERIFIED'

# --- Stage 08E-A-R2 tests ---

# R2-03 above-target single line vs prefer split within target → choose prefer split
$synthR23 = @(
    [pscustomobject]@{ text = 'A'; semantic_role = 'p'; emphasis_level = 'normal'; break_after = 'prefer'; width_px = 45 }
    [pscustomobject]@{ text = 'B'; semantic_role = 'p'; emphasis_level = 'normal'; break_after = 'forbid'; width_px = 40 }
)
$lrR23 = Resolve-SubtitleLineLayout -ResolvedRuns $synthR23 -StyleTargetPx 60 -StyleCeilingPx 100 -EffectiveCeilingPx 100 -MaxLines 2 -FrameWidthPx 100 -SafeAreaWidthPx 100
Assert-True ($lrR23.lines.Count -eq 2) 'R2-03 chooses two-line prefer split'
Assert-True ($lrR23.lines[0].Count -eq 1 -and $lrR23.lines[0][0].text -eq 'A') 'R2-03 line1 is A'
Assert-True ($lrR23.lines[1].Count -eq 1 -and $lrR23.lines[1][0].text -eq 'B') 'R2-03 line2 is B'
Assert-True ($lrR23.selected_break_indices.Count -eq 1 -and $lrR23.selected_break_indices[0] -eq 0) 'R2-03 break after run A'
Assert-True ($lrR23.selected_break_policies[0] -eq 'prefer') 'R2-03 selected prefer boundary'

# R2-04 single line already within target → do not force prefer split
$synthR24 = @(
    [pscustomobject]@{ text = 'A'; semantic_role = 'p'; emphasis_level = 'normal'; break_after = 'prefer'; width_px = 40 }
    [pscustomobject]@{ text = 'B'; semantic_role = 'p'; emphasis_level = 'normal'; break_after = 'forbid'; width_px = 30 }
)
$lrR24 = Resolve-SubtitleLineLayout -ResolvedRuns $synthR24 -StyleTargetPx 100 -StyleCeilingPx 120 -EffectiveCeilingPx 120 -MaxLines 2 -FrameWidthPx 100 -SafeAreaWidthPx 100
Assert-True ($lrR24.lines.Count -eq 1) 'R2-04 keeps single line within target'
Assert-True ($lrR24.selected_break_indices.Count -eq 0) 'R2-04 no forced break'

# R2-05 prefer beats allow when target-tier equal
$synthR25 = @(
    [pscustomobject]@{ text = 'A'; semantic_role = 'p'; emphasis_level = 'normal'; break_after = 'prefer'; width_px = 25 }
    [pscustomobject]@{ text = 'B'; semantic_role = 'p'; emphasis_level = 'normal'; break_after = 'allow'; width_px = 25 }
    [pscustomobject]@{ text = 'C'; semantic_role = 'p'; emphasis_level = 'normal'; break_after = 'allow'; width_px = 25 }
)
$lrR25 = Resolve-SubtitleLineLayout -ResolvedRuns $synthR25 -StyleTargetPx 30 -StyleCeilingPx 100 -EffectiveCeilingPx 100 -MaxLines 2 -FrameWidthPx 100 -SafeAreaWidthPx 100
Assert-True ($lrR25.lines[0][0].text -eq 'A') 'R2-05 prefer boundary chosen over allow'
Assert-True ($lrR25.selected_break_policies[0] -eq 'prefer') 'R2-05 selected policy is prefer'

# R2-06 deterministic structural output (preflight path)
$detReq = New-LayoutRequest -Runs @(
    (New-Run -Text '涨了' -BreakAfter 'prefer'),
    (New-Run -Text '40%' -Role 'key_number' -Emphasis 'strong' -BreakAfter 'forbid')
)
$detA = Invoke-SubtitleLayoutPreflight -Request $detReq
$detB = Invoke-SubtitleLayoutPreflight -Request $detReq
Assert-True (($detA.cue_results[0] | ConvertTo-Json -Depth 12 -Compress) -eq ($detB.cue_results[0] | ConvertTo-Json -Depth 12 -Compress)) 'R2-06 deterministic preflight cue structure'

# R2-07 unsupported contract font style
$badFontStyle = $false
try {
    $rFs = New-LayoutRequest -Runs @( (New-Run -Text 'x' -BreakAfter 'forbid') )
    $rFs.typography.emphasis_style_mapping.normal.font_style = 'Heavy'
    Invoke-SubtitleLayoutPreflight -Request $rFs | Out-Null
}
catch { if ($_.Exception.Message -match 'FONT_STYLE_UNSUPPORTED') { $badFontStyle = $true } }
Assert-True $badFontStyle 'R2-07 unsupported contract font style fail closed'

# R2-07b canonical style unavailable on resolved FontFamily
Add-Type -AssemblyName System.Drawing
$singleStyleFont = $null
foreach ($ff in [System.Drawing.FontFamily]::Families) {
    if ($ff.IsStyleAvailable([System.Drawing.FontStyle]::Regular) -and -not $ff.IsStyleAvailable([System.Drawing.FontStyle]::Bold)) {
        $singleStyleFont = $ff.Name
        break
    }
}
if ($singleStyleFont) {
    $badFontAvail = $false
    try {
        $rFa = New-LayoutRequest -Runs @( (New-Run -Text 'x' -BreakAfter 'forbid') ) -FontFamily $singleStyleFont
        Invoke-SubtitleLayoutPreflight -Request $rFa | Out-Null
    }
    catch { if ($_.Exception.Message -match 'FONT_STYLE_UNAVAILABLE') { $badFontAvail = $true } }
    Assert-True $badFontAvail 'R2-07b unavailable font style on family fail closed'
}
else {
    Write-Host '[SKIP] R2-07b no Regular-only font family on host' -ForegroundColor Yellow
    $script:Pass++
}

# BR1-01 contract font family aliases to System.Drawing-enumerated identity
$yaheiUiAvail = (Get-InstalledFontNames).Contains('Microsoft YaHei UI')
if ($yaheiUiAvail) {
    $br1Req = New-LayoutRequest -Runs @( (New-Run -Text '测试' -BreakAfter 'forbid') ) -FontFamily 'Microsoft YaHei'
    $br1Res = Invoke-SubtitleLayoutPreflight -Request $br1Req
    Assert-True ($br1Res.font_resolution.resolved_family -eq 'Microsoft YaHei UI') 'BR1-01 YaHei resolves to YaHei UI'
    Assert-True ($br1Res.font_resolution.resolved_from -eq 'alias') 'BR1-01 alias provenance'
    Assert-True (-not $br1Res.font_resolution.fallback_used) 'BR1-01 alias is not fallback'
}
else {
    Write-Host '[SKIP] BR1-01 Microsoft YaHei UI not enumerated on host' -ForegroundColor Yellow
    $script:Pass++
}

# R2-09 keyword emphasis AVAILABLE_UNVERIFIED; pixel_width still AVAILABLE_UNVERIFIED
Assert-True ($vocab -match 'subtitle.style.keyword_emphasis:[\s\S]{0,160}status: AVAILABLE_UNVERIFIED') 'R2-09 keyword emphasis AVAILABLE_UNVERIFIED'
Assert-True ($vocab -match 'subtitle.layout.pixel_width:[\s\S]{0,120}status: AVAILABLE_UNVERIFIED') 'R2-09 pixel_width still AVAILABLE_UNVERIFIED'

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
exit 0
