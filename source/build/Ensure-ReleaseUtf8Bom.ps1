#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$SourceRoot = Split-Path -Parent $PSScriptRoot
$relative = @(
    'build\release.ps1','build\build-release.ps1','build\lib\ProductInventory.ps1','build\lib\ReleaseTransaction.ps1',
    'tests\release-v2.ps1','tests\release-v2-transaction-fixtures.ps1','tests\release-encoding-gate.ps1','tests\release-smoke.ps1',
    'installer\init-video-workflow.ps1','tests\pre-release-consistency.ps1','tests\shared-asset-library.ps1',
    'tests\production-audio-mix-profile.ps1','tests\production-audio-loudness-repair.ps1','tests\production-pacing-reframe-qa.ps1',
    'tests\production-subtitle-readability.ps1','tests\production-subtitle-stroke-unblock.ps1','tests\production-continuous-execution.ps1'
)
$utf8Bom = New-Object System.Text.UTF8Encoding $true
foreach ($rel in $relative) {
    $p = Join-Path $SourceRoot $rel
    if (-not (Test-Path -LiteralPath $p)) { Write-Host "MISSING $rel"; continue }
    $bytes = [System.IO.File]::ReadAllBytes($p)
    $hasBom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
    $text = if ($hasBom) { $utf8Bom.GetString($bytes, 3, $bytes.Length - 3) } else { [System.Text.Encoding]::UTF8.GetString($bytes) }
    if ($text -match '[^\x00-\x7F]') { [System.IO.File]::WriteAllText($p, $text, $utf8Bom); Write-Host "BOM $rel" }
}
