#Requires -Version 5.1
<#
.SYNOPSIS
  Production Repair Step 4A — narration_short_v1 profile, loudness QA, mix regression.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$RepoRoot = Split-Path -Parent $Root
$Payload = Join-Path $Root 'payload'
$Pass = 0
$Fail = 0

function Assert-True {
    param([bool]$Condition, [string]$Name)
    if ($Condition) { Write-Host "[PASS] $Name" -ForegroundColor Green; $script:Pass++ }
    else { Write-Host "[FAIL] $Name" -ForegroundColor Red; $script:Fail++ }
}

function Invoke-Py {
    param([string[]]$PyArgs, [int[]]$AllowExitCodes = @(0, 2))
    $lines = & python @PyArgs 2>&1 | ForEach-Object { if ($_ -is [System.Management.Automation.ErrorRecord]) { $_.ToString() } else { "$_" } }
    $out = ($lines | Out-String).Trim()
    $code = $LASTEXITCODE
    if ($AllowExitCodes -notcontains $code) { throw "python failed ($code): $out" }
    $start = $out.IndexOf('{'); $end = $out.LastIndexOf('}')
    if ($start -ge 0 -and $end -gt $start) { $out = $out.Substring($start, $end - $start + 1) }
    return ,@($code, $out)
}

function Invoke-Ffmpeg {
    param([string[]]$FfmpegArgs)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & ffmpeg -hide_banner -y @FfmpegArgs 2>&1 | Out-Null
    $ErrorActionPreference = $prev
    if ($LASTEXITCODE -ne 0) { throw "ffmpeg failed: $($FfmpegArgs -join ' ')" }
}

Write-Host '=== Production Audio Mix Profile Tests (Step 4A) ===' -ForegroundColor Cyan
Write-Host ''

$utf8 = New-Object System.Text.UTF8Encoding $false
$profilePath = Join-Path $Payload 'video-workflow\runtime\narration-short-v1-audio-mix-profile.yaml'
$refPath = Join-Path $Payload 'video-workflow\templates\narration-short-v1-audio-mix-reference.md'
$audioQaCli = Join-Path $Payload 'video-workflow\tools\audio-loudness-qa.py'
$finalQaCli = Join-Path $Payload 'video-workflow\tools\final-artifact-qa.ps1'
$l1 = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\capabilities\davinci-resolve.md'), $utf8)
$vocab = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\capabilities\logical-capability-vocabulary.yaml'), $utf8)
$l3 = [System.IO.File]::ReadAllText((Join-Path $Payload '.cursor\skills\video-production\SKILL.md'), $utf8)
$closeout = Join-Path $RepoRoot 'validation\production-repair-step4a-audio-loudness-closeout.md'

$fixtureRoot = Join-Path $PSScriptRoot 'fixtures\audio-loudness'
New-Item -ItemType Directory -Force -Path $fixtureRoot | Out-Null

# 1 — Profile contract
Assert-True (Test-Path $profilePath) 'A01 profile exists'
$profile = [System.IO.File]::ReadAllText($profilePath, $utf8)
Assert-True ($profile -match 'profile_id:\s*narration_short_v1') 'A02 profile_id'
Assert-True ($profile -match 'target_lufs:\s*-16') 'A03 -16 LUFS target'
Assert-True ($profile -match 'tolerance_lu:\s*1') 'A04 tolerance'
Assert-True ($profile -match 'ceiling_dbtp:\s*-1') 'A05 true peak ceiling'
Assert-True ($profile -match 'final_audio_auto_repair:\s*VERIFIED') 'A06 auto repair VERIFIED'
Assert-True ($profile -match 'lra:\s*7') 'A06b LRA engineering parameter'
Assert-True ($profile -match 'not_dynamic_ducking:\s*true') 'A07 not ducking'
Assert-True ($profile -match 'verified_baseline_factor:\s*0\.15') 'A08 verified music fallback'

