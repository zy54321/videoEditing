#Requires -Version 5.1
Set-StrictMode -Version Latest

$Script:EffectPreservationAllowed = @('full', 'high', 'partial', 'low', 'none')
$Script:DegradationLevelAllowed = @('low', 'medium', 'high')
$Script:UnsafeFallbackTargets = @('UNSAFE', 'FAILED', 'UNKNOWN', 'DEFERRED', 'AVAILABLE_UNVERIFIED')

function Get-VocabularyStatusMap {
    param([string]$VocabPath)

    $text = [System.IO.File]::ReadAllText($VocabPath, (New-Object System.Text.UTF8Encoding $false))
    $map = @{}
    foreach ($m in [regex]::Matches($text, '(?m)^  ([a-z][a-z0-9_.]+):\s*\r?\n    status: ([A-Z_]+)')) {
        $map[$m.Groups[1].Value] = $m.Groups[2].Value
    }
    return $map
}

function Get-FallbackEntries {
    param([string]$PolicyText)

    $entries = [System.Collections.Generic.List[object]]::new()
    $fallbackBlocks = [regex]::Matches($PolicyText, '(?ms)^    fallback:\s*\r?\n(.*?)(?=^    (?:criticality|required|preferred|optional|forbidden):|\z)')

    foreach ($block in $fallbackBlocks) {
        $body = $block.Groups[1].Value
        $sourceMatches = [regex]::Matches($body, '(?ms)^      ([a-z][a-z0-9_.]+):\s*\r?\n((?:        - .*\r?\n(?:          .*\r?\n)*)+)')
        foreach ($src in $sourceMatches) {
            $sourceId = $src.Groups[1].Value
            $listBody = $src.Groups[2].Value
            $itemMatches = [regex]::Matches($listBody, '(?ms)^        - target: ([a-z][a-z0-9_.]+)\s*\r?\n((?:          [^\r\n]+\r?\n)+)')
            foreach ($item in $itemMatches) {
                $targetId = $item.Groups[1].Value
                $fields = @{}
                foreach ($line in ($item.Groups[2].Value -split '\r?\n')) {
                    if ($line -match '^\s+(\w+):\s*(.+)$') {
                        $fields[$matches[1]] = $matches[2].Trim()
                    }
                }
                $entries.Add([pscustomobject]@{
                        Source = $sourceId
                        Target = $targetId
                        Fields = $fields
                    })
            }
        }
    }
    return $entries
}

function Test-FallbackContract {
    param(
        [string]$PolicyPath,
        [hashtable]$VocabMap,
        [string]$Label = ''
    )

    $errors = [System.Collections.Generic.List[string]]::new()
    $text = [System.IO.File]::ReadAllText($PolicyPath, (New-Object System.Text.UTF8Encoding $false))
    $entries = Get-FallbackEntries -PolicyText $text
    $requiredFields = @('effect_preservation', 'degradation_level', 'style_impact', 'reason')

    foreach ($entry in $entries) {
        $tag = "$Label fallback $($entry.Source) -> $($entry.Target)"

        if ([string]::IsNullOrWhiteSpace($entry.Target)) {
            $errors.Add("$Label fallback $($entry.Source) missing target")
        }

        if (-not $VocabMap.ContainsKey($entry.Source)) {
            $errors.Add("$tag source not in vocabulary: $($entry.Source)")
        }
        if (-not $VocabMap.ContainsKey($entry.Target)) {
            $errors.Add("$tag target not in vocabulary: $($entry.Target)")
        }

        foreach ($field in $requiredFields) {
            if (-not $entry.Fields.ContainsKey($field) -or [string]::IsNullOrWhiteSpace($entry.Fields[$field])) {
                $errors.Add("$tag missing field: $field")
            }
        }

        if ($entry.Fields.ContainsKey('effect_preservation')) {
            if ($Script:EffectPreservationAllowed -notcontains $entry.Fields['effect_preservation']) {
                $errors.Add("$tag illegal effect_preservation: $($entry.Fields['effect_preservation'])")
            }
        }
        if ($entry.Fields.ContainsKey('degradation_level')) {
            if ($Script:DegradationLevelAllowed -notcontains $entry.Fields['degradation_level']) {
                $errors.Add("$tag illegal degradation_level: $($entry.Fields['degradation_level'])")
            }
        }

        if ($VocabMap.ContainsKey($entry.Target)) {
            $targetStatus = $VocabMap[$entry.Target]
            if ($targetStatus -ne 'VERIFIED') {
                $errors.Add("$tag target status not VERIFIED: $targetStatus")
            }
            if ($Script:UnsafeFallbackTargets -contains $targetStatus) {
                $errors.Add("$tag target is production-unsafe: $targetStatus")
            }
        }
    }

    return @{
        Entries = @($entries)
        Errors = [string[]]@($errors.ToArray())
    }
}
