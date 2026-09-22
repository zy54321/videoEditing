#Requires -Version 5.1
<#
.SYNOPSIS
  Mechanically derives capability coverage from policy + vocabulary (Stage 08D.1).
  Verifies capability-coverage.yaml snapshot when present.
#>
param(
    [string]$StyleId = 'observational-info-short',
    [string]$PayloadRoot = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $PayloadRoot) {
    $PayloadRoot = Join-Path (Split-Path -Parent $PSScriptRoot) 'payload'
}

function Get-VocabularyMap {
    param([string]$VocabPath)
    $text = Get-Content -LiteralPath $VocabPath -Raw -Encoding UTF8
    $map = @{}
    $matches = [regex]::Matches($text, '(?m)^  ([a-z][a-z0-9_.]+):\s*\r?\n    status: ([A-Z_]+)')
    foreach ($m in $matches) { $map[$m.Groups[1].Value] = $m.Groups[2].Value }
    return $map
}

function Get-PolicyIdsByCriticality {
    param([string]$PolicyPath)
    $text = Get-Content -LiteralPath $PolicyPath -Raw -Encoding UTF8
    $result = @{
        REQUIRED = [System.Collections.Generic.HashSet[string]]::new()
        PREFERRED = [System.Collections.Generic.HashSet[string]]::new()
        OPTIONAL = [System.Collections.Generic.HashSet[string]]::new()
    }
    $sections = [regex]::Matches($text, '(?ms)^  \w+:\s*\n(.*?)^    criticality: (REQUIRED|PREFERRED|OPTIONAL)\s*$')
    foreach ($sec in $sections) {
        $body = $sec.Groups[1].Value
        $crit = $sec.Groups[2].Value
        $ids = @()
        $ids += [regex]::Matches($body, '- ([a-z][a-z0-9_]*\.[a-z0-9_.]+)') | ForEach-Object { $_.Groups[1].Value }
        foreach ($listMatch in [regex]::Matches($body, '(?m)(?:required|preferred|optional):\s*\[([^\]]+)\]')) {
            $ids += ($listMatch.Groups[1].Value -split ',\s*') | ForEach-Object { $_.Trim() }
        }
        foreach ($id in $ids) { if ($id) { $result[$crit].Add($id) | Out-Null } }
    }
    return $result
}

function Get-FallbackTargets {
    param([string]$PolicyPath)
    $text = Get-Content -LiteralPath $PolicyPath -Raw -Encoding UTF8
    $map = @{}
    $entries = [regex]::Matches($text, '(?ms)      ([a-z][a-z0-9_.]+):\s*\n        - target: ([a-z][a-z0-9_.]+)')
    foreach ($e in $entries) { $map[$e.Groups[1].Value] = $e.Groups[2].Value }
    return $map
}

function Test-FallbackContractOk {
    param([string]$PolicyPath, [string]$VocabPath)
    $helper = Join-Path $PSScriptRoot 'validate-capability-fallbacks.ps1'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $helper -PolicyPath $PolicyPath -VocabPath $VocabPath | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Compute-CoverageStats {
    param($IdsByCrit, $VocabMap, $FallbackMap)
    $stats = @{}
    foreach ($crit in @('REQUIRED','PREFERRED','OPTIONAL')) {
        $ids = @($IdsByCrit[$crit])
        $verified = 0
        $fallbackCapable = 0
        $unresolved = 0
        foreach ($id in $ids) {
            $st = $VocabMap[$id]
            if (-not $st) { $unresolved++; continue }
            if ($st -eq 'VERIFIED') { $verified++ }
            elseif ($st -eq 'AVAILABLE_UNVERIFIED' -or $st -eq 'UNKNOWN') {
                $fb = $FallbackMap[$id]
                if ($fb -and $VocabMap[$fb] -eq 'VERIFIED') { $fallbackCapable++ }
                else { $unresolved++ }
            }
            else { $unresolved++ }
        }
        $key = $crit.ToLower()
        $stats[$key] = @{
            total = $ids.Count
            verified = $verified
            fallback_capable = $fallbackCapable
            unresolved = $unresolved
        }
    }
    return $stats
}

$vocabPath = Join-Path $PayloadRoot 'video-workflow\capabilities\logical-capability-vocabulary.yaml'
$policyPath = Join-Path $PayloadRoot ".cursor\skills\video-editing\$StyleId\capability-policy.yaml"
$coveragePath = Join-Path $PayloadRoot ".cursor\skills\video-editing\$StyleId\capability-coverage.yaml"

$vocabMap = Get-VocabularyMap -VocabPath $vocabPath
$idsByCrit = Get-PolicyIdsByCriticality -PolicyPath $policyPath
$fallbackMap = Get-FallbackTargets -PolicyPath $policyPath
$stats = Compute-CoverageStats -IdsByCrit $idsByCrit -VocabMap $vocabMap -FallbackMap $fallbackMap

if (-not (Test-FallbackContractOk -PolicyPath $policyPath -VocabPath $vocabPath)) {
    Write-Error 'Policy fallback contract validation failed'
    exit 1
}

if (Test-Path -LiteralPath $coveragePath) {
    $snap = Get-Content -LiteralPath $coveragePath -Raw -Encoding UTF8
    $checks = @(
        @{ k = 'required'; field = 'total'; val = $stats.required.total },
        @{ k = 'required'; field = 'verified'; val = $stats.required.verified },
        @{ k = 'required'; field = 'unresolved'; val = $stats.required.unresolved },
        @{ k = 'preferred'; field = 'total'; val = $stats.preferred.total },
        @{ k = 'preferred'; field = 'verified'; val = $stats.preferred.verified },
        @{ k = 'preferred'; field = 'fallback_capable'; val = $stats.preferred.fallback_capable },
        @{ k = 'preferred'; field = 'unresolved'; val = $stats.preferred.unresolved },
        @{ k = 'optional'; field = 'total'; val = $stats.optional.total },
        @{ k = 'optional'; field = 'verified'; val = $stats.optional.verified }
    )
    foreach ($c in $checks) {
        if ($snap -notmatch "(?m)^  $($c.field):\s*$($c.val)\s*$") {
            # allow nested under crit section
            $sectionPattern = "$($c.k):[\s\S]*?$($c.field):\s*$($c.val)"
            if ($snap -notmatch $sectionPattern) {
                Write-Error "Coverage snapshot stale: $($c.k).$($c.field) expected $($c.val) got check failed"
                exit 1
            }
        }
    }
}

Write-Output ($stats | ConvertTo-Json -Depth 4)
exit 0