# 2 — Reference / audit doc
Assert-True (Test-Path $refPath) 'A09 reference doc exists'
$ref = [System.IO.File]::ReadAllText($refPath, $utf8)
Assert-True ($ref -match '-24\.8 LUFS') 'A10 N02 V4 reference loudness'
Assert-True ($ref -match 'audio\.volume.*FAILED|FAILED.*audio\.volume') 'A11 audit audio.volume FAILED'

# 3 — Capability truth
Assert-True ($vocab -match 'audio\.final\.measure_loudness:[\s\S]{0,80}VERIFIED') 'A12 measure_loudness VERIFIED'
Assert-True ($vocab -match 'audio\.final\.true_peak_qa:[\s\S]{0,80}VERIFIED') 'A13 true_peak_qa VERIFIED'
Assert-True ($vocab -match 'audio\.final\.normalize_or_adjust:[\s\S]{0,80}VERIFIED') 'A14 normalize VERIFIED'
Assert-True ($vocab -match 'audio\.music\.duck:[\s\S]{0,80}UNKNOWN') 'A15 ducking unchanged UNKNOWN'
Assert-True ($vocab -match 'audio\.music\.level_under_voice:[\s\S]{0,120}VERIFIED') 'A16 level_under_voice still VERIFIED'
Assert-True ($l1 -match 'final_render\.audio_loudness_check[\s\S]{0,120}VERIFIED') 'A17 L1 loudness check VERIFIED'

# 4 — L3 wiring
Assert-True ($l3 -match 'narration-short-v1-audio-mix-profile\.yaml') 'A18 L3 profile reference'
Assert-True ($l3 -match 'FINAL_AUDIO_AUTO_REPAIR[\s\S]{0,80}VERIFIED') 'A19 L3 auto repair VERIFIED'
Assert-True ($l3 -match 'LOUDNESS_TOO_LOW') 'A20 L3 verdict codes'

# 5 — Generate fixtures
$voiceOnly = Join-Path $fixtureRoot 'voice_only.wav'
$musicOnly = Join-Path $fixtureRoot 'music_only.wav'
$voiceMusicPass = Join-Path $fixtureRoot 'voice_music_pass.wav'
$tooLow = Join-Path $fixtureRoot 'too_low.wav'
$tooHigh = Join-Path $fixtureRoot 'too_high.wav'
$peakBad = Join-Path $fixtureRoot 'peak_bad.wav'
$noAudioMp4 = Join-Path $fixtureRoot 'no_audio.mp4'

Invoke-Ffmpeg @('-f','lavfi','-i','sine=frequency=220:duration=6','-af','loudnorm=I=-16:TP=-1.5:LRA=11',$voiceOnly)
Invoke-Ffmpeg @('-f','lavfi','-i','sine=frequency=440:duration=6','-af','loudnorm=I=-20:TP=-2:LRA=11',$musicOnly)
Invoke-Ffmpeg @('-i',$voiceOnly,'-i',$musicOnly,'-filter_complex','[1:a]volume=0.15[m];[0:a][m]amix=inputs=2:duration=first,loudnorm=I=-16:TP=-1.5:LRA=11[aout]','-map','[aout]',$voiceMusicPass)
Invoke-Ffmpeg @('-f','lavfi','-i','sine=frequency=220:duration=4','-af','loudnorm=I=-30:TP=-3:LRA=5',$tooLow)
Invoke-Ffmpeg @('-f','lavfi','-i','sine=frequency=220:duration=4','-af','loudnorm=I=-10:TP=-1.5:LRA=5',$tooHigh)
Invoke-Ffmpeg @('-f','lavfi','-i','sine=frequency=220:duration=4','-af','volume=8,alimiter=limit=0.25',$peakBad)
Invoke-Ffmpeg @('-f','lavfi','-i','color=c=black:s=320x240:d=2','-an',$noAudioMp4)

