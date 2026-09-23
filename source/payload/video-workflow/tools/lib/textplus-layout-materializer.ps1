#Requires -Version 5.1
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot 'subtitle-layout-engine.ps1')

function Get-LineTextFromL1Line {
    param([object]$Line)
    return (($Line.runs | ForEach-Object { [string]$_.text }) -join '')
}

function Get-StyledTextFromL1Lines {
    param([array]$Lines)
    $parts = @()
    foreach ($ln in @($Lines)) {
        $parts += Get-LineTextFromL1Line -Line $ln
    }
    return ($parts -join "`n")
}

function Get-PredictedLineWidthsFromL1 {
    param([object]$CueResult)
    return @($CueResult.lines | ForEach-Object { [double]$_.width_px })
}

function Convert-ToIntArray {
    param([object]$Value)
    if ($null -eq $Value) { return @() }
    if ($Value -is [int]) { return @([int]$Value) }
    $items = @()
    foreach ($item in @($Value)) {
        if ($null -ne $item -and "$item" -ne '') { $items += [int]$item }
    }
    return $items
}

function Convert-ToStringArray {
    param([object]$Value)
    if ($null -eq $Value) { return @() }
    if ($Value -is [string]) { return @($Value) }
    $items = @()
    foreach ($item in @($Value)) {
        if ($null -ne $item -and "$item" -ne '') { $items += [string]$item }
    }
    return $items
}

function Select-L1SplitCandidate {
    param([array]$SplitCandidates)

    $candidates = @($SplitCandidates)
    if ($candidates.Count -eq 0) { return $null }

    $prefer = @($candidates | Where-Object { $_.boundary_policy -eq 'prefer' })
    if ($prefer.Count -gt 0) {
        return $prefer | Select-Object -First 1
    }
    $allow = @($candidates | Where-Object { $_.boundary_policy -eq 'allow' })
    if ($allow.Count -gt 0) {
        return $allow | Select-Object -First 1
    }
    return $null
}

function Split-RequestRunsAtIndex {
    param(
        [array]$Runs,
        [int]$AfterRunIndex
    )

    if ($AfterRunIndex -lt 0 -or $AfterRunIndex -ge ($Runs.Count - 1)) {
        throw "INVALID_SPLIT_INDEX: $AfterRunIndex"
    }

    $leftRuns = @($Runs[0..$AfterRunIndex])
    $rightRuns = @($Runs[($AfterRunIndex + 1)..($Runs.Count - 1)])
    return @{
        left_runs = $leftRuns
        right_runs = $rightRuns
    }
}

function New-RequestFromRuns {
    param(
        [object]$TemplateRequest,
        [string]$CueId,
        [array]$Runs
    )

    $cue = @{
        cue_id = $CueId
        runs = @($Runs)
    }
    $clone = $TemplateRequest | ConvertTo-Json -Depth 12 | ConvertFrom-Json
    $clone.cues = @($cue)
    return $clone
}

