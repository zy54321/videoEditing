#Requires -Version 5.1
<#
.SYNOPSIS
  Disposable smoke tests for init-video-workflow installer.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$Installer = Join-Path $Root 'installer\init-video-workflow.ps1'
$TmpRoot = Join-Path $PSScriptRoot '.tmp-installer'

$Pass = 0
$Fail = 0

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

function Invoke-Installer {
    param(
        [string]$Target,
        [string]$PayloadRoot,
        [switch]$DryRun,
        [switch]$TestSimulateFailure,
        [int]$TestSimulateFailureAfter = 1
    )
    $args = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $Installer, '-TargetPath', $Target, '-NoPause')
    if ($DryRun) { $args += '-DryRun' }
    if ($PayloadRoot) { $args += @('-PayloadRoot', $PayloadRoot) }
    if ($TestSimulateFailure) {
        $args += '-TestSimulateFailure'
        $args += @('-TestSimulateFailureAfter', $TestSimulateFailureAfter)
    }
    & powershell.exe @args | Out-Null
    return [int]$LASTEXITCODE
}

function New-EmptyWorkspace {
    param([string]$Name)
    $p = Join-Path $TmpRoot $Name
    if (Test-Path $p) { Remove-Item -LiteralPath $p -Recurse -Force }
    New-Item -ItemType Directory -Path $p -Force | Out-Null
    return $p
}

