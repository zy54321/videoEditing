#Requires -Version 5.1
<#
.SYNOPSIS
  Smoke tests for a built release package.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ReleasePath,
    [string]$ZipPath,
    [switch]$NoPause
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Release smoke must not mutate the candidate via Python bytecode (see TEST-R23).
$env:PYTHONDONTWRITEBYTECODE = '1'

$Pass = 0
$Fail = 0
$TmpRoot = Join-Path $PSScriptRoot '.tmp-release'

$MediaExtensions = @(
    '.mp4', '.mov', '.mkv', '.avi', '.webm', '.m4v',
    '.wav', '.mp3', '.m4a', '.aac', '.flac', '.ogg',
    '.jpg', '.jpeg', '.png', '.webp', '.gif', '.tif', '.tiff', '.bmp',
    '.srt', '.vtt', '.ass', '.ssa'
)

function Assert-True {
    param([bool]$Condition, [string]$Name)
    if ($Condition) {
        Write-Host "[PASS] $Name" -ForegroundColor Green
        $script:Pass++
    } else {
        Write-Host "[FAIL] $Name" -ForegroundColor Red
        $script:Fail++
    }
}

function Assert-ExitCode {
    param([int]$Actual, [int]$Expected, [string]$Name)
    Assert-True ($Actual -eq $Expected) "$Name (expected exit $Expected, got $Actual)"
}

function Invoke-ReleaseInstaller {
    param(
        [string]$Parent,
        [string]$WorkspaceName = 'release-test-production'
    )
    $installer = Join-Path $ReleasePath 'init-video-workflow.ps1'
    $args = @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $installer,
        '-TargetPath', $Parent,
        '-WorkspaceName', $WorkspaceName,
        '-NoPause'
    )
    & powershell.exe @args | Out-Null
    return [int]$LASTEXITCODE
}

function New-ParentDir {
    param([string]$Name)
    $p = Join-Path $TmpRoot $Name
    if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Recurse -Force }
    New-Item -ItemType Directory -Path $p -Force | Out-Null
    return $p
}

function Get-WorkspacePath {
    param(
        [string]$Parent,
        [string]$WorkspaceName = 'release-test-production'
    )
    return Join-Path $Parent $WorkspaceName
}

function Cleanup-Tmp {
    if (Test-Path -LiteralPath $TmpRoot) {
        Remove-Item -LiteralPath $TmpRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Test-HasMediaExtension {
    param([string]$Name)
    foreach ($ext in $MediaExtensions) {
        if ($Name.EndsWith($ext, [StringComparison]::OrdinalIgnoreCase)) { return $true }
    }
    return $false
}

$ReleasePath = [System.IO.Path]::GetFullPath($ReleasePath)
if (-not (Test-Path -LiteralPath $ReleasePath -PathType Container)) {
    Write-Error "Release path not found: $ReleasePath"
    exit 1
}

Cleanup-Tmp
New-Item -ItemType Directory -Path $TmpRoot -Force | Out-Null

Write-Host '=== Release Smoke Tests ===' -ForegroundColor Cyan
Write-Host "Release: $ReleasePath"
Write-Host ''

$requiredRootFiles = @(
    'init-video-workflow.bat',
    'init-video-workflow.ps1',
    'VERSION',
    'manifest.json',
    'SHA256SUMS.txt',
    'README.md'
)
$r01 = $true
foreach ($f in $requiredRootFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $ReleasePath $f))) { $r01 = $false }
}
if (-not (Test-Path -LiteralPath (Join-Path $ReleasePath 'payload') -PathType Container)) { $r01 = $false }
Assert-True $r01 'TEST-R01 required release files exist'

$version = (Get-Content -LiteralPath (Join-Path $ReleasePath 'VERSION') -Raw).Trim()
Assert-True ($version -notmatch '-dev$') "TEST-R02 VERSION is release form ($version)"

