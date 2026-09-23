#Requires -Version 5.1
<#
.SYNOPSIS
  Stage 08E-B BR1 — Windows / System.Drawing font authority audit.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Drawing

$fontsDir = Join-Path $env:WINDIR 'Fonts'
Write-Output "=== WINDOWS FONTS DIRECTORY ==="
Write-Output "Path: $fontsDir"

$yaheiPatterns = @('*yahei*', '*msyh*', '*simsun*', '*simhei*', '*mingliu*')
foreach ($pat in $yaheiPatterns) {
    $hits = Get-ChildItem -LiteralPath $fontsDir -Filter $pat -ErrorAction SilentlyContinue
    if ($hits) {
        Write-Output "-- pattern $pat --"
        $hits | ForEach-Object { Write-Output $_.Name }
    }
}

Write-Output ""
Write-Output "=== REGISTRY FONT FAMILIES (sample CJK-related) ==="
$regPaths = @(
    'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts'
)
foreach ($rp in $regPaths) {
    if (-not (Test-Path $rp)) { continue }
    Get-ItemProperty $rp | Get-Member -MemberType NoteProperty |
        Where-Object { $_.Name -notmatch '^PS' } |
        ForEach-Object {
            $name = $_.Name
            $file = (Get-ItemProperty $rp).$name
            if ($name -match 'YaHei|SimSun|SimHei|MingLi|Arial|Segoe|微软|宋体|雅黑') {
                Write-Output "$name => $file"
            }
        }
}

Write-Output ""
Write-Output "=== SYSTEM.DRAWING FONTFAMILY ENUMERATION (CJK + common) ==="
$drawFamilies = [System.Drawing.FontFamily]::Families | ForEach-Object { $_.Name }
$candidates = @(
    'Microsoft YaHei', 'Microsoft YaHei UI', '微软雅黑',
    'SimSun', '宋体', 'NSimSun', '新宋体',
    'SimHei', '黑体',
    'Malgun Gothic', 'Arial', 'Segoe UI', 'Tahoma', 'Times New Roman'
)
foreach ($c in $candidates) {
    $found = $drawFamilies -contains $c
    Write-Output "candidate='$c' enumerated=$found"
}

Write-Output ""
Write-Output "=== SYSTEM.DRAWING INSTANTIATION PROBE ==="
function Test-FontInstantiate {
    param([string]$Family, [string]$Style = 'Regular')
    try {
        $ff = New-Object System.Drawing.FontFamily($Family)
        $fs = [System.Drawing.FontStyle]::Regular
        switch ($Style) {
            'Bold' { $fs = [System.Drawing.FontStyle]::Bold }
            'Italic' { $fs = [System.Drawing.FontStyle]::Italic }
        }
        if (-not $ff.IsStyleAvailable($fs)) {
            return "NO_STYLE:$Style"
        }
        $font = New-Object System.Drawing.Font($ff, 48, $fs, [System.Drawing.GraphicsUnit]::Pixel)
        $font.Dispose()
        $ff.Dispose()
        return 'OK'
    }
    catch {
        return "FAIL:$($_.Exception.Message)"
    }
}

foreach ($c in $candidates) {
    if ($drawFamilies -contains $c) {
        Write-Output "instantiate '$c' Regular => $(Test-FontInstantiate -Family $c)"
    }
}

Write-Output ""
Write-Output "=== TOTAL SYSTEM.DRAWING FAMILIES: $($drawFamilies.Count) ==="
