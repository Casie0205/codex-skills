param(
    [string]$TargetRoot,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$packageRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$manifestPath = Join-Path $packageRoot 'manifest.json'

if (-not (Test-Path -LiteralPath $manifestPath)) {
    throw "Skill manifest not found: $manifestPath"
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json

if ([string]::IsNullOrWhiteSpace($TargetRoot)) {
    if (-not [string]::IsNullOrWhiteSpace($env:CODEX_HOME)) {
        $TargetRoot = Join-Path $env:CODEX_HOME 'skills'
    } else {
        $TargetRoot = Join-Path $HOME '.codex\skills'
    }
}

$targetRootResolved = [System.IO.Path]::GetFullPath($TargetRoot)
$installDirName = if ([string]::IsNullOrWhiteSpace($manifest.install_dir_name)) { $manifest.name } else { $manifest.install_dir_name }
$targetDir = Join-Path $targetRootResolved $installDirName
$backupDir = "$targetDir.bak"

New-Item -ItemType Directory -Force -Path $targetRootResolved | Out-Null

$existingVersion = $null
$existingManifestPath = Join-Path $targetDir 'manifest.json'
if (Test-Path -LiteralPath $existingManifestPath) {
    try {
        $existingManifest = Get-Content -LiteralPath $existingManifestPath -Raw | ConvertFrom-Json
        $existingVersion = $existingManifest.skill_version
    } catch {
        $existingVersion = $null
    }
}

if ((Test-Path -LiteralPath $targetDir) -and -not $Force) {
    if ($existingVersion -eq $manifest.skill_version) {
        Write-Host "Skill '$($manifest.name)' is already installed at version $existingVersion."
        Write-Host "Location: $targetDir"
        exit 0
    }
}

if (Test-Path -LiteralPath $backupDir) {
    Remove-Item -LiteralPath $backupDir -Recurse -Force
}

if (Test-Path -LiteralPath $targetDir) {
    Move-Item -LiteralPath $targetDir -Destination $backupDir
}

try {
    Copy-Item -LiteralPath $packageRoot -Destination $targetDir -Recurse -Force
    if (Test-Path -LiteralPath $backupDir) {
        Remove-Item -LiteralPath $backupDir -Recurse -Force
    }
} catch {
    if (Test-Path -LiteralPath $targetDir) {
        Remove-Item -LiteralPath $targetDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path -LiteralPath $backupDir) {
        Move-Item -LiteralPath $backupDir -Destination $targetDir -Force
    }
    throw
}

Write-Host "Installed skill '$($manifest.name)' version $($manifest.skill_version)"
Write-Host "Bundle: $($manifest.bundle_version)"
Write-Host "Location: $targetDir"
