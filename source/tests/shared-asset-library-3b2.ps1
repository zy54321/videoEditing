#Requires -Version 5.1
<#
.SYNOPSIS
  Step 3B-2 — Real Firefly music registration, catalog READY, library integration tests.
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
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { throw 'python not found' }
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $lines = & python @PyArgs 2>&1 | ForEach-Object { if ($_ -is [System.Management.Automation.ErrorRecord]) { $_.ToString() } else { "$_" } }
    $ErrorActionPreference = $prevEap
    $out = ($lines | Out-String)
    $code = $LASTEXITCODE
    if ($AllowExitCodes -notcontains $code) {
        throw "python failed ($code): $out"
    }
    $json = $out.Trim()
    $start = $json.IndexOf('{')
    $end = $json.LastIndexOf('}')
    if ($start -ge 0 -and $end -gt $start) {
        $json = $json.Substring($start, $end - $start + 1)
    }
    return ,@($code, $json)
}

Write-Host '=== Shared Asset Library 3B-2 Tests ===' -ForegroundColor Cyan
Write-Host ''

$utf8 = New-Object System.Text.UTF8Encoding $false
$configPath = Join-Path $Payload 'video-workflow\runtime\shared-asset-library-config.yaml'
$config = [System.IO.File]::ReadAllText($configPath, $utf8)
$astraRoot = 'E:\03_Media\02_Video\Davinci\Astra\assets'
$liveCatalog = Join-Path $astraRoot 'catalog\music.yaml'
$musicDir = Join-Path $astraRoot 'music'
$validateCli = Join-Path $Payload 'video-workflow\tools\shared-asset-catalog-validate.py'
$selectCli = Join-Path $Payload 'video-workflow\tools\shared-asset-music-select.py'
$resolveCli = Join-Path $Payload 'video-workflow\tools\shared-asset-resolve.py'
$l3 = [System.IO.File]::ReadAllText((Join-Path $Payload '.cursor\skills\video-production\SKILL.md'), $utf8)
$installer = [System.IO.File]::ReadAllText((Join-Path $Root 'installer\init-video-workflow.ps1'), $utf8)

$expectedFiles = @(
    'firefly_quiet_circuit_001.wav',
    'firefly_forward_current_001.wav',
    'firefly_glass_horizon_001.wav',
    'firefly_soft_pulse_001.wav'
)
$expectedIds = @(
    'music_firefly_quiet_circuit_001',
    'music_firefly_forward_current_001',
    'music_firefly_glass_horizon_001',
    'music_firefly_soft_pulse_001'
)

Assert-True (Test-Path $liveCatalog) 'T01 live catalog exists'
foreach ($f in $expectedFiles) {
    Assert-True (Test-Path (Join-Path $musicDir $f)) "T02 file exists: $f"
}

# 1-4 WAV validation + READY catalog
$val = Invoke-Py -PyArgs @($validateCli, '--catalog', $liveCatalog, '--root', $astraRoot)
$valJson = $val[1] | ConvertFrom-Json
Assert-True ($valJson.valid -eq $true) 'T03 catalog valid with 4 READY assets'
$readyCount = @($valJson.assets | Where-Object { $_.valid -eq $true }).Count
Assert-True ($readyCount -eq 4) 'T04 four READY assets'

# 3 asset_id uniqueness
$ids = @($valJson.assets | ForEach-Object { $_.asset_id })
Assert-True (($ids | Select-Object -Unique).Count -eq $ids.Count) 'T05 asset_id unique'

# 5 Adobe license metadata (parse catalog text)
$catalogText = [System.IO.File]::ReadAllText($liveCatalog, $utf8)
Assert-True ($catalogText -match 'Adobe Firefly Generate Music') 'T06 Adobe Firefly license source'
Assert-True ($catalogText -match 'evidence_url: https://www.adobe.com/products/firefly/features/ai-music-generator.html') 'T07 license evidence URL'
Assert-True ($catalogText -match 'royalty_free: true') 'T08 royalty_free recorded'

# 6 mood/style/energy filtering
$filter = Invoke-Py -PyArgs @(
    $selectCli, '--catalog', $liveCatalog, '--root', $astraRoot,
    '--moods', 'calm', '--styles', 'technology', '--energy', 'low'
)
$filterJson = $filter[1] | ConvertFrom-Json
Assert-True ($filterJson.ok -eq $true) 'T09 calm/technology/low filter ok'
Assert-True ($filterJson.candidates.Count -ge 2) 'T10 multiple calm technology matches'