# 6 — Voice-only measurement
$v = Invoke-Py -PyArgs @($audioQaCli, $voiceOnly, '--profile', $profilePath)
$vJson = $v[1] | ConvertFrom-Json
Assert-True ($v[0] -eq 0) 'B01 voice-only PASS exit 0'
Assert-True ($vJson.verdict -eq 'PASS') 'B02 voice-only verdict PASS'
Assert-True ($vJson.loudness.integrated_lufs -ge -17 -and $vJson.loudness.integrated_lufs -le -15) 'B03 voice-only in tolerance'

# 7 — Voice + music
$vm = Invoke-Py -PyArgs @($audioQaCli, $voiceMusicPass, '--profile', $profilePath, '--voice', $voiceOnly, '--music', $musicOnly)
$vmJson = $vm[1] | ConvertFrom-Json
Assert-True ($vm[0] -eq 0) 'C01 voice+music PASS exit 0'
Assert-True ($vmJson.verdict -eq 'PASS') 'C02 voice+music verdict PASS'
Assert-True ($null -ne $vmJson.music_attenuation_recommendation.factor) 'C03 attenuation recommendation present'
Assert-True ($vmJson.music_attenuation_recommendation.factor -ge 0.08 -and $vmJson.music_attenuation_recommendation.factor -le 0.35) 'C04 factor within profile clamp'

# 8 — Failure fixtures
$low = Invoke-Py -PyArgs @($audioQaCli, $tooLow, '--profile', $profilePath) -AllowExitCodes @(2)
$lowJson = $low[1] | ConvertFrom-Json
Assert-True ($lowJson.verdict -eq 'LOUDNESS_TOO_LOW') 'D01 too low detected'

$high = Invoke-Py -PyArgs @($audioQaCli, $tooHigh, '--profile', $profilePath) -AllowExitCodes @(2)
$highJson = $high[1] | ConvertFrom-Json
Assert-True ($highJson.verdict -eq 'LOUDNESS_TOO_HIGH') 'D02 too high detected'

$peak = Invoke-Py -PyArgs @($audioQaCli, $peakBad, '--profile', $profilePath) -AllowExitCodes @(2)
$peakJson = $peak[1] | ConvertFrom-Json
Assert-True ($peakJson.verdict -eq 'TRUE_PEAK_EXCEEDED') 'D03 true peak failure'

$noA = Invoke-Py -PyArgs @($audioQaCli, $noAudioMp4, '--profile', $profilePath) -AllowExitCodes @(2)
$noAJson = $noA[1] | ConvertFrom-Json
Assert-True ($noAJson.verdict -eq 'NO_AUDIO') 'D04 no audio failure'

# 9 — final-artifact-qa integration (audio section)
$qaTmp = Join-Path $fixtureRoot '.qa'
$vidPass = Join-Path $fixtureRoot 'voice_music_pass.mp4'
Invoke-Ffmpeg @('-i',$voiceMusicPass,'-f','lavfi','-i','color=c=black:s=320x240','-shortest','-c:v','libx264','-c:a','aac',$vidPass)
$qaOut = & powershell -NoProfile -File $finalQaCli -VideoPath $vidPass -QaRoot $qaTmp -RunId 'step4a-test' 2>&1
$qaReportPath = ($qaOut | Select-Object -First 1)
Assert-True (Test-Path -LiteralPath $qaReportPath) 'E01 final-artifact-qa report written'
$qaJson = Get-Content -LiteralPath $qaReportPath -Raw | ConvertFrom-Json
Assert-True ($qaJson.audio_loudness_qa.verdict -eq 'PASS') 'E02 final-artifact-qa audio PASS'

# 10 — Regressions
& powershell -NoProfile -File (Join-Path $PSScriptRoot 'shared-asset-library.ps1') | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'R01 shared asset library regression'
& powershell -NoProfile -File (Join-Path $PSScriptRoot 'capability-resolution-consistency.ps1') | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'R02 capability policy regression'
& powershell -NoProfile -File (Join-Path $PSScriptRoot 'production-subtitle-readability.ps1') | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'R03 subtitle readability regression'

Assert-True (Test-Path $closeout) 'Z01 closeout doc exists'

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
