#Requires -Version 5.1
Set-StrictMode -Version Latest

function Get-GitPorcelainLines {
    param([string]$ProjectRoot)
    $raw = git -C $ProjectRoot status --porcelain=v1 2>$null
    if (-not $raw) { return @() }
    $text = if ($raw -is [array]) { ($raw -join "`n") } else { [string]$raw }
    return @($text -split "`n" | ForEach-Object { $_.TrimEnd() } | Where-Object { $_ })
}

function Remove-UntrackedExceptPorcelain {
    param([string]$ProjectRoot, [string[]]$ExpectedPorcelain)
    $expectedUntracked = @()
    foreach ($line in @($ExpectedPorcelain)) {
        if ($line -match '^\?\? (.+)$') {
            $expectedUntracked += ($Matches[1].Trim() -replace '/', '\')
        }
    }
    $actualUntracked = @(git -C $ProjectRoot ls-files -o --exclude-standard 2>$null)
    foreach ($rel in $actualUntracked) {
        $norm = $rel -replace '/', '\'
        if ($expectedUntracked -notcontains $norm) {
            $full = Join-Path $ProjectRoot $rel
            if (Test-Path -LiteralPath $full) {
                Remove-Item -LiteralPath $full -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

function Test-GitPorcelainEqual {
    param([string[]]$Expected, [string[]]$Actual)
    $e = @( @($Expected) | Where-Object { $_ }) | Sort-Object
    $a = @( @($Actual) | Where-Object { $_ }) | Sort-Object
    if (@($e).Count -ne @($a).Count) { return $false }
    for ($i = 0; $i -lt @($e).Count; $i++) {
        if ($e[$i] -ne $a[$i]) { return $false }
    }
    return $true
}

function Write-ReleaseRecoveryRequired {
    param(
        $Transaction,
        [string]$Reason
    )
    Write-Host 'RELEASE_RECOVERY_REQUIRED' -ForegroundColor Red
    Write-Host "Reason: $Reason"
    Write-Host "Original HEAD: $($Transaction.OriginalHead)"
    Write-Host "Stash ref: $($Transaction.StashRef)"
    Write-Host 'Manual recovery: git reset --hard <original HEAD>; git clean -fd; git stash list; git stash apply --index <stash ref>'
    throw 'RELEASE_RECOVERY_REQUIRED'
}

function Restore-ReleaseTransactionWorkingTree {
    param(
        $Transaction,
        [string[]]$ReleasePathsToRemove = @()
    )
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    foreach ($p in $ReleasePathsToRemove) {
        if ($p -and (Test-Path -LiteralPath $p)) {
            Remove-Item -LiteralPath $p -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    git -C $Transaction.ProjectRoot reset --hard $Transaction.OriginalHead 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-ReleaseRecoveryRequired -Transaction $Transaction -Reason 'git reset --hard failed'
    }

    if ($env:RELEASE_TXN_TEST_FORCE_RESTORE_MISMATCH -eq '1') {
        Write-ReleaseRecoveryRequired -Transaction $Transaction -Reason 'test forced restore mismatch'
    }

    if ($Transaction.StashRef) {
        git -C $Transaction.ProjectRoot clean -fd 2>$null | Out-Null
        git -C $Transaction.ProjectRoot stash pop --index $Transaction.StashRef 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            git -C $Transaction.ProjectRoot stash apply --index $Transaction.StashRef 2>$null | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Write-ReleaseRecoveryRequired -Transaction $Transaction -Reason 'stash pop/apply failed — safety stash preserved'
            }
        }
        $expectedPorcelain = @($Transaction.StatusBefore -split "`n" | ForEach-Object { $_.TrimEnd() } | Where-Object { $_ })
        Remove-UntrackedExceptPorcelain -ProjectRoot $Transaction.ProjectRoot -ExpectedPorcelain $expectedPorcelain
    } else {
        git -C $Transaction.ProjectRoot clean -fd 2>$null | Out-Null
    }

    $versionPath = Join-Path $Transaction.ProjectRoot 'source\VERSION'
    if ($Transaction.OriginalVersion -and (Test-Path -LiteralPath $versionPath)) {
        $utf8 = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($versionPath, $Transaction.OriginalVersion + [Environment]::NewLine, $utf8)
    }

    $expected = @($Transaction.StatusBefore -split "`n" | ForEach-Object { $_.TrimEnd() } | Where-Object { $_ })
    $actual = Get-GitPorcelainLines -ProjectRoot $Transaction.ProjectRoot
    if (-not (Test-GitPorcelainEqual -Expected $expected -Actual $actual)) {
        if ($Transaction.StashRef) {
            Write-ReleaseRecoveryRequired -Transaction $Transaction -Reason 'git status after restore does not match transaction snapshot'
        }
    }

    if ($Transaction.StashRef) {
        $stashStillPresent = git -C $Transaction.ProjectRoot stash list 2>$null | Select-String -SimpleMatch $Transaction.StashRef
        if ($stashStillPresent) {
            git -C $Transaction.ProjectRoot stash drop $Transaction.StashRef 2>$null | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Write-ReleaseRecoveryRequired -Transaction $Transaction -Reason 'stash drop failed after verified restore'
            }
        }
        $Transaction.StashRef = $null
    }

    $ErrorActionPreference = $prevEap
    return $true
}

function New-ReleaseTransaction {
    param([string]$ProjectRoot)
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $txnId = [guid]::NewGuid().ToString('n').Substring(0, 12)
    $head = (git -C $ProjectRoot rev-parse HEAD).Trim()
    $branch = (git -C $ProjectRoot rev-parse --abbrev-ref HEAD).Trim()
    $versionPath = Join-Path $ProjectRoot 'source\VERSION'
    $originalVersion = if (Test-Path $versionPath) { (Get-Content -LiteralPath $versionPath -Raw).Trim() } else { '' }
    $statusLines = Get-GitPorcelainLines -ProjectRoot $ProjectRoot
    $statusBefore = ($statusLines -join "`n")
    $stashName = $null

    if (@($statusLines).Count -gt 0) {
        $pushOut = git -C $ProjectRoot stash push -u -m "release-txn:$txnId" 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) {
            throw "Release transaction: stash push failed: $pushOut"
        }
        if ($pushOut -notmatch 'No local changes to save') {
            $stashRef = (git -C $ProjectRoot stash list | Select-String -Pattern "release-txn:$txnId" | Select-Object -First 1)
            if (-not $stashRef) {
                throw 'Release transaction: could not locate safety stash after dirty push'
            }
            $stashName = ($stashRef.ToString() -split ':', 2)[0].Trim()
            git -C $ProjectRoot stash apply --index $stashName 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) {
                throw 'Release transaction: stash apply failed — safety stash preserved (not dropped)'
            }
        }
    }

    $txn = [PSCustomObject]@{
        Id = $txnId
        ProjectRoot = $ProjectRoot
        OriginalHead = $head
        OriginalBranch = $branch
        OriginalVersion = $originalVersion
        StatusBefore = $statusBefore
        StashRef = $stashName
        ReleaseCommit = $null
        Active = $true
        WasClean = (@($statusLines).Count -eq 0)
    }
    $ErrorActionPreference = $prevEap
    return $txn
}

function Complete-ReleaseTransaction {
    param($Transaction)
    if ($Transaction.StashRef) {
        $remaining = git -C $Transaction.ProjectRoot stash list 2>$null | Select-String -SimpleMatch $Transaction.StashRef
        if ($remaining) {
            git -C $Transaction.ProjectRoot stash drop $Transaction.StashRef 2>$null | Out-Null
        }
        $Transaction.StashRef = $null
    }
    $Transaction.Active = $false
}

function Abort-ReleaseTransaction {
    param(
        $Transaction,
        [string[]]$ReleasePathsToRemove = @()
    )
    if (-not $Transaction.Active) { return }

    Restore-ReleaseTransactionWorkingTree -Transaction $Transaction -ReleasePathsToRemove $ReleasePathsToRemove
    $Transaction.Active = $false
}

function Remove-ReleaseCommitIfAny {
    param($Transaction)
    if ($Transaction.ReleaseCommit) {
        git -C $Transaction.ProjectRoot reset --hard $Transaction.OriginalHead 2>$null | Out-Null
        $Transaction.ReleaseCommit = $null
        if ($Transaction.StashRef) {
            Restore-ReleaseTransactionWorkingTree -Transaction $Transaction
        }
    }
}
