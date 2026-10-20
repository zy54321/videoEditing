# R3 — static portrait reframe runtime (zoom-only cover)
$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Payload = Join-Path $RepoRoot 'payload'
$Tools = Join-Path $Payload 'video-workflow\tools'
$Lib = Join-Path $Tools 'lib'

function Assert-True($cond, $msg) {
    if (-not $cond) { throw "ASSERT_FAIL: $msg" }
}

$py = Join-Path $Lib 'static_portrait_reframe.py'
Assert-True (Test-Path $py) 'static_portrait_reframe.py exists'

$probeFixture = @{
    name = 'fixture-tl'
    tracks = @{
        video = @{
            tracks = @(
                @{
                    items = @(
                        @{
                            timeline_item_id = 'tid-1'
                            name = 'SRC01'
                            file_path = (Join-Path $PSScriptRoot 'fixtures\pacing-reframe\case-c-reframed.png')
                            item_index = 0
                        }
                    )
                }
            )
        }
    }
}

# Use ffprobe-friendly small video from fixtures if present; fallback pure contract math
$contractPy = @"
import json, sys
sys.path.insert(0, r'$Lib')
from static_portrait_reframe import reframe_op_for_item, neutral_crop, POLICY_VERSION, ROUTE_ID
op = reframe_op_for_item(timeline_item_id='x', source_w=1760, source_h=974, shot_id='SRC01')
assert op['transform']['ZoomX'] == op['transform']['ZoomY']
assert op['crop']['CropLeft'] == 0 and op['crop']['CropRight'] == 0
assert abs(op['transform']['ZoomX'] - 3.2124) < 0.001
assert op['visual_reframe_route'] == ROUTE_ID
print(POLICY_VERSION)
"@

$out = python -c $contractPy 2>&1
if ($LASTEXITCODE -ne 0) { throw "static_portrait_reframe contract test failed: $out" }
Assert-True ($out -match 'static-portrait-reframe.v1') 'policy id'

$cli = Join-Path $Tools 'build-static-portrait-reframe-plan.py'
Assert-True (Test-Path $cli) 'build-static-portrait-reframe-plan.py exists'

Write-Host 'production-r3-static-portrait-reframe: PASS'
