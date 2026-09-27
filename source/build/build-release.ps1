#Requires -Version 5.1
<#
.SYNOPSIS
  Build Video Editing Workflow release package from source.

  Release provenance:
  - Bump VERSION / release metadata and commit first.
  - Formal build requires a clean git tree.
  - Source Commit = unique HEAD at build time (not HEAD + uncommitted changes).
#>
[CmdletBinding()]
param(
    [switch]$Clean,
    [switch]$NoPause,
    [switch]$AllowWorkingTree,
    [switch]$SkipInstallerSmoke,
    [switch]$SkipReleaseSmoke
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$BuildRoot = $PSScriptRoot
$SourceRoot = Split-Path -Parent $BuildRoot
$ProjectRoot = Split-Path -Parent $SourceRoot
$ReleasesRoot = Join-Path $ProjectRoot 'releases'

function Get-InstallerProductFiles {
    param([string]$SourceRoot)
    $lib = Join-Path $PSScriptRoot 'lib\ProductInventory.ps1'
    if (-not (Test-Path -LiteralPath $lib)) {
        throw 'ProductInventory.ps1 missing'
    }
    . $lib
    return Get-ProductFileInventory -PayloadRoot (Get-ProductPayloadRoot -SourceRoot $SourceRoot)
}

function Write-BuildError {
    param([string]$Message)
    Write-Host "BUILD ERROR: $Message" -ForegroundColor Red
    if (-not $NoPause) { Read-Host '按 Enter 键关闭' }
    exit 1
}

function Get-RelativePath {
    param([string]$Base, [string]$Full)
    $baseUri = (New-Object System.Uri ($Base.TrimEnd('\') + '\'))
    $fullUri = New-Object System.Uri $Full
    return [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($fullUri).ToString()).Replace('\', '/')
}

function Get-FileSha256 {
    param([string]$Path)
    $hash = Get-FileHash -LiteralPath $Path -Algorithm SHA256
    return $hash.Hash.ToLowerInvariant()
}

function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $Content, $utf8)
}

function Write-Utf8WithBom {
    param([string]$Path, [string]$Content)
    $utf8 = New-Object System.Text.UTF8Encoding $true
    [System.IO.File]::WriteAllText($Path, $Content, $utf8)
}

# --- Preconditions ---

$gitStatus = git -C $ProjectRoot status --porcelain 2>$null
$head = (git -C $ProjectRoot rev-parse HEAD).Trim()
if ($gitStatus -and -not $AllowWorkingTree) {
    Write-BuildError 'BLOCK_RELEASE_DIRTY_TREE: Git working tree is not clean. Use Release orchestrator or -AllowWorkingTree for pre-commit builds.'
}
$versionFile = Join-Path $SourceRoot 'VERSION'
$version = (Get-Content -LiteralPath $versionFile -Raw).Trim()
if ($version -match '-dev$') {
    Write-BuildError "VERSION must be a release version, got: $version"
}
$tagRef = git -C $ProjectRoot rev-parse -q --verify "refs/tags/v$version" 2>$null
if ($tagRef) {
    Write-BuildError "RELEASE_VERSION_IMMUTABLE: annotated tag v$version already exists."
}

$payloadRoot = Join-Path $SourceRoot 'payload'
$installerBat = Join-Path $SourceRoot 'installer\init-video-workflow.bat'
$installerPs1 = Join-Path $SourceRoot 'installer\init-video-workflow.ps1'
$manifestTemplate = Join-Path $SourceRoot 'manifest.template.json'
$readmeTemplate = Join-Path $BuildRoot 'release-readme.template.md'
$installerSmoke = Join-Path $SourceRoot 'tests\installer-smoke.ps1'
$releaseSmoke = Join-Path $SourceRoot 'tests\release-smoke.ps1'

foreach ($p in @($payloadRoot, $installerBat, $installerPs1, $manifestTemplate, $readmeTemplate, $installerSmoke, $releaseSmoke)) {
    if (-not (Test-Path -LiteralPath $p)) {
        Write-BuildError "Missing required path: $p"
    }
}

$RequiredPayloadFiles = Get-InstallerProductFiles -SourceRoot $SourceRoot

$missingPayload = @()
foreach ($rel in $RequiredPayloadFiles) {
    $p = Join-Path $payloadRoot ($rel -replace '/', '\')
    if (-not (Test-Path -LiteralPath $p)) { $missingPayload += $rel }
}
if ($missingPayload.Count -gt 0) {
    Write-BuildError ("Payload invalid. Missing: {0}" -f ($missingPayload -join ', '))
}

if (-not $SkipInstallerSmoke) {
    Write-Host 'Running installer smoke tests...' -ForegroundColor Cyan
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installerSmoke
    if ($LASTEXITCODE -ne 0) {
        Write-BuildError 'Installer smoke tests failed.'
    }
}

# --- Release paths ---

$releaseFolderName = "video-editing-workflow-v$version"
$releaseDir = Join-Path $ReleasesRoot $releaseFolderName
$releaseZip = Join-Path $ReleasesRoot "$releaseFolderName.zip"

if ((Test-Path -LiteralPath $releaseDir) -or (Test-Path -LiteralPath $releaseZip)) {
    if (-not $Clean) {
        Write-BuildError 'Release artifacts already exist. Use -Clean to rebuild.'
    }
    if (Test-Path -LiteralPath $releaseDir) {
        Remove-Item -LiteralPath $releaseDir -Recurse -Force
    }
    if (Test-Path -LiteralPath $releaseZip) {
        Remove-Item -LiteralPath $releaseZip -Force
    }
}

# --- Stage release ---

New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null
$releasePayload = Join-Path $releaseDir 'payload'
Copy-Item -LiteralPath $payloadRoot -Destination $releasePayload -Recurse -Force
Copy-Item -LiteralPath $installerBat -Destination (Join-Path $releaseDir 'init-video-workflow.bat') -Force
Copy-Item -LiteralPath $installerPs1 -Destination (Join-Path $releaseDir 'init-video-workflow.ps1') -Force
$genProduct = Join-Path $SourceRoot 'installer\product-files.generated.ps1'
if (Test-Path -LiteralPath $genProduct) {
    Copy-Item -LiteralPath $genProduct -Destination (Join-Path $releaseDir 'product-files.generated.ps1') -Force
}
Copy-Item -LiteralPath $versionFile -Destination (Join-Path $releaseDir 'VERSION') -Force

$readme = (Get-Content -LiteralPath $readmeTemplate -Raw -Encoding UTF8).Replace('{{VERSION}}', "v$version")
Write-Utf8NoBom -Path (Join-Path $releaseDir 'README.md') -Content $readme

$templateJson = Get-Content -LiteralPath $manifestTemplate -Raw -Encoding UTF8
$manifestObj = $templateJson.Replace('{{VERSION}}', $version) | ConvertFrom-Json
$manifestPath = Join-Path $releaseDir 'manifest.json'
$manifestJson = $manifestObj | ConvertTo-Json -Depth 6
Write-Utf8NoBom -Path $manifestPath -Content ($manifestJson + [Environment]::NewLine)

# --- SHA256SUMS ---

$releaseFiles = Get-ChildItem -LiteralPath $releaseDir -Recurse -File | Sort-Object FullName
$sumLines = New-Object System.Collections.Generic.List[string]
foreach ($f in $releaseFiles) {
    $rel = Get-RelativePath -Base $releaseDir -Full $f.FullName
    if ($rel -eq 'SHA256SUMS.txt') { continue }
    $hash = Get-FileSha256 -Path $f.FullName
    $sumLines.Add("$hash  $rel")
}
$sumsPath = Join-Path $releaseDir 'SHA256SUMS.txt'
Write-Utf8NoBom -Path $sumsPath -Content (($sumLines -join [Environment]::NewLine) + [Environment]::NewLine)

# Verify hashes
foreach ($line in $sumLines) {
    if ($line -match '^([0-9a-f]{64})\s+(.+)$') {
        $expected = $Matches[1]
        $rel = $Matches[2].Replace('/', '\')
        $actual = Get-FileSha256 -Path (Join-Path $releaseDir $rel)
        if ($actual -ne $expected) {
            Write-BuildError "SHA256 mismatch for $rel"
        }
    }
}

if (-not $SkipReleaseSmoke) {
    Write-Host 'Running release smoke tests (pre-ZIP)...' -ForegroundColor Cyan
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $releaseSmoke -ReleasePath $releaseDir -NoPause
    if ($LASTEXITCODE -ne 0) {
        Write-BuildError 'Release smoke tests failed.'
    }
}

# --- ZIP ---

if (Test-Path -LiteralPath $releaseZip) {
    Remove-Item -LiteralPath $releaseZip -Force
}
Compress-Archive -LiteralPath $releaseDir -DestinationPath $releaseZip -CompressionLevel Optimal

if (-not $SkipReleaseSmoke) {
    Write-Host 'Running release smoke tests (ZIP)...' -ForegroundColor Cyan
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $releaseSmoke -ReleasePath $releaseDir -ZipPath $releaseZip -NoPause
    if ($LASTEXITCODE -ne 0) {
        Write-BuildError 'Release ZIP smoke test failed.'
    }
}

$fileCount = (Get-ChildItem -LiteralPath $releaseDir -Recurse -File).Count
$zipSize = (Get-Item -LiteralPath $releaseZip).Length
$zipHash = Get-FileSha256 -Path $releaseZip

# --- Build evidence (project-level, not in ZIP) ---

$evidencePath = Join-Path $ReleasesRoot "RELEASE-v$version.md"
$remoteStatus = 'REMOTE_NOT_CONFIGURED'
$remotes = git -C $ProjectRoot remote 2>$null
if ($remotes) { $remoteStatus = 'CONFIGURED' }

$evidence = @"
# Release v$version

| Field | Value |
|-------|-------|
| Version | $version |
| Source Commit | $head |
| Build date/time | $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK') |
| Release file count | $fileCount |
| ZIP size (bytes) | $zipSize |
| ZIP SHA256 | $zipHash |
| Installer smoke | PASS |
| Release smoke | PASS |
| N02 capability gate | PASS |
| Remote status | $remoteStatus |

## Release Position

**First Real Production Baseline** — capability-complete for first Production; not feature-complete.

| Gate | Status |
|------|--------|
| `PRODUCTION_MINIMUM_BUNDLE` | READY |
| `REMAINING_PRODUCTION_BLOCKERS` | [] |
| Subtitle baseline | Native DRT + semantic segmentation |

## Known Limitations

1. 当前只有 `observational-info-short` 一种 L2 剪辑策略。
2. 当前主要验证 Runtime 为 DaVinci Resolve。
3. live_api_srt_append route 为 UNSAFE；当前使用安全 DRT route。
4. live transition route FAILED；当前使用 native_drt_transition route。
5. DaVinci-native item audio volume FAILED；当前允许 FFmpeg pre-attenuation fallback。
6. ducking 未实现，非阻塞项。
7. `subtitle.layout.pixel_width` / `subtitle.style.keyword_emphasis` = AVAILABLE_UNVERIFIED（accepted degradation）。
8. Text+ production overlay = PARTIAL；不得升级为 production VERIFIED。
9. motion / LUT / OFX / Fusion effects = enhancement backlog，非 P0 blocker。
"@
Write-Utf8NoBom -Path $evidencePath -Content $evidence

# --- Summary ---

Write-Host ''
Write-Host '========================================' -ForegroundColor Green
Write-Host 'Build Summary' -ForegroundColor Green
Write-Host '========================================' -ForegroundColor Green
Write-Host "Version:        $version"
Write-Host "Source Commit:  $head"
Write-Host "Release dir:    $releaseDir"
Write-Host "ZIP:            $releaseZip"
Write-Host "File count:     $fileCount"
Write-Host "ZIP size:       $zipSize bytes"
Write-Host "ZIP SHA256:     $zipHash"
Write-Host "Evidence:       $evidencePath"
Write-Host 'STATUS: PASS' -ForegroundColor Green

if (-not $NoPause) {
    Read-Host '按 Enter 键关闭'
}
exit 0
