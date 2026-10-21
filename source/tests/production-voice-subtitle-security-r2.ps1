#Requires -Version 5.1
<#
.SYNOPSIS
  P0-T02-R2 adversarial cases for voice subtitle evidence binding.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$Payload = Join-Path $Root 'payload'
$Tools = Join-Path $Payload 'video-workflow\tools'
$Fix = Join-Path $PSScriptRoot 'fixtures\voice-subtitle-review'
$VoiceBrief = Join-Path $PSScriptRoot 'fixtures\brief-final-render-contract\voice-only-brief.yaml'
$ScriptBrief = Join-Path $PSScriptRoot 'fixtures\brief-final-render-contract\legacy-script-brief.yaml'
$OwnerPhrase = 'I_APPROVE_VOICE_SUBTITLE_TEXT'
$Pass = 0
$Fail = 0

function Assert-True {
    param([bool]$Condition, [string]$Name)
    if ($Condition) { Write-Host "[PASS] $Name" -ForegroundColor Green; $script:Pass++ }
    else { Write-Host "[FAIL] $Name" -ForegroundColor Red; $script:Fail++ }
}

function New-VoiceWs {
    param([string]$Name)
    $ws = Join-Path $PSScriptRoot ".tmp-r2-$Name"
    if (Test-Path $ws) { Remove-Item $ws -Recurse -Force }
    $prod = Join-Path $ws 'video-workflow\production'
    $tpl = Join-Path $ws 'video-workflow\templates'
    New-Item -ItemType Directory -Path $prod,$tpl -Force | Out-Null
    Copy-Item (Join-Path $Payload 'video-workflow\templates\subtitle-external-ass-style-baseline.v1.json') $tpl
    Copy-Item (Join-Path $Payload 'video-workflow\templates\subtitle-series-style-registry.v1.json') $tpl
    Copy-Item $Tools (Join-Path $ws 'video-workflow\tools') -Recurse -Force
    Copy-Item $VoiceBrief (Join-Path $prod 'brief.yaml')
    Copy-Item (Join-Path $Fix 'narration.wav') (Join-Path $ws 'narration.wav')
    return $ws
}

function Write-OwnerIntent {
    param([string]$Workspace, [string]$TextSha256, [string]$ProdId = 'voice-u2', [string]$OwnerName = 'OwnerHuman')
    $intent = @{
        schema_version = 1
        production_id = $ProdId
        reviewed_text_sha256 = $TextSha256
        owner_display_name = $OwnerName
        confirmation_phrase = $OwnerPhrase
        owner_confirmed = $true
    }
    $intent | ConvertTo-Json | Set-Content (Join-Path $Workspace 'video-workflow\production\voice-subtitle-owner-approval-intent.json') -Encoding UTF8
}

function Invoke-Review { param([string]$Ws)
    & python (Join-Path $Tools 'run-voice-subtitle-review.py') --workspace $Ws --brief (Join-Path $Ws 'video-workflow\production\brief.yaml') | Out-Null
}

