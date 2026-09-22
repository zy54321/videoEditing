#Requires -Version 5.1
<#
.SYNOPSIS
  Per-entry fallback contract validation (Stage 08D.1).
#>
param(
    [string]$PolicyPath,
    [string]$VocabPath = '',
    [string]$PayloadRoot = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$TestsRoot = $PSScriptRoot
. (Join-Path $TestsRoot 'lib\capability-fallback-contract.ps1')

if (-not $PayloadRoot) {
    $PayloadRoot = Join-Path (Split-Path -Parent $TestsRoot) 'payload'
}
if (-not $VocabPath) {
    $VocabPath = Join-Path $PayloadRoot 'video-workflow\capabilities\logical-capability-vocabulary.yaml'
}

$vocabMap = Get-VocabularyStatusMap -VocabPath $VocabPath
$fbResult = Test-FallbackContract -PolicyPath $PolicyPath -VocabMap $vocabMap -Label $PolicyPath
$fbErrors = @($fbResult.Errors)

if ($fbErrors.Count -gt 0) {
    foreach ($e in $fbErrors) { Write-Error $e }
    exit 1
}
exit 0
