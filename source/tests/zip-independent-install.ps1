#Requires -Version 5.1
<#
.SYNOPSIS
  Verify ZIP-only release install path (no files from dev repo).
#>
[CmdletBinding()]
param(
    [string]$ZipPath,
    [string]$ReleaseVersion
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$SourceRoot = Join-Path $ProjectRoot 'source'
if (-not $ReleaseVersion) {
    $ReleaseVersion = (Get-Content (Join-Path $SourceRoot 'VERSION') -Raw).Trim()
}
if (-not $ZipPath) {
    $ZipPath = Join-Path $ProjectRoot "releases\video-editing-workflow-v$ReleaseVersion.zip"
}
if (-not (Test-Path -LiteralPath $ZipPath)) {
    Write-Error "ZIP not found: $ZipPath"
    exit 1
}

$TmpRoot = Join-Path $PSScriptRoot '.tmp-zip-only'
$WorkspaceName = 'zip-test-production'

if (Test-Path $TmpRoot) { Remove-Item -LiteralPath $TmpRoot -Recurse -Force }
New-Item -ItemType Directory -Path $TmpRoot -Force | Out-Null

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory($ZipPath, $TmpRoot)

$releaseRoot = Join-Path $TmpRoot "video-editing-workflow-v$ReleaseVersion"
$installer = Join-Path $releaseRoot 'init-video-workflow.ps1'
if (-not (Test-Path -LiteralPath $installer)) {
    Write-Error 'ZIP missing init-video-workflow.ps1'
    exit 1
}
if (-not (Test-Path -LiteralPath (Join-Path $releaseRoot 'product-files.generated.ps1'))) {
    Write-Error 'ZIP missing product-files.generated.ps1 (not self-contained)'
    exit 1
}

$parent = Join-Path $TmpRoot 'workspace-parent'
New-Item -ItemType Directory -Path $parent -Force | Out-Null
$workspace = Join-Path $parent $WorkspaceName

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -TargetPath $parent -WorkspaceName $WorkspaceName -DryRun -NoPause | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Error "DryRun failed: $LASTEXITCODE"; exit 1 }

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -TargetPath $parent -WorkspaceName $WorkspaceName -NoPause | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Error "Install failed: $LASTEXITCODE"; exit 1 }

$checks = @(
    (Test-Path (Join-Path $workspace '.cursor\rules\production-entry-intake.mdc')),
    (Test-Path (Join-Path $workspace '.cursor\skills\video-production\SKILL.md')),
    (Test-Path (Join-Path $workspace 'video-workflow\production')),
    (Test-Path (Join-Path $workspace 'video-workflow\tools\native-drt-subtitle-stroke-inject.py')),
    (Test-Path (Join-Path $workspace 'video-workflow\runtime\native-drt-subtitle-readability-profile.yaml')),
    (-not (Test-Path (Join-Path $workspace 'video-workflow\production\brief.yaml'))),
    (-not (Test-Path (Join-Path $parent '.cursor'))),
    (-not (Test-Path (Join-Path $parent 'video-workflow')))
)
if ($checks -contains $false) { Write-Error 'Installed structure invalid'; exit 1 }

Remove-Item -LiteralPath $TmpRoot -Recurse -Force
Write-Host 'ZIP independent install: PASS' -ForegroundColor Green
exit 0
