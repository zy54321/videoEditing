#Requires -Version 5.1
<#
.SYNOPSIS
  Validates style-profile.yaml instances against style-profile-schema.yaml (Stage 08D.1).
#>
param(
    [string]$ProfilePath,
    [string]$SchemaPath = '',
    [string]$PayloadRoot = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$TestsRoot = $PSScriptRoot
. (Join-Path $TestsRoot 'lib\style-profile-schema.ps1')

if (-not $PayloadRoot) {
    $PayloadRoot = Join-Path (Split-Path -Parent $TestsRoot) 'payload'
}
if (-not $SchemaPath) {
    $SchemaPath = Join-Path $PayloadRoot 'video-workflow\templates\style-profile-schema.yaml'
}

$schema = Read-StyleProfileSchema -SchemaPath $SchemaPath
$profErrors = @(Test-StyleProfileAgainstSchema -ProfilePath $ProfilePath -Schema $schema -Label $ProfilePath)

if ($profErrors.Count -gt 0) {
    foreach ($e in $profErrors) { Write-Error $e }
    exit 1
}
exit 0
