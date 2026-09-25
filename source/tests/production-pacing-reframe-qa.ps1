#Requires -Version 5.1
<#
.SYNOPSIS
  Production Repair Step 4B — pacing + black-bar / reframe QA tests.
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

Write-Host '=== Production Pacing / Reframe QA Tests (Step 4B) ===' -ForegroundColor Cyan
Write-Host ''

$utf8 = New-Object System.Text.UTF8Encoding $false
$pacingProfile = Join-Path $Payload 'video-workflow\runtime\informational-short-pacing-v1-profile.yaml'
$bbProfile = Join-Path $Payload 'video-workflow\runtime\black-bar-reframe-qa-profile.yaml'
$pacingCli = Join-Path $Payload 'video-workflow\tools\pacing-qa.py'
$bbCli = Join-Path $Payload 'video-workflow\tools\black-bar-qa.py'
$finalQaCli = Join-Path $Payload 'video-workflow\tools\final-artifact-qa.ps1'
$refPath = Join-Path $Payload 'video-workflow\templates\informational-short-pacing-v1-reference.md'
$ref = [System.IO.File]::ReadAllText($refPath, $utf8)
$l1 = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\capabilities\davinci-resolve.md'), $utf8)
$vocab = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\capabilities\logical-capability-vocabulary.yaml'), $utf8)
$l3 = [System.IO.File]::ReadAllText((Join-Path $Payload '.cursor\skills\video-production\SKILL.md'), $utf8)
$bpTpl = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\templates\edit-blueprint.yaml'), $utf8)
$closeout = Join-Path $RepoRoot 'validation\production-repair-step4b-pacing-reframe-closeout.md'

$fixtureRoot = Join-Path $PSScriptRoot 'fixtures\pacing-reframe'
New-Item -ItemType Directory -Force -Path $fixtureRoot | Out-Null

# Contract
Assert-True (Test-Path $pacingProfile) 'A01 pacing profile exists'
Assert-True (Test-Path $bbProfile) 'A02 black-bar profile exists'
Assert-True ($ref -match 'Repair gap') 'A03 audit root cause documented'
Assert-True ($vocab -match 'qa\.pacing\.heuristic:[\s\S]{0,80}VERIFIED') 'A04 pacing heuristic VERIFIED'
Assert-True ($vocab -match 'qa\.visual\.reframe_repair_loop:[\s\S]{0,80}VERIFIED') 'A05 repair loop VERIFIED fixture'
Assert-True ($vocab -match 'visual\.reframe\.static:[\s\S]{0,80}VERIFIED') 'A06 static reframe unchanged'
Assert-True ($vocab -match 'visual\.motion\.push_in:[\s\S]{0,120}AVAILABLE_UNVERIFIED') 'A07 push-in not upgraded'
Assert-True ($bpTpl -match 'assembly_plan:') 'A08 blueprint assembly_plan field'
Assert-True ($l3 -match 'black-bar-qa\.py') 'A09 L3 black-bar tool'
Assert-True ($l3 -match 'pacing-qa\.py') 'A10 L3 pacing tool'

# Generate visual fixtures
$caseA = Join-Path $fixtureRoot 'case-a-fill.png'
$caseB = Join-Path $fixtureRoot 'case-b-letterbox.png'
$caseC = Join-Path $fixtureRoot 'case-c-reframed.png'
$caseD = Join-Path $fixtureRoot 'case-d-scene-black.png'
Invoke-Ffmpeg @('-f','lavfi','-i','color=c=0x4488cc:s=1080x1920:d=1','-frames:v','1',$caseA)
Invoke-Ffmpeg @('-f','lavfi','-i','color=c=0x224466:s=1080x1440:d=1','-vf','pad=1080:1920:0:240:black','-update','1','-frames:v','1',$caseB)
Invoke-Ffmpeg @('-f','lavfi','-i','color=c=0x224466:s=1080x1920:d=1','-update','1','-frames:v','1',$caseC)
Invoke-Ffmpeg @('-f','lavfi','-i','color=c=0x88aacc:s=1080x1920:d=1','-vf','drawbox=x=400:y=800:w=280:h=280:color=black:t=fill','-frames:v','1',$caseD)

# Case A — PASS
$bbA = Invoke-Py -PyArgs @($bbCli, $caseA, '--profile', $bbProfile)
$bbAJson = $bbA[1] | ConvertFrom-Json
Assert-True ($bbAJson.verdict -eq 'PASS') 'B01 case A PASS'

