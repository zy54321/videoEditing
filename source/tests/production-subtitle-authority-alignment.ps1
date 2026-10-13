#Requires -Version 5.1
<#
.SYNOPSIS
  R1 — Frozen Script authority, monotonic alignment, canonical subtitle cues.
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

Write-Host '=== R1 Subtitle Authority & Alignment Tests ===' -ForegroundColor Cyan

$pyTests = Join-Path $PSScriptRoot 'r1_subtitle_authority_tests.py'
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { throw 'python not found' }

& python $pyTests
if ($LASTEXITCODE -ne 0) { throw "R1 python tests failed ($LASTEXITCODE)" }
Assert-True $true 'R1-A..H python unit/integration suite'

$tools = Join-Path $Root 'payload\video-workflow\tools'
$cli = Join-Path $tools 'build-canonical-subtitle-cues.py'
$fixtureScript = Join-Path $PSScriptRoot 'fixtures\r1-subtitle-authority\frozen-asr-homophone.txt'
$fixtureAsr = Join-Path $PSScriptRoot 'fixtures\r1-subtitle-authority\asr-homophone.json'
$out = Join-Path $PSScriptRoot '.tmp-r1\canonical-cues.json'
if (Test-Path (Split-Path $out)) { Remove-Item -LiteralPath (Split-Path $out) -Recurse -Force -ErrorAction SilentlyContinue }
New-Item -ItemType Directory -Path (Split-Path $out) -Force | Out-Null

& python $cli --script $fixtureScript --asr $fixtureAsr --out $out
Assert-True ($LASTEXITCODE -eq 0) 'R1 CLI build-canonical-subtitle-cues exit 0'
$doc = Get-Content $out -Raw -Encoding UTF8 | ConvertFrom-Json
Assert-True ($doc.meta.status -eq 'OK') 'R1 CLI meta.status OK'
Assert-True ($doc.cues.Count -ge 1) 'R1 CLI produced cues'
$expectedNorm = (Get-Content -LiteralPath $fixtureScript -Raw -Encoding UTF8).Trim().Replace("`r", '').Replace("`n", '')
$flat = -join ($doc.cues | ForEach-Object { $_.text.Replace("`n", '') })
Assert-True ($flat -eq $expectedNorm) 'R1 CLI frozen text 100% preserved'
Assert-True ($flat -notmatch '实践') 'R1 CLI ASR homophone not in final cues'

$schema = Join-Path $Root 'payload\video-workflow\templates\canonical-subtitle-cue-list.schema.json'
Assert-True (Test-Path -LiteralPath $schema) 'R1 canonical cue schema present'
$vocab = Get-Content (Join-Path $Root 'payload\video-workflow\capabilities\logical-capability-vocabulary.yaml') -Raw -Encoding UTF8
Assert-True ($vocab -match 'subtitle\.authority\.frozen_script') 'R1 vocabulary entry frozen_script'
Assert-True ($vocab -match 'subtitle\.align\.monotonic') 'R1 vocabulary entry monotonic align'
Assert-True ($vocab -match 'subtitle\.cue\.canonical') 'R1 vocabulary entry canonical cue'

$l3 = Get-Content (Join-Path $Root 'payload\.cursor\skills\video-production\SKILL.md') -Raw -Encoding UTF8
Assert-True ($l3 -match 'build-canonical-subtitle-cues') 'R1 L3 references canonical cue pipeline'

Remove-Item -LiteralPath (Split-Path $out) -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
exit 0
