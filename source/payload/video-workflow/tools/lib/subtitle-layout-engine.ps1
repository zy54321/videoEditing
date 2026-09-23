#Requires -Version 5.1
Set-StrictMode -Version Latest

$Script:CanonicalEmphasisLevels = @('normal', 'subtle', 'medium', 'strong')
$Script:CanonicalBreakAfter = @('prefer', 'allow', 'forbid')
$Script:CanonicalFontStyles = @('Regular', 'Bold', 'Italic', 'BoldItalic')

function Get-InstalledFontNames {
    Add-Type -AssemblyName System.Drawing
    $names = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    foreach ($ff in [System.Drawing.FontFamily]::Families) {
        $names.Add($ff.Name) | Out-Null
    }
    return $names
}

function Resolve-SubtitleFont {
    param(
        [string]$Primary,
        [string]$Fallback,
        [string]$FontPolicy = 'allow_fallback'
    )

    $installed = Get-InstalledFontNames
    if ($installed.Contains($Primary)) {
        return @{
            requested_family = $Primary
            resolved_family = $Primary
            resolved_from = 'primary'
            fallback_used = $false
        }
    }
    if ($FontPolicy -eq 'allow_fallback' -and $Fallback -and $installed.Contains($Fallback)) {
        return @{
            requested_family = $Primary
            resolved_family = $Fallback
            resolved_from = 'fallback'
            fallback_used = $true
            warning = "FONT_FALLBACK: $Primary -> $Fallback"
        }
    }
    throw "FONT_NOT_FOUND: $Primary"
}

function Test-FontStyleAvailable {
    param([string]$FontFamily, [string]$FontStyleName)

    Add-Type -AssemblyName System.Drawing
    $ff = New-Object System.Drawing.FontFamily($FontFamily)
    $style = [System.Drawing.FontStyle]::Regular
    switch ($FontStyleName) {
        'Bold' { $style = [System.Drawing.FontStyle]::Bold }
        'Italic' { $style = [System.Drawing.FontStyle]::Italic }
        'BoldItalic' { $style = [System.Drawing.FontStyle]::Bold -bor [System.Drawing.FontStyle]::Italic }
        'Regular' { $style = [System.Drawing.FontStyle]::Regular }
        default { throw "FONT_STYLE_UNSUPPORTED: $FontStyleName" }
    }
    return $ff.IsStyleAvailable($style)
}

function Resolve-EmphasisLevel {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) { return 'normal' }
    if ($Script:CanonicalEmphasisLevels -contains $Value) { return $Value }
    throw "EMPHASIS_LEVEL_UNSUPPORTED: $Value"
}

function Resolve-BreakAfter {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) { return 'allow' }
    if ($Script:CanonicalBreakAfter -contains $Value) { return $Value }
    throw "BREAK_POLICY_UNSUPPORTED: $Value"
}

function Get-EmphasisMetrics {
    param($Typography, [string]$EmphasisLevel)

    $map = $Typography.emphasis_style_mapping
    if (-not $map) { throw 'EMPHASIS_MAPPING_MISSING' }
    $key = Resolve-EmphasisLevel -Value $EmphasisLevel
    if (-not $map.$key) { throw "EMPHASIS_MAPPING_MISSING: $key" }
    $entry = $map.$key
    $fontStyle = [string]$entry.font_style
    if ($Script:CanonicalFontStyles -notcontains $fontStyle) {
        throw "FONT_STYLE_UNSUPPORTED: $fontStyle"
    }
    return @{
        emphasis_level = $key
        size_multiplier = [double]$entry.size_multiplier
        font_style = $fontStyle
        tracking_px = [double]$entry.tracking_px
    }
}

