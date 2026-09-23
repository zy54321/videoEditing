#Requires -Version 5.1
Set-StrictMode -Version Latest

# Parses explicit structured fallback declarations in Style references:
#   `source.id` → fallback `target.id`
# capability-policy.yaml remains sole fallback authority.

$Script:ReferenceFallbackPattern = '`([a-z][a-z0-9_.]+)`\s*→\s*fallback(?:\s+gain\s+intent\s+via)?\s*`([a-z][a-z0-9_.]+)`'

function Get-ReferenceExplicitFallbacks {
    param([string]$ReferencesDir)

    $declarations = [System.Collections.Generic.List[object]]::new()
    $canonicalRefs = @(
        '01-directing.md', '02-visual-language.md', '03-editing-rhythm.md', '04-typography-graphics.md',
        '05-sound-music.md', '06-color-look-effects.md', '07-taste.md', '08-qa.md'
    )

    foreach ($file in $canonicalRefs) {
        $path = Join-Path $ReferencesDir $file
        if (-not (Test-Path -LiteralPath $path)) { continue }
        $text = [System.IO.File]::ReadAllText($path, (New-Object System.Text.UTF8Encoding $false))
        foreach ($m in [regex]::Matches($text, $Script:ReferenceFallbackPattern)) {
            $declarations.Add([pscustomobject]@{
                    File = $file
                    Source = $m.Groups[1].Value
                    Target = $m.Groups[2].Value
                })
        }
    }
    return $declarations
}

function Test-StyleReferenceCapabilityConsistency {
    param(
        [string]$PolicyPath,
        [string]$ReferencesDir,
        [hashtable]$VocabMap,
        [string]$Label = ''
    )

    $errors = [System.Collections.Generic.List[string]]::new()
    $policyFallbacks = Get-PolicyFallbackMap -PolicyPath $PolicyPath
    $declarations = Get-ReferenceExplicitFallbacks -ReferencesDir $ReferencesDir

    foreach ($decl in $declarations) {
        $tag = "$Label $($decl.File): $($decl.Source) -> $($decl.Target)"

        if (-not $VocabMap.ContainsKey($decl.Source)) {
            $errors.Add("$tag source not in vocabulary")
        }
        if (-not $VocabMap.ContainsKey($decl.Target)) {
            $errors.Add("$tag target not in vocabulary")
        }

        if (-not $policyFallbacks.ContainsKey($decl.Source)) {
            $errors.Add("$tag source has no fallback in capability-policy")
            continue
        }

        $expected = $policyFallbacks[$decl.Source]
        if ($decl.Target -ne $expected) {
            $errors.Add("$tag conflicts with capability-policy (expected $expected)")
        }

        if ($decl.Source -eq 'audio.music.duck' -and $decl.Target -eq 'audio.music.place') {
            $errors.Add("$tag deprecated duck->place mapping must not appear")
        }
    }

    return @{
        Declarations = @($declarations)
        Errors = [string[]]@($errors.ToArray())
    }
}
