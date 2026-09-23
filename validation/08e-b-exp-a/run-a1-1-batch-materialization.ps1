#Requires -Version 5.1
<#
.SYNOPSIS
  Generate A1.1 materialization plans for A07–A11 cases.
#>
[CmdletBinding()]
param(
    [string]$RepoRoot
)

if (-not $RepoRoot) {
    $scriptDir = $PSScriptRoot
    if (-not $scriptDir) { $scriptDir = 'E:\01_Work\01_PersonalProjects\011-video-editing-workflow\validation\08e-b-exp-a' }
    $RepoRoot = (Resolve-Path (Join-Path $scriptDir '..\..')).Path
}

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$runner = Join-Path $PSScriptRoot 'run-a1-1-materialization.ps1'
$plans = @(
    @{ Request = 'cases\A11-materialization-smoke.request.json'; CueId = 'A11' },
    @{ Request = 'cases\A07.request.json'; CueId = 'A07' },
    @{ Request = 'cases\A08.request.json'; CueId = 'A08' },
    @{ Request = 'cases\A09.request.json'; CueId = 'A09' },
    @{ Request = 'cases\A07-splittable.request.json'; CueId = 'A07' },
    @{ Request = 'cases\A08-splittable.request.json'; CueId = 'A08' },
    @{ Request = 'cases\A09-splittable.request.json'; CueId = 'A09' },
    @{ Request = 'cases\A10.request.json'; CueId = 'A10' }
)

foreach ($item in $plans) {
    $reqPath = Join-Path $PSScriptRoot $item.Request
    $cueId = $item.CueId
    $suffix = if ($item.Request -match 'splittable') { '-splittable' } else { '' }
    $out = Join-Path $PSScriptRoot "evidence\a1-1-materialization-$cueId$suffix.json"
    Write-Host "==> $cueId$suffix"
    & $runner -RequestPath $reqPath -CueId $cueId -OutPath $out -RepoRoot $RepoRoot | Out-Null
}

Write-Host 'DONE'
