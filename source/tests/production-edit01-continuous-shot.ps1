#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
& python (Join-Path $PSScriptRoot 'edit01_continuous_shot_check.py')
exit $LASTEXITCODE
