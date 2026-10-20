#Requires -Version 5.1
<#
.SYNOPSIS
  Post-render deliver closeout — external ASS (when opted in) + R2 gate + fail-closed assert.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspaceRoot,
    [string]$ContractPath = '',
    [switch]$SkipAudioLoudness,
    [switch]$ForceExternalAss
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$WorkspaceRoot = [System.IO.Path]::GetFullPath($WorkspaceRoot)
$tools = Join-Path $WorkspaceRoot 'video-workflow\tools'

$extRoute = Join-Path $tools 'invoke-external-ass-deliver-route.ps1'
$gatePs1 = Join-Path $tools 'run-final-artifact-gate.ps1'
$assertPs1 = Join-Path $tools 'assert-production-final-deliver.ps1'

$extArgs = @{ WorkspaceRoot = $WorkspaceRoot }
if ($ContractPath) { $extArgs['ContractPath'] = $ContractPath }
if ($ForceExternalAss) { $extArgs['Force'] = $true }

& $extRoute @extArgs
if ($LASTEXITCODE -ne 0) { throw 'EXTERNAL_ASS_DELIVER_ROUTE_FAILED' }

$gateArgs = @{ WorkspaceRoot = $WorkspaceRoot }
if ($ContractPath) { $gateArgs['ContractPath'] = $ContractPath }
if ($SkipAudioLoudness) { $gateArgs['SkipAudioLoudness'] = $true }

& $gatePs1 @gateArgs
if ($LASTEXITCODE -ne 0) { throw 'FINAL_ARTIFACT_GATE_FAILED' }

& $assertPs1 -WorkspaceRoot $WorkspaceRoot
if ($LASTEXITCODE -ne 0) { throw 'PRODUCTION_FINAL_DELIVER_ASSERT_FAILED' }

Write-Host 'PRODUCTION_DELIVER_CLOSEOUT: OK' -ForegroundColor Green
exit 0
