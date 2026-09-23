#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$matPath = Join-Path $repoRoot 'source\payload\video-workflow\tools\lib\textplus-layout-materializer.ps1'
. $matPath

$fail = 0

function Assert-Equal($name, $expected, $actual) {
    if ($expected -ne $actual) {
        Write-Host "FAIL $name expected=$expected actual=$actual"
        $fail++
    }
    else {
        Write-Host "PASS $name"
    }
}

# Case 1: multi-line from L1 lines
$lines = @(
    @{ runs = @(@{ text = 'AAA' }) },
    @{ runs = @(@{ text = 'BBB' }) }
)
$styled = Get-StyledTextFromL1Lines -Lines $lines
Assert-Equal 'newline_join' "AAA`nBBB" $styled

# Case 2: split candidate selection
$cands = @(
    @{ boundary_policy = 'forbid'; after_run_index = 0 },
    @{ boundary_policy = 'prefer'; after_run_index = 1 },
    @{ boundary_policy = 'allow'; after_run_index = 2 }
)
$pick = Select-L1SplitCandidate -SplitCandidates $cands
Assert-Equal 'split_prefer' 1 $pick.after_run_index

# Case 3: A11 smoke materialization plan
$a11Req = Join-Path $repoRoot 'validation\08e-b-exp-a\cases\A11-materialization-smoke.request.json'
$a11 = Invoke-TextPlusLayoutMaterializationFromFiles -RequestPath $a11Req -CueId 'A11'
Assert-Equal 'a11_status' 'READY' $a11.materialization_status
Assert-Equal 'a11_line_count' 2 $a11.materialized_cues[0].line_count
Assert-Equal 'a11_newline_pos' 10 $a11.materialized_cues[0].newline_positions[0]

# Case 4: atomic overflow blocked
$a07Req = Join-Path $repoRoot 'validation\08e-b-exp-a\cases\A07.request.json'
$a07 = Invoke-TextPlusLayoutMaterializationFromFiles -RequestPath $a07Req -CueId 'A07'
Assert-Equal 'a07_blocked' 'BLOCKED_NO_LEGAL_INTERNAL_BREAK' $a07.materialization_status

if ($fail -gt 0) {
    Write-Host "FAILED: $fail"
    exit 1
}
Write-Host 'ALL PASS'
exit 0
