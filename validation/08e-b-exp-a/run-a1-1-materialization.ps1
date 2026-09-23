#Requires -Version 5.1
<#
.SYNOPSIS
  Stage 08E-B A1.1 — L1 layout → Text+ materialization plan (validation).
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RequestPath,
    [string]$CueId,
    [string]$OutPath,
    [string]$PreflightPath,
    [string]$RepoRoot
)

if (-not $RepoRoot) {
    $scriptDir = $PSScriptRoot
    if (-not $scriptDir) { $scriptDir = 'E:\01_Work\01_PersonalProjects\011-video-editing-workflow\validation\08e-b-exp-a' }
    $RepoRoot = (Resolve-Path (Join-Path $scriptDir '..\..')).Path
}

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$matPath = Join-Path $RepoRoot 'source\payload\video-workflow\tools\lib\textplus-layout-materializer.ps1'
. $matPath

if (-not $CueId) {
    $reqJson = [System.IO.File]::ReadAllText($RequestPath, (New-Object System.Text.UTF8Encoding $false))
    $req = $reqJson | ConvertFrom-Json
    $CueId = [string]$req.cues[0].cue_id
}
if (-not $OutPath) {
    $OutPath = Join-Path $PSScriptRoot "evidence\a1-1-materialization-$CueId.json"
}

$plan = Invoke-TextPlusLayoutMaterializationFromFiles -RequestPath $RequestPath -PreflightPath $PreflightPath -CueId $CueId
New-Item -ItemType Directory -Force -Path (Split-Path $OutPath) | Out-Null
$plan | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $OutPath -Encoding UTF8
Write-Output $OutPath
$plan | ConvertTo-Json -Depth 8
