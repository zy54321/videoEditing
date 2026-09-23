#Requires -Version 5.1
<#
.SYNOPSIS
  Validates explicit Style Reference fallback declarations against capability-policy authority.
#>
param(
    [string]$StyleId = 'observational-info-short',
    [string]$PayloadRoot = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$TestsRoot = $PSScriptRoot
. (Join-Path $TestsRoot 'lib\capability-fallback-contract.ps1')
. (Join-Path $TestsRoot 'lib\style-reference-capability-consistency.ps1')

if (-not $PayloadRoot) {
    $PayloadRoot = Join-Path (Split-Path -Parent $TestsRoot) 'payload'
}

$policyPath = Join-Path $PayloadRoot ".cursor\skills\video-editing\$StyleId\capability-policy.yaml"
$refsDir = Join-Path $PayloadRoot ".cursor\skills\video-editing\$StyleId\references"
$vocabPath = Join-Path $PayloadRoot 'video-workflow\capabilities\logical-capability-vocabulary.yaml'
$vocabMap = Get-VocabularyStatusMap -VocabPath $vocabPath

$result = Test-StyleReferenceCapabilityConsistency -PolicyPath $policyPath -ReferencesDir $refsDir -VocabMap $vocabMap -Label $StyleId

if ($result.Errors.Count -gt 0) {
    foreach ($e in $result.Errors) { Write-Error $e }
    exit 1
}
exit 0
