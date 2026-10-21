#Requires -Version 5.1
<#
.SYNOPSIS
  U1 — Voice subtitle text review + canonical integration tests.
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
    $ws = Join-Path $PSScriptRoot ".tmp-u1-$Name"
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

function Complete-VoiceOwnerApproval {
    param([string]$Workspace)
    Write-OwnerIntent -Workspace $Workspace -TextSha256 (Get-ReviewedTextSha $Workspace)
    & python (Join-Path $Tools 'record-voice-subtitle-owner-approval.py') --workspace $Workspace | Out-Null
    return $LASTEXITCODE
}

Write-Host '=== U1 Voice Subtitle Authority ===' -ForegroundColor Cyan

# V1 single ASR -> NEEDS_OWNER_REVIEW, not CONTRACT_READY
$ws1 = New-VoiceWs 'single-asr'
Copy-Item (Join-Path $Fix 'asr-primary-clean.json') (Join-Path $ws1 'video-workflow\production\asr-timing-evidence.json')
& python (Join-Path $Tools 'run-voice-subtitle-review.py') --workspace $ws1 --brief (Join-Path $ws1 'video-workflow\production\brief.yaml') | Out-Null
Assert-True ($LASTEXITCODE -eq 2) 'V1 single ASR review exit 2'
$r1 = Get-Content (Join-Path $ws1 'video-workflow\production\voice-subtitle-review-result.json') -Raw | ConvertFrom-Json
Assert-True ($r1.status -eq 'NEEDS_OWNER_REVIEW') 'V1 NEEDS_OWNER_REVIEW'
Assert-True (-not (Test-Path (Join-Path $ws1 'video-workflow\production\voice-subtitle-approval.json'))) 'V1 no auto approval file'

# V2 dual ASR clean without provenance -> still NEEDS_OWNER_REVIEW (no AUTO_ACCEPT)
$ws2 = New-VoiceWs 'dual-clean'
Copy-Item (Join-Path $Fix 'asr-primary-clean.json') (Join-Path $ws2 'video-workflow\production\asr-timing-evidence.json')
Copy-Item (Join-Path $Fix 'asr-alt-clean.json') (Join-Path $ws2 'video-workflow\production\asr-timing-evidence-alt.json')
& python (Join-Path $Tools 'run-voice-subtitle-review.py') --workspace $ws2 --brief (Join-Path $ws2 'video-workflow\production\brief.yaml') | Out-Null
Assert-True ($LASTEXITCODE -eq 2) 'V2 dual clean without provenance exit 2'
$r2 = Get-Content (Join-Path $ws2 'video-workflow\production\voice-subtitle-review-result.json') -Raw | ConvertFrom-Json
Assert-True ($r2.status -eq 'NEEDS_OWNER_REVIEW') 'V2 no AUTO_ACCEPT without provenance'
Assert-True ($r2.auto_review_runtime_available -eq $false) 'V2 AUTO_REVIEW_RUNTIME_NOT_AVAILABLE flag'
Assert-True (-not (Test-Path (Join-Path $ws2 'video-workflow\production\voice-subtitle-approval.json'))) 'V2 no auto approval'

# V2b dual with provenance + owner intent -> OWNER_ACCEPTED path
Copy-Item (Join-Path $Fix 'asr-primary-provenance.json') (Join-Path $ws2 'video-workflow\production\asr-timing-evidence.json') -Force
Copy-Item (Join-Path $Fix 'asr-alt-provenance.json') (Join-Path $ws2 'video-workflow\production\asr-timing-evidence-alt.json') -Force
& python (Join-Path $Tools 'run-voice-subtitle-review.py') --workspace $ws2 --brief (Join-Path $ws2 'video-workflow\production\brief.yaml') | Out-Null
Assert-True ($LASTEXITCODE -eq 2) 'V2b provenance dual still needs owner exit 2'
Assert-True ((Complete-VoiceOwnerApproval -Workspace $ws2) -eq 0) 'V2b owner approval with intent'
$ap2 = Get-Content (Join-Path $ws2 'video-workflow\production\voice-subtitle-approval.json') -Raw | ConvertFrom-Json
Assert-True ($ap2.status -eq 'OWNER_ACCEPTED') 'V2b OWNER_ACCEPTED recorded'

