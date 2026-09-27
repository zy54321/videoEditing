#Requires -Version 5.1
<#
.SYNOPSIS
  Release System V2 orchestrator — one commit + annotated tag (local only).
#>
[CmdletBinding()]
param(
    [switch]$DryRun,
    [string]$Version,
    [switch]$Confirm,
    [switch]$NoPause,
    [ValidateSet('Patch', 'Minor', 'Major', 'Custom', 'Cancel')]
    [string]$VersionChoice,
    [string]$CustomVersion,
    [switch]$SimulateGateFail,
    [switch]$SimulateBuildFail,
    [switch]$SimulateTagFail
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$BuildRoot = $PSScriptRoot
$SourceRoot = Split-Path -Parent $BuildRoot
$ProjectRoot = Split-Path -Parent $SourceRoot

. (Join-Path $BuildRoot 'lib\ProductInventory.ps1')
. (Join-Path $BuildRoot 'lib\ReleaseVersion.ps1')
. (Join-Path $BuildRoot 'lib\ReleaseTransaction.ps1')

$txn = $null
$releasePaths = @()

function Write-ReleaseAbort {
    param([string]$Reason)
    Write-Host "RELEASE_ABORTED: $Reason" -ForegroundColor Red
    if ($txn) {
        Abort-ReleaseTransaction -Transaction $txn -ReleasePathsToRemove $releasePaths
    }
    if (-not $NoPause) { Read-Host '按 Enter 键关闭' }
    exit 1
}

function Get-ChangeSummary {
    $lines = git -C $ProjectRoot status --porcelain=v1 2>$null
    if (-not $lines) { return '(no changes)' }
    $shown = @($lines | Select-Object -First 40)
    if ($lines.Count -gt 40) { $shown += "... (+$($lines.Count - 40) more)" }
    return ($shown -join [Environment]::NewLine)
}

# Preflight: root runtime residue
$rootRuntime = Join-Path $ProjectRoot 'runtime'
if (Test-Path -LiteralPath $rootRuntime) {
    Write-ReleaseAbort 'root runtime/ residue present — remove or reconcile before release'
}

$versionFile = Join-Path $SourceRoot 'VERSION'
$currentVersion = (Get-Content -LiteralPath $versionFile -Raw).Trim()
$candidates = Get-ReleaseVersionCandidates -ProjectRoot $ProjectRoot -CurrentVersion $currentVersion
$latestTag = $candidates.LatestRelease

if (-not $Version) {
    if ($VersionChoice) {
        switch ($VersionChoice) {
            'Patch' { $Version = $candidates.Patch }
            'Minor' { $Version = $candidates.Minor }
            'Major' { $Version = $candidates.Major }
            'Custom' { $Version = $CustomVersion }
            'Cancel' { Write-Host 'RELEASE_CANCELLED'; exit 2 }
        }
    } elseif (-not $DryRun) {
        Write-Host '----------------------------------------'
        Write-Host 'Video Editing Workflow Release'
        Write-Host ''
        Write-Host "Current VERSION: $currentVersion"
        Write-Host "Latest Release:  v$latestTag"
        Write-Host ''
        Write-Host 'Select release:'
        Write-Host "[1] Patch  -> $($candidates.Patch)"
        Write-Host "[2] Minor  -> $($candidates.Minor)"
        Write-Host "[3] Major  -> $($candidates.Major)"
        Write-Host '[4] Custom'
        Write-Host '[Q] Cancel'
        Write-Host '----------------------------------------'
        $sel = Read-Host 'Choice'
        switch ($sel) {
            '1' { $Version = $candidates.Patch }
            '2' { $Version = $candidates.Minor }
            '3' { $Version = $candidates.Major }
            '4' {
                $Version = Read-Host 'Enter SemVer (e.g. 0.1.2)'
            }
            'Q' { Write-Host 'RELEASE_CANCELLED'; exit 2 }
            default { Write-ReleaseAbort 'invalid version selection' }
        }
    } else {
        $Version = $candidates.Patch
    }
}

try {
    Assert-ReleaseVersionValid -ProjectRoot $ProjectRoot -Version $Version
} catch {
    Write-ReleaseAbort $_.Exception.Message
}

$txn = New-ReleaseTransaction -ProjectRoot $ProjectRoot
$baseHead = $txn.OriginalHead
$txnId = $txn.Id

try {
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($versionFile, $Version + [Environment]::NewLine, $utf8)

    $inv = Sync-ProductInstallerInventory -SourceRoot $SourceRoot
    $inventoryHash = $inv.Hash

    if ($SimulateGateFail) { throw 'SIMULATED_GATE_FAIL' }
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $SourceRoot 'tests\release-gate.ps1') -Phase PreBuild
    if ($LASTEXITCODE -ne 0) { throw 'RELEASE_GATE_FAIL' }

    if ($SimulateBuildFail) { throw 'SIMULATED_BUILD_FAIL' }
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $BuildRoot 'build-release.ps1') `
        -AllowWorkingTree -Clean -NoPause -SkipInstallerSmoke
    if ($LASTEXITCODE -ne 0) { throw 'BUILD_FAIL' }

    $releaseDir = Join-Path $ProjectRoot "releases\video-editing-workflow-v$Version"
    $releaseZip = Join-Path $ProjectRoot "releases\video-editing-workflow-v$Version.zip"
    $releasePaths = @($releaseDir, $releaseZip, (Join-Path $ProjectRoot "releases\RELEASE-v$Version.md"))

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $SourceRoot 'tests\release-gate.ps1') `
        -Phase PostBuild -ReleaseVersion $Version -ReleaseDir $releaseDir -ZipPath $releaseZip
    if ($LASTEXITCODE -ne 0) { throw 'POST_BUILD_GATE_FAIL' }

    $zipHash = (Get-FileHash -LiteralPath $releaseZip -Algorithm SHA256).Hash.ToLowerInvariant()
    $changeSummary = Get-ChangeSummary

    Write-Host ''
    Write-Host '========================================' -ForegroundColor Cyan
    Write-Host 'READY TO RELEASE'
    Write-Host "Version:        v$Version"
    Write-Host "Base HEAD:      $baseHead"
    Write-Host 'Release Gate:   PASS'
    Write-Host 'Installer:      PASS'
    Write-Host 'ZIP Install:    PASS'
    Write-Host "ZIP:            $releaseZip"
    Write-Host "SHA256:         $zipHash"
    Write-Host "Inventory hash: $inventoryHash"
    Write-Host "Transaction:    $txnId"
    Write-Host ''
    Write-Host 'Changes to commit:'
    Write-Host $changeSummary
    Write-Host ''
    Write-Host "Commit: release: v$Version"
    Write-Host "Tag:    v$Version"
    Write-Host '========================================'

    $doConfirm = $Confirm
    if (-not $PSBoundParameters.ContainsKey('Confirm') -and -not $DryRun) {
        $ans = Read-Host '[Y] Release  [N] Cancel'
        $doConfirm = ($ans -match '^[Yy]$')
    }
    if ($DryRun) {
        Write-Host 'DRY_RUN complete (no commit/tag)' -ForegroundColor Yellow
        throw 'DRY_RUN'
    }
    if (-not $doConfirm) {
        Write-Host 'RELEASE_CANCELLED' -ForegroundColor Yellow
        throw 'OWNER_CANCEL'
    }

    git -C $ProjectRoot add source release.bat 2>$null | Out-Null
    git -C $ProjectRoot add "releases/video-editing-workflow-v$Version" "releases/video-editing-workflow-v$Version.zip" "releases/RELEASE-v$Version.md" 2>$null | Out-Null
    git -C $ProjectRoot add -u source 2>$null | Out-Null

    git -C $ProjectRoot commit -m "release: v$Version"
    if ($LASTEXITCODE -ne 0) { throw 'GIT_COMMIT_FAIL' }
    $txn.ReleaseCommit = (git -C $ProjectRoot rev-parse HEAD).Trim()

    if ($SimulateTagFail) { throw 'SIMULATED_TAG_FAIL' }
    git -C $ProjectRoot tag -a "v$Version" -m "Release v$Version"
    if ($LASTEXITCODE -ne 0) {
        Remove-ReleaseCommitIfAny -Transaction $txn
        throw 'GIT_TAG_FAIL'
    }

    Complete-ReleaseTransaction -Transaction $txn

    Write-Host ''
    Write-Host '========================================' -ForegroundColor Green
    Write-Host 'RELEASE SUCCESS'
    Write-Host "Version: v$Version"
    Write-Host "Commit:  $($txn.ReleaseCommit)"
    Write-Host "Tag:     v$Version"
    Write-Host "ZIP:     $releaseZip"
    Write-Host "SHA256:  $zipHash"
    Write-Host 'REMOTE_PUSH: NOT_PERFORMED'
    Write-Host '========================================' -ForegroundColor Green
    if (-not $NoPause) { Read-Host '按 Enter 键关闭' }
    exit 0
}
catch {
    if ($_.Exception.Message -eq 'DRY_RUN') {
        Abort-ReleaseTransaction -Transaction $txn -ReleasePathsToRemove $releasePaths
        if (-not $NoPause) { Read-Host '按 Enter 键关闭' }
        exit 0
    }
    if ($_.Exception.Message -eq 'OWNER_CANCEL') {
        Write-ReleaseAbort 'cancelled by operator'
    }
    Write-ReleaseAbort $_.Exception.Message
}