# Case B — DETECT
$bbB = Invoke-Py -PyArgs @($bbCli, $caseB, '--profile', $bbProfile) -AllowExitCodes @(2)
$bbBJson = $bbB[1] | ConvertFrom-Json
Assert-True ($bbBJson.verdict -in @('REPAIR_REQUIRED','SUSPECT_BLACK_BARS')) 'B02 case B detected'
Assert-True ($bbBJson.dominant_bar_type -eq 'letterbox') 'B03 case B letterbox'

# Case C — re-QA PASS after reframe simulation
$bbC = Invoke-Py -PyArgs @($bbCli, $caseC, '--profile', $bbProfile)
$bbCJson = $bbC[1] | ConvertFrom-Json
Assert-True ($bbCJson.verdict -eq 'PASS') 'B04 case C re-QA PASS'

# Case D — no false bar
$bbD = Invoke-Py -PyArgs @($bbCli, $caseD, '--profile', $bbProfile)
$bbDJson = $bbD[1] | ConvertFrom-Json
Assert-True ($bbDJson.verdict -eq 'PASS') 'B05 case D no false positive'

# Repair loop B→C
Assert-True ($bbBJson.repair_suggestion.needed -eq $true) 'B06 repair suggestion on case B'
Assert-True ($bbBJson.repair_suggestion.route -eq 'visual.reframe.static') 'B07 static reframe route'

# Pacing Case E — exempt
$caseE = Join-Path $fixtureRoot 'assembly-case-e.json'
$pE = Invoke-Py -PyArgs @($pacingCli, '--assembly-json', $caseE, '--profile', $pacingProfile)
$pEJson = $pE[1] | ConvertFrom-Json
Assert-True ($pEJson.verdict -eq 'PASS') 'C01 case E exempt PASS'
Assert-True ($pE[1] -match 'PACING_EXEMPT') 'C02 case E has exempt finding'

# Pacing Case F — repair candidate
$caseF = Join-Path $fixtureRoot 'assembly-case-f.json'
$pF = Invoke-Py -PyArgs @($pacingCli, '--assembly-json', $caseF, '--profile', $pacingProfile) -AllowExitCodes @(2)
$pFJson = $pF[1] | ConvertFrom-Json
Assert-True ($pFJson.verdict -eq 'PACING_REPAIR_CANDIDATE') 'C03 case F repair candidate'
Assert-True ($pF[1] -match 'unchanged_visual_span_across_semantic_beats') 'C04 span across beats flagged'
Assert-True ($pF[1] -match 'B07-S12') 'C05 traceable shot_id'

# Long shot warning
$warnPath = Join-Path $fixtureRoot 'assembly-warning.json'
$pW = Invoke-Py -PyArgs @($pacingCli, '--assembly-json', $warnPath, '--profile', $pacingProfile) -AllowExitCodes @(2)
$pWJson = $pW[1] | ConvertFrom-Json
Assert-True ($pWJson.verdict -eq 'PACING_WARNING') 'C06 7s warning'

# final-artifact integration with letterbox video
$vidB = Join-Path $fixtureRoot 'case-b.mp4'
Invoke-Ffmpeg @('-loop','1','-i',$caseB,'-t','2','-c:v','libx264','-pix_fmt','yuv420p',$vidB)
$qaTmp = Join-Path $fixtureRoot '.qa'
$qaOut = & powershell -NoProfile -File $finalQaCli -VideoPath $vidB -QaRoot $qaTmp -RunId 'step4b-bb' -SkipAudioLoudness 2>&1
$qaReport = ($qaOut | Select-Object -First 1)
$qaJson = Get-Content -LiteralPath $qaReport -Raw | ConvertFrom-Json
Assert-True ($qaJson.black_bar_check.method -eq 'black_bar_qa_multiframe') 'D01 final-artifact uses black_bar_qa'
Assert-True ($qaJson.black_bar_check.verdict -ne 'PASS') 'D02 letterbox video not PASS'

# Regressions
& powershell -NoProfile -File (Join-Path $PSScriptRoot 'production-audio-mix-profile.ps1') | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'R01 audio QA regression'
& powershell -NoProfile -File (Join-Path $PSScriptRoot 'shared-asset-library.ps1') | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'R02 shared asset regression'
& powershell -NoProfile -File (Join-Path $PSScriptRoot 'production-subtitle-readability.ps1') | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'R03 subtitle regression'
$stage08e = Join-Path $RepoRoot 'validation\stage-08e-acceptance-closeout.md'
Assert-True (Test-Path $stage08e) 'R04 Stage 08E closeout unchanged on disk'

Assert-True (Test-Path $closeout) 'Z01 closeout exists'

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