# V3 homophone divergence
$ws3 = New-VoiceWs 'homophone'
Copy-Item (Join-Path $Fix 'asr-homophone-primary.json') (Join-Path $ws3 'video-workflow\production\asr-timing-evidence.json')
Copy-Item (Join-Path $Fix 'asr-homophone-alt.json') (Join-Path $ws3 'video-workflow\production\asr-timing-evidence-alt.json')
& python (Join-Path $Tools 'run-voice-subtitle-review.py') --workspace $ws3 --brief (Join-Path $ws3 'video-workflow\production\brief.yaml') | Out-Null
Assert-True ($LASTEXITCODE -eq 2) 'V3 homophone exit 2'
$r3 = Get-Content (Join-Path $ws3 'video-workflow\production\voice-subtitle-review-result.json') -Raw | ConvertFrom-Json
Assert-True ($r3.anomaly_count -ge 1) 'V3 anomalies present'

# V4 owner approval after review (intent required)
Assert-True ((Complete-VoiceOwnerApproval -Workspace $ws3) -eq 0) 'V4 owner approval exit 0'
$ap4 = Get-Content (Join-Path $ws3 'video-workflow\production\voice-subtitle-approval.json') -Raw | ConvertFrom-Json
Assert-True ($ap4.owner_confirmed -eq $true) 'V4 owner_confirmed'

# V5 cannot record without intent artifact
$ws5 = New-VoiceWs 'no-intent'
Copy-Item (Join-Path $Fix 'asr-primary-clean.json') (Join-Path $ws5 'video-workflow\production\asr-timing-evidence.json')
& python (Join-Path $Tools 'run-voice-subtitle-review.py') --workspace $ws5 --brief (Join-Path $ws5 'video-workflow\production\brief.yaml') | Out-Null
$prevEa = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
& python (Join-Path $Tools 'record-voice-subtitle-owner-approval.py') --workspace $ws5 2>&1 | Out-Null
$v5Exit = $LASTEXITCODE
$ErrorActionPreference = $prevEa
Assert-True ($v5Exit -ne 0) 'V5 missing intent rejected'

# V6 hash drift invalidates approval
$ws6 = New-VoiceWs 'drift'
Copy-Item (Join-Path $Fix 'asr-primary-provenance.json') (Join-Path $ws6 'video-workflow\production\asr-timing-evidence.json')
Copy-Item (Join-Path $Fix 'asr-alt-provenance.json') (Join-Path $ws6 'video-workflow\production\asr-timing-evidence-alt.json')
& python (Join-Path $Tools 'run-voice-subtitle-review.py') --workspace $ws6 --brief (Join-Path $ws6 'video-workflow\production\brief.yaml') | Out-Null
Complete-VoiceOwnerApproval -Workspace $ws6 | Out-Null
$txt = Join-Path $ws6 'video-workflow\production\reviewed-subtitle-text.txt'
Set-Content $txt 'mutated' -Encoding UTF8
$py = @"
import sys
from pathlib import Path
sys.path.insert(0, r'$($Tools -replace "'","''")\\lib')
from voice_subtitle_review import approval_allows_canonical
ws = Path(r'$($ws6 -replace "'","''")')
ok, reason = approval_allows_canonical(ws, ws/'video-workflow/production/brief.yaml')
print(reason)
sys.exit(0 if ok else 1)
"@
& python -c $py 2>$null | Out-Null
Assert-True ($LASTEXITCODE -ne 0) 'V6 hash drift blocks canonical'

# V7 voice + owner approved -> CONTRACT_READY via build contract (ws2)
$build = Join-Path $Tools 'build-final-render-contract-from-brief.py'
$brief7 = Join-Path $ws2 'video-workflow\production\brief.yaml'
$out7 = & python $build --brief $brief7 --workspace $ws2 --json --dry-run 2>$null | Out-String
$j7 = $out7 | ConvertFrom-Json
Assert-True ($j7.status -eq 'CONTRACT_READY') 'V7 voice approved CONTRACT_READY'

# V8 canonical route after OWNER_ACCEPTED (ws2)
& python (Join-Path $PSScriptRoot 'bind-existing-timing-evidence.py') $ws2
$route = Join-Path $Tools 'invoke-frozen-script-subtitle-route.ps1'
& $route -WorkspaceRoot $ws2 -NoPause
Assert-True ($LASTEXITCODE -eq 0) 'V8 voice canonical route exit 0'
Assert-True (Test-Path (Join-Path $ws2 'video-workflow\production\canonical-subtitle-cues.json')) 'V8 canonical cues exist'

# V9 approval json states not final gate
$ap = Get-Content (Join-Path $ws2 'video-workflow\production\voice-subtitle-approval.json') -Raw | ConvertFrom-Json
Assert-True ($ap.final_delivery_gate -eq 'NOT_RUN') 'V9 not final gate pass'

Get-ChildItem (Join-Path $PSScriptRoot '.tmp-u1-*') -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed"
if ($Fail -gt 0) { exit 1 }
exit 0