$manifest = $null
$manifestOk = $false
try {
    $manifest = Get-Content -LiteralPath (Join-Path $ReleasePath 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $manifestOk = $true
} catch { $manifestOk = $false }
Assert-True $manifestOk 'TEST-R03 manifest parse PASS'

if ($manifestOk) {
    Assert-True ($manifest.version -eq $version) 'TEST-R04 manifest version matches VERSION'
} else {
    Assert-True $false 'TEST-R04 manifest version matches VERSION'
}

$componentOk = $false
if ($manifestOk) {
    $componentOk = $true
    foreach ($rule in $manifest.components.rules) {
        $p = Join-Path $ReleasePath "payload/.cursor/rules/$rule.mdc"
        if (-not (Test-Path -LiteralPath $p)) { $componentOk = $false }
    }
    foreach ($skill in $manifest.components.skills) {
        if ($skill -eq 'video-production') {
            $p = Join-Path $ReleasePath 'payload/.cursor/skills/video-production/SKILL.md'
        } else {
            $p = Join-Path $ReleasePath "payload/.cursor/skills/video-editing/$skill/SKILL.md"
        }
        if (-not (Test-Path -LiteralPath $p)) { $componentOk = $false }
    }
    foreach ($cap in $manifest.components.capabilities) {
        if ($cap -eq 'logical-capability-vocabulary') {
            $p = Join-Path $ReleasePath 'payload/video-workflow/capabilities/logical-capability-vocabulary.yaml'
        } else {
            $p = Join-Path $ReleasePath "payload/video-workflow/capabilities/$cap.md"
        }
        if (-not (Test-Path -LiteralPath $p)) { $componentOk = $false }
    }
    foreach ($tpl in $manifest.components.templates) {
        switch ($tpl) {
            'style-skill' {
                $p = Join-Path $ReleasePath 'payload/video-workflow/templates/style-skill/SKILL.md'
            }
            'subtitle-layout' {
                $p = Join-Path $ReleasePath 'payload/video-workflow/templates/subtitle-layout-request.json'
            }
            'capability-resolution' {
                $p = Join-Path $ReleasePath 'payload/video-workflow/templates/capability-resolution-result.yaml'
            }
            default {
                $p = Join-Path $ReleasePath "payload/video-workflow/templates/$tpl.yaml"
            }
        }
        if (-not (Test-Path -LiteralPath $p)) { $componentOk = $false }
    }
}
Assert-True $componentOk 'TEST-R05 manifest components match files'

$shaOk = $true
$sumsFile = Join-Path $ReleasePath 'SHA256SUMS.txt'
Get-Content -LiteralPath $sumsFile | ForEach-Object {
    if ($_ -match '^([0-9a-f]{64})\s+(.+)$') {
        $expected = $Matches[1]
        $rel = $Matches[2].Replace('/', '\')
        $target = Join-Path $ReleasePath $rel
        if (-not (Test-Path -LiteralPath $target)) { $shaOk = $false; return }
        $actual = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $expected) { $shaOk = $false }
    }
}
Assert-True $shaOk 'TEST-R06 SHA256 checksums verify'

$releasePayload = Join-Path $ReleasePath 'payload'
Assert-True (Test-Path -LiteralPath $releasePayload -PathType Container) 'TEST-R07 release payload at ./payload'

$parent = New-ParentDir 'install-parent'
$code = Invoke-ReleaseInstaller -Parent $parent
$ws = Get-WorkspacePath -Parent $parent
Assert-ExitCode -Actual $code -Expected 0 -Name 'TEST-R08 release installer installs to workspace child'
Assert-True (-not (Test-Path (Join-Path $parent '.cursor'))) 'TEST-R08b parent not polluted with .cursor'

$rulesOk = @(
    'video-workflow-core.mdc',
    'davinci-production.mdc',
    'production-entry-intake.mdc'
) | ForEach-Object { Test-Path (Join-Path $ws ".cursor\rules\$_") } | Where-Object { $_ -eq $false } | Measure-Object | Select-Object -ExpandProperty Count
Assert-True ($rulesOk -eq 0) 'TEST-R09 three rules installed'

$skillsOk = (Test-Path (Join-Path $ws '.cursor\skills\video-production\SKILL.md')) -and
    (Test-Path (Join-Path $ws '.cursor\skills\video-editing\observational-info-short\SKILL.md'))
Assert-True $skillsOk 'TEST-R10 two skills installed'

Assert-True (Test-Path (Join-Path $ws 'video-workflow\capabilities\davinci-resolve.md')) 'TEST-R11 capability installed'
Assert-True (Test-Path (Join-Path $ws 'video-workflow\templates\production-brief.yaml')) 'TEST-R12 template installed'

$prodDir = Join-Path $ws 'video-workflow\production'
Assert-True (Test-Path $prodDir -PathType Container) 'TEST-R13 production directory exists'
Assert-True (-not (Test-Path (Join-Path $prodDir 'brief.yaml'))) 'TEST-R14 brief.yaml absent after install'

$instOk = $false
try {
    $instJson = Get-Content (Join-Path $ws 'video-workflow\installation.json') -Raw | ConvertFrom-Json
    $instOk = ($instJson.version -eq $version)
} catch { $instOk = $false }
Assert-True $instOk 'TEST-R15 installation.json version matches release VERSION'

$code16 = Invoke-ReleaseInstaller -Parent $parent
Assert-ExitCode -Actual $code16 -Expected 31 -Name 'TEST-R16 re-install blocked'

$forbiddenNames = @('docs', 'research', 'validation', 'source', 'tests', '.git')
$r17 = $true
foreach ($name in $forbiddenNames) {
    if (Test-Path -LiteralPath (Join-Path $ReleasePath $name)) { $r17 = $false }
}
Get-ChildItem -LiteralPath $ReleasePath -Recurse -Directory | ForEach-Object {
    if ($forbiddenNames -contains $_.Name) { $r17 = $false }
}
Assert-True $r17 'TEST-R17 release contains no dev materials'

$r18 = $true
Get-ChildItem -LiteralPath $ReleasePath -Recurse -File | ForEach-Object {
    if (Test-HasMediaExtension -Name $_.Name) { $r18 = $false }
}
Assert-True $r18 'TEST-R18 release contains no production media files'

$r19 = $true
Get-ChildItem -LiteralPath $ReleasePath -Recurse -File | ForEach-Object {
    if (-not (Test-HasMediaExtension -Name $_.Name)) { return }
    $rel = $_.FullName.Substring($ReleasePath.Length).Replace('\', '/')
    if ($rel -match '(?i)/N02/|/N02[^/]*\.') { $r19 = $false }
    if ($_.Name -match '(?i)^N02.+\.' ) { $r19 = $false }
}
Assert-True $r19 'TEST-R19 no N02 production asset leakage'

$r23 = $true
Get-ChildItem -LiteralPath $ReleasePath -Recurse -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.Name -eq '__pycache__') { $r23 = $false }
}
Get-ChildItem -LiteralPath $ReleasePath -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.Extension -eq '.pyc') { $r23 = $false }
}
Assert-True $r23 'TEST-R23 release candidate has no Python bytecode artifacts'

