#Requires -Version 5.1
<#
.SYNOPSIS
  Assembly Repair R1 — micro-fragment, logical spans, approved alternates, convergence.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$Payload = Join-Path $Root 'payload'
$RepoRoot = Split-Path -Parent $Root
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

function Write-Fixture {
    param([string]$Path, [string]$Json)
    Set-Content -LiteralPath $Path -Value $Json -Encoding UTF8
}

Write-Host '=== Assembly Repair R1 Tests ===' -ForegroundColor Cyan

$reuseProfile = Join-Path $Payload 'video-workflow\runtime\informational-short-shot-reuse-v1-profile.yaml'
$pacingProfile = Join-Path $Payload 'video-workflow\runtime\informational-short-pacing-v1-profile.yaml'
$reuseCli = Join-Path $Payload 'video-workflow\tools\shot-reuse-qa.py'
$pacingCli = Join-Path $Payload 'video-workflow\tools\pacing-qa.py'
$loopCli = Join-Path $Payload 'video-workflow\tools\assembly-qa-repair-loop.py'
$repairLib = Join-Path $Payload 'video-workflow\tools\lib\assembly_repair.py'
$fixtureRoot = Join-Path $PSScriptRoot 'fixtures\shot-reuse'
$work = Join-Path $fixtureRoot '.work'
New-Item -ItemType Directory -Force -Path $fixtureRoot, $work | Out-Null

# A — micro fragment merge
$microMerge = Join-Path $fixtureRoot 'micro-merge-a.json'
Write-Fixture $microMerge @'
{"fps":24,"shots":[
  {"shot_id":"M0","source_asset":"A","timeline_start_sec":0,"timeline_duration_sec":5,
   "source_range":{"in_sec":0,"out_sec":5},"source_duration_sec":20},
  {"shot_id":"M1","source_asset":"A","timeline_start_sec":5,"timeline_duration_sec":0.042,
   "source_range":{"in_sec":5,"out_sec":5.042}}
]}
'@
$pA = Invoke-Py -PyArgs @($pacingCli, '--assembly-json', $microMerge, '--profile', $pacingProfile) -AllowExitCodes @(2)
$pAJson = $pA[1] | ConvertFrom-Json
Assert-True ($pAJson.metrics.micro_fragment_candidate_count -ge 1) 'A01 micro fragment detected'
$rA = Invoke-Py -PyArgs @($repairLib, '--stdin') -AllowExitCodes @(0) 2>$null
# use loop
$loopA = Invoke-Py -PyArgs @($loopCli, '--assembly-json', $microMerge, '--pacing-profile', $pacingProfile, '--reuse-profile', $reuseProfile, '--apply-repair') -AllowExitCodes @(0, 2)
$loopAJson = $loopA[1] | ConvertFrom-Json
Assert-True ($loopAJson.repair.action_count -ge 1) 'A02 micro merge action'
Assert-True ($loopAJson.assembly_plan.shots.Count -eq 1) 'A03 merged shot count'

# B — adjacent same source no false cooldown
$adjacent = Join-Path $fixtureRoot 'adjacent-same-source.json'
Write-Fixture $adjacent @'
{"fps":24,"shots":[
  {"shot_id":"A0","source_asset":"A","timeline_start_sec":0,"timeline_duration_sec":5},
  {"shot_id":"A1","source_asset":"A","timeline_start_sec":5,"timeline_duration_sec":5}
]}
'@
$uB = Invoke-Py -PyArgs @($reuseCli, '--assembly-json', $adjacent, '--profile', $reuseProfile)
$uBJson = $uB[1] | ConvertFrom-Json
Assert-True ($uBJson.verdict -eq 'PASS') 'B01 adjacent same-source no cooldown false positive'
Assert-True ($uBJson.metrics.logical_source_span_count -eq 1) 'B02 one logical span'

# C — A-B-A still detected
$pingPong = Join-Path $fixtureRoot 'ping-pong-aba.json'
Write-Fixture $pingPong @'
{"fps":24,"shots":[
  {"shot_id":"S0","source_asset":"A","timeline_duration_sec":4,"timeline_start_sec":0},
  {"shot_id":"S1","source_asset":"B","timeline_duration_sec":4,"timeline_start_sec":4},
  {"shot_id":"S2","source_asset":"A","timeline_duration_sec":4,"timeline_start_sec":8}
]}
'@
$pp = Invoke-Py -PyArgs @($reuseCli, '--assembly-json', $pingPong, '--profile', $reuseProfile) -AllowExitCodes @(2)
$ppJson = $pp[1] | ConvertFrom-Json
Assert-True ($ppJson.metrics.ping_pong_aba_count -ge 1) 'C01 A-B-A detected'

# D — non-empty editorial_reason exempt
$exemptEd = Join-Path $fixtureRoot 'editorial-exempt.json'
Write-Fixture $exemptEd @'
{"fps":24,"shots":[
  {"shot_id":"E0","source_asset":"A","timeline_duration_sec":0.042,"timeline_start_sec":0,"editorial_reason":"title flash beat"}
]}
'@
$pD = Invoke-Py -PyArgs @($pacingCli, '--assembly-json', $exemptEd, '--profile', $pacingProfile)
$pDJson = $pD[1] | ConvertFrom-Json
Assert-True ($pDJson.findings[0].verdict -eq 'PACING_EXEMPT') 'D01 editorial_reason exempt pacing'

