#Requires -Version 5.1
Set-StrictMode -Version Latest

function New-ReleaseTransaction {
    param([string]$ProjectRoot)
    $txnId = [guid]::NewGuid().ToString('n').Substring(0, 12)
    $head = (git -C $ProjectRoot rev-parse HEAD).Trim()
    $branch = (git -C $ProjectRoot rev-parse --abbrev-ref HEAD).Trim()
    $versionPath = Join-Path $ProjectRoot 'source\VERSION'
    $originalVersion = if (Test-Path $versionPath) { (Get-Content -LiteralPath $versionPath -Raw).Trim() } else { '' }
    $statusBefore = (git -C $ProjectRoot status --porcelain=v1 2>$null)

    git -C $ProjectRoot stash push -u -m "release-txn:$txnId" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw 'Release transaction: stash push failed'
    }
    $stashRef = (git -C $ProjectRoot stash list | Select-String -Pattern "release-txn:$txnId" | Select-Object -First 1).ToString()
    if (-not $stashRef) { throw 'Release transaction: could not locate safety stash' }
    $stashName = ($stashRef -split ':', 2)[0].Trim()

    git -C $ProjectRoot stash apply --index $stashName | Out-Null
    if ($LASTEXITCODE -ne 0) {
        git -C $ProjectRoot stash drop $stashName | Out-Null
        throw 'Release transaction: stash apply failed'
    }

    return [PSCustomObject]@{
        Id = $txnId
        ProjectRoot = $ProjectRoot
        OriginalHead = $head
        OriginalBranch = $branch
        OriginalVersion = $originalVersion
        StatusBefore = $statusBefore
        StashRef = $stashName
        ReleaseCommit = $null
        Active = $true
    }
}

function Complete-ReleaseTransaction {
    param($Transaction)
    if ($Transaction.StashRef) {
        git -C $Transaction.ProjectRoot stash drop $Transaction.StashRef 2>$null | Out-Null
    }
    $Transaction.Active = $false
}

function Abort-ReleaseTransaction {
    param(
        $Transaction,
        [string[]]$ReleasePathsToRemove = @()
    )
    if (-not $Transaction.Active) { return }

    foreach ($p in $ReleasePathsToRemove) {
        if ($p -and (Test-Path -LiteralPath $p)) {
            Remove-Item -LiteralPath $p -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    git -C $Transaction.ProjectRoot reset --hard $Transaction.OriginalHead 2>$null | Out-Null
    git -C $Transaction.ProjectRoot clean -fd 2>$null | Out-Null

    if ($Transaction.StashRef) {
        git -C $Transaction.ProjectRoot stash pop --index $Transaction.StashRef 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            git -C $Transaction.ProjectRoot stash apply --index $Transaction.StashRef 2>$null | Out-Null
            git -C $Transaction.ProjectRoot stash drop $Transaction.StashRef 2>$null | Out-Null
        }
    }

    $versionPath = Join-Path $Transaction.ProjectRoot 'source\VERSION'
    if ($Transaction.OriginalVersion) {
        $utf8 = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($versionPath, $Transaction.OriginalVersion + [Environment]::NewLine, $utf8)
    }

    $Transaction.Active = $false
}

function Remove-ReleaseCommitIfAny {
    param($Transaction)
    if ($Transaction.ReleaseCommit) {
        git -C $Transaction.ProjectRoot reset --hard $Transaction.OriginalHead 2>$null | Out-Null
        $Transaction.ReleaseCommit = $null
    }
}