$entryRule = Join-Path $ReleasePath 'payload\.cursor\rules\production-entry-intake.mdc'
$entryContent = Get-Content -LiteralPath $entryRule -Raw -Encoding UTF8
Assert-True ($entryContent -match '【制作视频】') 'TEST-R20 entry rule contains production entry token'
Assert-True ($entryContent -match 'alwaysApply:\s*true') 'TEST-R21 production entry rule alwaysApply=true'

if ($ZipPath) {
    $ZipPath = [System.IO.Path]::GetFullPath($ZipPath)
    $zipOk = $false
    if (Test-Path -LiteralPath $ZipPath) {
        $extractRoot = Join-Path $TmpRoot 'zip-extract'
        if (Test-Path -LiteralPath $extractRoot) { Remove-Item -LiteralPath $extractRoot -Recurse -Force }
        New-Item -ItemType Directory -Path $extractRoot -Force | Out-Null
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::ExtractToDirectory($ZipPath, $extractRoot)
        $folderName = Split-Path -Leaf $ReleasePath
        $top = Join-Path $extractRoot $folderName
        $zipOk = (Test-Path -LiteralPath (Join-Path $top 'init-video-workflow.bat')) -and
            (Test-Path -LiteralPath (Join-Path $top 'payload')) -and
            (Test-Path -LiteralPath (Join-Path $top 'manifest.json'))
    }
    Assert-True $zipOk 'TEST-R22 ZIP extracts with valid top-level structure'
} else {
    Write-Host '[SKIP] TEST-R22 ZIP test (no ZipPath)' -ForegroundColor Yellow
}

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })

Cleanup-Tmp

if ($Fail -gt 0) {
    if (-not $NoPause) { Read-Host '按 Enter 键关闭' }
    exit 1
}
exit 0
