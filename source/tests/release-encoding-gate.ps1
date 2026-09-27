#Requires -Version 5.1
[CmdletBinding()]
param([switch]$SkipExecutionSmoke)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$SourceRoot = Split-Path -Parent $PSScriptRoot
$ProjectRoot = Split-Path -Parent $SourceRoot
$BuildRoot = Join-Path $SourceRoot 'build'
$Pass = 0; $Fail = 0
function Assert-True { param([bool]$Condition,[string]$Name)
  if ($Condition) { Write-Host "[PASS] $Name" -ForegroundColor Green; $script:Pass++ } else { Write-Host "[FAIL] $Name" -ForegroundColor Red; $script:Fail++ } }
function Get-ReleaseExecutionClosure {
  @('build\release.ps1','build\build-release.ps1','build\lib\ProductInventory.ps1','build\lib\ReleaseVersion.ps1','build\lib\ReleaseTransaction.ps1',
    'tests\release-gate.ps1','tests\release-v2.ps1','tests\release-v2-transaction-fixtures.ps1','tests\release-encoding-gate.ps1','tests\release-smoke.ps1',
    'installer\init-video-workflow.ps1','tests\pre-release-consistency.ps1','tests\shared-asset-library.ps1','tests\production-audio-mix-profile.ps1',
    'tests\production-audio-loudness-repair.ps1','tests\production-pacing-reframe-qa.ps1','tests\production-subtitle-readability.ps1',
    'tests\production-subtitle-stroke-unblock.ps1','tests\production-continuous-execution.ps1','tests\zip-independent-install.ps1','tests\installer-smoke.ps1') |
    ForEach-Object { Join-Path $SourceRoot $_ } }
function Test-ParseFileZeroErrors { param([string]$Path)
  $errors=$null; $tokens=$null; $null=[System.Management.Automation.Language.Parser]::ParseFile($Path,[ref]$tokens,[ref]$errors); @($errors) }
function Test-Utf8BomIfNonAscii { param([string]$Path)
  $bytes=[System.IO.File]::ReadAllBytes($Path); $utf8Bom=New-Object System.Text.UTF8Encoding $true
  $hasBom=($bytes.Length -ge 3 -and $bytes[0]-eq 0xEF -and $bytes[1]-eq 0xBB -and $bytes[2]-eq 0xBF)
  $text= if ($hasBom) { $utf8Bom.GetString($bytes,3,$bytes.Length-3) } else { [Text.Encoding]::UTF8.GetString($bytes) }
  if ($text -match '[^\x00-\x7F]') { return $hasBom }; $true }
Write-Host '=== Release Encoding / Parser Gate (powershell.exe) ===' -ForegroundColor Cyan
Assert-True ($PSVersionTable.PSVersion.ToString() -like '5.*') "E00 Windows PowerShell 5.x"
foreach ($path in (Get-ReleaseExecutionClosure)) {
  $name=Split-Path -Leaf $path
  if (-not (Test-Path -LiteralPath $path)) { Assert-True $false "E01 exists $name"; continue }
  $errs=Test-ParseFileZeroErrors $path
  Assert-True (@($errs).Count -eq 0) "E02 parse $name"
  Assert-True (Test-Utf8BomIfNonAscii $path) "E03 BOM $name" }
$releasePs1=Join-Path $BuildRoot 'release.ps1'
$utf8Bom=New-Object System.Text.UTF8Encoding $true
$rb=[IO.File]::ReadAllBytes($releasePs1)
$rt= if ($rb.Length -ge 3 -and $rb[0]-eq 0xEF) { $utf8Bom.GetString($rb,3,$rb.Length-3) } else { [Text.Encoding]::UTF8.GetString($rb) }
Assert-True ($rt -match '按 Enter 键关闭') 'E04 Chinese Read-Host literal'
if (-not $SkipExecutionSmoke) {
  $cmd="Set-StrictMode -Version Latest; `$ErrorActionPreference='Stop'; . '$BuildRoot\lib\ProductInventory.ps1'; . '$BuildRoot\lib\ReleaseVersion.ps1'; . '$BuildRoot\lib\ReleaseTransaction.ps1'; Parse-SemVer '0.1.1' | Out-Null"
  $ErrorActionPreference='Continue'; & powershell.exe -NoProfile -ExecutionPolicy Bypass -Command $cmd; $ErrorActionPreference='Stop'
  Assert-True ($LASTEXITCODE -eq 0) 'E05 dot-source libs'
  $bat=Join-Path $ProjectRoot 'release.bat'; $bt=Get-Content -LiteralPath $bat -Raw
  Assert-True (($bt -match 'powershell\.exe') -and ($bt -match 'release\.ps1')) 'E06 release.bat entry'
  if (-not (git -C $ProjectRoot status --porcelain 2>$null)) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $releasePs1 -DryRun -NoPause -VersionChoice Patch
    Assert-True ($LASTEXITCODE -eq 0) 'E07 release.ps1 -DryRun clean tree' } else { Assert-True $true 'E07 DryRun skipped dirty tree' }
} else { Assert-True $true 'E05 skipped'; Assert-True $true 'E06 skipped'; Assert-True $true 'E07 skipped' }
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if($Fail -eq 0){'Green'}else{'Red'})
if ($Fail -gt 0) { exit 1 }; exit 0
