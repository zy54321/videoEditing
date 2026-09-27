#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$py = Join-Path $root 'validation\scripts\subtitle-route-fixture-experiment.py'
$json = Join-Path $root 'validation\subtitle-route-fixture-results.json'
python $py
if (-not (Test-Path -LiteralPath $json)) { throw "MISSING: $json" }
$data = Get-Content -LiteralPath $json -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $data.route_d_external_ass.burnin.ok) { throw 'ROUTE_D_FIXTURE_FAILED' }
Write-Output 'SUBTITLE_ROUTE_FIXTURE: PASS'
