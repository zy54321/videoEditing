#Requires -Version 5.1
<#
.SYNOPSIS
  Lightweight pre-release consistency checks.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$ProjectRoot = Split-Path -Parent $Root
$Payload = Join-Path $Root 'payload'
$Pass = 0
$Fail = 0

function Assert-True {
    param([bool]$Condition, [string]$Name)
    if ($Condition) {
        Write-Host "[PASS] $Name" -ForegroundColor Green
        $script:Pass++
    } else {
        Write-Host "[FAIL] $Name" -ForegroundColor Red
        $script:Fail++
    }
}

Write-Host '=== Pre-Release Consistency Tests ===' -ForegroundColor Cyan
Write-Host ''

# 1. Brief Required = Intake Gate Required
$briefRef = Get-Content (Join-Path $Payload 'video-workflow\templates\production-brief-reference.md') -Raw -Encoding UTF8
$intakeRule = Get-Content (Join-Path $Payload '.cursor\rules\production-entry-intake.mdc') -Raw -Encoding UTF8
$required = @('production.id', 'editing.skill', 'media.input', 'media.output', 'format.width', 'format.height', 'format.fps', 'output.filename')
$r1 = $true
foreach ($f in $required) {
    if ($briefRef -notmatch $f) { $r1 = $false }
    if ($intakeRule -notmatch $f) { $r1 = $false }
}
Assert-True $r1 'C01 Brief Required fields match Intake Gate Required fields'

# 2. production.id resolution rule
Assert-True ($intakeRule -match 'Production ID Resolution') 'C02 production.id resolution rule exists'
Assert-True ($intakeRule -match 'leaf directory name') 'C02 workspace leaf name candidate'

# 3. output.filename resolution rule
Assert-True ($intakeRule -match 'Output Filename Resolution') 'C03 output.filename resolution rule exists'
Assert-True ($intakeRule -match '_V1\.mp4') 'C03 default _V1.mp4 pattern'

# 4. manifest entry
$manifestTpl = Get-Content (Join-Path $Root 'manifest.template.json') -Raw -Encoding UTF8 | ConvertFrom-Json
Assert-True (($manifestTpl.PSObject.Properties.Name -contains 'entry') -and ($intakeRule -match $manifestTpl.entry)) 'C04 manifest entry matches intake rule'

# 5. manifest runtime model
Assert-True ($manifestTpl.runtime.model -eq 'external-runtime') 'C05 manifest runtime model exists'

# 6. production-entry-intake alwaysApply
Assert-True ($intakeRule -match 'alwaysApply:\s*true') 'C06 production-entry-intake alwaysApply=true'

# 7-8. L1 matrix summary vs rows
$l1 = Get-Content (Join-Path $Payload 'video-workflow\capabilities\davinci-resolve.md') -Raw -Encoding UTF8
$matrixTail = ($l1 -split '### Master Matrix', 2)[1]
$matrixSection = ($matrixTail -split '(?m)^---\s*$', 2)[0]
$rows = [regex]::Matches($matrixSection, '(?m)^\| ([\w.]+) \| [^|]+\| ([A-Z_]+) \|') | ForEach-Object {
    [PSCustomObject]@{ Id = $_.Groups[1].Value; Status = $_.Groups[2].Value }
}
$total = $rows.Count
$statusCounts = @{
    VERIFIED = 0
    AVAILABLE_UNVERIFIED = 0
    FAILED = 0
    UNKNOWN = 0
    UNAVAILABLE = 0
    DEFERRED = 0
}
foreach ($row in $rows) {
    if ($statusCounts.ContainsKey($row.Status)) {
        $statusCounts[$row.Status]++
    }
}
$sumStatuses = ($statusCounts.Values | Measure-Object -Sum).Sum
Assert-True ($total -gt 0) "C07 L1 matrix has $total rows"
Assert-True ($sumStatuses -eq $total) "C08 L1 status counts sum to total ($sumStatuses vs $total)"

# 9. N02 gate: subtitle.timing not MUST blocker
Assert-True ($l1 -match 'subtitle\.timing.*PRODUCTION_QA') 'C09 subtitle.timing marked PRODUCTION_QA'
Assert-True ($l1 -match 'N02_CAPABILITY_GATE[\s\S]*PASS') 'C09 N02_CAPABILITY_GATE PASS documented'
$mustRows = [regex]::Matches($l1, '\| \*\*MUST\*\* \|')
$noVerifiedConflict = $true
if ($l1 -match 'subtitle\.timing[\s\S]{0,120}\| \*\*MUST\*\*') { $noVerifiedConflict = $false }
Assert-True $noVerifiedConflict 'C09 subtitle.timing not N02 MUST blocker'

# 10. Installer ProductFiles all in payload preflight
$installer = Get-Content (Join-Path $Root 'installer\init-video-workflow.ps1') -Raw -Encoding UTF8
$pfMatch = [regex]::Match($installer, '\$ProductFiles = @\(([^)]+)\)', [System.Text.RegularExpressions.RegexOptions]::Singleline)
$productFiles = [regex]::Matches($pfMatch.Groups[1].Value, "'([^']+)'") | ForEach-Object { $_.Groups[1].Value }
$c10 = $true
foreach ($rel in $productFiles) {
    $p = Join-Path $Payload ($rel -replace '\\', '\')
    if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { $c10 = $false }
}
Assert-True ($installer -match 'foreach \(\$rel in \$ProductFiles\)' -and -not ($installer -match '\$RequiredPayloadFiles')) 'C10 installer uses single ProductFiles preflight'
Assert-True $c10 'C10 all ProductFiles exist in payload'

# 11. build dirty tree fail closed
$buildScript = Join-Path $Root 'build\build-release.ps1'
if (Test-Path -LiteralPath $buildScript) {
    $buildContent = Get-Content -LiteralPath $buildScript -Raw -Encoding UTF8
    Assert-True ($buildContent -match 'BLOCK_RELEASE_DIRTY_TREE') 'C11 build fails on dirty tree'
} else {
    Write-Host '[SKIP] C11 build-release.ps1 not present' -ForegroundColor Yellow
}

# 12. VERSION vs scope release state
$version = (Get-Content (Join-Path $Root 'VERSION') -Raw).Trim()
$scopeDoc = Get-Content (Join-Path $ProjectRoot 'docs\03-v0.1-scope.md') -Raw -Encoding UTF8
if ($scopeDoc -match '\| Release \| RELEASE_CANDIDATE \|') {
    Assert-True ($version -eq '0.1.0') 'C12 VERSION is 0.1.0 for RELEASE_CANDIDATE'
} elseif ($scopeDoc -match '\| Release \| RELEASED \|') {
    Assert-True ($version -eq '0.1.0') 'C12 VERSION is 0.1.0 for RELEASED'
} elseif ($scopeDoc -match '\| Release \| NOT STARTED \|') {
    Assert-True ($version -eq '0.1.0-dev') 'C12 VERSION is 0.1.0-dev before formal release'
} else {
    Assert-True $false 'C12 unrecognized Release scope state'
}

Write-Host ''
Write-Host "Results: $Pass passed, $Fail failed" -ForegroundColor $(if ($Fail -eq 0) { 'Green' } else { 'Red' })
if ($Fail -gt 0) { exit 1 }
exit 0
