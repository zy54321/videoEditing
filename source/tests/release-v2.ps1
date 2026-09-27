#Requires -Version 5.1
<#
.SYNOPSIS
  Release System V2 — version, authority, transaction, and regression tests.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$SourceRoot = Split-Path -Parent $PSScriptRoot
$ProjectRoot = Split-Path -Parent $SourceRoot
$BuildLib = Join-Path $SourceRoot 'build\lib'
$Pass = 0
$Fail = 0

function Assert-True {
    param([bool]$Condition, [string]$Name)
    if ($Condition) { Write-Host "[PASS] $Name" -ForegroundColor Green; $script:Pass++ }
    else { Write-Host "[FAIL] $Name" -ForegroundColor Red; $script:Fail++ }
}

. (Join-Path $BuildLib 'ReleaseVersion.ps1')
. (Join-Path $BuildLib 'ProductInventory.ps1')
. (Join-Path $BuildLib 'ReleaseTransaction.ps1')

Write-Host '=== Release V2 Tests ===' -ForegroundColor Cyan

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'release-encoding-gate.ps1') -SkipExecutionSmoke
Assert-True ($LASTEXITCODE -eq 0) 'V00 release-encoding-gate (PS 5.1 parse)'

# 1-7 version parsing / candidates
$cur = (Get-Content (Join-Path $SourceRoot 'VERSION') -Raw).Trim()
try { Parse-SemVer $cur | Out-Null; Assert-True $true 'V01 VERSION parses' } catch { Assert-True $false 'V01 VERSION parses' }

# Case A: X.Y.Z-dev formalizes to X.Y.Z when tag vX.Y.Z absent and Z-line >= latest release
$c = Get-ReleaseVersionCandidates -ProjectRoot $ProjectRoot -CurrentVersion '0.1.3-dev'
Assert-True ($c.Patch -eq '0.1.3') 'V02 Case A: 0.1.3-dev formalizes to patch 0.1.3 (latest v0.1.2)'
Assert-True ((Compare-SemVer $c.Patch $c.LatestRelease) -gt 0) 'V03 patch candidate > latest tag'

# Non-dev current below latest: patch candidate = next after latest tag (not re-release)
$c2 = Get-ReleaseVersionCandidates -ProjectRoot $ProjectRoot -CurrentVersion '0.1.1'
Assert-True ($c2.Patch -eq '0.1.3') 'V04 patch bump from 0.1.1 when latest is v0.1.2'
Assert-True ($c2.Minor -eq '0.2.0') 'V05 minor candidate'
Assert-True ($c2.Major -eq '1.0.0') 'V06 major candidate'

try { Assert-ReleaseVersionValid -ProjectRoot $ProjectRoot -Version 'not-a-version'; Assert-True $false 'V07 invalid semver rejected' } catch { Assert-True $true 'V07 invalid semver rejected' }

try { Assert-ReleaseVersionValid -ProjectRoot $ProjectRoot -Version '0.1.1'; Assert-True $false 'V08 duplicate/low version rejected' } catch { Assert-True $true 'V08 duplicate/low version rejected' }

# Case B: existing release tag is immutable (fail closed)
try { Assert-ReleaseVersionValid -ProjectRoot $ProjectRoot -Version '0.1.2'; Assert-True $false 'V08b Case B: tag v0.1.2 blocks re-release 0.1.2' } catch { Assert-True $true 'V08b Case B: tag v0.1.2 blocks re-release 0.1.2' }

# Case C: next dev line formalizes to its normalized version
$c4 = Get-ReleaseVersionCandidates -ProjectRoot $ProjectRoot -CurrentVersion '0.1.4-dev'
Assert-True ($c4.Patch -eq '0.1.4') 'V08c Case C: 0.1.4-dev formalizes to 0.1.4'

# Case D: dev formalize must not skip to next patch line
Assert-True ($c.Patch -ne '0.1.4') 'V08d Case D: 0.1.3-dev patch candidate is not 0.1.4'

# Dev matching an existing tag cannot re-formalize same version (bump instead)
$cStaleDev = Get-ReleaseVersionCandidates -ProjectRoot $ProjectRoot -CurrentVersion '0.1.2-dev'
Assert-True ($cStaleDev.Patch -eq '0.1.3') 'V08e dev 0.1.2-dev does not re-release tagged 0.1.2'

# Repo VERSION authority matches formalize semantics
$cRepo = Get-ReleaseVersionCandidates -ProjectRoot $ProjectRoot -CurrentVersion $cur
Assert-True ($cur -eq '0.1.3-dev') 'V08f repo VERSION is 0.1.3-dev'
Assert-True ($cRepo.Patch -eq '0.1.3') 'V08g repo VERSION formalizes to 0.1.3 for release'

