#Requires -Version 5.1
<#
.SYNOPSIS
  U2 — Brief → Final Render Contract generation and validation tests.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$Payload = Join-Path $Root 'payload'
$Tools = Join-Path $Payload 'video-workflow\tools'
$Cli = Join-Path $Tools 'build-final-render-contract-from-brief.py'
$Fix = Join-Path $PSScriptRoot 'fixtures\brief-final-render-contract'
$Pass = 0
$Fail = 0

function Assert-True {
    param([bool]$Condition, [string]$Name)
    if ($Condition) { Write-Host "[PASS] $Name" -ForegroundColor Green; $script:Pass++ }
    else { Write-Host "[FAIL] $Name" -ForegroundColor Red; $script:Fail++ }
}

function New-Workspace {
    param([string]$Name)
    $ws = Join-Path $PSScriptRoot ".tmp-u2-$Name"
    if (Test-Path $ws) { Remove-Item -LiteralPath $ws -Recurse -Force }
    $prod = Join-Path $ws 'video-workflow\production'
    $tpl = Join-Path $ws 'video-workflow\templates'
    New-Item -ItemType Directory -Path $prod -Force | Out-Null
    New-Item -ItemType Directory -Path $tpl -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $Payload 'video-workflow\templates\subtitle-external-ass-style-baseline.v1.json') -Destination $tpl
    Copy-Item -LiteralPath (Join-Path $Payload 'video-workflow\templates\subtitle-series-style-registry.v1.json') -Destination $tpl
    Copy-Item -LiteralPath $Tools -Destination (Join-Path $ws 'video-workflow\tools') -Recurse -Force
    return $ws
}

function Invoke-Build {
    param([string]$Ws, [string]$Brief, [switch]$DryRun)
    $args = @($Cli, '--brief', $Brief, '--workspace', $Ws, '--json')
    if (-not $DryRun) { $args += @('--out', (Join-Path $Ws 'video-workflow\production\final-render-contract.json'), '--force') }
    else { $args += '--dry-run' }
    $stdout = (& python @args 2>$null | Out-String).Trim()
    $code = $LASTEXITCODE
    if (-not $stdout) { throw 'Empty stdout from build CLI' }
    $json = $stdout | ConvertFrom-Json
    return @{ Code = $code; Json = $json }
}

Write-Host '=== U2 Brief → Final Render Contract ===' -ForegroundColor Cyan

# T1 Native DRT
$ws = New-Workspace 'native'
$brief = Join-Path $Fix 'native-drt-brief.yaml'
Copy-Item $brief (Join-Path $ws 'video-workflow\production\brief.yaml')
$r = Invoke-Build -Ws $ws -Brief $brief
Assert-True ($r.Code -eq 0) 'T1 native exit 0'
Assert-True ($r.Json.status -eq 'CONTRACT_READY') 'T1 CONTRACT_READY'
Assert-True ($r.Json.final_delivery_gate -eq 'NOT_RUN') 'T1 not final gate pass'
Assert-True ($r.Json.renderer_route -eq 'native_drt') 'T1 native_drt route'
$contractPath = Join-Path $ws 'video-workflow\production\final-render-contract.json'
$c = Get-Content $contractPath -Raw | ConvertFrom-Json
Assert-True ($c.subtitle_materialization -eq 'native_drt_burnin') 'T1 materialization'

# T2 External ASS
$ws2 = New-Workspace 'external'
$brief2 = Join-Path $Fix 'external-ass-brief.yaml'
Copy-Item $brief2 (Join-Path $ws2 'video-workflow\production\brief.yaml')
$r2 = Invoke-Build -Ws $ws2 -Brief $brief2
Assert-True ($r2.Code -eq 0) 'T2 external exit 0'
Assert-True ($r2.Json.renderer_route -eq 'external_ass') 'T2 external_ass route'
Assert-True ($r2.Json.resolved_baseline_id -eq 'astra-external-ass-n02prod-v1') 'T2 baseline id'
$cp2 = Join-Path $ws2 'video-workflow\production\final-render-contract.json'
$c2 = Get-Content $cp2 -Raw | ConvertFrom-Json
Assert-True ($c2.external_ass_style_baseline_id -eq 'astra-external-ass-n02prod-v1') 'T2 baseline persisted in contract'

# T3 Unknown baseline BLOCKED
$ws3 = New-Workspace 'bad-baseline'
$bad = Join-Path $ws3 'video-workflow\production\brief.yaml'
Copy-Item $brief2 $bad
$y = Get-Content $bad -Raw
$y = $y -replace 'astra-external-ass-n02prod-v1', 'no-such-baseline-v99'
Set-Content -LiteralPath $bad -Value $y -Encoding UTF8
$r3 = Invoke-Build -Ws $ws3 -Brief $bad -DryRun
Assert-True ($r3.Code -eq 1) 'T3 unknown baseline exit 1'
Assert-True ($r3.Json.status -eq 'BLOCKED') 'T3 BLOCKED'