function Invoke-TextPlusLayoutMaterialization {
    param(
        [object]$Request,
        [object]$PreflightResult,
        [string]$CueId,
        [int]$PartIndex = 0,
        [int]$TotalDurationFrames = 120,
        [int]$StartFrame = 0,
        [string]$FontPolicy = 'allow_fallback'
    )

    $cue = @($PreflightResult.cue_results | Where-Object { [string]$_.cue_id -eq $CueId } | Select-Object -First 1)
    if (-not $cue) { throw "CUE_NOT_FOUND: $CueId" }
    $cue = $cue[0]

    $reqCue = @($Request.cues | Where-Object { [string]$_.cue_id -eq $CueId } | Select-Object -First 1)
    if (-not $reqCue -or $reqCue.Count -eq 0) { throw "REQUEST_CUE_NOT_FOUND: $CueId" }
    $reqCue = $reqCue[0]
    $requestRuns = @($reqCue.runs)
    if ($requestRuns.Count -eq 0) { throw "REQUEST_CUE_RUNS_EMPTY: $CueId" }

    $status = [string]$cue.status
    $materialized = @()

    if ($status -eq 'CUE_SPLIT_REQUIRED') {
        $warnings = @($cue.warnings)
        if ($warnings -contains 'NO_LEGAL_INTERNAL_BREAK') {
            return @{
                materialization_status = 'BLOCKED_NO_LEGAL_INTERNAL_BREAK'
                reason = 'Atomic run exceeds ceiling; no split_candidates'
                cue_id = $CueId
                l1_status = $status
                split_candidates = @()
                materialized_cues = @()
            }
        }

        $candidate = Select-L1SplitCandidate -SplitCandidates @($cue.split_candidates)
        if (-not $candidate) {
            return @{
                materialization_status = 'BLOCKED_NO_SPLIT_CANDIDATE'
                reason = 'CUE_SPLIT_REQUIRED but no prefer/allow candidate'
                cue_id = $CueId
                l1_status = $status
                split_candidates = @($cue.split_candidates)
                materialized_cues = @()
            }
        }

        $split = Split-RequestRunsAtIndex -Runs $requestRuns -AfterRunIndex ([int]$candidate.after_run_index)
        $leftId = "${CueId}-A"
        $rightId = "${CueId}-B"
        $leftReq = New-RequestFromRuns -TemplateRequest $Request -CueId $leftId -Runs $split.left_runs
        $rightReq = New-RequestFromRuns -TemplateRequest $Request -CueId $rightId -Runs $split.right_runs
        $leftPf = Invoke-SubtitleLayoutPreflight -Request $leftReq -FontPolicy $FontPolicy
        $rightPf = Invoke-SubtitleLayoutPreflight -Request $rightReq -FontPolicy $FontPolicy

        $half = [Math]::Max(1, [int][Math]::Floor($TotalDurationFrames / 2))
        $leftMat = Invoke-TextPlusLayoutMaterialization -Request $leftReq -PreflightResult $leftPf -CueId $leftId -PartIndex $PartIndex -TotalDurationFrames $half -StartFrame $StartFrame -FontPolicy $FontPolicy
        $rightMat = Invoke-TextPlusLayoutMaterialization -Request $rightReq -PreflightResult $rightPf -CueId $rightId -PartIndex ($PartIndex + 1) -TotalDurationFrames ($TotalDurationFrames - $half) -StartFrame ($StartFrame + $half) -FontPolicy $FontPolicy

        $leftOut = if ($null -ne $leftMat.materialized_cues) { @($leftMat.materialized_cues) } else { @() }
        $rightOut = if ($null -ne $rightMat.materialized_cues) { @($rightMat.materialized_cues) } else { @() }
        $mergedCues = [System.Collections.ArrayList]@()
        foreach ($item in @($leftOut) + @($rightOut)) {
            if ($null -ne $item) { [void]$mergedCues.Add($item) }
        }
        return @{
            materialization_status = 'SPLIT'
            cue_id = $CueId
            l1_status = $status
            selected_split_candidate = $candidate
            materialized_cues = @($mergedCues.ToArray())
            child = @($leftMat, $rightMat)
        }
    }

    if ($status -notin @('PASS', 'PASS_WITH_WARNING')) {
        return @{
            materialization_status = 'BLOCKED_L1_STATUS'
            reason = "Unsupported L1 status: $status"
            cue_id = $CueId
            l1_status = $status
            materialized_cues = @()
        }
    }

    if ([int]$cue.line_count -lt 1 -or @($cue.lines).Count -lt 1) {
        return @{
            materialization_status = 'BLOCKED_NO_LINES'
            cue_id = $CueId
            l1_status = $status
            materialized_cues = @()
        }
    }

    $styled = Get-StyledTextFromL1Lines -Lines @($cue.lines)
    $newlinePositions = @()
    $offset = 0
    for ($i = 0; $i -lt @($cue.lines).Count; $i++) {
        if ($i -gt 0) { $newlinePositions += $offset }
        $offset += ([string](Get-LineTextFromL1Line -Line $cue.lines[$i])).Length
    }

    $matCue = [PSCustomObject]@{
        cue_id = $CueId
        part_index = $PartIndex
        l1_status = $status
        line_count = [int]$cue.line_count
        lines = @($cue.lines)
        selected_break_indices = (Convert-ToIntArray -Value $cue.selected_break_indices)
        selected_break_policies = (Convert-ToStringArray -Value $cue.selected_break_policies)
        styled_text = $styled
        newline_positions = $newlinePositions
        predicted_line_widths_px = @(Get-PredictedLineWidthsFromL1 -CueResult $cue)
        predicted_max_line_width_px = [double]$cue.max_line_width_px
        timing = [PSCustomObject]@{
            method = 'deterministic_equal_split_validation_only'
            start_frame = $StartFrame
            duration_frames = $TotalDurationFrames
            note = 'Not production subtitle timing authority'
        }
    }
    $materialized += $matCue

    return @{
        materialization_status = 'READY'
        cue_id = $CueId
        l1_status = $status
        materialized_cues = $materialized
    }
}

function Invoke-TextPlusLayoutMaterializationFromFiles {
    param(
        [string]$RequestPath,
        [string]$PreflightPath,
        [string]$CueId,
        [string]$FontPolicy = 'allow_fallback'
    )

    $requestJson = [System.IO.File]::ReadAllText($RequestPath, (New-Object System.Text.UTF8Encoding $false))
    $request = $requestJson | ConvertFrom-Json
    if ($PreflightPath) {
        $pfJson = [System.IO.File]::ReadAllText($PreflightPath, (New-Object System.Text.UTF8Encoding $false))
        $preflight = $pfJson | ConvertFrom-Json
    }
    else {
        $preflight = Invoke-SubtitleLayoutPreflight -Request $request -FontPolicy $FontPolicy
    }
    return Invoke-TextPlusLayoutMaterialization -Request $request -PreflightResult $preflight -CueId $CueId -FontPolicy $FontPolicy
}