function Validate-SubtitleLayoutRequest {
    param([object]$Request)

    if ([int]$Request.schema_version -ne 1) { throw "UNSUPPORTED_SCHEMA_VERSION: $($Request.schema_version)" }
    if (-not $Request.canvas) { throw 'CANVAS_MISSING' }
    if ([int]$Request.canvas.width_px -le 0) { throw 'CANVAS_WIDTH_INVALID' }
    if ([int]$Request.canvas.height_px -le 0) { throw 'CANVAS_HEIGHT_INVALID' }

    $layout = $Request.layout
    if (-not $layout) { throw 'LAYOUT_MISSING' }
    $left = if ($layout.safe_margins.left_px) { [double]$layout.safe_margins.left_px } else { 0 }
    $right = if ($layout.safe_margins.right_px) { [double]$layout.safe_margins.right_px } else { 0 }
    if ($left -lt 0 -or $right -lt 0) { throw 'SAFE_MARGIN_NEGATIVE' }
    if (($left + $right) -ge [int]$Request.canvas.width_px) { throw 'SAFE_MARGIN_EXCEEDS_FRAME' }

    $target = [double]$layout.target_width_ratio
    $ceiling = [double]$layout.hard_ceiling_ratio
    if ($target -le 0 -or $ceiling -le 0) { throw 'RATIO_NON_POSITIVE' }
    if ($target -gt $ceiling) { throw 'TARGET_EXCEEDS_CEILING_RATIO' }
    if ($ceiling -gt 1) { throw 'CEILING_RATIO_EXCEEDS_ONE' }
    if ([int]$layout.max_lines -lt 1) { throw 'MAX_LINES_INVALID' }

    $typography = $Request.typography
    if (-not $typography) { throw 'TYPOGRAPHY_MISSING' }
    if ([double]$typography.base_font_size_px -le 0) { throw 'BASE_FONT_SIZE_INVALID' }
    if ($null -ne $typography.tracking_px -and [double]$typography.tracking_px -lt 0) { throw 'TRACKING_INVALID' }
    if ($null -ne $typography.stroke_px -and [double]$typography.stroke_px -lt 0) { throw 'STROKE_INVALID' }
    if ($null -ne $typography.visual_padding_px -and [double]$typography.visual_padding_px -lt 0) { throw 'PADDING_INVALID' }
    if (-not $typography.emphasis_style_mapping) { throw 'EMPHASIS_MAPPING_MISSING' }
    foreach ($lvl in $Script:CanonicalEmphasisLevels) {
        if ($typography.emphasis_style_mapping.$lvl) {
            $fs = [string]$typography.emphasis_style_mapping.$lvl.font_style
            if ($Script:CanonicalFontStyles -notcontains $fs) { throw "FONT_STYLE_UNSUPPORTED: $fs" }
        }
    }

    if (-not $Request.cues -or @($Request.cues).Count -eq 0) { throw 'CUES_EMPTY' }
    foreach ($cue in @($Request.cues)) {
        if (-not $cue.runs -or @($cue.runs).Count -eq 0) { throw "CUE_RUNS_EMPTY: $($cue.cue_id)" }
        foreach ($run in @($cue.runs)) {
            if ($null -eq $run.text) { throw "RUN_TEXT_NULL: $($cue.cue_id)" }
            Resolve-EmphasisLevel -Value ([string]$run.emphasis_level) | Out-Null
            Resolve-BreakAfter -Value ([string]$run.break_after) | Out-Null
        }
    }
}

