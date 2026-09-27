#Requires -Version 5.1
Set-StrictMode -Version Latest

function Parse-SemVer {
    param([string]$Version)
    if ($Version -match '^(\d+)\.(\d+)\.(\d+)(?:-dev)?$') {
        $maj = [int]$Matches[1]
        $min = [int]$Matches[2]
        $pat = [int]$Matches[3]
        $isDev = $Version.EndsWith('-dev', [StringComparison]::Ordinal)
        return [PSCustomObject]@{
            Major = $maj
            Minor = $min
            Patch = $pat
            IsDev = $isDev
            Normalized = "$maj.$min.$pat"
        }
    }
    throw "Invalid SemVer: $Version"
}

function Format-SemVer {
    param([int]$Major, [int]$Minor, [int]$Patch)
    return "$Major.$Minor.$Patch"
}

function Compare-SemVer {
    param([string]$A, [string]$B)
    $va = Parse-SemVer $A
    $vb = Parse-SemVer $B
    if ($va.Major -ne $vb.Major) { return [Math]::Sign($va.Major - $vb.Major) }
    if ($va.Minor -ne $vb.Minor) { return [Math]::Sign($va.Minor - $vb.Minor) }
    return [Math]::Sign($va.Patch - $vb.Patch)
}

function Get-GitReleaseTags {
    param([string]$ProjectRoot)
    $raw = git -C $ProjectRoot tag --list 'v*' 2>$null
    if (-not $raw) { return @() }
    $tags = @($raw -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    $versions = @()
    foreach ($t in $tags) {
        if ($t -notmatch '^v(\d+\.\d+\.\d+)$') { continue }
        $versions += $Matches[1]
    }
    return $versions
}

function Get-LatestReleaseTagVersion {
    param([string]$ProjectRoot)
    $all = Get-GitReleaseTags -ProjectRoot $ProjectRoot
    if (-not $all -or $all.Count -eq 0) { return '0.0.0' }
    $latest = $all[0]
    foreach ($v in $all) {
        if ((Compare-SemVer $v $latest) -gt 0) { $latest = $v }
    }
    return $latest
}

function Test-GitTagExists {
    param([string]$ProjectRoot, [string]$Version)
    $tag = "v$Version"
    $out = git -C $ProjectRoot rev-parse -q --verify "refs/tags/$tag" 2>$null
    return [bool]$out
}

function Get-ReleaseVersionCandidates {
    param(
        [string]$ProjectRoot,
        [string]$CurrentVersion
    )
    $cur = Parse-SemVer $CurrentVersion
    $latest = Get-LatestReleaseTagVersion -ProjectRoot $ProjectRoot

    $patch = $null
    if ($cur.IsDev -and -not (Test-GitTagExists -ProjectRoot $ProjectRoot -Version $cur.Normalized)) {
        if ((Compare-SemVer $cur.Normalized $latest) -ge 0) {
            $patch = $cur.Normalized
        }
    }
    if (-not $patch) {
        $lv = Parse-SemVer $latest
        $patch = Format-SemVer -Major $lv.Major -Minor $lv.Minor -Patch ($lv.Patch + 1)
    }

    $lv = Parse-SemVer $latest
    $fromMinor = if ($cur.IsDev) { Parse-SemVer $cur.Normalized } else { $lv }
    $minor = Format-SemVer -Major $fromMinor.Major -Minor ($fromMinor.Minor + 1) -Patch 0
    $major = Format-SemVer -Major ($fromMinor.Major + 1) -Minor 0 -Patch 0

    return [PSCustomObject]@{
        Current = $CurrentVersion
        LatestRelease = $latest
        Patch = $patch
        Minor = $minor
        Major = $major
    }
}

function Assert-ReleaseVersionValid {
    param(
        [string]$ProjectRoot,
        [string]$Version
    )
    Parse-SemVer $Version | Out-Null
    if (Test-GitTagExists -ProjectRoot $ProjectRoot -Version $Version) {
        throw "RELEASE_VERSION_IMMUTABLE: tag v$Version already exists"
    }
    $latest = Get-LatestReleaseTagVersion -ProjectRoot $ProjectRoot
    if ((Compare-SemVer $Version $latest) -le 0) {
        throw "Release version $Version must be greater than latest release v$latest"
    }
}
