#Requires -Version 5.1
<#
.SYNOPSIS
  P0-T02-R4 — F02 canonical text authority mismatch.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$py = Join-Path $PSScriptRoot 'voice_subtitle_r4_f02_check.py'
& python $py
exit $LASTEXITCODE
