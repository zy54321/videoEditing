#Requires -Version 5.1
<#
.SYNOPSIS
  P0-T02 F06 — cue text and lines consistency.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
& python (Join-Path $PSScriptRoot 'voice_subtitle_f06_check.py')
exit $LASTEXITCODE
