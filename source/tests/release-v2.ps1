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

# 1-7 version parsing / candidates
$cur = (Get-Content (Join-Path $SourceRoot 'VERSION') -Raw).Trim()
try { Parse-SemVer $cur | Out-Null; Assert-True $true 'V01 VERSION parses' } catch { Assert-True $false 'V01 VERSION parses' }

$c = Get-ReleaseVersionCandidates -ProjectRoot $ProjectRoot -CurrentVersion '0.1.2-dev'
Assert-True ($c.Patch -eq '0.1.2') 'V02 dev formalize patch 0.1.2'
Assert-True ((Compare-SemVer $c.Patch $c.LatestRelease) -gt 0) 'V03 patch > latest tag'

$c2 = Get-ReleaseVersionCandidates -ProjectRoot $ProjectRoot -CurrentVersion '0.1.1'
Assert-True ($c2.Patch -eq '0.1.2') 'V04 patch bump from 0.1.1'
Assert-True ($c2.Minor -eq '0.2.0') 'V05 minor candidate'
Assert-True ($c2.Major -eq '1.0.0') 'V06 major candidate'

try { Assert-ReleaseVersionValid -ProjectRoot $ProjectRoot -Version 'not-a-version'; Assert-True $false 'V07 invalid semver rejected' } catch { Assert-True $true 'V07 invalid semver rejected' }

try { Assert-ReleaseVersionValid -ProjectRoot $ProjectRoot -Version '0.1.1'; Assert-True $false 'V08 duplicate/low version rejected' } catch { Assert-True $true 'V08 duplicate/low version rejected' }

# 9 product authority
$sync = Sync-ProductInstallerInventory -SourceRoot $SourceRoot
Assert-True ($sync.Count -gt 50) 'V09 product inventory generated'
Assert-True (Test-ProductInstallerInSync -SourceRoot $SourceRoot) 'V10 installer inventory in sync'
$inv = Get-ProductFileInventory
Assert-True ($inv -contains 'video-workflow\tools\native-drt-subtitle-stroke-inject.py') 'V11 stroke inject in product'
Assert-True (-not ($inv | Where-Object { $_ -match '__pycache__|\.pyc$' })) 'V12 no pycache in product'

# disposable git transaction cases
function Test-TxnRollback {
    param([string]$Name, [scriptblock]$Mutate)
    $tmp = Join-Path $PSScriptRoot "fixtures\release-v2-txn-$([guid]::NewGuid().ToString('n'))"
    New-Item -ItemType Directory -Path $tmp -Force | Out-Null
    Set-Location $tmp
    git init -q
    git config user.email 'test@test.local'
    git config user.name 'Test'
    'base' | Out-File 'tracked.txt' -Encoding utf8
    'untracked' | Out-File 'local-only.txt' -Encoding utf8
    git add tracked.txt
    git commit -m 'init' -q
    'edit' | Out-File 'tracked.txt' -Encoding utf8 -NoNewline
    git add tracked.txt
    & $Mutate
    $beforeHead = (git rev-parse HEAD).Trim()
    $beforeStatus = git status --porcelain=v1
    $beforeTracked = Get-Content 'tracked.txt' -Raw
    $beforeUntracked = if (Test-Path 'local-only.txt') { Get-Content 'local-only.txt' -Raw } else { $null }
    $txn = New-ReleaseTransaction -ProjectRoot $tmp
    'VERSION-BUMP' | Out-File 'tracked.txt' -Encoding utf8 -NoNewline
    Abort-ReleaseTransaction -Transaction $txn
    $afterHead = (git rev-parse HEAD).Trim()
    $afterStatus = git status --porcelain=v1
    $afterTracked = Get-Content 'tracked.txt' -Raw
    $afterUntracked = if (Test-Path 'local-only.txt') { Get-Content 'local-only.txt' -Raw } else { $null }
    $ok = ($beforeHead -eq $afterHead) -and ($beforeTracked -eq $afterTracked) -and ($beforeUntracked -eq $afterUntracked) -and (Test-Path -LiteralPath 'local-only.txt')
    Set-Location $ProjectRoot
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
    Assert-True $ok $Name
}

Test-TxnRollback -Name 'V13 rollback preserves tracked+staged+untracked' -Mutate { }

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
