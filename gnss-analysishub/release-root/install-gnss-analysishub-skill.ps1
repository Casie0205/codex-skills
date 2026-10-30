param(
    [string]$TargetRoot,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$releaseRoot = Split-Path -Parent $PSCommandPath
$installer = Join-Path (Split-Path -Parent $releaseRoot) 'scripts\install-skill.ps1'

if (-not (Test-Path -LiteralPath $installer)) {
    throw "Installer not found: $installer"
}

& $installer @PSBoundParameters