function Measure-RunWidthPx {
    param(
        [System.Drawing.Graphics]$Graphics,
        [string]$FontFamily,
        [double]$BaseFontSizePx,
        [hashtable]$Emphasis,
        [string]$Text,
        [double]$BaseTrackingPx,
        [double]$StrokePx,
        [double]$VisualPaddingPx
    )

    if (-not (Test-FontStyleAvailable -FontFamily $FontFamily -FontStyleName $Emphasis.font_style)) {
        throw "FONT_STYLE_UNAVAILABLE: $($Emphasis.font_style) on $FontFamily"
    }

    $size = [Math]::Max(1, $BaseFontSizePx * $Emphasis.size_multiplier)
    $style = [System.Drawing.FontStyle]::Regular
    switch ($Emphasis.font_style) {
        'Bold' { $style = [System.Drawing.FontStyle]::Bold }
        'Italic' { $style = [System.Drawing.FontStyle]::Italic }
        'BoldItalic' { $style = [System.Drawing.FontStyle]::Bold -bor [System.Drawing.FontStyle]::Italic }
    }
    $font = New-Object System.Drawing.Font($FontFamily, [single]$size, $style, [System.Drawing.GraphicsUnit]::Pixel)
    try {
        $chars = 0
        $lineCount = 0
        $sz = $Graphics.MeasureString([string]$Text, $font, [System.Drawing.PointF]::Empty, [System.Drawing.StringFormat]::GenericTypographic, [ref]$chars, [ref]$lineCount)
        $tracking = ($BaseTrackingPx + $Emphasis.tracking_px) * [Math]::Max(0, $Text.Length - 1)
        $stroke = $StrokePx * 2
        $padding = $VisualPaddingPx * 2
        return [math]::Round($sz.Width + $tracking + $stroke + $padding, 2)
    }
    finally {
        $font.Dispose()
    }
}

function Get-RunTextsConcat {
    param($Runs)
    return -join ($Runs | ForEach-Object { [string]$_.text })
}

function Get-LineWidth {
    param($Runs)
    $w = 0.0
    foreach ($r in @($Runs)) { $w += [double]$r.width_px }
    return [math]::Round($w, 2)
}

function Get-LinesFromBreakIndices {
    param([array]$Runs, [int[]]$BreakAfterRunIndices)

    $sorted = @($BreakAfterRunIndices | Sort-Object)
    $lines = [System.Collections.Generic.List[object]]::new()
    $start = 0
    foreach ($b in $sorted) {
        $lineRuns = for ($i = $start; $i -le $b; $i++) { $Runs[$i] }
        $lines.Add(@($lineRuns)) | Out-Null
        $start = $b + 1
    }
    if ($start -lt $Runs.Count) {
        $lineRuns = for ($i = $start; $i -lt $Runs.Count; $i++) { $Runs[$i] }
        $lines.Add(@($lineRuns)) | Out-Null
    }

    # Unary comma prevents PowerShell from unwrapping a single multi-run line on return.
    return , $lines
}

function Get-BreakSubsetsNonempty {
    param([int[]]$AllowedBreaks, [int]$MaxBreaks)

    $sets = New-Object 'System.Collections.Generic.List[int[]]'
    if ($AllowedBreaks.Count -eq 0) {
        return $sets
    }

    function Invoke-Combine {
        param([int]$Index, [System.Collections.Generic.List[int]]$Current)

        if ($Current.Count -gt $MaxBreaks) { return }
        if ($Index -ge $AllowedBreaks.Count) {
            if ($Current.Count -gt 0) {
                $sets.Add([int[]]@($Current.ToArray())) | Out-Null
            }
            return
        }

        $with = [System.Collections.Generic.List[int]]::new()
        foreach ($c in $Current) { $with.Add($c) | Out-Null }
        $with.Add($AllowedBreaks[$Index]) | Out-Null
        Invoke-Combine -Index ($Index + 1) -Current $with
        Invoke-Combine -Index ($Index + 1) -Current $Current
    }

    Invoke-Combine -Index 0 -Current ([System.Collections.Generic.List[int]]::new())

    $sorted = $sets.ToArray() |
        Sort-Object { $_.Length }, { ($_ | ForEach-Object { '{0:D4}' -f $_ }) -join ',' }
    $ordered = New-Object 'System.Collections.Generic.List[int[]]'
    foreach ($entry in @($sorted)) { $ordered.Add([int[]]$entry) | Out-Null }
    return $ordered
}

