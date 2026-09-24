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
$DefaultWorkspaceName = 'test-production'

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

function Get-WorkspacePath {
    param(
        [string]$Parent,
        [string]$WorkspaceName = $DefaultWorkspaceName
    )
    return Join-Path $Parent $WorkspaceName
}

function Invoke-Installer {
    param(
        [string]$Parent,
        [string]$WorkspaceName = $DefaultWorkspaceName,
        [string]$PayloadRoot,
        [switch]$DryRun,
        [switch]$TestSimulateFailure,
        [int]$TestSimulateFailureAfter = 1
    )
    $args = @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $Installer,
        '-TargetPath', $Parent,
        '-WorkspaceName', $WorkspaceName,
        '-NoPause'
    )
    if ($DryRun) { $args += '-DryRun' }
    if ($PayloadRoot) { $args += @('-PayloadRoot', $PayloadRoot) }
    if ($TestSimulateFailure) {
        $args += '-TestSimulateFailure'
        $args += @('-TestSimulateFailureAfter', $TestSimulateFailureAfter)
    }
    & powershell.exe @args | Out-Null
    return [int]$LASTEXITCODE
}

function New-ParentDir {
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

# TEST-01: fresh workspace install (Case A)
$parent1 = New-ParentDir 'test01-parent'
$code = Invoke-Installer -Parent $parent1
Assert-ExitCode -Actual $code -Expected 0 -Name 'TEST-01 fresh workspace install'
$ws1 = Get-WorkspacePath -Parent $parent1
Assert-True (Test-Path (Join-Path $ws1 '.cursor\rules\video-workflow-core.mdc')) 'TEST-01A workspace child contains .cursor'
Assert-True (Test-Path (Join-Path $ws1 'video-workflow\production')) 'TEST-01A workspace child contains video-workflow'

# TEST-01B: parent must not be polluted (Case B)
Assert-True (-not (Test-Path (Join-Path $parent1 '.cursor'))) 'TEST-01B parent has no .cursor'
Assert-True (-not (Test-Path (Join-Path $parent1 'video-workflow'))) 'TEST-01B parent has no video-workflow'

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
    (Test-Path (Join-Path $ws1 '.cursor\skills\video-editing\observational-info-short\style-profile.yaml')) -and
    (Test-Path (Join-Path $ws1 '.cursor\skills\video-editing\observational-info-short\references\08-qa.md'))
Assert-True $skillsOk 'TEST-03 skills and references present'

# TEST-04: capability, templates, knowledge, tools (Stage 08C)
$capOk = (Test-Path (Join-Path $ws1 'video-workflow\capabilities\davinci-resolve.md')) -and
    (Test-Path (Join-Path $ws1 'video-workflow\templates\production-brief.yaml')) -and
    (Test-Path (Join-Path $ws1 'video-workflow\templates\production-brief-reference.md')) -and
    (Test-Path (Join-Path $ws1 'video-workflow\templates\edit-blueprint.yaml')) -and
    (Test-Path (Join-Path $ws1 'video-workflow\templates\edit-blueprint-reference.md')) -and
    (Test-Path (Join-Path $ws1 'video-workflow\knowledge\editing-craft\README.md')) -and
    (Test-Path (Join-Path $ws1 'video-workflow\tools\final-artifact-qa.ps1')) -and
    (Test-Path (Join-Path $ws1 'video-workflow\capabilities\logical-capability-vocabulary.yaml')) -and
    (Test-Path (Join-Path $ws1 'video-workflow\templates\capability-resolution-result.yaml'))
Assert-True $capOk 'TEST-04 capability and templates present'

# TEST-04b: Stage 08E-B A1.1 materializer + font profiles installed
$matOk = (Test-Path (Join-Path $ws1 'video-workflow\tools\lib\textplus-layout-materializer.ps1')) -and
    (Test-Path (Join-Path $ws1 'video-workflow\runtime\textplus-font-profiles.yaml'))
Assert-True $matOk 'TEST-04b textplus materializer and font profiles present'

# TEST-04c: Stage 08E-B B-R2 CLS generator + canonical setting installed
$clsOk = (Test-Path (Join-Path $ws1 'video-workflow\tools\generate-textplus-cls-setting.py')) -and
    (Test-Path (Join-Path $ws1 'video-workflow\tools\lib\textplus_cls_setting.py')) -and
    (Test-Path (Join-Path $ws1 'video-workflow\runtime\textplus-cls-canonical.setting')) -and
    (Test-Path (Join-Path $ws1 'video-workflow\runtime\textplus-production-profile.yaml'))
Assert-True $clsOk 'TEST-04c textplus CLS generator canonical setting and production profile present'

# TEST-05: production dir exists, no brief
$prodDir = Join-Path $ws1 'video-workflow\production'
$test05 = (Test-Path $prodDir -PathType Container) -and (-not (Test-Path (Join-Path $prodDir 'brief.yaml')))
Assert-True $test05 'TEST-05 production dir exists, brief.yaml absent'

# TEST-06: installation.json parse and workspace path
$jsonPath = Join-Path $ws1 'video-workflow\installation.json'
$jsonOk = $false
try {
    $j = Get-Content $jsonPath -Raw | ConvertFrom-Json
    $expectedWs = [System.IO.Path]::GetFullPath($ws1)
    $actualWs = [System.IO.Path]::GetFullPath($j.workspace)
    $jsonOk = ($j.product -eq 'video-editing-workflow') -and ($j.brief_created -eq $false) -and ($actualWs -eq $expectedWs)
} catch { $jsonOk = $false }
Assert-True $jsonOk 'TEST-06 installation.json parse and workspace path'

# TEST-07: re-install same workspace
$code7 = Invoke-Installer -Parent $parent1
Assert-ExitCode -Actual $code7 -Expected 31 -Name 'TEST-07 re-install blocked WORKSPACE_ALREADY_INITIALIZED'

# TEST-08: existing workspace directory blocked (Case C)
$parent8 = New-ParentDir 'test08-parent'
$existingWs8 = Get-WorkspacePath -Parent $parent8
New-Item -ItemType Directory -Path (Join-Path $existingWs8 '.cursor\rules') -Force | Out-Null
Copy-Item (Join-Path $ws1 '.cursor\rules\video-workflow-core.mdc') (Join-Path $existingWs8 '.cursor\rules\video-workflow-core.mdc')
$code8 = Invoke-Installer -Parent $parent8
Assert-ExitCode -Actual $code8 -Expected 12 -Name 'TEST-08 existing workspace WORKSPACE_DIRECTORY_EXISTS'

# TEST-09: existing workspace with brief blocked (Case C)
$parent9 = New-ParentDir 'test09-parent'
$existingWs9 = Get-WorkspacePath -Parent $parent9 -WorkspaceName 'bound-production'
New-Item -ItemType Directory -Path (Join-Path $existingWs9 'video-workflow\production') -Force | Out-Null
Set-Content -Path (Join-Path $existingWs9 'video-workflow\production\brief.yaml') -Value 'version: 1'
$code9 = Invoke-Installer -Parent $parent9 -WorkspaceName 'bound-production'
Assert-ExitCode -Actual $code9 -Expected 12 -Name 'TEST-09 existing workspace with brief WORKSPACE_DIRECTORY_EXISTS'

# TEST-10: dry run no changes
$parent10 = New-ParentDir 'test10-parent'
$marker = Join-Path $parent10 'user-marker.txt'
Set-Content -Path $marker -Value 'keep'
$before = (Get-ChildItem -LiteralPath $parent10 -Recurse -Force | Measure-Object).Count
$code10 = Invoke-Installer -Parent $parent10 -DryRun
$after = (Get-ChildItem -LiteralPath $parent10 -Recurse -Force | Measure-Object).Count
Assert-ExitCode -Actual $code10 -Expected 0 -Name 'TEST-10 dry run exit 0'
Assert-True (($before -eq $after) -and (Test-Path $marker)) 'TEST-10 dry run no file changes'
Assert-True (-not (Test-Path (Get-WorkspacePath -Parent $parent10))) 'TEST-10 dry run does not create workspace child'

# TEST-11: does not touch pre-existing parent file
$parent11 = New-ParentDir 'test11-parent'
$userFile = Join-Path $parent11 'my-notes.txt'
Set-Content -Path $userFile -Value 'owner data'
Invoke-Installer -Parent $parent11 | Out-Null
Assert-True (Test-Path -LiteralPath $userFile) 'TEST-11 parent user file still exists'
Assert-True ((Get-Content -LiteralPath $userFile -Raw).Trim() -eq 'owner data') 'TEST-11 preserves pre-existing parent files'

# TEST-12: no workspace-config.yaml
Assert-True (-not (Test-Path (Join-Path $ws1 'workspace-config.yaml'))) 'TEST-12 no workspace-config.yaml created'

# TEST-13: missing payload file blocks install, parent unchanged
$parent13 = New-ParentDir 'test13-parent'
$payloadCopy = Join-Path $TmpRoot 'payload-copy'
if (Test-Path $payloadCopy) { Remove-Item -LiteralPath $payloadCopy -Recurse -Force }
Copy-Item -LiteralPath (Join-Path $Root 'payload') -Destination $payloadCopy -Recurse -Force
Remove-Item -LiteralPath (Join-Path $payloadCopy '.cursor\rules\video-workflow-core.mdc') -Force
$before13 = (Get-ChildItem -LiteralPath $parent13 -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object).Count
$code13 = Invoke-Installer -Parent $parent13 -PayloadRoot $payloadCopy
$after13 = (Get-ChildItem -LiteralPath $parent13 -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object).Count
Assert-ExitCode -Actual $code13 -Expected 21 -Name 'TEST-13 missing payload file PAYLOAD_INVALID'
Assert-True ($before13 -eq $after13) 'TEST-13 parent unchanged after PAYLOAD_INVALID'

# TEST-14: copy failure rollback cleans workspace child (Case D)
$parent14 = New-ParentDir 'test14-parent'
$userFile14 = Join-Path $parent14 'owner.txt'
Set-Content -Path $userFile14 -Value 'keep'
$code14 = Invoke-Installer -Parent $parent14 -TestSimulateFailure
Assert-ExitCode -Actual $code14 -Expected 40 -Name 'TEST-14 simulated copy failure'
Assert-True (-not (Test-Path (Get-WorkspacePath -Parent $parent14))) 'TEST-14 rollback removes created workspace child'
Assert-True (-not (Test-Path (Join-Path $parent14 '.cursor'))) 'TEST-14 parent has no .cursor after rollback'
Assert-True ((Get-Content -LiteralPath $userFile14 -Raw).Trim() -eq 'keep') 'TEST-14 preserves pre-existing parent file'

# TEST-14b: parent-level .cursor is never touched
$parent14b = New-ParentDir 'test14b-parent'
New-Item -ItemType Directory -Path (Join-Path $parent14b '.cursor\rules') -Force | Out-Null
Set-Content -Path (Join-Path $parent14b '.cursor\rules\custom.mdc') -Value 'owner rule' -Encoding UTF8
Invoke-Installer -Parent $parent14b -TestSimulateFailure | Out-Null
Assert-True (Test-Path (Join-Path $parent14b '.cursor\rules\custom.mdc')) 'TEST-14b preserves parent-level .cursor'
Assert-True (-not (Test-Path (Get-WorkspacePath -Parent $parent14b))) 'TEST-14b does not leave workspace child after rollback'

# TEST-15A: rollback removes entire workspace child after late failure
$parent15a = New-ParentDir 'test15a-parent'
$userFile15a = Join-Path $parent15a 'owner-notes.txt'
Set-Content -Path $userFile15a -Value 'keep'
$code15a = Invoke-Installer -Parent $parent15a -TestSimulateFailure -TestSimulateFailureAfter 16
Assert-ExitCode -Actual $code15a -Expected 40 -Name 'TEST-15A knowledge rollback simulated failure'
Assert-True (-not (Test-Path (Get-WorkspacePath -Parent $parent15a))) 'TEST-15A rollback removes workspace child'
Assert-True ((Get-Content -LiteralPath $userFile15a -Raw).Trim() -eq 'keep') 'TEST-15A preserves pre-existing parent file'

# TEST-15B: parent sibling directory untouched
$parent15b = New-ParentDir 'test15b-parent'
$siblingDir = Join-Path $parent15b 'owner-sibling'
New-Item -ItemType Directory -Path $siblingDir -Force | Out-Null
Set-Content -Path (Join-Path $siblingDir 'marker.txt') -Value 'stay'
Invoke-Installer -Parent $parent15b -TestSimulateFailure -TestSimulateFailureAfter 16 | Out-Null
Assert-True (Test-Path (Join-Path $siblingDir 'marker.txt')) 'TEST-15B preserves parent sibling directory'
Assert-True (-not (Test-Path (Get-WorkspacePath -Parent $parent15b))) 'TEST-15B workspace child removed after rollback'

# TEST-16: invalid workspace name blocked
$parent16 = New-ParentDir 'test16-parent'
$code16 = Invoke-Installer -Parent $parent16 -WorkspaceName '..'
Assert-ExitCode -Actual $code16 -Expected 13 -Name 'TEST-16 invalid workspace name blocked'

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })

Cleanup-Tmp

if ($Fail -gt 0) { exit 1 }
exit 0
