#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$testPy = Join-Path $PSScriptRoot 'textplus_cls_setting_tests.py'

python $testPy
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
Write-Host 'textplus-cls-setting.ps1 ALL PASS'
exit 0