# T4 Explicit route not silently replaced (external must stay external)
Assert-True ($r2.Json.renderer_route -eq 'external_ass') 'T4 route preserved external'

# T5 Path mismatch BLOCKED — tamper contract final path vs brief
$ws5 = New-Workspace 'path-mismatch'
Copy-Item $brief (Join-Path $ws5 'video-workflow\production\brief.yaml')
Invoke-Build -Ws $ws5 -Brief $brief | Out-Null
$cp = Join-Path $ws5 'video-workflow\production\final-render-contract.json'
$doc = Get-Content $cp -Raw | ConvertFrom-Json
$doc.final_artifact_path = 'C:\wrong\path.mp4'
$doc | ConvertTo-Json -Depth 6 | Set-Content $cp -Encoding UTF8
$validatePy = @"
import json, sys
from pathlib import Path
sys.path.insert(0, r'$($Tools -replace "'","''")\\lib')
import yaml
from brief_final_render_contract import load_brief_yaml, validate_contract_matches_brief
from final_render_contract import load_final_render_contract
ws = Path(r'$($ws5 -replace "'","''")')
brief = load_brief_yaml(ws / 'video-workflow/production/brief.yaml')
c = load_final_render_contract(ws / 'video-workflow/production/final-render-contract.json')
errs = validate_contract_matches_brief(brief, c, workspace_root=ws, brief_dir=ws/'video-workflow/production')
print(errs)
sys.exit(0 if errs else 1)
"@
$verr = & python -c $validatePy 2>&1 | Select-Object -Last 1
Assert-True ($LASTEXITCODE -eq 0) 'T5 path mismatch detected'
Assert-True ($verr -match 'BRIEF_CONTRACT_FINAL_PATH_MISMATCH') 'T5 mismatch code'

# T6 Legacy script brief (no delivery section)
$ws6 = New-Workspace 'legacy'
$brief6 = Join-Path $Fix 'legacy-script-brief.yaml'
Copy-Item $brief6 (Join-Path $ws6 'video-workflow\production\brief.yaml')
$r6 = Invoke-Build -Ws $ws6 -Brief $brief6 -DryRun
Assert-True ($r6.Code -eq 0) 'T6 legacy exit 0'
Assert-True ($r6.Json.renderer_route -eq 'native_drt') 'T6 legacy defaults native_drt'

# T7 Voice-only INCOMPLETE
$ws7 = New-Workspace 'voice'
$brief7 = Join-Path $Fix 'voice-only-brief.yaml'
Copy-Item $brief7 (Join-Path $ws7 'video-workflow\production\brief.yaml')
$r7 = Invoke-Build -Ws $ws7 -Brief $brief7 -DryRun
Assert-True ($r7.Code -eq 2) 'T7 voice-only exit 2'
Assert-True ($r7.Json.status -eq 'INCOMPLETE') 'T7 INCOMPLETE'

# T8 Deterministic regen
$ws8 = New-Workspace 'deterministic'
Copy-Item $brief (Join-Path $ws8 'video-workflow\production\brief.yaml')
Invoke-Build -Ws $ws8 -Brief $brief | Out-Null
$h1 = (Get-FileHash (Join-Path $ws8 'video-workflow\production\final-render-contract.json') -Algorithm SHA256).Hash
Invoke-Build -Ws $ws8 -Brief $brief | Out-Null
$h2 = (Get-FileHash (Join-Path $ws8 'video-workflow\production\final-render-contract.json') -Algorithm SHA256).Hash
Assert-True ($h1 -eq $h2) 'T8 deterministic SHA256'

# Series ref resolves
$ws9 = New-Workspace 'series'
$seriesBrief = Join-Path $ws9 'video-workflow\production\brief.yaml'
Copy-Item $brief2 $seriesBrief
$sy = Get-Content $seriesBrief -Raw
$sy = $sy -replace 'external_ass_style_baseline_id: astra-external-ass-n02prod-v1', 'external_ass_style_baseline_id: ""'
$sy = $sy -replace 'subtitle_series_style_ref: ""', 'subtitle_series_style_ref: "xinjian-kouwen:ep01_subtitle"'
Set-Content -LiteralPath $seriesBrief -Value $sy -Encoding UTF8
$r9 = Invoke-Build -Ws $ws9 -Brief $seriesBrief -DryRun
Assert-True ($r9.Code -eq 0) 'T9 series ref exit 0'
Assert-True ($r9.Json.resolved_baseline_id -eq 'astra-external-ass-n02prod-v1') 'T9 series ref resolves'

# Unresolved series ref
$ws10 = New-Workspace 'series-bad'
Copy-Item $seriesBrief (Join-Path $ws10 'video-workflow\production\brief.yaml')
$sy2 = Get-Content (Join-Path $ws10 'video-workflow\production\brief.yaml') -Raw
$sy2 = $sy2 -replace 'xinjian-kouwen:ep01_subtitle', '沿用上集字幕'
Set-Content -LiteralPath (Join-Path $ws10 'video-workflow\production\brief.yaml') -Value $sy2 -Encoding UTF8
$r10 = Invoke-Build -Ws $ws10 -Brief (Join-Path $ws10 'video-workflow\production\brief.yaml') -DryRun
Assert-True ($r10.Code -eq 1) 'T10 NL series ref BLOCKED'
Assert-True ($r10.Json.status -eq 'BLOCKED') 'T10 BLOCKED status'

# T11 Voice + subtitles false → CONTRACT_READY (R2-03)
$ws11 = New-Workspace 'voice-nosub'
$brief11 = Join-Path $Fix 'voice-no-subtitles-brief.yaml'
Copy-Item $brief11 (Join-Path $ws11 'video-workflow\production\brief.yaml')
$r11 = Invoke-Build -Ws $ws11 -Brief $brief11
Assert-True ($r11.Code -eq 0) 'T11 voice no subtitles exit 0'
Assert-True ($r11.Json.status -eq 'CONTRACT_READY') 'T11 CONTRACT_READY'
$c11 = Get-Content (Join-Path $ws11 'video-workflow\production\final-render-contract.json') -Raw | ConvertFrom-Json
Assert-True ($c11.subtitle_materialization -eq 'na') 'T11 subtitle na'

# T12 Preparation invoke PASS
$prep = Join-Path $Tools 'invoke-production-preparation-contract.ps1'
& $prep -WorkspaceRoot $ws
Assert-True ($LASTEXITCODE -eq 0) 'T12 preparation contract PASS'
$pr = Get-Content (Join-Path $ws 'video-workflow\production\preparation-contract-result.json') -Raw | ConvertFrom-Json
Assert-True ($pr.render_preparation_contract -eq 'PASS') 'T12 render_prep PASS'
Assert-True ($pr.final_delivery_gate_status -eq 'NOT_RUN') 'T12 final gate not run'

# T13 assert-render-preparation-contract
$assertPrep = Join-Path $Tools 'assert-render-preparation-contract.ps1'
& $assertPrep -WorkspaceRoot $ws
Assert-True ($LASTEXITCODE -eq 0) 'T13 assert render prep PASS'

# T14 assert blocked without preparation result
$ws14 = New-Workspace 'no-prep'
Copy-Item $brief (Join-Path $ws14 'video-workflow\production\brief.yaml')
& $assertPrep -WorkspaceRoot $ws14 2>$null | Out-Null
Assert-True ($LASTEXITCODE -eq 4) 'T14 assert blocked without prep result'

# T15 voice subtitle pending → preparation PENDING exit 2
$ws15 = New-Workspace 'voice-prep'
Copy-Item $brief7 (Join-Path $ws15 'video-workflow\production\brief.yaml')
& $prep -WorkspaceRoot $ws15 2>$null | Out-Null
Assert-True ($LASTEXITCODE -eq 2) 'T15 voice prep PENDING exit 2'
$pr15 = Get-Content (Join-Path $ws15 'video-workflow\production\preparation-contract-result.json') -Raw | ConvertFrom-Json
Assert-True ($pr15.render_preparation_contract -eq 'PENDING') 'T15 render_prep PENDING'

# T16 blocked baseline → preparation exit 1
& $prep -WorkspaceRoot $ws3 -NoWrite 2>$null | Out-Null
Assert-True ($LASTEXITCODE -eq 1) 'T16 blocked prep exit 1'

# T17 series ref stored on contract
Invoke-Build -Ws $ws9 -Brief $seriesBrief | Out-Null
$c9 = Get-Content (Join-Path $ws9 'video-workflow\production\final-render-contract.json') -Raw | ConvertFrom-Json
Assert-True ($c9.subtitle_series_style_ref -eq 'xinjian-kouwen:ep01_subtitle') 'T17 series ref on contract'

Get-ChildItem (Join-Path $PSScriptRoot '.tmp-u2-*') -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed"
if ($Fail -gt 0) { exit 1 }
exit 0
