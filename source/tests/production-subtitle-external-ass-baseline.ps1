#Requires -Version 5.1
<#
.SYNOPSIS
  Subtitle Style Baseline Closure — regression (T01–T04).
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$Payload = Join-Path $Root 'payload'
$Tools = Join-Path $Payload 'video-workflow\tools'
$Templates = Join-Path $Payload 'video-workflow\templates'
$Lib = Join-Path $Tools 'lib'
$Pass = 0
$Fail = 0

function Assert-True {
    param([bool]$Condition, [string]$Name)
    if ($Condition) { Write-Host "[PASS] $Name" -ForegroundColor Green; $script:Pass++ }
    else { Write-Host "[FAIL] $Name" -ForegroundColor Red; $script:Fail++ }
}

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { throw 'REQUIRED_TOOL_MISSING: python' }

$baselineJson = Join-Path $Templates 'subtitle-external-ass-style-baseline.v1.json'
$toAssCli = Join-Path $Tools 'canonical-to-external-ass.py'
$burnCli = Join-Path $Tools 'external-ass-burnin.py'
$fixtureCanon = Join-Path $PSScriptRoot 'fixtures\external-ass-baseline\canonical-cues-fixture.json'
$tmp = Join-Path $env:TEMP "subtitle-baseline-closure-$([Guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $tmp -Force | Out-Null

# T01 — baseline file exists and matches N02Prod field set
$baseline = Get-Content -LiteralPath $baselineJson -Raw -Encoding UTF8 | ConvertFrom-Json
Assert-True ($baseline.baseline_id -eq 'astra-external-ass-n02prod-v1') 'T01 baseline_id'
Assert-True ($baseline.style.Name -eq 'N02Prod') 'T01 style Name'
Assert-True ($baseline.style.Fontsize -eq '52') 'T01 Fontsize'
Assert-True ($baseline.style.Outline -eq '4') 'T01 Outline'
Assert-True ($baseline.provenance.source_ass_sha256.Length -eq 64) 'T01 provenance sha256'

# T02 — fixture ASS generation + text match
$fixtureAss = Join-Path $tmp 'fixture.ass'
& python $toAssCli --canonical $fixtureCanon --out $fixtureAss --manifest (Join-Path $tmp 'manifest.json')
Assert-True ($LASTEXITCODE -eq 0) 'T02 fixture canonical-to-external-ass exit 0'
$assText = Get-Content -LiteralPath $fixtureAss -Raw -Encoding UTF8
Assert-True ($assText -match 'Style: N02Prod,Microsoft YaHei UI,52') 'T02 style line present'
Assert-True (($assText -split 'Dialogue:').Count -eq 5) 'T02 four dialogue lines' # header split + 4
Assert-True ($assText.Contains('\N')) 'T02 multiline backslash-N preserved'

# T02 fail-closed — blocked canonical
$blocked = Join-Path $tmp 'blocked.json'
@{ schema_version = 1; pipeline_id = 'subtitle.authority_alignment_v1'; meta = @{ status = 'BLOCKED' }; cues = @() } |
    ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $blocked -Encoding UTF8
$prevEap = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
& python $toAssCli --canonical $blocked --out (Join-Path $tmp 'x.ass') 2>&1 | Out-Null
$blockedExit = $LASTEXITCODE
& python $toAssCli --canonical $fixtureCanon --out (Join-Path $tmp 'y.ass') --baseline (Join-Path $tmp 'nope.json') 2>&1 | Out-Null
$missingBaselineExit = $LASTEXITCODE
$ErrorActionPreference = $prevEap
Assert-True ($blockedExit -ne 0) 'T02 fail-closed BLOCKED canonical'
Assert-True ($missingBaselineExit -ne 0) 'T02 fail-closed missing baseline'

# T03 — burn-in (minimal ffmpeg master)
$master = Join-Path $tmp 'master.mp4'
if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    Push-Location $tmp
    ffmpeg -y -hide_banner -loglevel error -f lavfi -i 'color=c=#404040:s=1080x1920:d=2' -f lavfi -i 'sine=d=2' -shortest -c:v libx264 -pix_fmt yuv420p -c:a aac master.mp4 2>$null | Out-Null
    Pop-Location
    $outMp4 = Join-Path $tmp 'burnin.mp4'
    & python $burnCli --clean-master $master --ass $fixtureAss --out $outMp4
    Assert-True ($LASTEXITCODE -eq 0) 'T03 burn-in exit 0'
    Assert-True (Test-Path -LiteralPath $outMp4) 'T03 burn-in output exists'
}
else {
    Write-Host '[SKIP] T03 ffmpeg not installed' -ForegroundColor Yellow
}

# T04 — N03 golden replay (optional, media present)
$n03Canon = 'E:\03_Media\02_Video\Davinci\Astra\2026-10-12\N03\video-workflow\production\canonical-subtitle-cues.json'
$n03GoldenAss = 'E:\03_Media\02_Video\Davinci\Astra\2026-10-12\output\N03_V9.ass'
$n03GoldenSha = '1eb853869dccae97992258bf86f77a57ab4a40e581853f4a47eea49e9d38b856'
if ((Test-Path -LiteralPath $n03Canon) -and (Test-Path -LiteralPath $n03GoldenAss)) {
    $replayAss = Join-Path $tmp 'n03_replay.ass'
    & python $toAssCli --canonical $n03Canon --out $replayAss
    Assert-True ($LASTEXITCODE -eq 0) 'T04 N03 canonical replay exit 0'
    $replayBytes = [System.IO.File]::ReadAllBytes($replayAss)
    $sha = [System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash($replayBytes)).Replace('-', '').ToLowerInvariant()
    Assert-True ($sha -eq $n03GoldenSha) 'T04 N03_V9.ass byte-identical replay'
    $dialogueCount = ([regex]::Matches((Get-Content -LiteralPath $replayAss -Raw), '(?m)^Dialogue:')).Count
    Assert-True ($dialogueCount -eq 43) 'T04 cue count 43'
}
else {
    Write-Host '[SKIP] T04 N03 media paths not available' -ForegroundColor Yellow
}

# T04 — R2 gate on existing N03 contract (read-only)
$n03Contract = 'E:\03_Media\02_Video\Davinci\Astra\2026-10-12\N03\video-workflow\production\final-render-contract-v9.json'
$n03Final = 'E:\03_Media\02_Video\Davinci\Astra\2026-10-12\output\N03_V9.mp4'
if ((Test-Path -LiteralPath $n03Contract) -and (Test-Path -LiteralPath $n03Final)) {
    $gateOut = Join-Path $tmp 'gate.json'
    $gateCli = Join-Path $Tools 'run-final-artifact-gate.py'
    & python $gateCli --contract $n03Contract --work-dir $tmp --out $gateOut
    Assert-True ($LASTEXITCODE -eq 0) 'T04 FINAL_ARTIFACT_GATE exit 0'
    $gate = Get-Content $gateOut -Raw | ConvertFrom-Json
    Assert-True ($gate.verdict -eq 'PASS') 'T04 FINAL_ARTIFACT_GATE PASS'
    Assert-True ($gate.checks.FINAL_RENDER_SUBTITLE_BURNIN -eq 'PASS') 'T04 FINAL_RENDER_SUBTITLE_BURNIN PASS'
}
else {
    Write-Host '[SKIP] T04 R2 gate replay (N03 contract/final missing)' -ForegroundColor Yellow
}

Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "---"
Write-Host "Pass: $Pass Fail: $Fail"
if ($Fail -gt 0) { exit 1 }
