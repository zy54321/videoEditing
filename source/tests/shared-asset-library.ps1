#Requires -Version 5.1
<#
.SYNOPSIS
  Step 3A — Shared Asset Library V1 foundation tests.
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

Write-Host '=== Shared Asset Library Tests ===' -ForegroundColor Cyan
Write-Host ''

$utf8 = New-Object System.Text.UTF8Encoding $false
$configPath = Join-Path $Payload 'video-workflow\runtime\shared-asset-library-config.yaml'
$schemaPath = Join-Path $Payload 'video-workflow\templates\shared-asset-catalog.schema.yaml'
$refPath = Join-Path $Payload 'video-workflow\templates\shared-asset-music-metadata-reference.md'
$l1 = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\capabilities\davinci-resolve.md'), $utf8)
$vocab = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\capabilities\logical-capability-vocabulary.yaml'), $utf8)
$l3 = [System.IO.File]::ReadAllText((Join-Path $Payload '.cursor\skills\video-production\SKILL.md'), $utf8)
$briefRef = [System.IO.File]::ReadAllText((Join-Path $Payload 'video-workflow\templates\production-brief-reference.md'), $utf8)
$installer = [System.IO.File]::ReadAllText((Join-Path $Root 'installer\init-video-workflow.ps1'), $utf8)
$closeout = Join-Path $RepoRoot 'validation\production-repair-step3a-shared-asset-library-closeout.md'

$fixtureRoot = Join-Path $PSScriptRoot 'fixtures\shared-asset-library'
$catalogPath = Join-Path $fixtureRoot 'catalog\music.yaml'
$validateCli = Join-Path $Payload 'video-workflow\tools\shared-asset-catalog-validate.py'
$selectCli = Join-Path $Payload 'video-workflow\tools\shared-asset-music-select.py'
$resolveCli = Join-Path $Payload 'video-workflow\tools\shared-asset-resolve.py'

# Contract files
Assert-True (Test-Path $configPath) 'S01 runtime config exists'
$config = [System.IO.File]::ReadAllText($configPath, $utf8)
Assert-True ($config -match 'shared_asset_root:.*Astra/assets') 'S02 canonical Astra assets root'
Assert-True ($config -match 'music: catalog/music.yaml') 'S03 music catalog path'
Assert-True (Test-Path $schemaPath) 'S04 schema exists'
Assert-True (Test-Path $refPath) 'S05 metadata reference exists'
$ref = [System.IO.File]::ReadAllText($refPath, $utf8)
Assert-True ($ref -match 'MUSIC_ASSET_NOT_AVAILABLE') 'S05b missing asset code documented'

# A — valid READY music searchable
$sel = Invoke-Py -PyArgs @($selectCli, '--catalog', $catalogPath, '--root', $fixtureRoot, '--mood', 'calm', '--energy', 'low')
$selJson = $sel[1] | ConvertFrom-Json
Assert-True ($sel[0] -eq 0) 'A01 calm filter exit 0'
Assert-True ($selJson.ok -eq $true) 'A02 calm filter ok'
Assert-True ($selJson.candidates[0].asset_id -eq 'music-calm-ready-01') 'A03 calm candidate'

# B — missing license cannot be READY (catalog validation)
$val = Invoke-Py -PyArgs @($validateCli, '--catalog', $catalogPath, '--root', $fixtureRoot) -AllowExitCodes @(0, 1, 2)
$valJson = $val[1] | ConvertFrom-Json
Assert-True ($valJson.valid -eq $false) 'B01 catalog with gaps invalid'
$noLic = $valJson.assets | Where-Object { $_.asset_id -eq 'music-no-license-01' }
Assert-True ($noLic.valid -eq $false) 'B02 missing license not valid'

# C — missing file fail closed
$missing = $valJson.assets | Where-Object { $_.asset_id -eq 'music-missing-file-01' }
Assert-True ($missing.valid -eq $false) 'C01 READY missing file fails validate'
Assert-True (($missing.errors | Out-String) -match 'file:missing') 'C02 file missing error'

# D — mood / energy filtering
$tense = Invoke-Py -PyArgs @($selectCli, '--catalog', $catalogPath, '--root', $fixtureRoot, '--mood', 'tense', '--energy', 'high')
$tenseJson = $tense[1] | ConvertFrom-Json
Assert-True ($tenseJson.candidates[0].asset_id -eq 'music-tense-high-01') 'D01 tense/high match'
$none = Invoke-Py -PyArgs @($selectCli, '--catalog', $catalogPath, '--root', $fixtureRoot, '--mood', 'warm', '--energy', 'low')
Assert-True ($none[0] -eq 2) 'D02 no match returns exit 2'
$noneJson = $none[1] | ConvertFrom-Json
Assert-True ($noneJson.code -eq 'MUSIC_ASSET_NOT_AVAILABLE') 'D03 MUSIC_ASSET_NOT_AVAILABLE'

# E — asset_id resolution
$res = Invoke-Py -PyArgs @($resolveCli, 'music-calm-ready-01', '--catalog', $catalogPath, '--root', $fixtureRoot)
$resJson = $res[1] | ConvertFrom-Json
$expected = (Join-Path $fixtureRoot 'music\calm-ready.mp3')
Assert-True ($resJson.ok -eq $true) 'E01 resolve ok'
Assert-True ($resJson.path -eq $expected) 'E02 resolved absolute path'

# F — path traversal blocked
$badCatalog = Join-Path $fixtureRoot 'catalog\bad-traversal.yaml'
@'
schema_version: 1
catalog_id: bad
assets:
  - asset_id: bad-01
    type: music
    path: ../outside.mp3
    title: Bad
    duration: 10
    mood: calm
    energy: low
    bpm: null
    loopable: true
    license:
      type: royalty_free
      source: x
      commercial_use: true
      attribution_required: false
    source_url: ""
    status: READY
'@ | Set-Content -Path $badCatalog -Encoding UTF8
$badVal = Invoke-Py -PyArgs @($validateCli, '--catalog', $badCatalog, '--root', $fixtureRoot) -AllowExitCodes @(0, 1, 2)
$badJson = $badVal[1] | ConvertFrom-Json
Assert-True (($badJson.assets[0].errors | Out-String) -match 'path:unsafe') 'F01 traversal rejected'
Remove-Item $badCatalog -Force -ErrorAction SilentlyContinue

# G — production / release isolation
Assert-True ($installer -notmatch '03_Media\\02_Video\\Davinci\\Astra\\assets') 'G01 installer does not bundle shared assets'
Assert-True ($l3 -match 'MUSIC_ASSET_NOT_AVAILABLE') 'G02 L3 missing music code'
Assert-True ($l3 -match 'audio\.music\.place') 'G03 L3 defers placement to existing capability'
Assert-True ($briefRef -match 'asset_id') 'G04 brief supports asset_id'
Assert-True ($l1 -match 'music\.library\.select[\s\S]{0,120}VERIFIED') 'G05 L1 library select VERIFIED'
Assert-True (Test-Path $closeout) 'G06 closeout doc exists'

# Regression — subtitle step 2 unchanged
$readTest = Join-Path $PSScriptRoot 'production-subtitle-readability.ps1'
if (Test-Path $readTest) {
    & powershell -NoProfile -File $readTest | Out-Null
    Assert-True ($LASTEXITCODE -eq 0) 'R01 subtitle readability regression'
}

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