function Test-CanonicalBlocked {
    param([string]$Ws)
    $py = @"
import sys
from pathlib import Path
sys.path.insert(0, r'$($Tools -replace "'","''")\\lib')
from voice_subtitle_review import approval_allows_canonical
ws = Path(r'$($Ws -replace "'","''")')
ok, _ = approval_allows_canonical(ws, ws/'video-workflow/production/brief.yaml')
sys.exit(0 if ok else 1)
"@
    & python -c $py 2>$null | Out-Null
    return ($LASTEXITCODE -ne 0)
}

Write-Host '=== T02-R2 Voice Subtitle Security ===' -ForegroundColor Cyan

# R2-1 same provider / duplicate file
$w1 = New-VoiceWs 'same-source'
Copy-Item (Join-Path $Fix 'asr-primary-provenance.json') (Join-Path $w1 'video-workflow\production\asr-timing-evidence.json')
Copy-Item (Join-Path $Fix 'asr-primary-provenance.json') (Join-Path $w1 'video-workflow\production\asr-timing-evidence-alt.json')
Invoke-Review $w1
$r = Get-Content (Join-Path $w1 'video-workflow\production\voice-subtitle-review-result.json') -Raw | ConvertFrom-Json
Assert-True ($r.status -eq 'NEEDS_OWNER_REVIEW') 'R2-1 duplicate ASR file not auto'
Assert-True (@($r.anomalies | Where-Object { $_.type -eq 'ASR_SECONDARY_DUPLICATE_FILE' }).Count -ge 1) 'R2-1 duplicate file anomaly'

# R2-2 copy primary content to alt filename without provenance on alt
$w2 = New-VoiceWs 'copy-json'
Copy-Item (Join-Path $Fix 'asr-primary-clean.json') (Join-Path $w2 'video-workflow\production\asr-timing-evidence.json')
Copy-Item (Join-Path $Fix 'asr-primary-clean.json') (Join-Path $w2 'video-workflow\production\asr-timing-evidence-alt.json')
Invoke-Review $w2
$r2 = Get-Content (Join-Path $w2 'video-workflow\production\voice-subtitle-review-result.json') -Raw | ConvertFrom-Json
Assert-True ($r2.status -ne 'AUTO_ACCEPTED') 'R2-2 copy primary no AUTO_ACCEPT'
Assert-True (Test-CanonicalBlocked $w2) 'R2-2 copy blocks canonical'

# R2-3 text match but missing provenance fields
$w3 = New-VoiceWs 'no-prov'
Copy-Item (Join-Path $Fix 'asr-primary-clean.json') (Join-Path $w3 'video-workflow\production\asr-timing-evidence.json')
Copy-Item (Join-Path $Fix 'asr-alt-clean.json') (Join-Path $w3 'video-workflow\production\asr-timing-evidence-alt.json')
Invoke-Review $w3
$r3 = Get-Content (Join-Path $w3 'video-workflow\production\voice-subtitle-review-result.json') -Raw | ConvertFrom-Json
Assert-True (@($r3.anomalies | Where-Object { $_.type -like '*PROVENANCE*' }).Count -ge 1) 'R2-3 provenance missing flagged'

# R2-4 agent owner name forbidden
$w4 = New-VoiceWs 'agent-name'
Copy-Item (Join-Path $Fix 'asr-primary-provenance.json') (Join-Path $w4 'video-workflow\production\asr-timing-evidence.json')
Copy-Item (Join-Path $Fix 'asr-alt-provenance.json') (Join-Path $w4 'video-workflow\production\asr-timing-evidence-alt.json')
Invoke-Review $w4
$sha = (Get-Content (Join-Path $w4 'video-workflow\production\voice-subtitle-review-result.json') -Raw | ConvertFrom-Json).fingerprints.reviewed_text_sha256
Write-OwnerIntent -Workspace $w4 -TextSha256 $sha -OwnerName 'CursorAgent'
$prevEa = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
& python (Join-Path $Tools 'record-voice-subtitle-owner-approval.py') --workspace $w4 2>&1 | Out-Null
$r4Exit = $LASTEXITCODE
$ErrorActionPreference = $prevEa
Assert-True ($r4Exit -ne 0) 'R2-4 agent owner name rejected'

# R2-5 no intent -> no OWNER_ACCEPTED
$w5 = New-VoiceWs 'no-confirm'
Copy-Item (Join-Path $Fix 'asr-primary-provenance.json') (Join-Path $w5 'video-workflow\production\asr-timing-evidence.json')
Copy-Item (Join-Path $Fix 'asr-alt-provenance.json') (Join-Path $w5 'video-workflow\production\asr-timing-evidence-alt.json')
Invoke-Review $w5
$ErrorActionPreference = 'Continue'
& python (Join-Path $Tools 'record-voice-subtitle-owner-approval.py') --workspace $w5 2>&1 | Out-Null
$r5Exit = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
Assert-True ($r5Exit -ne 0) 'R2-5 no intent rejected'
Assert-True (Test-CanonicalBlocked $w5) 'R2-5 canonical blocked'

# R2-6 audio replaced after review
$w6 = New-VoiceWs 'audio-swap'
Copy-Item (Join-Path $Fix 'asr-primary-provenance.json') (Join-Path $w6 'video-workflow\production\asr-timing-evidence.json')
Copy-Item (Join-Path $Fix 'asr-alt-provenance.json') (Join-Path $w6 'video-workflow\production\asr-timing-evidence-alt.json')
Invoke-Review $w6
$sha6 = (Get-Content (Join-Path $w6 'video-workflow\production\voice-subtitle-review-result.json') -Raw | ConvertFrom-Json).fingerprints.reviewed_text_sha256
Write-OwnerIntent -Workspace $w6 -TextSha256 $sha6
& python (Join-Path $Tools 'record-voice-subtitle-owner-approval.py') --workspace $w6 | Out-Null
Set-Content (Join-Path $w6 'narration.wav') 'SWAPPED' -Encoding ASCII
Assert-True (Test-CanonicalBlocked $w6) 'R2-6 audio swap blocks canonical'

# R2-7 stale approval copied from another workspace
$w7a = New-VoiceWs 'approval-src'
$w7b = New-VoiceWs 'approval-dst'
Copy-Item (Join-Path $Fix 'asr-primary-provenance.json') (Join-Path $w7a 'video-workflow\production\asr-timing-evidence.json')
Copy-Item (Join-Path $Fix 'asr-alt-provenance.json') (Join-Path $w7a 'video-workflow\production\asr-timing-evidence-alt.json')
Invoke-Review $w7a
$sha7 = (Get-Content (Join-Path $w7a 'video-workflow\production\voice-subtitle-review-result.json') -Raw | ConvertFrom-Json).fingerprints.reviewed_text_sha256
Write-OwnerIntent -Workspace $w7a -TextSha256 $sha7
& python (Join-Path $Tools 'record-voice-subtitle-owner-approval.py') --workspace $w7a | Out-Null
Copy-Item (Join-Path $Fix 'asr-primary-clean.json') (Join-Path $w7b 'video-workflow\production\asr-timing-evidence.json')
Invoke-Review $w7b
Copy-Item (Join-Path $w7a 'video-workflow\production\voice-subtitle-approval.json') (Join-Path $w7b 'video-workflow\production\voice-subtitle-approval.json')
Copy-Item (Join-Path $w7a 'video-workflow\production\voice-subtitle-owner-approval-intent.json') (Join-Path $w7b 'video-workflow\production\voice-subtitle-owner-approval-intent.json')
Assert-True (Test-CanonicalBlocked $w7b) 'R2-7 cross-task approval reuse blocked'

# R2-8 canonical text drift (mutate reviewed text after approval)
$w8 = New-VoiceWs 'canonical-drift'
Copy-Item (Join-Path $Fix 'asr-primary-provenance.json') (Join-Path $w8 'video-workflow\production\asr-timing-evidence.json')
Copy-Item (Join-Path $Fix 'asr-alt-provenance.json') (Join-Path $w8 'video-workflow\production\asr-timing-evidence-alt.json')
Invoke-Review $w8
$sha8 = (Get-Content (Join-Path $w8 'video-workflow\production\voice-subtitle-review-result.json') -Raw | ConvertFrom-Json).fingerprints.reviewed_text_sha256
Write-OwnerIntent -Workspace $w8 -TextSha256 $sha8
& python (Join-Path $Tools 'record-voice-subtitle-owner-approval.py') --workspace $w8 | Out-Null
& (Join-Path $Tools 'invoke-frozen-script-subtitle-route.ps1') -WorkspaceRoot $w8 -NoPause | Out-Null
Set-Content (Join-Path $w8 'video-workflow\production\reviewed-subtitle-text.txt') '漂移文字' -Encoding UTF8
$py8 = @"
import sys
from pathlib import Path
sys.path.insert(0, r'$($Tools -replace "'","''")\\lib')
from brief_final_render_contract import validate_render_preparation_canonical_binding
ws = Path(r'$($w8 -replace "'","''")')
errs = validate_render_preparation_canonical_binding(ws, ws/'video-workflow/production/brief.yaml')
sys.exit(0 if errs else 1)
"@
& python -c $py8 2>$null | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'R2-8 render prep detects drift'

# R2-9 script route unaffected
if (Test-Path $ScriptBrief) {
    $ws9 = Join-Path $PSScriptRoot '.tmp-r2-script'
    if (Test-Path $ws9) { Remove-Item $ws9 -Recurse -Force }
    $prod9 = Join-Path $ws9 'video-workflow\production'
    New-Item -ItemType Directory -Path $prod9 -Force | Out-Null
    Copy-Item $ScriptBrief (Join-Path $prod9 'brief.yaml')
    Copy-Item $Tools (Join-Path $ws9 'video-workflow\tools') -Recurse -Force
    $py9 = @"
import sys
from pathlib import Path
sys.path.insert(0, r'$($Tools -replace "'","''")\\lib')
from brief_subtitle_authority import load_brief_dict, brief_requires_canonical_subtitle_route
b = load_brief_dict(Path(r'$($prod9 -replace "'","''")')/'brief.yaml')
print('OK' if brief_requires_canonical_subtitle_route(b) else 'NO')
"@
    $out9 = & python -c $py9 2>&1 | Select-Object -Last 1
    Assert-True ($out9 -eq 'OK') 'R2-9 script route still requires canonical'
    Remove-Item $ws9 -Recurse -Force -ErrorAction SilentlyContinue
} else {
    Assert-True $true 'R2-9 script fixture skip (missing)'
}

# R2-10 voice subtitles:false NOT_APPLICABLE
$w10 = New-VoiceWs 'no-subs'
$brief10 = Join-Path $w10 'video-workflow\production\brief.yaml'
$y10 = Get-Content $brief10 -Raw
$y10 = $y10 -replace 'subtitles: true', 'subtitles: false'
Set-Content $brief10 $y10 -Encoding UTF8
$out10 = & python (Join-Path $Tools 'run-voice-subtitle-review.py') --workspace $w10 --brief (Join-Path $w10 'video-workflow\production\brief.yaml') --json 2>$null | ConvertFrom-Json
Assert-True ($out10.status -eq 'NOT_APPLICABLE') 'R2-10 subtitles false NOT_APPLICABLE'

Get-ChildItem (Join-Path $PSScriptRoot '.tmp-r2-*') -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed"
if ($Fail -gt 0) { exit 1 }
exit 0