function Cleanup-Tmp {
    if (Test-Path -LiteralPath $TmpRoot) {
        Remove-Item -LiteralPath $TmpRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

if (-not (Test-Path -LiteralPath $Installer)) {
    Write-Error "Installer not found: $Installer"
    exit 1
}

Cleanup-Tmp
New-Item -ItemType Directory -Path $TmpRoot -Force | Out-Null

Write-Host '=== Installer Smoke Tests ===' -ForegroundColor Cyan
Write-Host ''

# TEST-01: fresh workspace install
$ws1 = New-EmptyWorkspace 'test01-fresh'
$code = Invoke-Installer -Target $ws1
Assert-ExitCode -Actual $code -Expected 0 -Name 'TEST-01 fresh workspace install'

# TEST-02: 3 rules
$rules = @(
    'video-workflow-core.mdc',
    'davinci-production.mdc',
    'production-entry-intake.mdc'
)
$rulesOk = $true
foreach ($r in $rules) {
    if (-not (Test-Path (Join-Path $ws1 ".cursor\rules\$r"))) { $rulesOk = $false }
}
Assert-True $rulesOk 'TEST-02 three rules present'

# TEST-03: skills
$skillsOk = (Test-Path (Join-Path $ws1 '.cursor\skills\video-production\SKILL.md')) -and
    (Test-Path (Join-Path $ws1 '.cursor\skills\video-editing\observational-info-short\SKILL.md')) -and
    (Test-Path (Join-Path $ws1 '.cursor\skills\video-editing\observational-info-short\references\style.md')) -and
    (Test-Path (Join-Path $ws1 '.cursor\skills\video-editing\observational-info-short\references\qa.md'))
Assert-True $skillsOk 'TEST-03 skills and references present'

# TEST-04: capability, templates, knowledge, tools (Stage 08C)
$capOk = (Test-Path (Join-Path $ws1 'video-workflow\capabilities\davinci-resolve.md')) -and
    (Test-Path (Join-Path $ws1 'video-workflow\templates\production-brief.yaml')) -and
    (Test-Path (Join-Path $ws1 'video-workflow\templates\production-brief-reference.md')) -and
    (Test-Path (Join-Path $ws1 'video-workflow\templates\edit-blueprint.yaml')) -and
    (Test-Path (Join-Path $ws1 'video-workflow\templates\edit-blueprint-reference.md')) -and
    (Test-Path (Join-Path $ws1 'video-workflow\knowledge\editing-craft\README.md')) -and
    (Test-Path (Join-Path $ws1 'video-workflow\tools\final-artifact-qa.ps1'))
Assert-True $capOk 'TEST-04 capability and templates present'

# TEST-05: production dir exists, no brief
$prodDir = Join-Path $ws1 'video-workflow\production'
$test05 = (Test-Path $prodDir -PathType Container) -and (-not (Test-Path (Join-Path $prodDir 'brief.yaml')))
Assert-True $test05 'TEST-05 production dir exists, brief.yaml absent'

# TEST-06: installation.json parse
$jsonPath = Join-Path $ws1 'video-workflow\installation.json'
$jsonOk = $false
try {
    $j = Get-Content $jsonPath -Raw | ConvertFrom-Json
    $jsonOk = ($j.product -eq 'video-editing-workflow') -and ($j.brief_created -eq $false)
} catch { $jsonOk = $false }
Assert-True $jsonOk 'TEST-06 installation.json parse'

# TEST-07: re-install same workspace
$code7 = Invoke-Installer -Target $ws1
Assert-ExitCode -Actual $code7 -Expected 31 -Name 'TEST-07 re-install blocked WORKSPACE_ALREADY_INITIALIZED'

# TEST-08: conflict without installation.json
$ws8 = New-EmptyWorkspace 'test08-conflict'
New-Item -ItemType Directory -Path (Join-Path $ws8 '.cursor\rules') -Force | Out-Null
Copy-Item (Join-Path $ws1 '.cursor\rules\video-workflow-core.mdc') (Join-Path $ws8 '.cursor\rules\video-workflow-core.mdc')
$code8 = Invoke-Installer -Target $ws8
Assert-ExitCode -Actual $code8 -Expected 30 -Name 'TEST-08 pre-existing file INSTALL_FILE_CONFLICT'

# TEST-09: brief.yaml blocks install (priority)
$ws9 = New-EmptyWorkspace 'test09-bound'
New-Item -ItemType Directory -Path (Join-Path $ws9 'video-workflow\production') -Force | Out-Null
Set-Content -Path (Join-Path $ws9 'video-workflow\production\brief.yaml') -Value 'version: 1'
$code9 = Invoke-Installer -Target $ws9
Assert-ExitCode -Actual $code9 -Expected 33 -Name 'TEST-09 existing brief.yaml PRODUCTION_ALREADY_BOUND'

# TEST-10: dry run no changes
$ws10 = New-EmptyWorkspace 'test10-dryrun'
$marker = Join-Path $ws10 'user-marker.txt'
Set-Content -Path $marker -Value 'keep'
$before = (Get-ChildItem -LiteralPath $ws10 -Recurse -Force | Measure-Object).Count
$code10 = Invoke-Installer -Target $ws10 -DryRun
$after = (Get-ChildItem -LiteralPath $ws10 -Recurse -Force | Measure-Object).Count
Assert-ExitCode -Actual $code10 -Expected 0 -Name 'TEST-10 dry run exit 0'
Assert-True (($before -eq $after) -and (Test-Path $marker)) 'TEST-10 dry run no file changes'

# TEST-11: does not touch pre-existing user file
$ws11 = New-EmptyWorkspace 'test11-userfile'
$userFile = Join-Path $ws11 'my-notes.txt'
Set-Content -Path $userFile -Value 'owner data'
Invoke-Installer -Target $ws11 | Out-Null
Assert-True (Test-Path -LiteralPath $userFile) 'TEST-11 user file still exists'
Assert-True ((Get-Content -LiteralPath $userFile -Raw).Trim() -eq 'owner data') 'TEST-11 preserves pre-existing user files'

# TEST-12: no workspace-config.yaml
$ws12 = $ws1
Assert-True (-not (Test-Path (Join-Path $ws12 'workspace-config.yaml'))) 'TEST-12 no workspace-config.yaml created'

# TEST-13: missing payload file blocks install, target unchanged
$ws13 = New-EmptyWorkspace 'test13-payload-invalid'
$payloadCopy = Join-Path $TmpRoot 'payload-copy'
if (Test-Path $payloadCopy) { Remove-Item -LiteralPath $payloadCopy -Recurse -Force }
Copy-Item -LiteralPath (Join-Path $Root 'payload') -Destination $payloadCopy -Recurse -Force
Remove-Item -LiteralPath (Join-Path $payloadCopy '.cursor\rules\video-workflow-core.mdc') -Force
$before13 = (Get-ChildItem -LiteralPath $ws13 -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object).Count
$code13 = Invoke-Installer -Target $ws13 -PayloadRoot $payloadCopy
$after13 = (Get-ChildItem -LiteralPath $ws13 -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object).Count
Assert-ExitCode -Actual $code13 -Expected 21 -Name 'TEST-13 missing payload file PAYLOAD_INVALID'
Assert-True ($before13 -eq $after13) 'TEST-13 target unchanged after PAYLOAD_INVALID'

# TEST-14: copy failure rollback cleans empty created dirs
$ws14 = New-EmptyWorkspace 'test14-rollback'
$userFile14 = Join-Path $ws14 'owner.txt'
Set-Content -Path $userFile14 -Value 'keep'
$code14 = Invoke-Installer -Target $ws14 -TestSimulateFailure
Assert-ExitCode -Actual $code14 -Expected 40 -Name 'TEST-14 simulated copy failure'
Assert-True (-not (Test-Path (Join-Path $ws14 '.cursor'))) 'TEST-14 rollback removes created .cursor'
Assert-True ((Get-Content -LiteralPath $userFile14 -Raw).Trim() -eq 'keep') 'TEST-14 preserves pre-existing user file'

$ws14b = New-EmptyWorkspace 'test14b-rollback-existing'
New-Item -ItemType Directory -Path (Join-Path $ws14b '.cursor\rules') -Force | Out-Null
Set-Content -Path (Join-Path $ws14b '.cursor\rules\custom.mdc') -Value 'owner rule' -Encoding UTF8
Invoke-Installer -Target $ws14b -TestSimulateFailure | Out-Null
Assert-True (Test-Path (Join-Path $ws14b '.cursor\rules\custom.mdc')) 'TEST-14 preserves pre-existing .cursor'

# TEST-15: rollback removes nested knowledge dirs after mid-install failure
$ws15 = New-EmptyWorkspace 'test15-knowledge-rollback'
$userFile15 = Join-Path $ws15 'owner-notes.txt'
Set-Content -Path $userFile15 -Value 'keep'
$code15 = Invoke-Installer -Target $ws15 -TestSimulateFailure -TestSimulateFailureAfter 16
Assert-ExitCode -Actual $code15 -Expected 40 -Name 'TEST-15 knowledge rollback simulated failure'
Assert-True (-not (Test-Path (Join-Path $ws15 'video-workflow\knowledge'))) 'TEST-15 rollback removes created knowledge tree'
Assert-True ((Get-Content -LiteralPath $userFile15 -Raw).Trim() -eq 'keep') 'TEST-15 preserves pre-existing user file'

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })

Cleanup-Tmp

if ($Fail -gt 0) { exit 1 }
exit 0
