#Requires -Version 5.1
<#
.SYNOPSIS
  Production Repair Step 4A-Repair — loudnorm two-pass final audio repair tests (Cases A–G).
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

function Get-FileSha256 {
    param([string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Probe-VideoMeta {
    param([string]$Path)
    $json = & ffprobe -v error -print_format json -show_streams -show_format $Path 2>&1 | Out-String
    return $json | ConvertFrom-Json
}

Write-Host '=== Production Audio Loudness Repair Tests (Step 4A-Repair) ===' -ForegroundColor Cyan
Write-Host ''

$utf8 = New-Object System.Text.UTF8Encoding $false
$profilePath = Join-Path $Payload 'video-workflow\runtime\narration-short-v1-audio-mix-profile.yaml'
$repairCli = Join-Path $Payload 'video-workflow\tools\final-audio-loudness-repair.py'
$orchestrator = Join-Path $Payload 'video-workflow\tools\final-artifact-audio-qa-repair.ps1'
$audioQaCli = Join-Path $Payload 'video-workflow\tools\audio-loudness-qa.py'
$vocab = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\capabilities\logical-capability-vocabulary.yaml'), $utf8)
$l3 = [System.IO.File]::ReadAllText((Join-Path $Payload '.cursor\skills\video-production\SKILL.md'), $utf8)
$closeout = Join-Path $RepoRoot 'validation\production-repair-step4a-repair-loudnorm-closeout.md'

$fixtureRoot = Join-Path $PSScriptRoot 'fixtures\audio-loudness-repair'
New-Item -ItemType Directory -Force -Path $fixtureRoot | Out-Null
$workDir = Join-Path $fixtureRoot '.work'

# Profile / truth
$profile = [System.IO.File]::ReadAllText($profilePath, $utf8)
Assert-True ($profile -match 'final_audio_auto_repair:\s*VERIFIED') 'A01 profile auto repair VERIFIED'
Assert-True ($profile -match 'max_retries:\s*1') 'A02 max_retries 1'
Assert-True ($profile -match 'lra:\s*7') 'A03 LRA 7'
Assert-True ($vocab -match 'audio\.final\.normalize_or_adjust:[\s\S]{0,80}VERIFIED') 'A04 vocab normalize VERIFIED'
Assert-True ($vocab -match 'final_audio\.auto_repair:[\s\S]{0,80}VERIFIED') 'A05 vocab FINAL_AUDIO_AUTO_REPAIR VERIFIED'
Assert-True ($l3 -match 'final-artifact-audio-qa-repair\.ps1') 'A06 L3 orchestrator wired'

# Fixtures
$passWav = Join-Path $fixtureRoot 'pass.wav'
$tooLow = Join-Path $fixtureRoot 'too_low.wav'
$tooHigh = Join-Path $fixtureRoot 'too_high.wav'
$peakBad = Join-Path $fixtureRoot 'peak_bad.wav'
$noAudioMp4 = Join-Path $fixtureRoot 'no_audio.mp4'
$tooLowMp4 = Join-Path $fixtureRoot 'too_low.mp4'

Invoke-Ffmpeg @('-f','lavfi','-i','sine=frequency=220:duration=5','-af','loudnorm=I=-16:TP=-1.5:LRA=7',$passWav)
Invoke-Ffmpeg @('-f','lavfi','-i','sine=frequency=220:duration=5','-af','loudnorm=I=-25:TP=-3:LRA=7',$tooLow)
Invoke-Ffmpeg @('-f','lavfi','-i','sine=frequency=220:duration=5','-af','loudnorm=I=-10:TP=-1.5:LRA=7',$tooHigh)
Invoke-Ffmpeg @('-f','lavfi','-i','sine=frequency=220:duration=5','-af','volume=8,alimiter=limit=0.25',$peakBad)
Invoke-Ffmpeg @('-f','lavfi','-i','color=c=black:s=640x360:d=3','-an',$noAudioMp4)
Invoke-Ffmpeg @('-f','lavfi','-i','color=c=black:s=640x360:d=3','-f','lavfi','-i','sine=frequency=330:duration=3','-af','loudnorm=I=-25:TP=-3:LRA=7','-map','0:v:0','-map','1:a:0','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',$tooLowMp4)

# Case A — too low
$caseA = Invoke-Py -PyArgs @($repairCli, $tooLow, '--profile', $profilePath, '--work-dir', $workDir) -AllowExitCodes @(0)
$aJson = $caseA[1] | ConvertFrom-Json
Assert-True ($aJson.before_qa.verdict -eq 'LOUDNESS_TOO_LOW') 'B01 Case A detect too low'
Assert-True ($aJson.after_qa.verdict -eq 'PASS') 'B02 Case A post-repair PASS'
Assert-True ($aJson.after_qa.loudness.integrated_lufs -ge -17 -and $aJson.after_qa.loudness.integrated_lufs -le -15) 'B03 Case A integrated in range'
Assert-True ($aJson.after_qa.loudness.true_peak_dbtp -le -1) 'B04 Case A true peak OK'
Assert-True ($null -ne $aJson.repair.pass1_measured.input_i) 'B05 Case A pass1 measured input_i'
Assert-True ($aJson.repair.pass2_filter -match 'measured_I=') 'B06 Case A pass2 uses measured values'

# Case B — too high
$caseB = Invoke-Py -PyArgs @($repairCli, $tooHigh, '--profile', $profilePath, '--work-dir', $workDir) -AllowExitCodes @(0)
$bJson = $caseB[1] | ConvertFrom-Json
Assert-True ($bJson.before_qa.verdict -eq 'LOUDNESS_TOO_HIGH') 'C01 Case B detect too high'
Assert-True ($bJson.after_qa.verdict -eq 'PASS') 'C02 Case B post-repair PASS'

# Case C — peak
$caseC = Invoke-Py -PyArgs @($repairCli, $peakBad, '--profile', $profilePath, '--work-dir', $workDir) -AllowExitCodes @(0, 2)
$cJson = $caseC[1] | ConvertFrom-Json
Assert-True ($cJson.before_qa.verdict -eq 'TRUE_PEAK_EXCEEDED') 'D01 Case C detect peak'
Assert-True (($cJson.after_qa.verdict -eq 'PASS') -or ($cJson.status -eq 'FINAL_AUDIO_REPAIR_FAILED')) 'D02 Case C repair outcome explicit'

# Case D — already pass
$caseD = Invoke-Py -PyArgs @($repairCli, $passWav, '--profile', $profilePath, '--work-dir', $workDir) -AllowExitCodes @(0)
$dJson = $caseD[1] | ConvertFrom-Json
Assert-True ($dJson.verdict -eq 'NO_REPAIR_REQUIRED') 'E01 Case D NO_REPAIR_REQUIRED'
Assert-True ($dJson.attempts -eq 0) 'E02 Case D zero attempts'

# Case E — MP4 video preserved
$beforeMeta = Probe-VideoMeta -Path $tooLowMp4
$caseE = Invoke-Py -PyArgs @($repairCli, $tooLowMp4, '--profile', $profilePath, '--work-dir', $workDir) -AllowExitCodes @(0)
$eJson = $caseE[1] | ConvertFrom-Json
$afterMeta = Probe-VideoMeta -Path $eJson.repaired_artifact
$bv = $beforeMeta.streams | Where-Object { $_.codec_type -eq 'video' } | Select-Object -First 1
$av = $afterMeta.streams | Where-Object { $_.codec_type -eq 'video' } | Select-Object -First 1
Assert-True ($eJson.video_preserved -eq $true) 'F01 Case E video_preserved flag'
Assert-True ($bv.codec_name -eq $av.codec_name) 'F02 Case E video codec unchanged'
Assert-True ($bv.width -eq $av.width -and $bv.height -eq $av.height) 'F03 Case E resolution unchanged'
Assert-True ($bv.r_frame_rate -eq $av.r_frame_rate) 'F04 Case E fps unchanged'
Assert-True ($eJson.after_qa.verdict -eq 'PASS') 'F05 Case E post-repair audio PASS'

# Case F — no audio
$caseF = Invoke-Py -PyArgs @($repairCli, $noAudioMp4, '--profile', $profilePath, '--work-dir', $workDir) -AllowExitCodes @(2)
$fJson = $caseF[1] | ConvertFrom-Json
Assert-True ($fJson.verdict -eq 'BLOCKED') 'G01 Case F BLOCKED'
Assert-True ($fJson.before_qa.verdict -eq 'NO_AUDIO') 'G02 Case F NO_AUDIO'

# Case G — simulate failure preserves original
$origHash = Get-FileSha256 -Path $tooLow
$env:LOUDNORM_REPAIR_SIMULATE_FAIL = '1'
try {
    $caseG = Invoke-Py -PyArgs @($repairCli, $tooLow, '--profile', $profilePath, '--work-dir', (Join-Path $workDir 'fail-sim')) -AllowExitCodes @(2)
    $gJson = $caseG[1] | ConvertFrom-Json
    Assert-True ($gJson.status -eq 'FINAL_AUDIO_REPAIR_FAILED') 'H01 Case G repair failed status'
    Assert-True ((Get-FileSha256 -Path $tooLow) -eq $origHash) 'H02 Case G original hash preserved'
    Assert-True ($null -eq $gJson.PSObject.Properties['promoted_to']) 'H03 Case G no promote on failure'
}
finally {
    Remove-Item Env:LOUDNORM_REPAIR_SIMULATE_FAIL -ErrorAction SilentlyContinue
}

# Orchestrator loop
$orchOut = & powershell -NoProfile -File $orchestrator -VideoPath $tooLow -WorkDir (Join-Path $workDir 'orch-low') 2>&1
$orchStatus = ($orchOut | Select-Object -Last 1)
Assert-True ($orchStatus -match 'REPAIR_PASS') 'I01 orchestrator repair pass'
$orchReport = Get-Content -LiteralPath ($orchOut | Select-Object -First 1) -Raw | ConvertFrom-Json
Assert-True ($orchReport.repair_attempted -eq $true) 'I02 orchestrator attempted repair'
Assert-True ($orchReport.after_qa.verdict -eq 'PASS') 'I03 orchestrator after_qa PASS'

$orchPass = & powershell -NoProfile -File $orchestrator -VideoPath $passWav -WorkDir (Join-Path $workDir 'orch-pass') 2>&1
Assert-True (($orchPass | Select-Object -Last 1) -eq 'NO_REPAIR_REQUIRED') 'I04 orchestrator no-op on PASS'

# Max attempts = 1 (profile contract)
Assert-True ($aJson.max_attempts -eq 1) 'J01 max_attempts 1'
Assert-True ($aJson.attempts -le 1) 'J02 single repair attempt'

# Regressions
& powershell -NoProfile -File (Join-Path $PSScriptRoot 'production-audio-mix-profile.ps1') | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'R01 Step 4A regression'
& powershell -NoProfile -File (Join-Path $PSScriptRoot 'production-pacing-reframe-qa.ps1') | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'R02 Step 4B regression'
& powershell -NoProfile -File (Join-Path $PSScriptRoot 'shared-asset-library.ps1') | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'R03 shared asset library regression'
& powershell -NoProfile -File (Join-Path $PSScriptRoot 'capability-resolution-consistency.ps1') | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'R04 capability policy regression'
& powershell -NoProfile -File (Join-Path $PSScriptRoot 'production-subtitle-readability.ps1') | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'R05 subtitle regression'

Assert-True (Test-Path $closeout) 'Z01 closeout doc exists'

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
