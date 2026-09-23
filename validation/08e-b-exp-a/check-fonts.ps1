. (Join-Path (Split-Path $PSScriptRoot -Parent -Parent) 'source\payload\video-workflow\tools\lib\subtitle-layout-engine.ps1')
$n = Get-InstalledFontNames
foreach ($c in @('Microsoft YaHei','Microsoft YaHei UI','SimHei','SimSun','Arial','Segoe UI')) {
    Write-Output "$c=$($n.Contains($c))"
}