# E — window counting skips exempt
$windowEx = Join-Path $fixtureRoot 'window-exempt.json'
Write-Fixture $windowEx @'
{"fps":24,"shots":[
  {"shot_id":"W0","source_asset":"A","timeline_start_sec":0,"timeline_duration_sec":4},
  {"shot_id":"W1","source_asset":"B","timeline_start_sec":4,"timeline_duration_sec":4},
  {"shot_id":"WX","source_asset":"A","timeline_start_sec":8,"timeline_duration_sec":4,"reuse_exempt":true},
  {"shot_id":"W2","source_asset":"A","timeline_start_sec":20,"timeline_duration_sec":4}
]}
'@
$uE = Invoke-Py -PyArgs @($reuseCli, '--assembly-json', $windowEx, '--profile', $reuseProfile) -AllowExitCodes @(0, 2)
$uEJson = $uE[1] | ConvertFrom-Json
$winFind = @($uEJson.findings | Where-Object { $_.reason -eq 'same_source_window_exceeded' })
Assert-True ($winFind.Count -eq 0) 'E01 exempt shot excluded from window violations'

# F — no arbitrary alternate (office)
$officeNoAlt = Join-Path $fixtureRoot 'office-no-alternate.json'
Write-Fixture $officeNoAlt @'
{"fps":24,"shots":[
  {"shot_id":"O0","source_asset":"office","timeline_start_sec":0,"timeline_duration_sec":4},
  {"shot_id":"O1","source_asset":"office","timeline_start_sec":4,"timeline_duration_sec":4},
  {"shot_id":"O2","source_asset":"office","timeline_start_sec":8,"timeline_duration_sec":4}
]}
'@
$loopF = Invoke-Py -PyArgs @($loopCli, '--assembly-json', $officeNoAlt, '--pacing-profile', $pacingProfile, '--reuse-profile', $reuseProfile, '--apply-repair') -AllowExitCodes @(0, 2)
$loopFJson = $loopF[1] | ConvertFrom-Json
$altActions = @($loopFJson.repair.actions | Where-Object { $_.repair.action -eq 'clip.alternate_source' })
Assert-True ($altActions.Count -eq 0) 'F01 no unapproved alternate swap'

# G — approved alternate
$approvedAlt = Join-Path $fixtureRoot 'approved-alternate.json'
Write-Fixture $approvedAlt @'
{"fps":24,"shots":[
  {"shot_id":"S0","source_asset":"A","timeline_duration_sec":4,"timeline_start_sec":0},
  {"shot_id":"S1","source_asset":"B","timeline_duration_sec":4,"timeline_start_sec":4},
  {"shot_id":"S2","source_asset":"A","timeline_duration_sec":4,"timeline_start_sec":8,
   "alternate_source_assets":[{"source_asset":"C","source_duration_sec":30,"source_range":{"in_sec":1,"out_sec":5}}]}
]}
'@
$loopG = Invoke-Py -PyArgs @($loopCli, '--assembly-json', $approvedAlt, '--pacing-profile', $pacingProfile, '--reuse-profile', $reuseProfile, '--apply-repair') -AllowExitCodes @(0, 2)
$loopGJson = $loopG[1] | ConvertFrom-Json
Assert-True ($loopGJson.repair.action_count -ge 1) 'G01 approved alternate repair action'
Assert-True ($loopGJson.assembly_plan.shots[2].source_asset -eq 'C') 'G02 swapped to approved C'

# H — insufficient alternate duration
$badAlt = Join-Path $fixtureRoot 'alternate-insufficient.json'
Write-Fixture $badAlt @'
{"fps":24,"shots":[
  {"shot_id":"S0","source_asset":"A","timeline_duration_sec":4,"timeline_start_sec":0},
  {"shot_id":"S1","source_asset":"B","timeline_duration_sec":4,"timeline_start_sec":4},
  {"shot_id":"S2","source_asset":"A","timeline_duration_sec":4,"timeline_start_sec":8,
   "alternate_source_assets":[{"source_asset":"C","source_duration_sec":1}]}
]}
'@
$loopH = Invoke-Py -PyArgs @($loopCli, '--assembly-json', $badAlt, '--pacing-profile', $pacingProfile, '--reuse-profile', $reuseProfile, '--apply-repair') -AllowExitCodes @(0, 2)
$loopHJson = $loopH[1] | ConvertFrom-Json
Assert-True ($loopHJson.repair.blocked.Count -ge 1) 'H01 blocked when alternate duration insufficient'

# I — source range validation (unit)
$valPy = @"
import json, sys
sys.path.insert(0, r'$($Payload -Replace '\\','/')/video-workflow/tools/lib')
from assembly_shot_utils import validate_source_range
shot = {'source_asset': 'x', 'source_duration_sec': 5.0}
ok, err = validate_source_range(shot, 4.0, 6.0)
assert not ok and err == 'source_range_out_of_bounds'
print('ok')
"@
$valPy | python
Assert-True ($LASTEXITCODE -eq 0) 'I01 source range OOB fail closed'

# J — NOT_CONVERGED when after QA still failing
$loopJ = Invoke-Py -PyArgs @($loopCli, '--assembly-json', $pingPong, '--pacing-profile', $pacingProfile, '--reuse-profile', $reuseProfile, '--apply-repair') -AllowExitCodes @(2)
$loopJJson = $loopJ[1] | ConvertFrom-Json
Assert-True ($loopJJson.status -eq 'ASSEMBLY_REPAIR_NOT_CONVERGED') 'J01 NOT_CONVERGED without approved fix'
Assert-True ($loopJJson.ok -eq $false) 'J02 overall ok false'

$pacingYaml = Get-Content -LiteralPath $pacingProfile -Raw
Assert-True ($pacingYaml -match 'max_frames:\s*2') 'Z01 pacing micro_fragment profile'

& powershell -NoProfile -File (Join-Path $PSScriptRoot 'production-pacing-reframe-qa.ps1') | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'Z02 pacing reframe regression'

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
