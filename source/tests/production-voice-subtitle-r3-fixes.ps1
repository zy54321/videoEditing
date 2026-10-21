#Requires -Version 5.1
<#
.SYNOPSIS
  P0-T02-R3 — F01–F05 audit fix regression tests.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$Payload = Join-Path $Root 'payload'
$Tools = Join-Path $Payload 'video-workflow\tools'
$Fix = Join-Path $PSScriptRoot 'fixtures\voice-subtitle-review'
$VoiceBrief = Join-Path $PSScriptRoot 'fixtures\brief-final-render-contract\voice-only-brief.yaml'
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
    $ws = Join-Path $PSScriptRoot ".tmp-r3-$Name"
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

function Get-ReviewedTextSha {
    param([string]$Workspace)
    $py = @"
import sys
from pathlib import Path
sys.path.insert(0, r'$($Tools -replace "'","''")\\lib')
from voice_subtitle_review import sha256_text
p = Path(r'$($Workspace -replace "'","''")')/'video-workflow/production/reviewed-subtitle-text.txt'
print(sha256_text(p.read_text(encoding='utf-8-sig').strip()))
"@
    return (& python -c $py).Trim()
}

function Write-OwnerIntent {
    param([string]$Workspace, [string]$TextSha256)
    $intent = @{
        schema_version = 1
        production_id = 'voice-u2'
        reviewed_text_sha256 = $TextSha256
        owner_display_name = 'OwnerHuman'
        confirmation_phrase = $OwnerPhrase
        owner_confirmed = $true
    }
    $intent | ConvertTo-Json | Set-Content (Join-Path $Workspace 'video-workflow\production\voice-subtitle-owner-approval-intent.json') -Encoding UTF8
}

function Setup-ApprovedVoiceWs {
    param([string]$Name)
    $ws = New-VoiceWs $Name
    Copy-Item (Join-Path $Fix 'asr-primary-provenance.json') (Join-Path $ws 'video-workflow\production\asr-timing-evidence.json')
    Copy-Item (Join-Path $Fix 'asr-alt-provenance.json') (Join-Path $ws 'video-workflow\production\asr-timing-evidence-alt.json')
    & python (Join-Path $Tools 'run-voice-subtitle-review.py') --workspace $ws --brief (Join-Path $ws 'video-workflow\production\brief.yaml') | Out-Null
    return $ws
}

function Test-CanonicalOk {
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
    return ($LASTEXITCODE -eq 0)
}

Write-Host '=== P0-T02-R3 F01–F05 ===' -ForegroundColor Cyan

# F01 Owner typo fix positive
$w1 = Setup-ApprovedVoiceWs 'f01-typo'
$revisedText = [char]0x4F60 + [char]0x597D + [char]0x4E16 + [char]0x7559
Set-Content (Join-Path $w1 'video-workflow\production\reviewed-subtitle-text.txt') $revisedText -Encoding UTF8
Write-OwnerIntent -Workspace $w1 -TextSha256 (Get-ReviewedTextSha $w1)
& python (Join-Path $Tools 'record-voice-subtitle-owner-approval.py') --workspace $w1 | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'F01 owner revised text approval'
$r1 = Get-Content (Join-Path $w1 'video-workflow\production\voice-subtitle-review-result.json') -Raw | ConvertFrom-Json
Assert-True ($r1.fingerprints.asr_draft_text_sha256 -ne $r1.fingerprints.confirmed_reviewed_text_sha256) 'F01 draft vs confirmed fingerprints differ'
Assert-True (Test-CanonicalOk $w1) 'F01 canonical allowed after owner revision'

# F01 unapproved edit invalidates
$unauthEdit = [char]0x672A + [char]0x6388 + [char]0x6743 + [char]0x4FEE + [char]0x6539
Set-Content (Join-Path $w1 'video-workflow\production\reviewed-subtitle-text.txt') $unauthEdit -Encoding UTF8
Assert-True (-not (Test-CanonicalOk $w1)) 'F01 unapproved edit blocks canonical'

# F02 stale gate after text drift
$w2 = Setup-ApprovedVoiceWs 'f02-gate'
$sha2 = Get-ReviewedTextSha $w2
Write-OwnerIntent -Workspace $w2 -TextSha256 $sha2
& python (Join-Path $Tools 'record-voice-subtitle-owner-approval.py') --workspace $w2 | Out-Null
& python (Join-Path $PSScriptRoot 'bind-existing-timing-evidence.py') $w2
& (Join-Path $Tools 'invoke-frozen-script-subtitle-route.ps1') -WorkspaceRoot $w2 -NoPause | Out-Null
$py2 = @"
import sys
from pathlib import Path
sys.path.insert(0, r'$($Tools -replace "'","''")\\lib')
from brief_final_render_contract import validate_render_preparation_canonical_binding
ws = Path(r'$($w2 -replace "'","''")')
errs = validate_render_preparation_canonical_binding(ws, ws/'video-workflow/production/brief.yaml')
sys.exit(0 if not errs else 1)
"@
& python -c $py2 2>$null | Out-Null
Assert-True ($LASTEXITCODE -eq 0) 'F02 render prep OK with live gate'
$driftText = [char]0x6F02 + [char]0x79FB + [char]0x540E + [char]0x6587 + [char]0x5B57
Set-Content (Join-Path $w2 'video-workflow\production\reviewed-subtitle-text.txt') $driftText -Encoding UTF8
& python -c $py2 2>$null | Out-Null
Assert-True ($LASTEXITCODE -ne 0) 'F02 stale gate blocked after text drift'

# F03 primary ASR deleted
$w3 = Setup-ApprovedVoiceWs 'f03-asr'
$sha3 = Get-ReviewedTextSha $w3
Write-OwnerIntent -Workspace $w3 -TextSha256 $sha3
& python (Join-Path $Tools 'record-voice-subtitle-owner-approval.py') --workspace $w3 | Out-Null
Remove-Item (Join-Path $w3 'video-workflow\production\asr-timing-evidence.json') -Force
Assert-True (-not (Test-CanonicalOk $w3)) 'F03 primary ASR missing blocks'

# F03 voice audio missing
$w3b = Setup-ApprovedVoiceWs 'f03-voice'
$sha3b = Get-ReviewedTextSha $w3b
Write-OwnerIntent -Workspace $w3b -TextSha256 $sha3b
& python (Join-Path $Tools 'record-voice-subtitle-owner-approval.py') --workspace $w3b | Out-Null
Remove-Item (Join-Path $w3b 'narration.wav') -Force
Assert-True (-not (Test-CanonicalOk $w3b)) 'F03 voice audio missing blocks'

# F04 re-review must not overwrite owner text
$w4 = Setup-ApprovedVoiceWs 'f04-preserve'
$sha4 = Get-ReviewedTextSha $w4
Write-OwnerIntent -Workspace $w4 -TextSha256 $sha4
& python (Join-Path $Tools 'record-voice-subtitle-owner-approval.py') --workspace $w4 | Out-Null
$preserveMarker = [char]0x4EBA + [char]0x5DE5 + [char]0x4FDD + [char]0x7559 + [char]0x7A3F
Set-Content (Join-Path $w4 'video-workflow\production\reviewed-subtitle-text.txt') $preserveMarker -Encoding UTF8
& python (Join-Path $Tools 'run-voice-subtitle-review.py') --workspace $w4 --brief (Join-Path $w4 'video-workflow\production\brief.yaml') | Out-Null
$txt4 = Get-Content (Join-Path $w4 'video-workflow\production\reviewed-subtitle-text.txt') -Raw -Encoding UTF8
Assert-True ($txt4.Trim() -eq $preserveMarker) 'F04 re-review preserves edited text'
$r4 = Get-Content (Join-Path $w4 'video-workflow\production\voice-subtitle-review-result.json') -Raw | ConvertFrom-Json
Assert-True ($r4.review_artifact_write.reviewed_text_preserved -eq $true) 'F04 preserve flag set'

# F05 missing primary ASR — stable BLOCKED, no reviewed file
$w5 = New-VoiceWs 'f05-blocked'
$prevEa = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
& python (Join-Path $Tools 'run-voice-subtitle-review.py') --workspace $w5 --brief (Join-Path $w5 'video-workflow\production\brief.yaml') --json 2>&1 | Out-Null
$e5 = $LASTEXITCODE
$ErrorActionPreference = $prevEa
Assert-True ($e5 -eq 1) 'F05 exit 1 BLOCKED'
$r5 = Get-Content (Join-Path $w5 'video-workflow\production\voice-subtitle-review-result.json') -Raw | ConvertFrom-Json
Assert-True ($r5.status -eq 'BLOCKED') 'F05 status BLOCKED'
Assert-True (-not (Test-Path (Join-Path $w5 'video-workflow\production\reviewed-subtitle-text.txt'))) 'F05 no reviewed text artifact'

Get-ChildItem (Join-Path $PSScriptRoot '.tmp-r3-*') -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed"
if ($Fail -gt 0) { exit 1 }
exit 0
