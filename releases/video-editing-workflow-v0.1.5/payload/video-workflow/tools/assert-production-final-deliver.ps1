#Requires -Version 5.1
<#
.SYNOPSIS
  Fail-closed — Production Complete requires FINAL_ARTIFACT_GATE PASS + SHA256 bindings.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspaceRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$WorkspaceRoot = [System.IO.Path]::GetFullPath($WorkspaceRoot)
$verifyPy = Join-Path $WorkspaceRoot 'video-workflow\tools\verify-production-final-deliver.py'
if (-not (Test-Path -LiteralPath $verifyPy)) {
    Write-Host 'PRODUCTION_COMPLETE_BLOCKED: verify-production-final-deliver.py missing' -ForegroundColor Red
    exit 4
}

& python $verifyPy --workspace $WorkspaceRoot
exit $LASTEXITCODE