function Score-LineLayoutCandidate {
    param(
        [array]$Lines,
        [double]$StyleTargetPx,
        [double]$EffectiveCeilingPx
    )

    $preferBreaks = 0
    $allowBreaks = 0
    $linesAboveTarget = 0
    $imbalance = 0.0
    foreach ($line in $Lines) {
        $lineRuns = @($line)
        $lw = Get-LineWidth -Runs $lineRuns
        $imbalance += [math]::Abs($lw - $StyleTargetPx)
        if ($lw -gt $StyleTargetPx) { $linesAboveTarget++ }
        $last = $lineRuns[$lineRuns.Count - 1]
        if ($last.break_after -eq 'prefer') { $preferBreaks++ }
        elseif ($last.break_after -eq 'allow') { $allowBreaks++ }
    }

    # Tier 0 = every line within style target; tier 1 = some line above target but legal (<= ceiling).
    $targetTier = if ($linesAboveTarget -eq 0) { 0 } else { 1 }

    return [pscustomobject]@{
        target_tier = $targetTier
        lines_above_target = $linesAboveTarget
        line_count = $Lines.Count
        prefer_breaks = $preferBreaks
        allow_breaks = $allowBreaks
        imbalance = [math]::Round($imbalance, 4)
        max_width = ($Lines | ForEach-Object { Get-LineWidth -Runs $_ } | Measure-Object -Maximum).Maximum
    }
}

function Get-SelectedBreakPolicies {
    param([array]$ResolvedRuns, [int[]]$BreakIndices)

    $policies = @()
    foreach ($idx in @($BreakIndices | Sort-Object)) {
        if ($idx -ge 0 -and $idx -lt $ResolvedRuns.Count) {
            $policies += [string]$ResolvedRuns[$idx].break_after
        }
    }
    return $policies
}

function Build-SplitCandidates {
    param([array]$Runs, [double]$EffectiveCeilingPx)

    $candidates = @()
    for ($i = 0; $i -lt ($Runs.Count - 1); $i++) {
        $policy = $Runs[$i].break_after
        if ($policy -eq 'forbid') { continue }
        $left = Get-RunTextsConcat -Runs ($Runs[0..$i])
        $right = Get-RunTextsConcat -Runs ($Runs[($i + 1)..($Runs.Count - 1)])
        $candidates += @{
            after_run_index = $i
            boundary_policy = $policy
            left_text_preview = $left
            right_text_preview = $right
            reason = 'legal semantic boundary for L3 re-segmentation'
        }
    }
    return $candidates
}

