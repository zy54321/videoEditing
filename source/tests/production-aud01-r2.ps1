#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
& python (Join-Path $PSScriptRoot 'aud01_r2_integration_check.py')
exit $LASTEXITCODE