# 9 product authority
$sync = Sync-ProductInstallerInventory -SourceRoot $SourceRoot
Assert-True ($sync.Count -gt 50) 'V09 product inventory generated'
Assert-True (Test-ProductInstallerInSync -SourceRoot $SourceRoot) 'V10 installer inventory in sync'
$inv = Get-ProductFileInventory
Assert-True ($inv -contains 'video-workflow\tools\native-drt-subtitle-stroke-inject.py') 'V11 stroke inject in product'
Assert-True (-not ($inv | Where-Object { $_ -match '__pycache__|\.pyc$' })) 'V12 no pycache in product'
Assert-True (-not ($inv | Where-Object { $_ -match '(^|\\)video-workflow\\\.qa\\' })) 'V12b no video-workflow/.qa in product'

# disposable git transaction (legacy smoke — full matrix in release-v2-transaction-fixtures.ps1)
function Test-TxnRollback {
    param([string]$Name, [scriptblock]$Mutate)
    $tmp = Join-Path $PSScriptRoot "fixtures\release-v2-txn-$([guid]::NewGuid().ToString('n'))"
    New-Item -ItemType Directory -Path $tmp -Force | Out-Null
    git -C $tmp init -q
    git -C $tmp config user.email 'test@test.local'
    git -C $tmp config user.name 'Test'
    'base' | Out-File (Join-Path $tmp 'tracked.txt') -Encoding utf8
    'untracked' | Out-File (Join-Path $tmp 'local-only.txt') -Encoding utf8
    git -C $tmp add tracked.txt
    git -C $tmp commit -m 'init' -q
    'edit' | Out-File (Join-Path $tmp 'tracked.txt') -Encoding utf8 -NoNewline
    git -C $tmp add tracked.txt
    & $Mutate
    $beforeHead = (git -C $tmp rev-parse HEAD).Trim()
    $beforePorcelain = Get-GitPorcelainLines -ProjectRoot $tmp
    $beforeTracked = Get-Content (Join-Path $tmp 'tracked.txt') -Raw
    $beforeUntracked = if (Test-Path (Join-Path $tmp 'local-only.txt')) { Get-Content (Join-Path $tmp 'local-only.txt') -Raw } else { $null }
    $txn = New-ReleaseTransaction -ProjectRoot $tmp
    'VERSION-BUMP' | Out-File (Join-Path $tmp 'tracked.txt') -Encoding utf8 -NoNewline
    Abort-ReleaseTransaction -Transaction $txn
    $afterHead = (git -C $tmp rev-parse HEAD).Trim()
    $afterPorcelain = Get-GitPorcelainLines -ProjectRoot $tmp
    $afterTracked = Get-Content (Join-Path $tmp 'tracked.txt') -Raw
    $afterUntracked = if (Test-Path (Join-Path $tmp 'local-only.txt')) { Get-Content (Join-Path $tmp 'local-only.txt') -Raw } else { $null }
    $ok = ($beforeHead -eq $afterHead) -and (Test-GitPorcelainEqual -Expected $beforePorcelain -Actual $afterPorcelain) -and ($beforeTracked -eq $afterTracked) -and ($beforeUntracked -eq $afterUntracked) -and (Test-Path -LiteralPath (Join-Path $tmp 'local-only.txt'))
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
    Assert-True $ok $Name
}

Test-TxnRollback -Name 'V13 rollback preserves tracked+staged+untracked' -Mutate { }

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'release-v2-transaction-fixtures.ps1')
Assert-True ($LASTEXITCODE -eq 0) 'V13b transaction fixture suite'

# immutable tag on real repo (read-only)
$tag01 = git -C $ProjectRoot rev-parse -q --verify refs/tags/v0.1.1 2>$null
Assert-True ($null -ne $tag01 -and $tag01 -ne '') 'V14 v0.1.1 tag exists (immutable guard target)'

# build script guards
$build = Get-Content (Join-Path $SourceRoot 'build\build-release.ps1') -Raw
Assert-True ($build -match 'RELEASE_VERSION_IMMUTABLE') 'V15 build immutable tag guard'
Assert-True ($build -match 'AllowWorkingTree') 'V16 build AllowWorkingTree'

# release orchestrator exists
Assert-True (Test-Path (Join-Path $ProjectRoot 'release.bat')) 'V17 release.bat'
Assert-True (Test-Path (Join-Path $SourceRoot 'build\release.ps1')) 'V18 release.ps1'
Assert-True (Test-Path (Join-Path $SourceRoot 'tests\release-gate.ps1')) 'V19 release-gate.ps1'

# no root runtime residue
Assert-True (-not (Test-Path (Join-Path $ProjectRoot 'runtime'))) 'V20 no root runtime residue'

# regressions (subset — full gate in CI)
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $SourceRoot 'tests\release-gate.ps1') -Phase PreBuild
Assert-True ($LASTEXITCODE -eq 0) 'V21 release-gate PreBuild'

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
exit 0
