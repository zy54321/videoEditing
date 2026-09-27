#Requires -Version 5.1
param(
    [string]$ProjectRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$BuildLib = Join-Path (Split-Path -Parent $PSScriptRoot) 'build\lib'
. (Join-Path $BuildLib 'ReleaseTransaction.ps1')

$Pass = 0
$Fail = 0

function Assert-True {
    param([bool]$Condition, [string]$Name)
    if ($Condition) { Write-Host "[PASS] $Name" -ForegroundColor Green; $script:Pass++ }
    else { Write-Host "[FAIL] $Name" -ForegroundColor Red; $script:Fail++ }
}

function Assert-GitState {
    param(
        [string]$RepoRoot,
        [string]$ExpectedHead,
        [string[]]$ExpectedPorcelain,
        [hashtable]$FileContents = @{}
    )
    $head = (git -C $RepoRoot rev-parse HEAD).Trim()
    $porcelain = Get-GitPorcelainLines -ProjectRoot $RepoRoot
    $headOk = ($head -eq $ExpectedHead)
    $statusOk = Test-GitPorcelainEqual -Expected $ExpectedPorcelain -Actual $porcelain
    $filesOk = $true
    foreach ($k in $FileContents.Keys) {
        $path = Join-Path $RepoRoot $k
        if (-not (Test-Path -LiteralPath $path)) { $filesOk = $false; break }
        $content = (Get-Content -LiteralPath $path -Raw).TrimEnd("`r", "`n")
        $expectedContent = "$($FileContents[$k])".TrimEnd("`r", "`n")
        if ($content -ne $expectedContent) { $filesOk = $false; break }
    }
    return ($headOk -and $statusOk -and $filesOk)
}

function New-DisposableRepo {
    $tmp = Join-Path $PSScriptRoot "fixtures\release-v2-txn-$([guid]::NewGuid().ToString('n'))"
    New-Item -ItemType Directory -Path $tmp -Force | Out-Null
    git -C $tmp init -q
    git -C $tmp config user.email 'test@test.local'
    git -C $tmp config user.name 'Test'
    New-Item -ItemType Directory -Path (Join-Path $tmp 'docs') -Force | Out-Null
    'base-tracked' | Out-File (Join-Path $tmp 'tracked.txt') -Encoding utf8 -NoNewline
    'docs-base' | Out-File (Join-Path $tmp 'docs\note.md') -Encoding utf8 -NoNewline
    git -C $tmp add tracked.txt docs/note.md
    git -C $tmp commit -m 'init' -q
    return $tmp
}

function Remove-DisposableRepo {
    param([string]$RepoRoot)
    if ($RepoRoot -and (Test-Path -LiteralPath $RepoRoot)) {
        Remove-Item -LiteralPath $RepoRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host '=== Release V2 Transaction Fixtures ===' -ForegroundColor Cyan

# T01 clean repo → txn → mutate → abort
$repo = New-DisposableRepo
try {
    $head0 = (git -C $repo rev-parse HEAD).Trim()
    $txn = New-ReleaseTransaction -ProjectRoot $repo
    Assert-True ($null -eq $txn.StashRef) 'T01 clean txn StashRef null'
    'mutated' | Out-File (Join-Path $repo 'during-txn.txt') -Encoding utf8
    Abort-ReleaseTransaction -Transaction $txn
    $ok = Assert-GitState -RepoRoot $repo -ExpectedHead $head0 -ExpectedPorcelain @() -FileContents @{ 'tracked.txt' = 'base-tracked' }
    Assert-True $ok 'T01 clean abort restores HEAD/status/files'
} finally { Remove-DisposableRepo $repo }

# T02 clean repo → txn → mutate → simulated release commit (add -A)
$repo = New-DisposableRepo
try {
    $head0 = (git -C $repo rev-parse HEAD).Trim()
    $txn = New-ReleaseTransaction -ProjectRoot $repo
    'release-line' | Out-File (Join-Path $repo 'docs\note.md') -Encoding utf8 -NoNewline
    'new-artifact' | Out-File (Join-Path $repo 'artifact.txt') -Encoding utf8
    git -C $repo add -A
    git -C $repo commit -m 'release: test-sim' -q
    $txn.ReleaseCommit = (git -C $repo rev-parse HEAD).Trim()
    Complete-ReleaseTransaction -Transaction $txn
    $porcelain = Get-GitPorcelainLines -ProjectRoot $repo
    $hasBoth = (Test-Path (Join-Path $repo 'artifact.txt')) -and ((Get-Content (Join-Path $repo 'docs\note.md') -Raw) -eq 'release-line')
    Assert-True ((@($porcelain).Count -eq 0) -and $hasBoth -and ($txn.ReleaseCommit -ne $head0)) 'T02 clean txn success path commit + clean tree'
} finally { Remove-DisposableRepo $repo }

# T03 tracked unstaged only
$repo = New-DisposableRepo
try {
    $head0 = (git -C $repo rev-parse HEAD).Trim()
    'edited-unstaged' | Out-File (Join-Path $repo 'tracked.txt') -Encoding utf8 -NoNewline
    $before = Get-GitPorcelainLines -ProjectRoot $repo
    $txn = New-ReleaseTransaction -ProjectRoot $repo
    Assert-True ($null -ne $txn.StashRef) 'T03 dirty txn has stash'
    'txn-bump' | Out-File (Join-Path $repo 'tracked.txt') -Encoding utf8 -NoNewline
    Abort-ReleaseTransaction -Transaction $txn
    $ok = Assert-GitState -RepoRoot $repo -ExpectedHead $head0 -ExpectedPorcelain $before -FileContents @{ 'tracked.txt' = 'edited-unstaged' }
    Assert-True $ok 'T03 unstaged rollback exact status + content'
} finally { Remove-DisposableRepo $repo }

# T04 staged only
$repo = New-DisposableRepo
try {
    $head0 = (git -C $repo rev-parse HEAD).Trim()
    'staged-only' | Out-File (Join-Path $repo 'tracked.txt') -Encoding utf8 -NoNewline
    git -C $repo add tracked.txt
    $before = Get-GitPorcelainLines -ProjectRoot $repo
    $txn = New-ReleaseTransaction -ProjectRoot $repo
    Abort-ReleaseTransaction -Transaction $txn
    $ok = Assert-GitState -RepoRoot $repo -ExpectedHead $head0 -ExpectedPorcelain $before -FileContents @{ 'tracked.txt' = 'staged-only' }
    Assert-True $ok 'T04 staged rollback preserves index state'
} finally { Remove-DisposableRepo $repo }

# T05 untracked only
$repo = New-DisposableRepo
try {
    $head0 = (git -C $repo rev-parse HEAD).Trim()
    'u-only' | Out-File (Join-Path $repo 'local-only.txt') -Encoding utf8
    $before = Get-GitPorcelainLines -ProjectRoot $repo
    $txn = New-ReleaseTransaction -ProjectRoot $repo
    Remove-Item (Join-Path $repo 'local-only.txt') -Force
    Abort-ReleaseTransaction -Transaction $txn
    $ok = Assert-GitState -RepoRoot $repo -ExpectedHead $head0 -ExpectedPorcelain $before -FileContents @{ 'local-only.txt' = 'u-only' }
    Assert-True $ok 'T05 untracked rollback'
} finally { Remove-DisposableRepo $repo }

# T06 mixed staged + unstaged + untracked + docs
$repo = New-DisposableRepo
try {
    $head0 = (git -C $repo rev-parse HEAD).Trim()
    'mixed-unstaged' | Out-File (Join-Path $repo 'tracked.txt') -Encoding utf8 -NoNewline
    'mixed-docs' | Out-File (Join-Path $repo 'docs\note.md') -Encoding utf8 -NoNewline
    git -C $repo add docs/note.md
    'mixed-u' | Out-File (Join-Path $repo 'extra.txt') -Encoding utf8
    $before = Get-GitPorcelainLines -ProjectRoot $repo
    $txn = New-ReleaseTransaction -ProjectRoot $repo
    'during' | Out-File (Join-Path $repo 'during.txt') -Encoding utf8
    Abort-ReleaseTransaction -Transaction $txn
    $ok = Assert-GitState -RepoRoot $repo -ExpectedHead $head0 -ExpectedPorcelain $before -FileContents @{
        'tracked.txt' = 'mixed-unstaged'
        'docs\note.md' = 'mixed-docs'
        'extra.txt' = 'mixed-u'
    }
    Assert-True $ok 'T06 mixed dirty rollback semantic state'
} finally { Remove-DisposableRepo $repo }

# T07 mixed dirty → single commit via git add -A (release freeze simulation)
$repo = New-DisposableRepo
try {
    $txn = New-ReleaseTransaction -ProjectRoot $repo
    'u-pre' | Out-File (Join-Path $repo 'pre-untracked.txt') -Encoding utf8
    'staged-pre' | Out-File (Join-Path $repo 'docs\note.md') -Encoding utf8 -NoNewline
    git -C $repo add docs/note.md
    'unstaged-pre' | Out-File (Join-Path $repo 'tracked.txt') -Encoding utf8 -NoNewline
    git -C $repo add -A
    git -C $repo commit -m 'release: mixed-freeze' -q
    $filesInCommit = git -C $repo show --name-only --pretty=format: HEAD
    $names = @($filesInCommit | Where-Object { $_ })
    $need = @('pre-untracked.txt', 'docs/note.md', 'tracked.txt')
    $found = 0
    foreach ($n in $need) {
        if ($names | Where-Object { ($_ -replace '\\', '/') -eq $n }) { $found++ }
    }
    $hasAll = ($found -eq $need.Count)
    Complete-ReleaseTransaction -Transaction $txn
    Assert-True ($hasAll -eq 3) 'T07 git add -A freezes staged+unstaged+untracked+docs in one commit'
} finally { Remove-DisposableRepo $repo }

# T08 stash preserved when abort restore uses invalid stash ref
$repo = New-DisposableRepo
try {
    'dirty' | Out-File (Join-Path $repo 'tracked.txt') -Encoding utf8 -NoNewline
    $txn = New-ReleaseTransaction -ProjectRoot $repo
    $realStashLine = git -C $repo stash list | Select-String 'release-txn' | Select-Object -First 1
    Assert-True ($null -ne $realStashLine) 'T08 safety stash created'
    $txn.StashRef = 'stash@{999}'
    $recovered = $false
    try {
        Abort-ReleaseTransaction -Transaction $txn
    } catch {
        $recovered = $true
    }
    $stashStill = git -C $repo stash list | Select-String 'release-txn'
    Assert-True ($recovered -and $null -ne $stashStill) 'T08 invalid restore leaves safety stash intact'
} finally { Remove-DisposableRepo $repo }

# T09 status mismatch does not drop stash
$repo = New-DisposableRepo
try {
    'x' | Out-File (Join-Path $repo 'tracked.txt') -Encoding utf8 -NoNewline
    $txn = New-ReleaseTransaction -ProjectRoot $repo
    $stashBefore = git -C $repo stash list | Select-String 'release-txn'
    $env:RELEASE_TXN_TEST_FORCE_RESTORE_MISMATCH = '1'
    $recovered = $false
    try {
        Abort-ReleaseTransaction -Transaction $txn
    } catch {
        $recovered = $true
    } finally {
        Remove-Item Env:RELEASE_TXN_TEST_FORCE_RESTORE_MISMATCH -ErrorAction SilentlyContinue
    }
    $stashAfter = git -C $repo stash list | Select-String 'release-txn'
    $stashOk = $recovered -and $null -ne $stashBefore -and $null -ne $stashAfter
    Assert-True $stashOk 'T09 forced mismatch preserves stash'
} finally { Remove-DisposableRepo $repo }

Write-Host ''
Write-Host "Transaction fixtures: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
exit 0
