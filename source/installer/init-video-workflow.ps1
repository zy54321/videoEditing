#Requires -Version 5.1
<#
.SYNOPSIS
  Video Editing Workflow — Single-Production Workspace Installer
#>
[CmdletBinding()]
param(
    [string]$TargetPath,
    [string]$WorkspaceName,
    [string]$PayloadRoot,
    [switch]$DryRun,
    [switch]$NoPause,
    [switch]$TestSimulateFailure,
    [int]$TestSimulateFailureAfter = 1
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Exit codes
$EXIT_SUCCESS = 0
$EXIT_CANCELLED = 2
$EXIT_TARGET_NOT_FOUND = 10
$EXIT_TARGET_NOT_WRITABLE = 11
$EXIT_WORKSPACE_EXISTS = 12
$EXIT_WORKSPACE_NAME_INVALID = 13
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
    '.cursor\skills\video-editing\observational-info-short\style-profile.yaml',
    '.cursor\skills\video-editing\observational-info-short\capability-policy.yaml',
    '.cursor\skills\video-editing\observational-info-short\capability-coverage.yaml',
    '.cursor\skills\video-editing\observational-info-short\references\01-directing.md',
    '.cursor\skills\video-editing\observational-info-short\references\02-visual-language.md',
    '.cursor\skills\video-editing\observational-info-short\references\03-editing-rhythm.md',
    '.cursor\skills\video-editing\observational-info-short\references\04-typography-graphics.md',
    '.cursor\skills\video-editing\observational-info-short\references\05-sound-music.md',
    '.cursor\skills\video-editing\observational-info-short\references\06-color-look-effects.md',
    '.cursor\skills\video-editing\observational-info-short\references\07-taste.md',
    '.cursor\skills\video-editing\observational-info-short\references\08-qa.md',
    '.cursor\skills\video-editing\observational-info-short\references\directing.md',
    '.cursor\skills\video-editing\observational-info-short\references\visual-language.md',
    '.cursor\skills\video-editing\observational-info-short\references\editing.md',
    '.cursor\skills\video-editing\observational-info-short\references\typography-graphics.md',
    '.cursor\skills\video-editing\observational-info-short\references\sound-music.md',
    '.cursor\skills\video-editing\observational-info-short\references\color-effects.md',
    '.cursor\skills\video-editing\observational-info-short\references\qa.md',
    '.cursor\skills\video-editing\observational-info-short\references\style.md',
    'video-workflow\capabilities\davinci-resolve.md',
    'video-workflow\capabilities\logical-capability-vocabulary.yaml',
    'video-workflow\knowledge\editing-craft\README.md',
    'video-workflow\knowledge\editing-craft\directing-story.md',
    'video-workflow\knowledge\editing-craft\visual-language.md',
    'video-workflow\knowledge\editing-craft\editing-rhythm.md',
    'video-workflow\knowledge\editing-craft\writing-and-picture.md',
    'video-workflow\knowledge\editing-craft\typography-graphics.md',
    'video-workflow\knowledge\editing-craft\sound-music.md',
    'video-workflow\knowledge\editing-craft\color-look-effects.md',
    'video-workflow\knowledge\editing-craft\aesthetic-qa.md',
    'video-workflow\knowledge\editing-craft\reference-cards\README.md',
    'video-workflow\knowledge\editing-craft\reference-cards\RC-VIS-001.yaml',
    'video-workflow\templates\style-skill\SKILL.md',
    'video-workflow\templates\style-skill\style-profile.yaml',
    'video-workflow\templates\style-skill\capability-policy.yaml',
    'video-workflow\templates\style-skill\references\01-directing.md',
    'video-workflow\templates\style-skill\references\02-visual-language.md',
    'video-workflow\templates\style-skill\references\03-editing-rhythm.md',
    'video-workflow\templates\style-skill\references\04-typography-graphics.md',
    'video-workflow\templates\style-skill\references\05-sound-music.md',
    'video-workflow\templates\style-skill\references\06-color-look-effects.md',
    'video-workflow\templates\style-skill\references\07-taste.md',
    'video-workflow\templates\style-skill\references\08-qa.md',
    'video-workflow\templates\style-profile-schema.yaml',
    'video-workflow\templates\production-brief.yaml',
    'video-workflow\templates\production-brief-reference.md',
    'video-workflow\templates\edit-blueprint.yaml',
    'video-workflow\templates\edit-blueprint-reference.md',
    'video-workflow\templates\capability-resolution-result.yaml',
    'video-workflow\templates\capability-resolution-reference.md',
    'video-workflow\templates\subtitle-layout-reference.md',
    'video-workflow\templates\subtitle-layout-request.json',
    'video-workflow\templates\subtitle-layout-result.json',
    'video-workflow\tools\final-artifact-qa.ps1',
    'video-workflow\tools\subtitle-layout-preflight.ps1',
    'video-workflow\tools\lib\subtitle-layout-engine.ps1',
    'video-workflow\tools\lib\textplus-layout-materializer.ps1',
    'video-workflow\tools\generate-textplus-cls-setting.py',
    'video-workflow\tools\lib\textplus_cls_setting.py',
    'video-workflow\runtime\textplus-font-profiles.yaml',
    'video-workflow\runtime\textplus-production-profile.yaml',
    'video-workflow\runtime\textplus-cls-canonical.setting'
)

