#Requires -Version 5.1
<#
.SYNOPSIS
  N02 repair bundle — shot reuse QA + assembly repair loop (minimal governance).
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
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

Write-Host '=== Production Shot Reuse / Assembly Repair ===' -ForegroundColor Cyan

$reuseProfile = Join-Path $Payload 'video-workflow\runtime\informational-short-shot-reuse-v1-profile.yaml'
$pacingProfile = Join-Path $Payload 'video-workflow\runtime\informational-short-pacing-v1-profile.yaml'
$reuseCli = Join-Path $Payload 'video-workflow\tools\shot-reuse-qa.py'
$loopCli = Join-Path $Payload 'video-workflow\tools\assembly-qa-repair-loop.py'
$fixtureRoot = Join-Path $PSScriptRoot 'fixtures\shot-reuse'
New-Item -ItemType Directory -Force -Path $fixtureRoot | Out-Null

$pingPong = Join-Path $fixtureRoot 'ping-pong-aba.json'
@'
{
  "shots": [
    {"shot_id": "S0", "source_asset": "A", "timeline_duration_sec": 4, "timeline_start_sec": 0},
    {"shot_id": "S1", "source_asset": "B", "timeline_duration_sec": 4, "timeline_start_sec": 4},
    {"shot_id": "S2", "source_asset": "A", "timeline_duration_sec": 4, "timeline_start_sec": 8},
    {"shot_id": "SP", "source_asset": "C", "timeline_duration_sec": 4, "timeline_start_sec": 20}
  ]
}
'@ | Set-Content -LiteralPath $pingPong -Encoding UTF8

$longOffice = Join-Path $fixtureRoot 'same-source-span.json'
@'
{
  "shots": [
    {"shot_id": "O0", "source_asset": "office", "timeline_duration_sec": 4, "timeline_start_sec": 0},
    {"shot_id": "O1", "source_asset": "office", "timeline_duration_sec": 4, "timeline_start_sec": 4},
    {"shot_id": "O2", "source_asset": "office", "timeline_duration_sec": 4, "timeline_start_sec": 8}
  ]
}
'@ | Set-Content -LiteralPath $longOffice -Encoding UTF8

Assert-True (Test-Path $reuseProfile) 'SR01 reuse profile exists'

$pp = Invoke-Py -PyArgs @($reuseCli, '--assembly-json', $pingPong, '--profile', $reuseProfile) -AllowExitCodes @(2)
$ppJson = $pp[1] | ConvertFrom-Json
Assert-True ($ppJson.metrics.ping_pong_aba_count -ge 1) 'SR02 detects A-B-A'
Assert-True ($ppJson.verdict -eq 'STRONG_REPAIR_CANDIDATE') 'SR03 strong repair verdict'

$pacingCli = Join-Path $Payload 'video-workflow\tools\pacing-qa.py'
$pace = Invoke-Py -PyArgs @($pacingCli, '--assembly-json', $longOffice, '--profile', $pacingProfile) -AllowExitCodes @(0, 2)
$paceJson = $pace[1] | ConvertFrom-Json
Assert-True ($paceJson.verdict -eq 'PACING_REPAIR_CANDIDATE') 'SR04 same-source span pacing repair'

$work = Join-Path $fixtureRoot '.work'
New-Item -ItemType Directory -Force -Path $work | Out-Null
$loop = Invoke-Py -PyArgs @($loopCli, '--assembly-json', $pingPong, '--pacing-profile', $pacingProfile, '--reuse-profile', $reuseProfile, '--apply-repair', '--out', (Join-Path $work 'loop.json')) -AllowExitCodes @(0, 2)
$loopJson = $loop[1] | ConvertFrom-Json
Assert-True ($loopJson.repair_applied -eq $true) 'SR05 repair loop applied'
Assert-True ($loopJson.repair.action_count -ge 1) 'SR06 repair actions emitted'

$utf8 = New-Object System.Text.UTF8Encoding $false
$profile = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\runtime\narration-short-v1-audio-mix-profile.yaml'), $utf8)
Assert-True ($profile -match 'encoder_safety_margin_dbtp:\s*0\.5') 'SR07 audio encoder margin'
Assert-True ($profile -match 'repair_target_dbtp:\s*-1\.5') 'SR08 audio repair TP target'
Assert-True ($profile -match 'sample_rate_hz:\s*48000') 'SR09 output 48kHz'

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