function Resolve-SubtitleLineLayout {
    param(
        [array]$ResolvedRuns,
        [double]$StyleTargetPx,
        [double]$StyleCeilingPx,
        [double]$EffectiveCeilingPx,
        [int]$MaxLines,
        [double]$FrameWidthPx,
        [double]$SafeAreaWidthPx
    )

    $warnings = [System.Collections.Generic.List[string]]::new()
    $splitCandidates = @()

    foreach ($run in $ResolvedRuns) {
        if ([double]$run.width_px -gt $EffectiveCeilingPx) {
            $warnings.Add('NO_LEGAL_INTERNAL_BREAK') | Out-Null
            return @{
                lines = @()
                status = 'CUE_SPLIT_REQUIRED'
                overflow = $true
                split_required = $true
                split_candidates = @()
                warnings = @($warnings)
                width_band = 'ABOVE_CEILING'
            }
        }
    }

    $allowedBreaks = @()
    for ($i = 0; $i -lt ($ResolvedRuns.Count - 1); $i++) {
        if ($ResolvedRuns[$i].break_after -ne 'forbid') { $allowedBreaks += $i }
    }

    $maxBreaks = [Math]::Max(0, $MaxLines - 1)
    $subsets = New-Object 'System.Collections.Generic.List[int[]]'
    $subsets.Add([int[]]@()) | Out-Null
    foreach ($breakSet in (Get-BreakSubsetsNonempty -AllowedBreaks $allowedBreaks -MaxBreaks $maxBreaks)) {
        $subsets.Add([int[]]$breakSet) | Out-Null
    }
    $valid = @()

    foreach ($breakSet in $subsets) {
        $breakIndices = [int[]]$breakSet
        $lines = Get-LinesFromBreakIndices -Runs $ResolvedRuns -BreakAfterRunIndices $breakIndices
        if ($lines.Count -gt $MaxLines) { continue }
        $ok = $true
        foreach ($line in $lines) {
            if ((Get-LineWidth -Runs $line) -gt $EffectiveCeilingPx) { $ok = $false; break }
        }
        if ($ok) {
            $score = Score-LineLayoutCandidate -Lines $lines -StyleTargetPx $StyleTargetPx -EffectiveCeilingPx $EffectiveCeilingPx
            $breakStore = New-Object 'System.Collections.Generic.List[int]'
            foreach ($b in @([int[]]$breakSet)) { $breakStore.Add([int]$b) | Out-Null }
            $valid += [pscustomobject]@{ breaks = $breakStore; lines = $lines; score = $score }
        }
    }

    if ($valid.Count -eq 0) {
        $splitCandidates = Build-SplitCandidates -Runs $ResolvedRuns -EffectiveCeilingPx $EffectiveCeilingPx
        $warnings.Add('CUE_SPLIT_REQUIRED_NO_VALID_LAYOUT') | Out-Null
        return @{
            lines = @()
            status = 'CUE_SPLIT_REQUIRED'
            overflow = $true
            split_required = $true
            split_candidates = $splitCandidates
            warnings = @($warnings)
            width_band = 'ABOVE_CEILING'
        }
    }

    # Ranking: target-band tier > target fit > prefer boundary > line count (tie-break only) > fixed break-index order.
    # line_count is a legality constraint, not "fewer lines is always better".
    $best = $valid | Sort-Object `
        @{ Expression = { $_.score.target_tier } }, `
        @{ Expression = { $_.score.lines_above_target } }, `
        @{ Expression = { $_.score.imbalance } }, `
        @{ Expression = { - $_.score.prefer_breaks } }, `
        @{ Expression = { $_.score.allow_breaks } }, `
        @{ Expression = { $_.score.line_count } }, `
        @{ Expression = { ($_.breaks | ForEach-Object { '{0:D4}' -f $_ }) -join ',' } } `
        | Select-Object -First 1

    $lines = $best.lines
    $selectedBreakIndices = [int[]]@($best.breaks.ToArray())
    $policyList = New-Object 'System.Collections.Generic.List[string]'
    foreach ($p in (Get-SelectedBreakPolicies -ResolvedRuns $ResolvedRuns -BreakIndices $selectedBreakIndices)) {
        $policyList.Add([string]$p) | Out-Null
    }
    $selectedBreakPolicies = $policyList
    $maxLineWidth = ($lines | ForEach-Object { Get-LineWidth -Runs $_ } | Measure-Object -Maximum).Maximum
    $overflow = $maxLineWidth -gt $EffectiveCeilingPx
    $widthBand = 'WITHIN_TARGET'
    if ($maxLineWidth -gt $EffectiveCeilingPx) { $widthBand = 'ABOVE_CEILING' }
    elseif ($maxLineWidth -gt $StyleTargetPx) { $widthBand = 'ABOVE_TARGET_WITHIN_CEILING' }

    $status = 'PASS'
    if ($overflow) { $status = 'OVERFLOW' }
    elseif ($widthBand -eq 'ABOVE_TARGET_WITHIN_CEILING') { $status = 'PASS_WITH_WARNING' }

    return @{
        lines = $lines
        status = $status
        overflow = $overflow
        split_required = $false
        split_candidates = @()
        warnings = @($warnings)
        width_band = $widthBand
        max_line_width_px = [math]::Round([double]$maxLineWidth, 2)
        selected_break_indices = $selectedBreakIndices
        selected_break_policies = $selectedBreakPolicies
    }
}