$CreatedPaths = [System.Collections.Generic.List[string]]::new()
$PreExistingPaths = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$CopyStarted = $false
$WorkspaceRootCreated = $false
$parentPath = $null
$workspace = $null

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
    Write-Host '请使用 Cursor 打开以上 Workspace。'
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

function Test-WorkspaceNameValid {
    param([string]$Name)
    if ([string]::IsNullOrWhiteSpace($Name)) { return $false }
    if ($Name -eq '.' -or $Name -eq '..') { return $false }
    if ($Name -match '[\\/:*?"<>|]') { return $false }
    if ($Name.Trim() -ne $Name) { return $false }
    if ($Name.Contains('..')) { return $false }
    return $true
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

function Register-PreExistingPaths {
    param([string]$Workspace)
    $candidates = @(
        '.cursor',
        '.cursor\rules',
        '.cursor\skills',
        'video-workflow',
        'video-workflow\capabilities',
        'video-workflow\knowledge',
        'video-workflow\knowledge\editing-craft',
        'video-workflow\tools',
        'video-workflow\templates',
        'video-workflow\production'
    )
    foreach ($rel in $candidates) {
        $p = Join-Path $Workspace $rel
        if (Test-Path -LiteralPath $p) {
            $PreExistingPaths.Add([System.IO.Path]::GetFullPath($p)) | Out-Null
        }
    }
}

function Test-PayloadFile {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
    try {
        $fs = [System.IO.File]::OpenRead($Path)
        $fs.Close()
        return $true
    } catch {
        return $false
    }
}

function Remove-EmptyProductDirs {
    param([string]$Workspace)
    $relDirs = @(
        '.cursor\skills\video-editing\observational-info-short\references',
        '.cursor\skills\video-editing\observational-info-short',
        '.cursor\skills\video-editing',
        '.cursor\skills\video-production',
        '.cursor\skills',
        '.cursor\rules',
        '.cursor',
        'video-workflow\production',
        'video-workflow\templates',
        'video-workflow\tools',
        'video-workflow\knowledge\editing-craft',
        'video-workflow\knowledge',
        'video-workflow\capabilities',
        'video-workflow'
    )
    foreach ($rel in $relDirs) {
        $p = Join-Path $Workspace $rel
        if (-not (Test-Path -LiteralPath $p)) { continue }
        $full = [System.IO.Path]::GetFullPath($p)
        if ($PreExistingPaths.Contains($full)) { continue }
        if ((Get-ChildItem -LiteralPath $p -Force | Measure-Object).Count -eq 0) {
            try { Remove-Item -LiteralPath $p -Force -Recurse } catch { }
        }
    }
}

function Remove-WorkspaceRootIfCreated {
    param(
        [string]$Workspace,
        [bool]$WasCreated
    )
    if (-not $WasCreated) { return }
    if ([string]::IsNullOrWhiteSpace($Workspace)) { return }
    if (-not (Test-Path -LiteralPath $Workspace)) { return }
    try {
        Remove-Item -LiteralPath $Workspace -Recurse -Force
    } catch { }
}

function Rollback-Created {
    param(
        [string]$Workspace,
        [bool]$RemoveWorkspaceRoot = $false
    )
    foreach ($p in ($CreatedPaths | Where-Object { -not (Test-Path -LiteralPath $_ -PathType Container) } | Sort-Object { $_.Length } -Descending)) {
        if (Test-Path -LiteralPath $p) {
            try { Remove-Item -LiteralPath $p -Force } catch { }
        }
    }
    foreach ($p in ($CreatedPaths | Where-Object { Test-Path -LiteralPath $_ -PathType Container } | Sort-Object { $_.Length } -Descending)) {
        $full = [System.IO.Path]::GetFullPath($p)
        if ($PreExistingPaths.Contains($full)) { continue }
        if (-not (Test-Path -LiteralPath $p)) { continue }
        try {
            if ((Get-ChildItem -LiteralPath $p -Force | Measure-Object).Count -eq 0) {
                Remove-Item -LiteralPath $p -Force -Recurse
            }
        } catch { }
    }
    if ($Workspace) { Remove-EmptyProductDirs -Workspace $Workspace }
    Remove-WorkspaceRootIfCreated -Workspace $Workspace -WasCreated:$RemoveWorkspaceRoot
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
    if ($PayloadRoot) {
        $payloadRoot = [System.IO.Path]::GetFullPath($PayloadRoot)
    } else {
        $payloadRoot = Resolve-PayloadRoot
    }
    if (-not $payloadRoot -or -not (Test-Path -LiteralPath $payloadRoot -PathType Container)) {
        Write-ErrorAndExit -Code 'PAYLOAD_NOT_FOUND' -Message 'Could not locate payload directory.' -ExitCode $EXIT_PAYLOAD_NOT_FOUND
    }

    $missingPayload = @()
    foreach ($rel in $ProductFiles) {
        $p = Join-Path $payloadRoot ($rel -replace '\\', [IO.Path]::DirectorySeparatorChar)
        if (-not (Test-PayloadFile -Path $p)) { $missingPayload += $rel }
    }
    if ($missingPayload.Count -gt 0) {
        Write-ErrorAndExit -Code 'PAYLOAD_INVALID' -Message ("Missing or unreadable: {0}" -f ($missingPayload -join ', ')) -ExitCode $EXIT_PAYLOAD_INVALID
    }

    if (-not $TargetPath) {
        Add-Type -AssemblyName System.Windows.Forms | Out-Null
        $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
        $dialog.Description = '请选择存放本次 Production Workspace 的父目录，然后输入 Workspace 名称。'
        $dialog.ShowNewFolderButton = $true
        $result = $dialog.ShowDialog()
        if ($result -ne [System.Windows.Forms.DialogResult]::OK) {
            Write-Host 'INSTALL_CANCELLED'
            if (-not $NoPause) { Read-Host '按 Enter 键关闭' }
            exit $EXIT_CANCELLED
        }
        $TargetPath = $dialog.SelectedPath
    }

    if ([string]::IsNullOrWhiteSpace($TargetPath)) {
        Write-ErrorAndExit -Code 'TARGET_PARENT_NOT_FOUND' -Message 'Workspace parent path is empty.' -ExitCode $EXIT_TARGET_NOT_FOUND
    }

    $parentPath = [System.IO.Path]::GetFullPath($TargetPath.Trim())

    if (-not $WorkspaceName) {
        if ($PSCmdlet.MyInvocation.BoundParameters.ContainsKey('TargetPath')) {
            Write-ErrorAndExit -Code 'WORKSPACE_NAME_REQUIRED' -Message 'WorkspaceName is required when TargetPath is supplied on the command line.' -ExitCode $EXIT_WORKSPACE_NAME_INVALID
        }
        Write-Host ''
        Write-Host '请输入 Workspace 名称（将创建于所选父目录下）：'
        $WorkspaceName = Read-Host 'Workspace Name'
    }

    if (-not (Test-WorkspaceNameValid -Name $WorkspaceName)) {
        Write-ErrorAndExit -Code 'WORKSPACE_NAME_INVALID' -Message 'Workspace name must be a single non-empty directory name without path separators or illegal characters.' -ExitCode $EXIT_WORKSPACE_NAME_INVALID
    }

    $workspace = [System.IO.Path]::GetFullPath((Join-Path $parentPath $WorkspaceName))
    $parentNormalized = [System.IO.Path]::GetFullPath($parentPath)
    if (-not $workspace.StartsWith($parentNormalized.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) {
        Write-ErrorAndExit -Code 'WORKSPACE_NAME_INVALID' -Message 'Workspace name resolves outside the selected parent directory.' -ExitCode $EXIT_WORKSPACE_NAME_INVALID
    }

    Write-Host ''
    Write-Host 'Parent:'
    Write-Host $parentPath
    Write-Host ''
    Write-Host 'Workspace:'
    Write-Host $workspace
    Write-Host ''
    Write-Host 'Media input/output 将在以后输入【制作视频】时由 Agent 主动询问。'
    Write-Host ''

    if (-not (Test-Path -LiteralPath $parentPath -PathType Container)) {
        Write-ErrorAndExit -Code 'TARGET_PARENT_NOT_FOUND' -Message "Parent directory does not exist: $parentPath" -ExitCode $EXIT_TARGET_NOT_FOUND
    }

    if (-not (Test-TargetWritable -Path $parentPath)) {
        Write-ErrorAndExit -Code 'TARGET_PARENT_NOT_WRITABLE' -Message "Cannot write to parent directory: $parentPath" -ExitCode $EXIT_TARGET_NOT_WRITABLE
    }

    if (Test-Path -LiteralPath $workspace) {
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
        Write-ErrorAndExit -Code 'WORKSPACE_DIRECTORY_EXISTS' -Message "Workspace directory already exists: $workspace" -ExitCode $EXIT_WORKSPACE_EXISTS
    }

    $briefPath = Join-Path $workspace 'video-workflow\production\brief.yaml'
    if (Test-Path -LiteralPath $briefPath) {
        Write-ErrorAndExit -Code 'PRODUCTION_ALREADY_BOUND' -Message 'brief.yaml already exists. This workspace is bound to a production.' -ExitCode $EXIT_PRODUCTION_BOUND
    }

    if ($DryRun) {
        Write-Host 'DRY RUN — no files will be written.'
        Write-Host ''
        Write-Host 'Parent:'
        Write-Host $parentPath
        Write-Host ''
        Write-Host 'Workspace:'
        Write-Host $workspace
        Write-Host ''
        Write-Host 'Would create:'
        foreach ($rel in $ProductFiles) {
            Write-Host "  $WorkspaceName\$rel"
        }
        Write-Host "  $WorkspaceName\video-workflow\production\  (empty)"
        Write-Host "  $WorkspaceName\video-workflow\installation.json"
        Write-Host ''
        Write-Host 'STATUS: DRY_RUN_PASS'
        exit $EXIT_SUCCESS
    }

    try {
        New-Item -ItemType Directory -Path $workspace -Force | Out-Null
        $WorkspaceRootCreated = $true
        $CreatedPaths.Add($workspace) | Out-Null
    } catch {
        Write-ErrorAndExit -Code 'WORKSPACE_CREATE_FAILED' -Message $_.Exception.Message -ExitCode $EXIT_TARGET_NOT_WRITABLE
    }

    Register-PreExistingPaths -Workspace $workspace

    $CopyStarted = $true
    $copyIndex = 0
    foreach ($rel in $ProductFiles) {
        try {
            Copy-ProductFile -SourceRoot $payloadRoot -Workspace $workspace -RelativePath $rel
            $copyIndex++
            if ($TestSimulateFailure -and $copyIndex -eq $TestSimulateFailureAfter) {
                throw 'TestSimulateFailure: simulated copy failure'
            }
        } catch {
            Rollback-Created -Workspace $workspace -RemoveWorkspaceRoot:$WorkspaceRootCreated
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
        Rollback-Created -Workspace $workspace -RemoveWorkspaceRoot:$WorkspaceRootCreated
        Write-ErrorAndExit -Code 'INSTALL_COPY_FAILED' -Message $_.Exception.Message -ExitCode $EXIT_COPY_FAILED
    }

    try {
        Verify-Installation -Workspace $workspace -Version $version
    } catch {
        Rollback-Created -Workspace $workspace -RemoveWorkspaceRoot:$WorkspaceRootCreated
        if (Test-Path -LiteralPath $installJsonPath) { Remove-Item -LiteralPath $installJsonPath -Force }
        Write-ErrorAndExit -Code 'INSTALL_VERIFY_FAILED' -Message $_.Exception.Message -ExitCode $EXIT_VERIFY_FAILED
    }

    $WorkspaceRootCreated = $false
    Write-SuccessAndExit -Version $version -Workspace $workspace
} catch {
    if ($workspace) {
        Rollback-Created -Workspace $workspace -RemoveWorkspaceRoot:$WorkspaceRootCreated
    } else {
        Rollback-Created
    }
    Write-ErrorAndExit -Code 'INSTALL_COPY_FAILED' -Message $_.Exception.Message -ExitCode $EXIT_COPY_FAILED
}