# 7 N02-like ranking
$n02 = Invoke-Py -PyArgs @(
    $selectCli, '--catalog', $liveCatalog, '--root', $astraRoot,
    '--moods', 'calm,thoughtful', '--styles', 'technology,documentary',
    '--usage', 'narration background', '--energy', 'low'
)
$n02Json = $n02[1] | ConvertFrom-Json
Assert-True ($n02Json.ok -eq $true) 'T11 N02-like query ok'
$ranked = @($n02Json.candidates | ForEach-Object { $_.asset_id })
Assert-True ($ranked[0] -eq 'music_firefly_glass_horizon_001') 'T12 Glass Horizon ranks first'
Assert-True ($ranked -contains 'music_firefly_quiet_circuit_001') 'T13 Quiet Circuit in ranking'
Assert-True ($ranked -contains 'music_firefly_soft_pulse_001') 'T14 Soft Pulse in ranking'
Assert-True ($ranked[0] -ne 'music_firefly_forward_current_001') 'T15 Forward Current not first'

# 8 asset_id resolve
foreach ($aid in $expectedIds) {
    $res = Invoke-Py -PyArgs @($resolveCli, $aid, '--catalog', $liveCatalog, '--root', $astraRoot)
    $resJson = $res[1] | ConvertFrom-Json
    Assert-True ($resJson.ok -eq $true) "T16 resolve ok: $aid"
    Assert-True (Test-Path $resJson.path) "T17 resolved path exists: $aid"
}

# 9 path traversal (reuse fixture pattern)
$badCatalog = Join-Path $PSScriptRoot 'fixtures\shared-asset-library\catalog\bad-traversal-live.yaml'
@'
schema_version: 1
catalog_id: bad
assets:
  - asset_id: bad-01
    type: music
    path: ../outside.wav
    title: Bad
    duration: 10
    mood: calm
    energy: low
    loopable: true
    license:
      type: test
      source: x
      commercial_use: true
      attribution_required: false
      evidence_url: https://example.com/x
    status: READY
'@ | Set-Content -Path $badCatalog -Encoding UTF8
$badVal = Invoke-Py -PyArgs @($validateCli, '--catalog', $badCatalog, '--root', $astraRoot) -AllowExitCodes @(0, 1, 2)
$badJson = $badVal[1] | ConvertFrom-Json
Assert-True (($badJson.assets[0].errors | Out-String) -match 'path:unsafe') 'T18 path traversal blocked'
Remove-Item $badCatalog -Force -ErrorAction SilentlyContinue

# 10 MUSIC_ASSET_NOT_AVAILABLE
$none = Invoke-Py -PyArgs @(
    $selectCli, '--catalog', $liveCatalog, '--root', $astraRoot,
    '--moods', 'orchestral', '--styles', 'classical', '--energy', 'high'
)
Assert-True ($none[0] -eq 2) 'T19 impossible combo exit 2'
$noneJson = $none[1] | ConvertFrom-Json
Assert-True ($noneJson.code -eq 'MUSIC_ASSET_NOT_AVAILABLE') 'T20 MUSIC_ASSET_NOT_AVAILABLE'

# 11 L3 integration contract
Assert-True ($l3 -match 'music\.library\.search') 'T21 L3 music.library.search'
Assert-True ($l3 -match 'music\.library\.select') 'T22 L3 music.library.select'
Assert-True ($l3 -match 'music\.library\.resolve') 'T23 L3 music.library.resolve'
Assert-True ($l3 -match 'assets\.music\.asset_id') 'T24 L3 asset_id only in logical layer'
Assert-True ($l3 -match 'audio\.music\.place') 'T25 L3 handoff to audio.music.place'

# 12 release isolation
Assert-True ($installer -notmatch '03_Media\\02_Video\\Davinci\\Astra\\assets') 'T26 release does not bundle shared assets'

# 13 production directory isolation
Assert-True (-not (Test-Path (Join-Path $Payload 'video-workflow\production\brief.yaml'))) 'T27 no production brief in dev payload'

# Regression — Step 3A tests still pass
& powershell -NoProfile -File (Join-Path $PSScriptRoot 'shared-asset-library.ps1') | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'T28 Step 3A regression'

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
