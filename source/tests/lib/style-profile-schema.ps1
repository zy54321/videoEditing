#Requires -Version 5.1
Set-StrictMode -Version Latest

function Read-StyleProfileSchema {
    param([string]$SchemaPath)

    $text = [System.IO.File]::ReadAllText($SchemaPath, (New-Object System.Text.UTF8Encoding $false))

    # required_top_level is first list block; identity_required is second
    $topBlock = [regex]::Match($text, '(?ms)required_top_level:\s*\r?\n((?:  - [^\r\n]+\r?\n)+?)(?=\r?\n\S)')
    $idBlock = [regex]::Match($text, '(?ms)identity_required:\s*\r?\n((?:  - [^\r\n]+\r?\n)+?)(?=\r?\n\S)')
    $requiredTop = [regex]::Matches($topBlock.Groups[1].Value, '(?m)^  - ([a-z_]+)') | ForEach-Object { $_.Groups[1].Value }
    $identityRequired = [regex]::Matches($idBlock.Groups[1].Value, '(?m)^  - ([a-z_]+)') | ForEach-Object { $_.Groups[1].Value }

    $intensityScale = [regex]::Matches($text, '(?ms)intensity_scale:.*?\n((?:  - .+\n)+)') |
        Select-Object -First 1 |
        ForEach-Object { [regex]::Matches($_.Groups[1].Value, '(?m)^  - ([^\n]+)') | ForEach-Object { $_.Groups[1].Value.Trim() } }

    $psychMatch = [regex]::Match($text, 'psychological_distance:\s*\r?\n    type: semantic\s*\r?\n    allowed:\s*\[([^\]]+)\]')
    $psychAllowed = @($psychMatch.Groups[1].Value -split ',\s*' | ForEach-Object { $_.Trim() })

    $tasteFields = @{}
    foreach ($m in [regex]::Matches($text, '(?m)^  (\w+):\s*\{ type: intensity')) {
        $tasteFields[$m.Groups[1].Value] = 'intensity'
    }
    if ($psychMatch.Success) { $tasteFields['psychological_distance'] = 'semantic' }

    $axesMatch = [regex]::Match($text, 'taste_axes_strength_allowed:\s*\[([^\]]+)\]')
    $axesStrength = @($axesMatch.Groups[1].Value -split ',\s*' | ForEach-Object { $_.Trim() })

    return @{
        RequiredTopLevel = $requiredTop
        IdentityRequired = $identityRequired
        IntensityScale = @($intensityScale)
        PsychologicalDistanceAllowed = $psychAllowed
        TasteProfileFields = $tasteFields
        TasteAxesStrengthAllowed = $axesStrength
    }
}

function Get-YamlSectionKeys {
    param([string]$Text, [string]$SectionName)

    $match = [regex]::Match($Text, "(?ms)^${SectionName}:\s*\r?\n((?:  [^\n]+\n)+)")
    if (-not $match.Success) { return @{} }

    $map = @{}
    foreach ($line in ($match.Groups[1].Value -split '\r?\n')) {
        if ($line -match '^  (\w+):\s*(.*)$') {
            $map[$matches[1]] = $matches[2].Trim()
        }
    }
    return $map
}

function Get-YamlTopLevelKeys {
    param([string]$Text)

    $keys = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($line in ($Text -split '\r?\n')) {
        if ($line -match '^([a-z_]+):\s*') { $keys.Add($matches[1]) | Out-Null }
    }
    return $keys
}

function Test-StyleProfileAgainstSchema {
    param(
        [string]$ProfilePath,
        [hashtable]$Schema,
        [string]$Label = ''
    )

    $errors = [System.Collections.Generic.List[string]]::new()
    $text = [System.IO.File]::ReadAllText($ProfilePath, (New-Object System.Text.UTF8Encoding $false))
    $topKeys = Get-YamlTopLevelKeys -Text $text

    foreach ($req in $Schema.RequiredTopLevel) {
        if (-not $topKeys.Contains($req)) {
            $errors.Add("$Label missing required top-level field: $req")
        }
    }

    $identity = Get-YamlSectionKeys -Text $text -SectionName 'identity'
    foreach ($req in $Schema.IdentityRequired) {
        if (-not $identity.ContainsKey($req) -or [string]::IsNullOrWhiteSpace($identity[$req])) {
            $errors.Add("$Label identity missing or empty: $req")
        }
    }

    $taste = Get-YamlSectionKeys -Text $text -SectionName 'taste_profile'
    foreach ($field in $Schema.TasteProfileFields.Keys) {
        if (-not $taste.ContainsKey($field)) {
            $errors.Add("$Label taste_profile missing field: $field")
            continue
        }
        $val = $taste[$field]
        $ftype = $Schema.TasteProfileFields[$field]
        if ($ftype -eq 'intensity') {
            if ($Schema.IntensityScale -notcontains $val) {
                $errors.Add("$Label taste_profile.$field illegal intensity value: $val")
            }
        }
        elseif ($ftype -eq 'semantic') {
            if ($Schema.PsychologicalDistanceAllowed -notcontains $val) {
                $errors.Add("$Label taste_profile.$field illegal semantic value: $val")
            }
        }
    }

    foreach ($key in $taste.Keys) {
        if (-not $Schema.TasteProfileFields.ContainsKey($key)) {
            $errors.Add("$Label taste_profile undeclared field: $key")
        }
    }

    if ($text -match '(?m)^taste_axes:\s*\r?\n') {
        $axes = Get-YamlSectionKeys -Text $text -SectionName 'taste_axes'
        foreach ($axis in $axes.Keys) {
            $strength = $axes[$axis]
            if ($Schema.TasteAxesStrengthAllowed -notcontains $strength) {
                $errors.Add("$Label taste_axes.$axis illegal strength: $strength")
            }
        }
    }

    return [string[]]@($errors.ToArray())
}
