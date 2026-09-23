Add-Type -AssemblyName System.Drawing
[System.Drawing.FontFamily]::Families | ForEach-Object { $_.Name } | Sort-Object | Out-File -FilePath (Join-Path $PSScriptRoot 'evidence\system-drawing-families.txt') -Encoding utf8
Write-Output (Join-Path $PSScriptRoot 'evidence\system-drawing-families.txt')
