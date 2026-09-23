#Requires -Version 5.1
Set-StrictMode -Version Latest

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

function Get-EmphasisMetrics {
    param($Typography, [string]$EmphasisLevel)

    $map = $Typography.emphasis_style_mapping
    if (-not $map) { throw 'EMPHASIS_MAPPING_MISSING' }
    $key = if ($EmphasisLevel) { $EmphasisLevel } else { 'normal' }
    if (-not $map.$key) { $key = 'normal' }
    $entry = $map.$key
    return @{
        size_multiplier = [double]$entry.size_multiplier
        font_style = [string]$entry.font_style
        tracking_px = [double]$entry.tracking_px
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
        $lines = 0
        $sz = $Graphics.MeasureString([string]$Text, $font, [System.Drawing.PointF]::Empty, [System.Drawing.StringFormat]::GenericTypographic, [ref]$chars, [ref]$lines)
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

function Invoke-SubtitleLayoutPreflight {
    param(
        [object]$Request,
        [string]$FontPolicy = 'allow_fallback'
    )

    Add-Type -AssemblyName System.Drawing
    $bmp = New-Object System.Drawing.Bitmap 1, 1
    $graphics = [System.Drawing.Graphics]::FromImage($bmp)
    $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias

    $canvasW = [int]$Request.canvas.width_px
    $layout = $Request.layout
    $margins = $layout.safe_margins
    $left = if ($margins.left_px) { [double]$margins.left_px } else { 0 }
    $right = if ($margins.right_px) { [double]$margins.right_px } else { 0 }
    $usableWidth = $canvasW - $left - $right
    $targetPx = $usableWidth * [double]$layout.target_width_ratio
    $ceilingPx = $usableWidth * [double]$layout.hard_ceiling_ratio
    $maxLines = [int]$layout.max_lines

    $typography = $Request.typography
    $fontRes = Resolve-SubtitleFont -Primary $typography.font_family -Fallback $typography.fallback_font_family -FontPolicy $FontPolicy
    $globalWarnings = @()
    if ($fontRes.ContainsKey('warning') -and $fontRes.warning) { $globalWarnings += $fontRes.warning }

    $cueResults = @()

    foreach ($cue in $Request.cues) {
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
                emphasis_level = if ($r.emphasis_level) { [string]$r.emphasis_level } else { 'normal' }
                break_after = if ($r.break_after) { [string]$r.break_after } else { 'allow' }
                width_px = $width
            }
        }

        $lines = [System.Collections.Generic.List[object]]::new()
        $current = [System.Collections.Generic.List[object]]::new()
        $currentWidth = 0.0
        $warnings = [System.Collections.Generic.List[string]]::new()
        $splitRequired = $false

        for ($i = 0; $i -lt $resolvedRuns.Count; $i++) {
            $run = $resolvedRuns[$i]
            if ($run.width_px -gt $ceilingPx) {
                $splitRequired = $true
                $warnings.Add('RUN_EXCEEDS_CEILING_SINGLE_RUN') | Out-Null
            }

            $wouldWidth = $currentWidth + $run.width_px
            $shouldBreak = $false
            if ($current.Count -gt 0) {
                $prev = $current[$current.Count - 1]
                if ($wouldWidth -gt $ceilingPx -and $prev.break_after -ne 'forbid') {
                    $shouldBreak = $true
                }
                elseif ($wouldWidth -gt $targetPx -and $prev.break_after -eq 'prefer') {
                    $shouldBreak = $true
                }
                elseif ($wouldWidth -gt $ceilingPx -and $prev.break_after -eq 'allow') {
                    $shouldBreak = $true
                }
            }

            if ($shouldBreak) {
                $lines.Add(@($current.ToArray())) | Out-Null
                $current = [System.Collections.Generic.List[object]]::new()
                $currentWidth = 0.0
            }

            $current.Add($run) | Out-Null
            $currentWidth += $run.width_px
        }
        if ($current.Count -gt 0) {
            $lines.Add(@($current.ToArray())) | Out-Null
        }

        if ($lines.Count -gt $maxLines) {
            $splitRequired = $true
            $warnings.Add('CUE_SPLIT_REQUIRED_MAX_LINES') | Out-Null
        }

        $lineResults = @()
        $maxLineWidth = 0.0
        for ($li = 0; $li -lt $lines.Count; $li++) {
            $lr = $lines[$li]
            $lw = 0.0
            foreach ($rr in $lr) { $lw += $rr.width_px }
            if ($lw -gt $maxLineWidth) { $maxLineWidth = $lw }
            $lineResults += @{
                line_index = $li + 1
                runs = @($lr | ForEach-Object {
                        @{
                            text = $_.text
                            semantic_role = $_.semantic_role
                            emphasis_level = $_.emphasis_level
                            break_after = $_.break_after
                            width_px = $_.width_px
                        }
                    })
                width_px = [math]::Round($lw, 2)
                width_ratio = [math]::Round($lw / $usableWidth, 4)
            }
        }

        $maxRatio = if ($usableWidth -gt 0) { [math]::Round($maxLineWidth / $usableWidth, 4) } else { 0 }
        $overflow = $maxLineWidth -gt $ceilingPx
        if ($overflow) { $warnings.Add('ABOVE_HARD_CEILING') | Out-Null }
        $widthBand = 'WITHIN_TARGET'
        if ($maxLineWidth -gt $ceilingPx) { $widthBand = 'ABOVE_CEILING' }
        elseif ($maxLineWidth -gt $targetPx) { $widthBand = 'ABOVE_TARGET_WITHIN_CEILING' }

        $flatRuns = @()
        foreach ($ln in $lineResults) {
            foreach ($rr in $ln.runs) {
                $flatRuns += [pscustomobject]@{ text = $rr.text }
            }
        }
        $outputText = Get-RunTextsConcat -Runs $flatRuns
        $contentPreserved = ($outputText -eq $inputText)

        $status = 'PASS'
        if ($splitRequired) { $status = 'CUE_SPLIT_REQUIRED' }
        elseif ($overflow) { $status = 'OVERFLOW' }
        elseif ($widthBand -eq 'ABOVE_TARGET_WITHIN_CEILING') { $status = 'PASS_WITH_WARNING' }

        $cueResults += @{
            cue_id = [string]$cue.cue_id
            status = $status
            line_count = $lineResults.Count
            lines = $lineResults
            max_line_width_px = [math]::Round($maxLineWidth, 2)
            max_line_width_ratio = $maxRatio
            target_width_ratio = [double]$layout.target_width_ratio
            hard_ceiling_ratio = [double]$layout.hard_ceiling_ratio
            width_band = $widthBand
            overflow = $overflow
            split_required = $splitRequired
            warnings = @($warnings)
            content_preserved = $contentPreserved
        }
    }

    $graphics.Dispose()
    $bmp.Dispose()

    return @{
        schema_version = 1
        measurement_backend = 'System.Drawing'
        graphics_unit = 'Pixel'
        font_resolution = $fontRes
        warnings = @($globalWarnings)
        cue_results = $cueResults
    }
}