function Invoke-SubtitleLayoutPreflight {
    param(
        [object]$Request,
        [string]$FontPolicy = 'allow_fallback'
    )

    Validate-SubtitleLayoutRequest -Request $Request

    Add-Type -AssemblyName System.Drawing
    $bmp = New-Object System.Drawing.Bitmap 1, 1
    $graphics = [System.Drawing.Graphics]::FromImage($bmp)
    $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias

    $frameW = [int]$Request.canvas.width_px
    $layout = $Request.layout
    $margins = $layout.safe_margins
    $left = if ($margins.left_px) { [double]$margins.left_px } else { 0 }
    $right = if ($margins.right_px) { [double]$margins.right_px } else { 0 }
    $safeAreaW = $frameW - $left - $right
    $styleTargetPx = $frameW * [double]$layout.target_width_ratio
    $styleCeilingPx = $frameW * [double]$layout.hard_ceiling_ratio
    $effectiveCeilingPx = [Math]::Min($styleCeilingPx, $safeAreaW)
    $maxLines = [int]$layout.max_lines

    $typography = $Request.typography
    $fontRes = Resolve-SubtitleFont -Primary $typography.font_family -Fallback $typography.fallback_font_family -FontPolicy $FontPolicy
    $globalWarnings = [System.Collections.Generic.List[string]]::new()
    if ($fontRes.ContainsKey('warning') -and $fontRes.warning) { $globalWarnings.Add($fontRes.warning) | Out-Null }

    foreach ($lvl in $Script:CanonicalEmphasisLevels) {
        if ($typography.emphasis_style_mapping.$lvl) {
            $fs = [string]$typography.emphasis_style_mapping.$lvl.font_style
            if (-not (Test-FontStyleAvailable -FontFamily $fontRes.resolved_family -FontStyleName $fs)) {
                throw "FONT_STYLE_UNAVAILABLE: $fs on $($fontRes.resolved_family)"
            }
        }
    }

    if ([double]$typography.stroke_px -gt 0 -or [double]$typography.visual_padding_px -gt 0) {
        $globalWarnings.Add('MEASUREMENT_CONSERVATIVE_BOUND: stroke/padding applied per-run may over-estimate composite line bounds; not Resolve renderer parity') | Out-Null
    }

    $cueResults = @()

    foreach ($cue in @($Request.cues)) {
        $runs = @($cue.runs)
        $inputText = Get-RunTextsConcat -Runs $runs
        $resolvedRuns = @()
        foreach ($r in $runs) {
            $emph = Get-EmphasisMetrics -Typography $typography -EmphasisLevel ([string]$r.emphasis_level)
            $width = Measure-RunWidthPx -Graphics $graphics -FontFamily $fontRes.resolved_family `
                -BaseFontSizePx ([double]$typography.base_font_size_px) -Emphasis $emph -Text ([string]$r.text) `
                -BaseTrackingPx ([double]$typography.tracking_px) -StrokePx ([double]$typography.stroke_px) `
                -VisualPaddingPx ([double]$typography.visual_padding_px)
            $resolvedRuns += [pscustomobject]@{
                text = [string]$r.text
                semantic_role = [string]$r.semantic_role
                emphasis_level = $emph.emphasis_level
                break_after = Resolve-BreakAfter -Value ([string]$r.break_after)
                width_px = $width
            }
        }

        $layoutResult = Resolve-SubtitleLineLayout `
            -ResolvedRuns $resolvedRuns `
            -StyleTargetPx $styleTargetPx `
            -StyleCeilingPx $styleCeilingPx `
            -EffectiveCeilingPx $effectiveCeilingPx `
            -MaxLines $maxLines `
            -FrameWidthPx $frameW `
            -SafeAreaWidthPx $safeAreaW

        $lineResults = @()
        $li = 0
        foreach ($line in @($layoutResult.lines)) {
            $li++
            $lw = Get-LineWidth -Runs $line
            $lineResults += @{
                line_index = $li
                runs = @($line | ForEach-Object {
                        @{
                            text = $_.text
                            semantic_role = $_.semantic_role
                            emphasis_level = $_.emphasis_level
                            break_after = $_.break_after
                            width_px = $_.width_px
                        }
                    })
                width_px = $lw
                width_ratio_frame = if ($frameW -gt 0) { [math]::Round($lw / $frameW, 4) } else { 0 }
                width_ratio_safe_area = if ($safeAreaW -gt 0) { [math]::Round($lw / $safeAreaW, 4) } else { 0 }
            }
        }

        $maxLineWidth = 0.0
        if ($layoutResult.ContainsKey('max_line_width_px') -and $null -ne $layoutResult.max_line_width_px) {
            $maxLineWidth = [double]$layoutResult.max_line_width_px
        }
        if ($lineResults.Count -gt 0) {
            $maxLineWidth = ($lineResults | ForEach-Object { [double]$_.width_px } | Measure-Object -Maximum).Maximum
        }

        $flatRuns = @()
        foreach ($ln in $lineResults) {
            foreach ($rr in $ln.runs) { $flatRuns += [pscustomobject]@{ text = $rr.text } }
        }
        $contentPreserved = (Get-RunTextsConcat -Runs $flatRuns) -eq $inputText

        $cueWarnings = @($layoutResult.warnings)
        if ($layoutResult.width_band -eq 'ABOVE_TARGET_WITHIN_CEILING') {
            $cueWarnings += 'ABOVE_STYLE_TARGET_WITHIN_FRAME_CEILING'
        }

        $cueResults += @{
            cue_id = [string]$cue.cue_id
            status = $layoutResult.status
            line_count = $lineResults.Count
            lines = $lineResults
            frame_width_px = $frameW
            safe_area_width_px = [math]::Round($safeAreaW, 2)
            style_target_width_px = [math]::Round($styleTargetPx, 2)
            style_hard_ceiling_px = [math]::Round($styleCeilingPx, 2)
            effective_ceiling_px = [math]::Round($effectiveCeilingPx, 2)
            max_line_width_px = [math]::Round($maxLineWidth, 2)
            max_line_width_ratio_frame = if ($frameW -gt 0) { [math]::Round($maxLineWidth / $frameW, 4) } else { 0 }
            max_line_width_ratio_safe_area = if ($safeAreaW -gt 0) { [math]::Round($maxLineWidth / $safeAreaW, 4) } else { 0 }
            max_line_width_ratio = if ($frameW -gt 0) { [math]::Round($maxLineWidth / $frameW, 4) } else { 0 }
            target_width_ratio = [double]$layout.target_width_ratio
            hard_ceiling_ratio = [double]$layout.hard_ceiling_ratio
            width_band = $layoutResult.width_band
            overflow = [bool]$layoutResult.overflow
            split_required = [bool]$layoutResult.split_required
            split_candidates = @($layoutResult.split_candidates)
            selected_break_indices = if ($layoutResult.ContainsKey('selected_break_indices')) { [int[]]@($layoutResult.selected_break_indices) } else { @() }
            selected_break_policies = if ($layoutResult.ContainsKey('selected_break_policies')) {
                [string[]]@($layoutResult.selected_break_policies.ToArray())
            }
            else { @() }
            warnings = $cueWarnings
            content_preserved = $contentPreserved
        }
    }

    $graphics.Dispose()
    $bmp.Dispose()

    return @{
        schema_version = 1
        measurement_backend = 'System.Drawing'
        graphics_unit = 'Pixel'
        measurement_limitations = @(
            'Per-run stroke/padding may conservatively over-estimate composite bounds'
            'Preflight PASS does not prove Resolve/Fusion/Text+ renderer parity'
        )
        font_resolution = $fontRes
        warnings = @($globalWarnings)
        cue_results = $cueResults
    }
}
