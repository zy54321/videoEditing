#Requires -Version 5.1
<#
.SYNOPSIS
  Video Editing Workflow — Single-Production Workspace Installer
#>
[CmdletBinding()]
param(
    [string]$TargetPath,
    [switch]$DryRun,
    [switch]$NoPause
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Exit codes
$EXIT_SUCCESS = 0
$EXIT_CANCELLED = 2
$EXIT_TARGET_NOT_FOUND = 10
$EXIT_TARGET_NOT_WRITABLE = 11
$EXIT_PAYLOAD_NOT_FOUND = 20
$EXIT_PAYLOAD_INVALID = 21
$EXIT_FILE_CONFLICT = 30
$EXIT_ALREADY_INITIALIZED = 31
$EXIT_STATE_INVALID = 32
$EXIT_PRODUCTION_BOUND = 33
$EXIT_COPY_FAILED = 40
$EXIT_VERIFY_FAILED = 41

$ProductFiles = @(
    '.cursor\rules\video-workflow-core.mdc',
    '.cursor\rules\davinci-production.mdc',
    '.cursor\rules\production-entry-intake.mdc',
    '.cursor\skills\video-production\SKILL.md',
    '.cursor\skills\video-editing\observational-info-short\SKILL.md',
    '.cursor\skills\video-editing\observational-info-short\references\style.md',
    '.cursor\skills\video-editing\observational-info-short\references\qa.md',
    'video-workflow\capabilities\davinci-resolve.md',
    'video-workflow\templates\production-brief.yaml',
    'video-workflow\templates\production-brief-reference.md'
)

$RequiredPayloadFiles = @(
    '.cursor\rules\video-workflow-core.mdc',
    '.cursor\rules\davinci-production.mdc',
    '.cursor\rules\production-entry-intake.mdc',
    '.cursor\skills\video-production\SKILL.md',
    '.cursor\skills\video-editing\observational-info-short\SKILL.md',
    'video-workflow\capabilities\davinci-resolve.md',
    'video-workflow\templates\production-brief.yaml'
)

$CreatedPaths = [System.Collections.Generic.List[string]]::new()

function Write-ErrorAndExit {
    param(
        [string]$Code,
        [string]$Message,
        [int]$ExitCode
    )
    Write-Host ''
    Write-Host 'ERROR:' -ForegroundColor Red
    Write-Host $Code
    if ($Message) { Write-Host $Message }
    if (-not $NoPause) {
        Write-Host ''
        Read-Host '按 Enter 键关闭'
    }
    exit $ExitCode
}

function Write-SuccessAndExit {
    param(
        [string]$Version,
        [string]$Workspace
    )
    Write-Host ''
    Write-Host '========================================' -ForegroundColor Green
    Write-Host 'Video Editing Workflow 安装完成' -ForegroundColor Green
    Write-Host '========================================' -ForegroundColor Green
    Write-Host ''
    Write-Host "版本："
    Write-Host $Version
    Write-Host ''
    Write-Host "Workspace："
    Write-Host $Workspace
    Write-Host ''
    Write-Host '实例模式：'
    Write-Host 'Single Production'
    Write-Host ''
    Write-Host '下一步：'
    Write-Host ''
    Write-Host '1. 用 Cursor 打开这个 Workspace'
    Write-Host '2. 输入：'
    Write-Host ''
    Write-Host '【制作视频】'
    Write-Host ''
    Write-Host 'Agent 会主动询问：'
    Write-Host '- 视频类型'
    Write-Host '- input'
    Write-Host '- output'
    Write-Host ''
    Write-Host '无需编写复杂 Prompt。'
    Write-Host ''
    Write-Host '注意：'
    Write-Host '这个 Workspace 只用于一条视频 Production。'
    Write-Host '制作新视频请重新运行 Release 初始化新的 Workspace。'
    Write-Host ''
    Write-Host 'STATUS: PASS' -ForegroundColor Green
    if (-not $NoPause) {
        Write-Host ''
        Read-Host '按 Enter 键关闭'
    }
    exit $EXIT_SUCCESS
}

function Resolve-PayloadRoot {
    $candidates = @(
        (Join-Path $PSScriptRoot 'payload'),
        (Join-Path $PSScriptRoot '..\payload')
    )
    foreach ($c in $candidates) {
        $resolved = [System.IO.Path]::GetFullPath($c)
        if (Test-Path -LiteralPath $resolved -PathType Container) {
            return $resolved
        }
    }
    return $null
}

function Get-ProductVersion {
    $candidates = @(
        (Join-Path $PSScriptRoot 'VERSION'),
        (Join-Path $PSScriptRoot '..\VERSION')
    )
    foreach ($c in $candidates) {
        if (Test-Path -LiteralPath $c -PathType Leaf) {
            $v = (Get-Content -LiteralPath $c -Raw).Trim()
            if ($v) { return $v }
        }
    }
    throw 'VERSION file not found'
}

function Test-TargetWritable {
    param([string]$Path)
    try {
        $testFile = Join-Path $Path (".vew-write-test-{0}" -f [guid]::NewGuid().ToString('N'))
        [System.IO.File]::WriteAllText($testFile, 'ok')
        Remove-Item -LiteralPath $testFile -Force
        return $true
    } catch {
        return $false
    }
}

function Get-InstallationState {
    param([string]$Workspace)
    $jsonPath = Join-Path $Workspace 'video-workflow\installation.json'
    if (-not (Test-Path -LiteralPath $jsonPath)) {
        return @{ Exists = $false }
    }
    try {
        $raw = Get-Content -LiteralPath $jsonPath -Raw -Encoding UTF8
        $obj = $raw | ConvertFrom-Json
        if ($obj.product -ne 'video-editing-workflow') {
            return @{ Exists = $true; Valid = $false; Path = $jsonPath }
        }
        return @{ Exists = $true; Valid = $true; Object = $obj; Path = $jsonPath }
    } catch {
        return @{ Exists = $true; Valid = $false; Path = $jsonPath }
    }
}

function Rollback-Created {
    foreach ($p in ($CreatedPaths | Sort-Object { $_.Length } -Descending)) {
        if (Test-Path -LiteralPath $p) {
            try {
                if ((Get-Item -LiteralPath $p).PSIsContainer) {
                    if ((Get-ChildItem -LiteralPath $p -Force | Measure-Object).Count -eq 0) {
                        Remove-Item -LiteralPath $p -Force -Recurse
                    }
                } else {
                    Remove-Item -LiteralPath $p -Force
                }
            } catch {
                # best effort
            }
        }
    }
}

function Copy-ProductFile {
    param(
        [string]$SourceRoot,
        [string]$Workspace,
        [string]$RelativePath
    )
    $src = Join-Path $SourceRoot ($RelativePath -replace '\\', [IO.Path]::DirectorySeparatorChar)
    $dst = Join-Path $Workspace $RelativePath
    $dstDir = Split-Path -Parent $dst
    if (-not (Test-Path -LiteralPath $dstDir)) {
        New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
        if ($CreatedPaths -notcontains $dstDir) { $CreatedPaths.Add($dstDir) | Out-Null }
    }
    Copy-Item -LiteralPath $src -Destination $dst -Force
    if ($CreatedPaths -notcontains $dst) { $CreatedPaths.Add($dst) | Out-Null }
}

function Verify-Installation {
    param(
        [string]$Workspace,
        [string]$Version
    )
    foreach ($rel in $ProductFiles) {
        $p = Join-Path $Workspace $rel
        if (-not (Test-Path -LiteralPath $p -PathType Leaf)) {
            throw "Missing installed file: $rel"
        }
    }
    $prodDir = Join-Path $Workspace 'video-workflow\production'
    if (-not (Test-Path -LiteralPath $prodDir -PathType Container)) {
        throw 'Missing video-workflow\production directory'
    }
    $brief = Join-Path $prodDir 'brief.yaml'
    if (Test-Path -LiteralPath $brief) {
        throw 'brief.yaml must not exist after install'
    }
    $jsonPath = Join-Path $Workspace 'video-workflow\installation.json'
    if (-not (Test-Path -LiteralPath $jsonPath)) {
        throw 'Missing installation.json'
    }
    $null = Get-Content -LiteralPath $jsonPath -Raw | ConvertFrom-Json
}

# --- Main ---

try {
    $version = Get-ProductVersion
    $payloadRoot = Resolve-PayloadRoot
    if (-not $payloadRoot) {
        Write-ErrorAndExit -Code 'PAYLOAD_NOT_FOUND' -Message 'Could not locate payload directory.' -ExitCode $EXIT_PAYLOAD_NOT_FOUND
    }

    $missingPayload = @()
    foreach ($rel in $RequiredPayloadFiles) {
        $p = Join-Path $payloadRoot ($rel -replace '\\', [IO.Path]::DirectorySeparatorChar)
        if (-not (Test-Path -LiteralPath $p)) { $missingPayload += $rel }
    }
    if ($missingPayload.Count -gt 0) {
        Write-ErrorAndExit -Code 'PAYLOAD_INVALID' -Message ("Missing: {0}" -f ($missingPayload -join ', ')) -ExitCode $EXIT_PAYLOAD_INVALID
    }

    if (-not $TargetPath) {
        Add-Type -AssemblyName System.Windows.Forms | Out-Null
        $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
        $dialog.Description = '请选择本次视频 Production 的 Cursor Workspace。一个 Workspace 只服务一个 Production。'
        $dialog.ShowNewFolderButton = $false
        $result = $dialog.ShowDialog()
        if ($result -ne [System.Windows.Forms.DialogResult]::OK) {
            Write-Host 'INSTALL_CANCELLED'
            if (-not $NoPause) { Read-Host '按 Enter 键关闭' }
            exit $EXIT_CANCELLED
        }
        $TargetPath = $dialog.SelectedPath
    }

    if ([string]::IsNullOrWhiteSpace($TargetPath)) {
        Write-ErrorAndExit -Code 'TARGET_WORKSPACE_NOT_FOUND' -Message 'Target path is empty.' -ExitCode $EXIT_TARGET_NOT_FOUND
    }

    $workspace = [System.IO.Path]::GetFullPath($TargetPath.Trim())

    Write-Host ''
    Write-Host 'Target Workspace:'
    Write-Host $workspace
    Write-Host ''
    Write-Host 'Media input/output 将在以后输入【制作视频】时由 Agent 主动询问。'
    Write-Host ''

    if (-not (Test-Path -LiteralPath $workspace -PathType Container)) {
        Write-ErrorAndExit -Code 'TARGET_WORKSPACE_NOT_FOUND' -Message "Directory does not exist: $workspace" -ExitCode $EXIT_TARGET_NOT_FOUND
    }

    if (-not (Test-TargetWritable -Path $workspace)) {
        Write-ErrorAndExit -Code 'TARGET_WORKSPACE_NOT_WRITABLE' -Message "Cannot write to: $workspace" -ExitCode $EXIT_TARGET_NOT_WRITABLE
    }

    $briefPath = Join-Path $workspace 'video-workflow\production\brief.yaml'
    if (Test-Path -LiteralPath $briefPath) {
        Write-ErrorAndExit -Code 'PRODUCTION_ALREADY_BOUND' -Message 'brief.yaml already exists. This workspace is bound to a production.' -ExitCode $EXIT_PRODUCTION_BOUND
    }

    $installState = Get-InstallationState -Workspace $workspace
    if ($installState.Exists) {
        if (-not $installState.Valid) {
            Write-ErrorAndExit -Code 'INSTALLATION_STATE_INVALID' -Message "Invalid installation.json at $($installState.Path)" -ExitCode $EXIT_STATE_INVALID
        }
        $obj = $installState.Object
        Write-Host 'ERROR:'
        Write-Host 'WORKSPACE_ALREADY_INITIALIZED'
        Write-Host ''
        Write-Host "Installed version: $($obj.version)"
        Write-Host "Install time: $($obj.installed_at)"
        Write-Host "Workspace: $($obj.workspace)"
        Write-Host ''
        Write-Host '此 Workspace 已经是 Single-Production Instance。制作新视频请初始化另一个 Workspace。'
        if (-not $NoPause) { Read-Host '按 Enter 键关闭' }
        exit $EXIT_ALREADY_INITIALIZED
    }

    $conflicts = @()
    foreach ($rel in $ProductFiles) {
        $dst = Join-Path $workspace $rel
        if (Test-Path -LiteralPath $dst) { $conflicts += $rel }
    }
    $installJsonDst = Join-Path $workspace 'video-workflow\installation.json'
    if (Test-Path -LiteralPath $installJsonDst) { $conflicts += 'video-workflow\installation.json' }

    if ($conflicts.Count -gt 0) {
        Write-ErrorAndExit -Code 'INSTALL_FILE_CONFLICT' -Message ("Conflicting files:{0}{1}" -f [Environment]::NewLine, ($conflicts -join [Environment]::NewLine)) -ExitCode $EXIT_FILE_CONFLICT
    }

    if ($DryRun) {
        Write-Host 'DRY RUN — no files will be written.'
        Write-Host ''
        Write-Host 'Would create:'
        foreach ($rel in $ProductFiles) {
            Write-Host "  $rel"
        }
        Write-Host '  video-workflow\production\  (empty)'
        Write-Host '  video-workflow\installation.json'
        Write-Host ''
        Write-Host 'STATUS: DRY_RUN_PASS'
        exit $EXIT_SUCCESS
    }

    foreach ($rel in $ProductFiles) {
        try {
            Copy-ProductFile -SourceRoot $payloadRoot -Workspace $workspace -RelativePath $rel
        } catch {
            Rollback-Created
            Write-ErrorAndExit -Code 'INSTALL_COPY_FAILED' -Message $_.Exception.Message -ExitCode $EXIT_COPY_FAILED
        }
    }

    $prodDir = Join-Path $workspace 'video-workflow\production'
    if (-not (Test-Path -LiteralPath $prodDir)) {
        New-Item -ItemType Directory -Path $prodDir -Force | Out-Null
        $CreatedPaths.Add($prodDir) | Out-Null
    }

    $installDoc = @{
        product = 'video-editing-workflow'
        version = $version
        instance_model = 'single-production'
        installed_at = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ssK')
        workspace = $workspace
        brief_created = $false
    } | ConvertTo-Json -Depth 3

    $installJsonPath = Join-Path $workspace 'video-workflow\installation.json'
    try {
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($installJsonPath, $installDoc + [Environment]::NewLine, $utf8NoBom)
        $CreatedPaths.Add($installJsonPath) | Out-Null
    } catch {
        Rollback-Created
        Write-ErrorAndExit -Code 'INSTALL_COPY_FAILED' -Message $_.Exception.Message -ExitCode $EXIT_COPY_FAILED
    }

    try {
        Verify-Installation -Workspace $workspace -Version $version
    } catch {
        Rollback-Created
        if (Test-Path -LiteralPath $installJsonPath) { Remove-Item -LiteralPath $installJsonPath -Force }
        Write-ErrorAndExit -Code 'INSTALL_VERIFY_FAILED' -Message $_.Exception.Message -ExitCode $EXIT_VERIFY_FAILED
    }

    Write-SuccessAndExit -Version $version -Workspace $workspace
} catch {
    Rollback-Created
    Write-ErrorAndExit -Code 'INSTALL_COPY_FAILED' -Message $_.Exception.Message -ExitCode $EXIT_COPY_FAILED
}
