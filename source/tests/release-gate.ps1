#Requires -Version 5.1
<#
.SYNOPSIS
  Unified Release QA orchestrator (Release System V2).
.PARAMETER Phase
  PreBuild | PostBuild | All
#>
[CmdletBinding()]
param(
    [ValidateSet('PreBuild', 'PostBuild', 'All')]
    [string]$Phase = 'All',
    [string]$ReleaseVersion,
    [string]$ReleaseDir,
    [string]$ZipPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$SourceRoot = Split-Path -Parent $PSScriptRoot
$ProjectRoot = Split-Path -Parent $SourceRoot
$Tests = $PSScriptRoot

function Invoke-TestScript {
    param([string]$Path, [string]$Name)
    if (-not (Test-Path -LiteralPath $Path)) { throw "Missing test script: $Path" }
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Path
    if ($LASTEXITCODE -ne 0) { throw "$Name failed (exit $LASTEXITCODE)" }
}

function Run-PreBuild {
    . (Join-Path $SourceRoot 'build\lib\ProductInventory.ps1')
    $sync = Sync-ProductInstallerInventory -SourceRoot $SourceRoot
    if (-not (Test-ProductInstallerInSync -SourceRoot $SourceRoot)) {
        throw 'Product inventory / installer generated list out of sync'
    }

    Invoke-TestScript (Join-Path $Tests 'pre-release-consistency.ps1') 'pre-release-consistency'
    Invoke-TestScript (Join-Path $Tests 'installer-smoke.ps1') 'installer-smoke'
    Invoke-TestScript (Join-Path $Tests 'shared-asset-library.ps1') 'shared-asset-library'
    Invoke-TestScript (Join-Path $Tests 'production-audio-mix-profile.ps1') 'production-audio-mix-profile'
    Invoke-TestScript (Join-Path $Tests 'production-audio-loudness-repair.ps1') 'production-audio-loudness-repair'
    Invoke-TestScript (Join-Path $Tests 'production-pacing-reframe-qa.ps1') 'production-pacing-reframe-qa'
    Invoke-TestScript (Join-Path $Tests 'production-subtitle-readability.ps1') 'production-subtitle-readability'
    Invoke-TestScript (Join-Path $Tests 'production-subtitle-authority-alignment.ps1') 'production-subtitle-authority-alignment'
    Invoke-TestScript (Join-Path $Tests 'production-subtitle-stroke-unblock.ps1') 'production-subtitle-stroke-unblock'
    Invoke-TestScript (Join-Path $Tests 'production-continuous-execution.ps1') 'production-continuous-execution'
}

function Run-PostBuild {
    param([string]$Ver, [string]$Dir, [string]$Zip)
    if (-not $Dir -or -not (Test-Path -LiteralPath $Dir)) {
        throw 'PostBuild requires -ReleaseDir'
    }
    $releaseSmoke = Join-Path $Tests 'release-smoke.ps1'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $releaseSmoke -ReleasePath $Dir -NoPause
    if ($LASTEXITCODE -ne 0) { throw 'release-smoke failed' }
    if ($Zip) {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $releaseSmoke -ReleasePath $Dir -ZipPath $Zip -NoPause
        if ($LASTEXITCODE -ne 0) { throw 'release-smoke ZIP failed' }
    }
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Tests 'zip-independent-install.ps1') `
        -ZipPath $Zip -ReleaseVersion $Ver
    if ($LASTEXITCODE -ne 0) { throw 'zip-independent-install failed' }
}

Write-Host "=== Release Gate ($Phase) ===" -ForegroundColor Cyan
if ($Phase -eq 'PreBuild' -or $Phase -eq 'All') { Run-PreBuild }
if ($Phase -eq 'PostBuild' -or $Phase -eq 'All') {
    if (-not $ReleaseVersion) {
        $ReleaseVersion = (Get-Content (Join-Path $SourceRoot 'VERSION') -Raw).Trim()
    }
    if (-not $ZipPath -and $ReleaseVersion) {
        $ZipPath = Join-Path $ProjectRoot "releases\video-editing-workflow-v$ReleaseVersion.zip"
    }
    Run-PostBuild -Ver $ReleaseVersion -Dir $ReleaseDir -Zip $ZipPath
}
Write-Host 'RELEASE_GATE = PASS' -ForegroundColor Green
exit 0
