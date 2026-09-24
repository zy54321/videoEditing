#Requires -Version 5.1
<#
.SYNOPSIS
  Verify ZIP-only release install path.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$SourceRoot = Join-Path $ProjectRoot 'source'
$releaseVersion = (Get-Content (Join-Path $SourceRoot 'VERSION') -Raw).Trim()
$ZipPath = Join-Path $ProjectRoot "releases\video-editing-workflow-v$releaseVersion.zip"
$TmpRoot = Join-Path $PSScriptRoot '.tmp-zip-only'

if (Test-Path $TmpRoot) { Remove-Item -LiteralPath $TmpRoot -Recurse -Force }
New-Item -ItemType Directory -Path $TmpRoot -Force | Out-Null

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory($ZipPath, $TmpRoot)

$releaseRoot = Join-Path $TmpRoot "video-editing-workflow-v$releaseVersion"
$installer = Join-Path $releaseRoot 'init-video-workflow.ps1'
$ws = Join-Path $TmpRoot 'workspace'
New-Item -ItemType Directory -Path $ws -Force | Out-Null

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -TargetPath $ws -DryRun -NoPause | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Error "DryRun failed: $LASTEXITCODE"; exit 1 }

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -TargetPath $ws -NoPause | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Error "Install failed: $LASTEXITCODE"; exit 1 }

$checks = @(
    (Test-Path (Join-Path $ws '.cursor\rules\production-entry-intake.mdc')),
    (Test-Path (Join-Path $ws '.cursor\skills\video-production\SKILL.md')),
    (Test-Path (Join-Path $ws 'video-workflow\production')),
    (-not (Test-Path (Join-Path $ws 'video-workflow\production\brief.yaml')))
)
if ($checks -contains $false) { Write-Error 'Installed structure invalid'; exit 1 }

Remove-Item -LiteralPath $TmpRoot -Recurse -Force
Write-Host 'ZIP independent install: PASS' -ForegroundColor Green
exit 0
