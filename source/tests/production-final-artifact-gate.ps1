#Requires -Version 5.1
<#
.SYNOPSIS
  R2 — Final Artifact Gate E2E (A–E).
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$Pass = 0
$Fail = 0

function Assert-True {
    param([bool]$Condition, [string]$Name)
    if ($Condition) { Write-Host "[PASS] $Name" -ForegroundColor Green; $script:Pass++ }
    else { Write-Host "[FAIL] $Name" -ForegroundColor Red; $script:Fail++ }
}

function Require-Cmd([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) { throw "REQUIRED_TOOL_MISSING: $Name" }
}

function New-FixtureMp4 {
    param(
        [string]$OutPath,
        [bool]$WithBurnInText,
        [string]$AssDialogueWindow = '0:00:00.50,0:00:04.50'
    )
    Require-Cmd ffmpeg
    $dir = Split-Path -Parent $OutPath
    $name = Split-Path -Leaf $OutPath
    $assPath = Join-Path $dir 'fixture-burnin.ass'
    if ($WithBurnInText) {
        $dialogue = "Dialogue: 0,$AssDialogueWindow,Default,,0,0,0,,BURNIN_OK"
        @"
[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,52,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,0,2,72,72,280,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
$dialogue
"@ | Set-Content -LiteralPath $assPath -Encoding UTF8
    }
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    Push-Location $dir
    try {
        if ($WithBurnInText) {
            & ffmpeg -y -hide_banner -loglevel error `
                -f lavfi -i 'color=c=#505050:s=1080x1920:d=5' `
                -f lavfi -i 'sine=frequency=440:duration=5' `
                -vf 'ass=fixture-burnin.ass' -shortest -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 128k $name 2>&1 | Out-Null
        }
        else {
            & ffmpeg -y -hide_banner -loglevel error `
                -f lavfi -i 'color=c=#505050:s=1080x1920:d=5' `
                -f lavfi -i 'sine=frequency=440:duration=5' `
                -shortest -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 128k $name 2>&1 | Out-Null
        }
    }
    finally {
        Pop-Location
    }
    $ErrorActionPreference = $prev
    if (-not (Test-Path -LiteralPath $OutPath)) { throw "FFMPEG_FIXTURE_FAILED: $OutPath" }
}

function New-AssBurnInFromMaster {
    param(
        [string]$MasterPath,
        [string]$OutPath
    )
    $dir = Split-Path -Parent $OutPath
    $name = Split-Path -Leaf $OutPath
    $assPath = Join-Path $dir 'fixture-burnin-from-master.ass'
    @'
[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,52,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,0,2,72,72,280,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.50,0:00:04.50,Default,,0,0,0,,BURNIN_OK
'@ | Set-Content -LiteralPath $assPath -Encoding UTF8
    Push-Location $dir
    try {
        & ffmpeg -y -hide_banner -loglevel error -i $MasterPath -vf 'ass=fixture-burnin-from-master.ass' -c:v libx264 -pix_fmt yuv420p -c:a copy $name 2>&1 | Out-Null
    }
    finally { Pop-Location }
    if (-not (Test-Path -LiteralPath $OutPath)) { throw "ASS_BURNIN_FAILED: $OutPath" }
}

function New-FalsePositiveBrightObjectMp4 {
    param([string]$OutPath)
    $dir = Split-Path -Parent $OutPath
    $name = Split-Path -Leaf $OutPath
    $vf = 'drawbox=x=228:y=ih*0.70:w=624:h=112:color=black@1:t=8,drawbox=x=240:y=ih*0.72:w=600:h=88:color=white@1:t=fill'
    Push-Location $dir
    try {
        & ffmpeg -y -hide_banner -loglevel error `
            -f lavfi -i 'color=c=#505050:s=1080x1920:d=5' `
            -f lavfi -i 'sine=frequency=440:duration=5' `
            -vf $vf -shortest -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 128k $name 2>&1 | Out-Null
    }
    finally { Pop-Location }
    if (-not (Test-Path -LiteralPath $OutPath)) { throw "FALSE_POSITIVE_FIXTURE_FAILED: $OutPath" }
}

Write-Host '=== R2 Final Artifact Gate (E2E) ===' -ForegroundColor Cyan

$toolsSrc = Join-Path $Root 'payload\video-workflow\tools'
$gatePy = Join-Path $toolsSrc 'run-final-artifact-gate.py'
$verifyPy = Join-Path $toolsSrc 'verify-production-final-deliver.py'
$tmp = Join-Path $PSScriptRoot '.tmp-r2-final-gate'
if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force }
$prod = Join-Path $tmp 'video-workflow\production'
$qaDir = Join-Path $tmp 'video-workflow\.qa\r2-run'
New-Item -ItemType Directory -Path $prod -Force | Out-Null
Copy-Item -LiteralPath $toolsSrc -Destination (Join-Path $tmp 'video-workflow\tools') -Recurse -Force

$cleanA = Join-Path $prod 'case_a_clean.mp4'
$burnMp4 = Join-Path $prod 'case_a_burnin.mp4'
$cleanMp4 = Join-Path $prod 'case_b_clean.mp4'
$falsePositiveMp4 = Join-Path $prod 'case_c_false_positive.mp4'
New-FixtureMp4 -OutPath $cleanA -WithBurnInText $false
New-AssBurnInFromMaster -MasterPath $cleanA -OutPath $burnMp4
New-FixtureMp4 -OutPath $cleanMp4 -WithBurnInText $false
New-FalsePositiveBrightObjectMp4 -OutPath $falsePositiveMp4

$canonical = Join-Path $prod 'canonical-subtitle-cues.json'
@{
    schema_version = 1
    cues           = @(
        @{
            cue_id = 'c01'
            start  = 0.5
            end    = 4.5
            text   = 'BURNIN_OK'
            lines  = @('BURNIN_OK')
        }
    )
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $canonical -Encoding UTF8

function Invoke-GateToFile {
    param($ContractPath, $OutJson, $WorkSubdir)
    $qaReport = Join-Path (Join-Path $qaDir $WorkSubdir) 'final-artifact-qa.json'
    New-Item -ItemType Directory -Path (Split-Path $qaReport) -Force | Out-Null
    @{
        black_bar_check   = @{ verdict = 'NO_EDGE_BLACK_PATTERN' }
        audio_loudness_qa = @{ skipped = $true }
    } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $qaReport -Encoding UTF8
    $workDir = Join-Path (Join-Path $qaDir $WorkSubdir) 'frames'
    & python $gatePy --contract $ContractPath --qa-report $qaReport --work-dir $workDir --out $OutJson 2>&1 | Out-Null
    return [int]$LASTEXITCODE
}

# Case A — differential burn-in PASS
$contractA = Join-Path $prod 'final-render-contract-a.json'
@{
    schema_version               = 1
    deliver_authority            = 'final_mp4_burned'
    renderer_route               = 'external_ass'
    render_source_timeline       = 'R2_FIXTURE_A'
    clean_master_path            = $cleanA
    final_artifact_path          = $burnMp4
    subtitle_materialization     = 'external_ass_burnin'
    burnin_method                = 'ffmpeg_libass'
    resolve_subtitle_export_mode = 'burn_into_video'
    sidecar_subtitle_paths       = @()
    expected_resolution          = @{ width = 1080; height = 1920 }
    expected_fps                 = 25
    expected_duration_seconds    = 5
    canonical_subtitle_cues_path = $canonical
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $contractA -Encoding UTF8

$outA = Join-Path $prod 'gate-a.json'
$ecA = Invoke-GateToFile -ContractPath $contractA -OutJson $outA -WorkSubdir 'a'
Assert-True ($ecA -eq 0) 'Case A gate exit 0'
$gateA = Get-Content -LiteralPath $outA -Raw -Encoding UTF8 | ConvertFrom-Json
Assert-True ($gateA.verdict -eq 'PASS') 'Case A FINAL_ARTIFACT_GATE PASS'
Assert-True ($gateA.checks.FINAL_RENDER_SUBTITLE_BURNIN -eq 'PASS') 'Case A FINAL_RENDER_SUBTITLE_BURNIN PASS'
Assert-True ($null -ne $gateA.evidence_bindings.contract_sha256) 'Case A evidence bindings present'

# Case B — N03 separate subtitle file regression
$sidecar = Join-Path $prod 'deliver.ttml'
'<?xml version="1.0"?><tt xmlns="http://www.w3.org/ns/ttml"><body><div><p>sidecar only</p></div></body></tt>' | Set-Content -LiteralPath $sidecar -Encoding UTF8
$contractB = Join-Path $prod 'final-render-contract-b.json'
@{
    schema_version               = 1
    deliver_authority            = 'final_mp4_burned'
    renderer_route               = 'native_drt'
    render_source_timeline       = 'R2_FIXTURE_B_N03'
    final_artifact_path          = $cleanMp4
    subtitle_materialization     = 'native_drt_burnin'
    burnin_method                = 'resolve_export_burn_in'
    resolve_subtitle_export_mode = 'separate_subtitle_file'
    sidecar_subtitle_paths       = @($sidecar)
    expected_resolution          = @{ width = 1080; height = 1920 }
    expected_fps                 = 25
    expected_duration_seconds    = 5
    canonical_subtitle_cues_path = $canonical
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $contractB -Encoding UTF8

$outB = Join-Path $prod 'gate-b.json'
$ecB = Invoke-GateToFile -ContractPath $contractB -OutJson $outB -WorkSubdir 'b'
Assert-True ($ecB -ne 0) 'Case B gate exit non-zero'
$gateB = Get-Content -LiteralPath $outB -Raw -Encoding UTF8 | ConvertFrom-Json
Assert-True ($gateB.verdict -eq 'FAIL') 'Case B FINAL_ARTIFACT_GATE FAIL'
Assert-True ($gateB.checks.FINAL_RENDER_SUBTITLE_BURNIN -eq 'FAIL') 'Case B FINAL_RENDER_SUBTITLE_BURNIN FAIL'
$errJoin = ($gateB.errors | ForEach-Object { $_ }) -join ' '
Assert-True ($errJoin -match 'N03_SEPARATE') 'Case B N03 separate export flagged'

# Case C — bright object false positive (no real burn-in)
$contractC = Join-Path $prod 'final-render-contract-c.json'
@{
    schema_version               = 1
    deliver_authority            = 'final_mp4_burned'
    renderer_route               = 'native_drt'
    render_source_timeline       = 'R2_FIXTURE_C_FALSE_POSITIVE'
    final_artifact_path          = $falsePositiveMp4
    subtitle_materialization     = 'native_drt_burnin'
    burnin_method                = 'resolve_export_burn_in'
    resolve_subtitle_export_mode = 'burn_into_video'
    sidecar_subtitle_paths       = @()
    expected_resolution          = @{ width = 1080; height = 1920 }
    expected_fps                 = 25
    expected_duration_seconds    = 5
    canonical_subtitle_cues_path = $canonical
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $contractC -Encoding UTF8

$outC = Join-Path $prod 'gate-c.json'
$ecC = Invoke-GateToFile -ContractPath $contractC -OutJson $outC -WorkSubdir 'c'
Assert-True ($ecC -ne 0) 'Case C gate exit non-zero'
$gateC = Get-Content -LiteralPath $outC -Raw -Encoding UTF8 | ConvertFrom-Json
Assert-True ($gateC.checks.FINAL_RENDER_SUBTITLE_BURNIN -ne 'PASS') 'Case C FINAL_RENDER_SUBTITLE_BURNIN not PASS'

# Case D — stale PASS after artifact swap
$prodContract = Join-Path $prod 'final-render-contract.json'
Copy-Item -LiteralPath $contractA -Destination $prodContract -Force
$gateProd = Join-Path $prod 'final-artifact-gate-result.json'
Copy-Item -LiteralPath $outA -Destination $gateProd -Force
Copy-Item -LiteralPath $cleanMp4 -Destination $burnMp4 -Force
& python $verifyPy --workspace $tmp 2>$null
Assert-True ($LASTEXITCODE -eq 4) 'Case D verify blocked after artifact swap'

# Case E — stale PASS after contract mutation
Copy-Item -LiteralPath $outA -Destination $gateProd -Force
Copy-Item -LiteralPath $cleanA -Destination $burnMp4 -Force
New-AssBurnInFromMaster -MasterPath $cleanA -OutPath $burnMp4
$contractMut = Get-Content -LiteralPath $prodContract -Raw -Encoding UTF8 | ConvertFrom-Json
$contractMut.render_source_timeline = 'MUTATED_AFTER_GATE'
$contractMut | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $prodContract -Encoding UTF8
& python $verifyPy --workspace $tmp 2>$null
Assert-True ($LASTEXITCODE -eq 4) 'Case E verify blocked after contract change'

$l3 = Get-Content (Join-Path $Root 'payload\.cursor\skills\video-production\SKILL.md') -Raw -Encoding UTF8
Assert-True ($l3 -match 'run-final-artifact-gate') 'L3 references final artifact gate orchestrator'
Assert-True ($l3 -match 'evidence_bindings|contract_sha256') 'L3 or docs reference SHA bindings'

$vocab = Get-Content (Join-Path $Root 'payload\video-workflow\capabilities\logical-capability-vocabulary.yaml') -Raw -Encoding UTF8
Assert-True ($vocab -match 'final_render\.artifact_gate') 'R2 vocabulary final_render.artifact_gate'

Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
exit 0
