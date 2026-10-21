#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
& python (Join-Path $PSScriptRoot 'vid01_timing_check.py')
exit $LASTEXITCODE
