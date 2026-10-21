#Requires -Version 5.1
<#
.SYNOPSIS
  R1 Production orchestration — Frozen Script + ASR evidence → Canonical Subtitle Cues + gate.
.DESCRIPTION
  Mandatory path when Brief requires frozen script subtitle authority.
  Writes video-workflow/production/canonical-subtitle-cues.json and gate result.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspaceRoot,
    [string]$BriefPath = '',
    [string]$AsrEvidencePath = '',
    [switch]$NoPause
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$WorkspaceRoot = [System.IO.Path]::GetFullPath($WorkspaceRoot)
$tools = Join-Path $WorkspaceRoot 'video-workflow\tools'
$prod = Join-Path $WorkspaceRoot 'video-workflow\production'

if ([string]::IsNullOrWhiteSpace($BriefPath)) {
    $BriefPath = Join-Path $prod 'brief.yaml'
}
if ([string]::IsNullOrWhiteSpace($AsrEvidencePath)) {
    $AsrEvidencePath = Join-Path $prod 'asr-timing-evidence.json'
}

$buildCli = Join-Path $tools 'build-canonical-subtitle-cues.py'
$gateCli = Join-Path $tools 'validate-canonical-subtitle-authority-gate.py'
$detectPy = @"
import json, sys
from pathlib import Path
sys.path.insert(0, r'$($tools -replace "'","''")\\lib')
from pathlib import Path
from brief_subtitle_authority import load_brief_dict, brief_requires_canonical_subtitle_route
ws = Path(r'$($WorkspaceRoot -replace "'","''")')
bpath = Path(r'$($BriefPath -replace "'","''")')
b = load_brief_dict(bpath)
print('REQUIRED' if brief_requires_canonical_subtitle_route(b, workspace_root=ws, brief_path=bpath) else 'SKIP')
"@

$need = & python -c $detectPy 2>&1 | Select-Object -Last 1
if ($need -eq 'SKIP') {
    Write-Host 'FROZEN_SCRIPT_SUBTITLE_ROUTE: SKIP (Brief does not require canonical authority)'
    exit 0
}
if ($need -ne 'REQUIRED') {
    throw "BRIEF_DETECT_FAILED: $need"
}

$resolveTimingPy = @"
import sys
from pathlib import Path
sys.path.insert(0, r'$($tools -replace "'","''")\\lib')
from brief_subtitle_authority import load_brief_dict, voice_subtitle_review_pending
from voice_subtitle_review import resolve_voice_audio_path
from voice_subtitle_paths import reviewed_text_path
ws = Path(r'$($WorkspaceRoot -replace "'","''")')
bpath = Path(r'$($BriefPath -replace "'","''")')
b = load_brief_dict(bpath)
script = None
if voice_subtitle_review_pending(b):
    script = reviewed_text_path(ws)
else:
    try:
        from frozen_script_authority import _resolve_script_path
        script = _resolve_script_path(b, bpath.parent)
    except Exception:
        script = None
voice = resolve_voice_audio_path(b, ws)
audio_ext = {'.wav', '.mp3', '.flac', '.m4a', '.aac', '.aiff', '.aif'}
if voice is None or voice.suffix.lower() not in audio_ext or not voice.is_file():
    voice = None
print('SCRIPT=' + (str(script) if script is not None and Path(script).is_file() else ''))
print('VOICE=' + (str(voice) if voice is not None else ''))
"@
$timingBind = & python -c $resolveTimingPy 2>&1
$scriptForTiming = ''
$voiceForTiming = ''
foreach ($line in @($timingBind)) {
    $text = [string]$line
    if ($text.StartsWith('SCRIPT=')) { $scriptForTiming = $text.Substring(7) }
    if ($text.StartsWith('VOICE=')) { $voiceForTiming = $text.Substring(6) }
}
$timingCli = Join-Path $tools 'invoke-subtitle-timing-evidence.ps1'
if (Test-Path -LiteralPath $timingCli) {
    $timingArgs = @{ WorkspaceRoot = $WorkspaceRoot; BriefPath = $BriefPath }
    if (-not [string]::IsNullOrWhiteSpace($scriptForTiming)) { $timingArgs.ScriptPath = $scriptForTiming }
    if (-not [string]::IsNullOrWhiteSpace($voiceForTiming)) { $timingArgs.VoiceAudioPath = $voiceForTiming }
    & $timingCli @timingArgs
    if ($LASTEXITCODE -ne 0) {
        throw 'SUBTITLE_TIMING_EVIDENCE_BLOCKED'
    }
}

foreach ($p in @($BriefPath, $AsrEvidencePath, $buildCli, $gateCli)) {
    if (-not (Test-Path -LiteralPath $p)) {
        throw "FROZEN_SCRIPT_SUBTITLE_ROUTE_BLOCKED: missing $p"
    }
}

$canonicalOut = Join-Path $prod 'canonical-subtitle-cues.json'
$gateOut = Join-Path $prod 'subtitle-canonical-gate-result.json'

$detectVoicePy = @"
import sys
from pathlib import Path
sys.path.insert(0, r'$($tools -replace "'","''")\\lib')
from brief_subtitle_authority import load_brief_dict, voice_subtitle_review_pending, voice_canonical_script_path
b = load_brief_dict(Path(r'$($BriefPath -replace "'","''")'))
ws = Path(r'$($WorkspaceRoot -replace "'","''")')
print('VOICE_REVIEWED' if voice_subtitle_review_pending(b) else 'BRIEF_SCRIPT')
"@

$voiceMode = & python -c $detectVoicePy 2>&1 | Select-Object -Last 1
if ($voiceMode -eq 'VOICE_REVIEWED') {
    $reviewedScript = Join-Path $prod 'reviewed-subtitle-text.txt'
    if (-not (Test-Path -LiteralPath $reviewedScript)) {
        throw 'FROZEN_SCRIPT_SUBTITLE_ROUTE_BLOCKED: reviewed-subtitle-text.txt missing'
    }
    & python $buildCli --script $reviewedScript --asr $AsrEvidencePath --out $canonicalOut
} else {
    & python $buildCli --brief $BriefPath --asr $AsrEvidencePath --out $canonicalOut
}
if ($LASTEXITCODE -ne 0) {
    throw 'CANONICAL_SUBTITLE_BUILD_FAILED'
}
$alignCli = Join-Path $tools 'apply-frozen-word-alignment.py'
$alignPath = Join-Path $prod 'subtitle-word-alignment.json'
if ((Test-Path -LiteralPath $alignCli) -and (Test-Path -LiteralPath $alignPath)) {
    & python $alignCli --canonical $canonicalOut --alignment $alignPath
    if ($LASTEXITCODE -ne 0) {
        throw 'FROZEN_WORD_ALIGNMENT_APPLY_FAILED'
    }
}

$gateArgs = @($gateCli, '--canonical', $canonicalOut, '--asr', $AsrEvidencePath, '--out', $gateOut)
if ($voiceMode -eq 'VOICE_REVIEWED') {
    $gateArgs += @('--script', (Join-Path $prod 'reviewed-subtitle-text.txt'))
} else {
    $gateArgs += @('--brief', $BriefPath)
}
& python @gateArgs
if ($LASTEXITCODE -ne 0) {
    throw 'SUBTITLE_CANONICAL_AUTHORITY_GATE_FAIL'
}

Write-Host 'SUBTITLE_CANONICAL_AUTHORITY_GATE: PASS' -ForegroundColor Green
if (-not $NoPause) { }
exit 0
