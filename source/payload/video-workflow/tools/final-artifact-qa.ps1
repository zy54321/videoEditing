#Requires -Version 5.1
<#
.SYNOPSIS
  Lightweight Final Artifact QA helper — FFmpeg/ffprobe only.
.DESCRIPTION
  Probes a rendered MP4, extracts representative frames, runs basic black-bar heuristic.
  Writes outputs under video-workflow/.qa/ (never media.input / media.output).
.PARAMETER VideoPath
  Absolute path to final rendered MP4.
.PARAMETER QaRoot
  QA output root (default: video-workflow/.qa under Workspace).
.PARAMETER Timestamps
  Optional explicit timestamps in seconds for frame extraction.
.PARAMETER RunId
  Optional run id folder name (default: timestamp).
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$VideoPath,
    [string]$QaRoot = '',
    [string[]]$Timestamps = @(),
    [string]$RunId = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "REQUIRED_TOOL_MISSING: $Name"
    }
}

function Get-EdgeBlackRatio {
    param(
        [string]$ImagePath,
        [int]$BandPx = 8,
        [int]$Threshold = 24
    )
    Add-Type -AssemblyName System.Drawing
    $bmp = [System.Drawing.Bitmap]::FromFile($ImagePath)
    $w = $bmp.Width
    $h = $bmp.Height
    $dark = 0
    $total = 0
    for ($x = 0; $x -lt $w; $x++) {
        for ($y = 0; $y -lt $h; $y++) {
            $inBand = ($x -lt $BandPx) -or ($x -ge ($w - $BandPx)) -or ($y -lt $BandPx) -or ($y -ge ($h - $BandPx))
            if (-not $inBand) { continue }
            $c = $bmp.GetPixel($x, $y)
            $lum = [int](0.299 * $c.R + 0.587 * $c.G + 0.114 * $c.B)
            $total++
            if ($lum -le $Threshold) { $dark++ }
        }
    }
    $bmp.Dispose()
    if ($total -eq 0) { return 0 }
    return [math]::Round($dark / $total, 4)
}

Require-Command ffmpeg
Require-Command ffprobe

if (-not (Test-Path -LiteralPath $VideoPath)) {
    throw "VIDEO_NOT_FOUND: $VideoPath"
}

$videoPath = (Resolve-Path -LiteralPath $VideoPath).Path
if ([string]::IsNullOrWhiteSpace($QaRoot)) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $wfRoot = Split-Path -Parent $scriptDir
    $QaRoot = Join-Path $wfRoot '.qa'
}
if ([string]::IsNullOrWhiteSpace($RunId)) {
    $RunId = (Get-Date -Format 'yyyyMMdd-HHmmss')
}

$runDir = Join-Path $QaRoot $RunId
$framesDir = Join-Path $runDir 'frames'
New-Item -ItemType Directory -Force -Path $framesDir | Out-Null

$parsedTimestamps = @()
if ($Timestamps.Count -gt 0) {
    foreach ($entry in $Timestamps) {
        foreach ($part in ($entry -split ',')) {
            $t = $part.Trim()
            if ($t) { $parsedTimestamps += [double]$t }
        }
    }
}
$Timestamps = $parsedTimestamps

$probeJson = & ffprobe -v error -print_format json -show_format -show_streams $videoPath
$probe = $probeJson | ConvertFrom-Json
$vStream = $probe.streams | Where-Object { $_.codec_type -eq 'video' } | Select-Object -First 1
$duration = [double]$probe.format.duration

if ($Timestamps.Count -eq 0) {
    $Timestamps = @(
        [math]::Max(0.5, $duration * 0.1),
        [math]::Max(1.0, $duration * 0.5),
        [math]::Max(1.5, $duration * 0.9)
    ) | Sort-Object -Unique
}

$frameManifest = @()
$idx = 0
foreach ($ts in $Timestamps) {
    $idx++
    $out = Join-Path $framesDir ("frame_{0:D2}_{1:F2}s.png" -f $idx, $ts)
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & ffmpeg -y -ss $ts -i $videoPath -frames:v 1 $out 2>&1 | Out-Null
    $ErrorActionPreference = $prevEap
    if (-not (Test-Path -LiteralPath $out)) {
        throw "FRAME_EXTRACT_FAILED: $out at ${ts}s"
    }
    $edgeBlack = Get-EdgeBlackRatio -ImagePath $out
    $frameManifest += [PSCustomObject]@{
        index = $idx
        timestamp_seconds = $ts
        path = $out
        edge_black_ratio = $edgeBlack
        black_bar_suspect = ($edgeBlack -ge 0.55)
    }
}

$suspectCount = @($frameManifest | Where-Object { $_.black_bar_suspect }).Count
$blackBarVerdict = if ($suspectCount -ge 2) { 'SUSPECT_BLACK_BARS' } elseif ($suspectCount -eq 1) { 'AUTOMATED_SCREEN + VISUAL_CONFIRM' } else { 'NO_EDGE_BLACK_PATTERN' }

$report = [ordered]@{
    run_id = $RunId
    video = $videoPath
    probed_at = (Get-Date).ToString('o')
    duration_seconds = $duration
    width = [int]$vStream.width
    height = [int]$vStream.height
    fps = $vStream.r_frame_rate
    codec = $vStream.codec_name
    frames = $frameManifest
    black_bar_check = @{
        verdict = $blackBarVerdict
        suspect_frames = $suspectCount
        total_frames = $frameManifest.Count
        method = 'edge_band_luminance_heuristic'
    }
    subtitle_visual_qa = @{
        note = 'Extract frames at subtitle cue midpoints; Agent vision or Owner review required for text visibility.'
        pipeline = 'VERIFIED_EXECUTABLE'
    }
}

$reportPath = Join-Path $runDir 'final-artifact-qa.json'
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $reportPath -Encoding UTF8

Write-Output $reportPath
Write-Output $blackBarVerdict
