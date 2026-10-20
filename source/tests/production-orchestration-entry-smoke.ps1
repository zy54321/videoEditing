#Requires -Version 5.1
<#
.SYNOPSIS
  Product-entry orchestration smoke — isolated workspace, official invoke scripts only.
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

Write-Host '=== Production orchestration entry smoke ===' -ForegroundColor Cyan

$tmp = Join-Path $PSScriptRoot '.tmp-orchestration-smoke'
if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force }
$prod = Join-Path $tmp 'video-workflow\production'
$toolsSrc = Join-Path $Root 'payload\video-workflow\tools'
New-Item -ItemType Directory -Path $prod -Force | Out-Null
Copy-Item -LiteralPath $toolsSrc -Destination (Join-Path $tmp 'video-workflow\tools') -Recurse -Force
$tplDst = Join-Path $tmp 'video-workflow\templates'
New-Item -ItemType Directory -Path $tplDst -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $Root 'payload\video-workflow\templates\subtitle-external-ass-style-baseline.v1.json') -Destination $tplDst

# --- R1 chain (product subtitle orchestrator) ---
$r1Fixture = Join-Path $PSScriptRoot 'fixtures\r1-subtitle-production-e2e'
Copy-Item -LiteralPath (Join-Path $r1Fixture 'brief.yaml') -Destination (Join-Path $prod 'brief.yaml')
Copy-Item -LiteralPath (Join-Path $r1Fixture 'frozen-script.txt') -Destination (Join-Path $prod 'frozen-script.txt')
Copy-Item -LiteralPath (Join-Path $r1Fixture 'asr-timing-evidence.json') -Destination (Join-Path $prod 'asr-timing-evidence.json')

$route = Join-Path $tmp 'video-workflow\tools\invoke-frozen-script-subtitle-route.ps1'
& $route -WorkspaceRoot $tmp -NoPause
Assert-True ($LASTEXITCODE -eq 0) 'S01 invoke-frozen-script-subtitle-route'

# --- R3 plan (no Resolve apply) ---
$landscape = Join-Path $tmp 'landscape_src.mp4'
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    throw 'SMOKE_BLOCKED: ffmpeg required'
}
Push-Location $tmp
ffmpeg -y -hide_banner -loglevel error -f lavfi -i 'color=c=#336699:s=1760x974:d=1' -pix_fmt yuv420p landscape_src.mp4 2>$null | Out-Null
Pop-Location

$probe = @{
    name = 'smoke-timeline'
    tracks = @{
        video = @{
            tracks = @(
                @{
                    items = @(
                        @{
                            timeline_item_id = 'smoke-item-1'
                            name = 'landscape_src.mp4'
                            file_path = $landscape
                            item_index = 0
                        }
                    )
                }
            )
        }
    }
}
$probePath = Join-Path $prod 'timeline-probe.json'
$probe | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $probePath -Encoding UTF8

$reframe = Join-Path $tmp 'video-workflow\tools\invoke-static-portrait-reframe.ps1'
& $reframe -WorkspaceRoot $tmp
Assert-True ($LASTEXITCODE -eq 0) 'S02 invoke-static-portrait-reframe plan'
$planPath = Join-Path $prod 'static-portrait-reframe-plan.json'
$plan = Get-Content $planPath -Raw | ConvertFrom-Json
Assert-True ($plan.policy_id -eq 'static-portrait-reframe.v1') 'S02 policy id'
Assert-True ($plan.shots[0].resolve_crop.CropLeft -eq 0) 'S02 zoom-only crop'

# --- External ASS deliver + R2 closeout ---
$outDir = Join-Path $tmp 'output'
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$clean = Join-Path $outDir 'smoke_clean_master.mp4'
$final = Join-Path $outDir 'smoke_final.mp4'
Push-Location $tmp
ffmpeg -y -hide_banner -loglevel error -f lavfi -i 'color=c=#404040:s=1080x1920:r=24:d=30' -f lavfi -i 'sine=d=30' -shortest -r 24 -c:v libx264 -pix_fmt yuv420p -c:a aac $clean 2>$null | Out-Null
Pop-Location

$contract = @{
    schema_version = 1
    deliver_authority = 'final_mp4_burned'
    renderer_route = 'external_ass'
    subtitle_materialization = 'external_ass_burnin'
    subtitle_export_mode = 'burn_in'
    clean_master_path = $clean
    final_artifact_path = $final
    canonical_subtitle_cues_path = (Join-Path $prod 'canonical-subtitle-cues.json')
    expected_width = 1080
    expected_height = 1920
    expected_fps = 24.0
}
$contractPath = Join-Path $prod 'final-render-contract.json'
$contract | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $contractPath -Encoding UTF8

$closeout = Join-Path $tmp 'video-workflow\tools\invoke-production-deliver-closeout.ps1'
& $closeout -WorkspaceRoot $tmp -SkipAudioLoudness
Assert-True ($LASTEXITCODE -eq 0) 'S03 invoke-production-deliver-closeout'
Assert-True (Test-Path -LiteralPath $final) 'S03 final mp4 exists'
$deliverResult = Join-Path $prod 'external-ass-deliver-result.json'
Assert-True (Test-Path -LiteralPath $deliverResult) 'S03 external-ass-deliver-result.json'
$gateResult = Join-Path $prod 'final-artifact-gate-result.json'
$gate = Get-Content $gateResult -Raw | ConvertFrom-Json
Assert-True ($gate.verdict -eq 'PASS') 'S03 FINAL_ARTIFACT_GATE PASS'

# --- Fail-closed: missing clean master ---
Remove-Item -LiteralPath $clean -Force
$extOnly = Join-Path $tmp 'video-workflow\tools\invoke-external-ass-deliver-route.ps1'
$failClosed = $false
try {
    & $extOnly -WorkspaceRoot $tmp 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { $failClosed = $true }
} catch {
    $failClosed = $true
}
Assert-True $failClosed 'S04 external ASS fails when clean master missing'

# --- L3 references orchestrators ---
$l3 = Get-Content (Join-Path $Root 'payload\.cursor\skills\video-production\SKILL.md') -Raw -Encoding UTF8
Assert-True ($l3 -match 'invoke-external-ass-deliver-route') 'S05 L3 external ASS orchestrator'
Assert-True ($l3 -match 'invoke-static-portrait-reframe') 'S05 L3 reframe orchestrator'
Assert-True ($l3 -match 'invoke-production-deliver-closeout') 'S05 L3 deliver closeout'

Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed"
if ($Fail -gt 0) { exit 1 }
exit 0
