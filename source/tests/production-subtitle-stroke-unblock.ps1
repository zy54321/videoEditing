#Requires -Version 5.1
<#
.SYNOPSIS
  Production Repair Step 5 — native subtitle stroke template capture/inject contracts.
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

Write-Host '=== Production Subtitle Stroke Unblock Tests (Step 5) ===' -ForegroundColor Cyan
Write-Host ''

$utf8 = New-Object System.Text.UTF8Encoding $false
$probeRoot = Join-Path $RepoRoot 'validation\subtitle-stroke-probe'
$baselineDrt = Join-Path $probeRoot 'probe-style-fields.drt'
$styledDrt = Join-Path $probeRoot 'probe-track-style.drt'
$templateDir = Join-Path $Payload 'video-workflow\runtime\native-drt-subtitle-stroke-template'
$captureCli = Join-Path $Payload 'video-workflow\tools\native-drt-subtitle-stroke-capture.py'
$injectCli = Join-Path $Payload 'video-workflow\tools\native-drt-subtitle-stroke-inject.py'
$probePs1 = Join-Path $Payload 'video-workflow\tools\native-drt-subtitle-readability-probe.ps1'
$profilePath = Join-Path $Payload 'video-workflow\runtime\native-drt-subtitle-readability-profile.yaml'
$vocab = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\capabilities\logical-capability-vocabulary.yaml'), $utf8)
$closeout = Join-Path $RepoRoot 'validation\production-repair-step5-subtitle-readability-closeout.md'

Assert-True (Test-Path $baselineDrt) 'S01 baseline probe drt exists'
Assert-True (Test-Path $captureCli) 'S02 capture cli exists'
Assert-True (Test-Path $injectCli) 'S03 inject cli exists'

$profile = [System.IO.File]::ReadAllText($profilePath, $utf8)
Assert-True ($profile -match 'native_drt_effect_filters_ba_template') 'S04 profile documents Route A template'
Assert-True ($profile -match 'stroke_automation:\s*BLOCKED') 'S05 stroke_automation still BLOCKED'

$fixtureTpl = Join-Path $PSScriptRoot 'fixtures\subtitle-stroke-unblock\.capture-out'
New-Item -ItemType Directory -Force -Path $fixtureTpl | Out-Null

# Step 2 probe pair has no styled blob — capture must fail closed
$cap = Invoke-Py -PyArgs @($captureCli, $baselineDrt, $styledDrt, '--template-dir', $fixtureTpl) -AllowExitCodes @(2)
$capJson = $cap[1] | ConvertFrom-Json
Assert-True ($capJson.template_valid -eq $false) 'S06 capture rejects unstyled probe pair'
Assert-True ($capJson.diff.changed -eq $false) 'S07 probe pair EffectFiltersBA unchanged (both empty)'

# Injection contract with disposable fake template (not production truth)
$tmpTpl = Join-Path $PSScriptRoot 'fixtures\subtitle-stroke-unblock\.template'
New-Item -ItemType Directory -Force -Path $tmpTpl | Out-Null
$fakeBlob = 'FAKE_STYLE_BLOB_FOR_UNIT_TEST_ONLY'
$b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($fakeBlob))
$b64 | Set-Content -LiteralPath (Join-Path $tmpTpl 'effect-filters-ba.b64') -Encoding ASCII -NoNewline
@{
    schema_version = 1
    route = 'native_drt_effect_filters_ba_template'
    status = 'READY'
    artifact = @{ effect_filters_ba_b64 = 'effect-filters-ba.b64' }
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $tmpTpl 'template-manifest.json') -Encoding UTF8

$outDrt = Join-Path $PSScriptRoot 'fixtures\subtitle-stroke-unblock\injected.drt'
if (Test-Path $outDrt) { Remove-Item -LiteralPath $outDrt -Force }
$inj = Invoke-Py -PyArgs @($injectCli, $baselineDrt, $outDrt, '--template-dir', $tmpTpl)
$injJson = $inj[1] | ConvertFrom-Json
Assert-True (Test-Path $outDrt) 'S08 inject produces output drt'
Assert-True ($injJson.injected_len -gt 0) 'S09 injected blob non-empty'

# Probe orchestrator without paths → owner checkpoint
$orch = & powershell -NoProfile -File $probePs1 2>&1 | ForEach-Object { "$_" }
Assert-True (($orch | Select-Object -Last 1) -eq 'OWNER_MANUAL_GOLD_STANDARD_REQUIRED') 'S10 probe requests gold standard'

# Truth unchanged
Assert-True ($vocab -match 'subtitle\.render\.readability_stroke:[\s\S]{0,120}status:\s*BLOCKED') 'S11 vocab readability_stroke BLOCKED'

# Regressions
& powershell -NoProfile -File (Join-Path $PSScriptRoot 'production-subtitle-readability.ps1') | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'R01 subtitle readability regression'
& powershell -NoProfile -File (Join-Path $PSScriptRoot 'production-audio-loudness-repair.ps1') | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'R02 audio repair regression'
& powershell -NoProfile -File (Join-Path $PSScriptRoot 'production-pacing-reframe-qa.ps1') | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'R03 pacing/black-bar regression'
& powershell -NoProfile -File (Join-Path $PSScriptRoot 'shared-asset-library.ps1') | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'R04 shared asset regression'

Assert-True (Test-Path $closeout) 'Z01 closeout doc exists'

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
