param(
    [Parameter(Mandatory = $true)]
    [string]$Destination
)

$ErrorActionPreference = 'Stop'

$skillRoot = Split-Path -Parent $PSScriptRoot
$template = Join-Path $skillRoot 'assets\slides-template.md'
$themeSource = Join-Path $skillRoot 'assets\theme'
$destinationRoot = [System.IO.Path]::GetFullPath($Destination)
$slidesTarget = Join-Path $destinationRoot 'slides.md'
$themeTarget = Join-Path $destinationRoot 'theme'
$assetsTarget = Join-Path $destinationRoot 'assets'

if (Test-Path -LiteralPath $slidesTarget) {
    throw "Refusing to overwrite existing file: $slidesTarget"
}
if (Test-Path -LiteralPath $themeTarget) {
    throw "Refusing to replace existing directory: $themeTarget"
}
if (-not (Test-Path -LiteralPath $template -PathType Leaf)) {
    throw "Template is missing: $template"
}
if (-not (Test-Path -LiteralPath $themeSource -PathType Container)) {
    throw "Theme is missing: $themeSource"
}

New-Item -ItemType Directory -Path $destinationRoot -Force | Out-Null
New-Item -ItemType Directory -Path $assetsTarget -Force | Out-Null
Copy-Item -LiteralPath $template -Destination $slidesTarget
Copy-Item -LiteralPath $themeSource -Destination $themeTarget -Recurse

Write-Output $slidesTarget
Write-Output $themeTarget
Write-Output $assetsTarget
