[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$StartPath,
    [string]$TriggerPath
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Get-CtclibDatasetRoot {
    param([Parameter(Mandatory)][string]$Path)

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    if (Test-Path -LiteralPath $fullPath -PathType Leaf) {
        $fullPath = Split-Path -Parent $fullPath
    }
    $current = Get-Item -LiteralPath $fullPath
    while ($null -ne $current) {
        if ($current.Name -eq 'ctclib') {
            return $current.FullName
        }
        $current = $current.Parent
    }
    throw "Could not locate a parent directory named 'ctclib': $Path"
}

function Get-ObjectProperty {
    param(
        [AllowNull()]$Object,
        [Parameter(Mandatory)][string]$Name
    )

    if ($null -eq $Object) {
        return $null
    }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) {
        return $null
    }
    return $property.Value
}

function Get-RelativePath {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$Path
    )

    $rootWithSeparator = $Root.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    return $Path.Substring($rootWithSeparator.Length).Replace('\', '/')
}

function Get-DirectorySizeBytes {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        return 0
    }
    $sum = (Get-ChildItem -LiteralPath $Path -Recurse -File -Force |
        Measure-Object -Property Length -Sum).Sum
    if ($null -eq $sum) {
        return 0
    }
    return [int64]$sum
}

function Get-OutputKind {
    param(
        [Parameter(Mandatory)][string]$RelativePath,
        [AllowNull()]$Summary,
        [Parameter(Mandatory)][string]$Root
    )

    $sourceConfig = [string](Get-ObjectProperty -Object $Summary -Name 'SourceConfig')
    $signature = ($RelativePath + ' ' + $sourceConfig).ToLowerInvariant()
    if ($signature -match 'error-observability') {
        return 'CALIB / error observability'
    }
    if ($RelativePath -match 'install[_-]car2vio[_-]final') {
        return 'NAV / official VIO-on'
    }
    if ($RelativePath -match 'vioshift.*_no_vio$') {
        return 'NAV / official VIO-off'
    }
    if ($signature -match 'install-car2vio-calib') {
        return 'CALIB / VIO installation'
    }
    if ($RelativePath -match '^decode_' -or $signature -match 'decode') {
        return 'DECODE / source extraction'
    }
    if ($signature -match 'extrinsics') {
        return 'CALIB / extrinsics'
    }
    if ($signature -match 'imu-delay|imu_delay') {
        return 'VALIDATION / IMU delay'
    }
    if ($signature -match 'default.*probe|probe.*default') {
        return 'PROBE / IMU defaults'
    }
    if ($signature -match 'gnss-only') {
        return 'NAV / historical GNSS-only'
    }
    if ($signature -match 'basic.*vio') {
        return 'NAV / historical basic'
    }
    if (
        $RelativePath -match 'calib' -or
        (Test-Path -LiteralPath (Join-Path (Join-Path $Root $RelativePath) 'dr_est.prodef'))
    ) {
        return 'CALIB / general'
    }
    return 'OUTPUT / general'
}

function Get-RetentionLabel {
    param([Parameter(Mandatory)][string]$Kind)

    if ($Kind -match 'official VIO') {
        return 'KEEP / current formal navigation'
    }
    if ($Kind -match '^DECODE') {
        return 'KEEP / input provenance'
    }
    if ($Kind -match '^CALIB') {
        return 'REVIEW / calibration evidence'
    }
    if ($Kind -match '^VALIDATION') {
        return 'REVIEW / validation evidence'
    }
    if ($Kind -match 'historical') {
        return 'DELETE-CANDIDATE / historical navigation'
    }
    if ($Kind -match '^PROBE') {
        return 'DELETE-CANDIDATE / parameter probe'
    }
    return 'REVIEW / unclassified output'
}

function Format-TableText {
    param([AllowNull()][string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return ''
    }
    return $Value.Replace('|', '\|').Replace("`r", ' ').Replace("`n", ' ')
}

$root = Get-CtclibDatasetRoot -Path $StartPath
$generatedAt = Get-Date
$summaryByOutput = @{}
$allRunSummaries = @()

$summaryFiles = @(
    Get-ChildItem -LiteralPath $root -Recurse -File -Filter 'summary.json' -Force |
        Where-Object {
            $_.FullName -match '\\runs\\' -or $_.Directory.Name -eq '_run'
        }
)
foreach ($summaryFile in $summaryFiles) {
    try {
        $summary = Get-Content -LiteralPath $summaryFile.FullName -Raw -Encoding UTF8 |
            ConvertFrom-Json
    }
    catch {
        continue
    }
    $outputValue = Get-ObjectProperty -Object $summary -Name 'OutputDir'
    if ([string]::IsNullOrWhiteSpace([string]$outputValue)) {
        $outputValue = Get-ObjectProperty -Object $summary -Name 'Workspace'
    }
    if ([string]::IsNullOrWhiteSpace([string]$outputValue)) {
        continue
    }
    $outputPath = [System.IO.Path]::GetFullPath([string]$outputValue)
    $runEntry = [pscustomobject]@{
        RunRelativePath = Get-RelativePath -Root $root -Path $summaryFile.Directory.FullName
        RunLastWriteTime = $summaryFile.LastWriteTime
        OutputPath = $outputPath
        OutputRelativePath = Get-RelativePath -Root $root -Path $outputPath
        Status = [string](Get-ObjectProperty -Object $summary -Name 'Status')
        ExitCode = Get-ObjectProperty -Object $summary -Name 'ExitCode'
        DurationSeconds = Get-ObjectProperty -Object $summary -Name 'DurationSeconds'
        SourceConfig = [string](Get-ObjectProperty -Object $summary -Name 'SourceConfig')
    }
    $allRunSummaries += $runEntry
    $key = $outputPath.ToLowerInvariant()
    if (-not $summaryByOutput.ContainsKey($key) -or
        $summaryByOutput[$key].RunLastWriteTime -lt $runEntry.RunLastWriteTime) {
        $summaryByOutput[$key] = $runEntry
    }
}

$candidateMap = @{}
foreach ($runEntry in $allRunSummaries) {
    if (Test-Path -LiteralPath $runEntry.OutputPath -PathType Container) {
        $candidateMap[$runEntry.OutputPath.ToLowerInvariant()] = $runEntry.OutputPath
    }
}
$artifactNames = @(
    'ctclib.ctccfg',
    'dr_est.prodef',
    'ins_insplot.txt',
    'ins_novatel.ASC',
    'gnss_rtkplot.txt'
)
$artifactFiles = @(
    Get-ChildItem -LiteralPath $root -Recurse -File -Force |
        Where-Object {
            ($artifactNames -contains $_.Name) -and
            ($_.FullName -notmatch '\\runs\\|\\_batch\\|\\_run\\')
        }
)
foreach ($artifact in $artifactFiles) {
    $candidateMap[$artifact.DirectoryName.ToLowerInvariant()] = $artifact.DirectoryName
}

$entries = @()
foreach ($outputPath in ($candidateMap.Values | Sort-Object)) {
    if (-not $outputPath.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
        continue
    }
    $relativePath = Get-RelativePath -Root $root -Path $outputPath
    $summary = $summaryByOutput[$outputPath.ToLowerInvariant()]
    $kind = Get-OutputKind -RelativePath $relativePath -Summary $summary -Root $root
    $retention = Get-RetentionLabel -Kind $kind
    $insPlotPath = Join-Path $outputPath 'ins_insplot.txt'
    $insNovatelPath = Join-Path $outputPath 'ins_novatel.ASC'
    $hasNavigation = (
        ((Test-Path -LiteralPath $insPlotPath) -and
            ((Get-Item -LiteralPath $insPlotPath).Length -gt 0)) -or
        ((Test-Path -LiteralPath $insNovatelPath) -and
            ((Get-Item -LiteralPath $insNovatelPath).Length -gt 0))
    )
    $sourceConfig = if ($null -ne $summary) { $summary.SourceConfig } else { '' }
    $sourceName = if ([string]::IsNullOrWhiteSpace($sourceConfig)) {
        ''
    }
    else {
        Split-Path -Leaf $sourceConfig
    }
    $entries += [pscustomobject]@{
        RelativePath = $relativePath
        AbsolutePath = $outputPath
        Kind = $kind
        Retention = $retention
        LastWriteTime = (Get-Item -LiteralPath $outputPath).LastWriteTime
        SizeBytes = Get-DirectorySizeBytes -Path $outputPath
        HasNavigation = $hasNavigation
        RunStatus = if ($null -ne $summary) { $summary.Status } else { '' }
        ExitCode = if ($null -ne $summary) { $summary.ExitCode } else { $null }
        SourceConfig = $sourceName
        LatestRun = if ($null -ne $summary) { $summary.RunRelativePath } else { '' }
    }
}
$entries = @($entries | Sort-Object RelativePath)

$officialEntries = @($entries | Where-Object { $_.Retention -like 'KEEP / current formal*' })
$cleanupEntries = @($entries | Where-Object { $_.Retention -like 'DELETE-CANDIDATE*' })
$reviewEntries = @($entries | Where-Object { $_.Retention -like 'REVIEW*' })
$keepEntries = @($entries | Where-Object { $_.Retention -like 'KEEP*' })

$markdown = New-Object System.Collections.Generic.List[string]
$markdown.Add('# CTCLib Output Index')
$markdown.Add('')
$markdown.Add('Status: auto-generated. Do not edit manually; updated after every `run-decode` or `run-solve`.')
$markdown.Add('')
$markdown.Add('## Table of Contents')
$markdown.Add('')
$markdown.Add('- [Current formal outputs](#current-formal-outputs)')
$markdown.Add('- [All output units](#all-output-units)')
$markdown.Add('- [Execution records](#execution-records)')
$markdown.Add('- [Cleanup guidance](#cleanup-guidance)')
$markdown.Add('')
$markdown.Add("Updated: $($generatedAt.ToString('yyyy-MM-dd HH:mm:ss'))")
$markdown.Add('')
$markdown.Add("Root: ``$root``")
if (-not [string]::IsNullOrWhiteSpace($TriggerPath)) {
    $markdown.Add('')
    $markdown.Add("Trigger path: ``$([System.IO.Path]::GetFullPath($TriggerPath))``")
}
$markdown.Add('')
$markdown.Add('## Current formal outputs')
$markdown.Add('')
if ($officialEntries.Count -eq 0) {
    $markdown.Add('No output was classified as the current formal navigation result.')
}
else {
    $markdown.Add('| Output | Kind | Latest status |')
    $markdown.Add('| --- | --- | --- |')
    foreach ($entry in $officialEntries) {
        $markdown.Add((
            '| `{0}` | {1} | {2} |' -f
                (Format-TableText $entry.RelativePath),
                (Format-TableText $entry.Kind),
                (Format-TableText $entry.RunStatus)
        ))
    }
}
$markdown.Add('')
$markdown.Add('## All output units')
$markdown.Add('')
if ($entries.Count -eq 0) {
    $markdown.Add('No output units found.')
}
else {
    $markdown.Add('| Output | Kind | Navigation | Latest status | Source config | Retention | Updated | Size MiB |')
    $markdown.Add('| --- | --- | --- | --- | --- | --- | --- | ---: |')
    foreach ($entry in $entries) {
        $markdown.Add((
            '| `{0}` | {1} | {2} | {3} | {4} | {5} | {6} | {7:F2} |' -f
                (Format-TableText $entry.RelativePath),
                (Format-TableText $entry.Kind),
                $(if ($entry.HasNavigation) { 'yes' } else { 'no' }),
                (Format-TableText $entry.RunStatus),
                (Format-TableText $entry.SourceConfig),
                (Format-TableText $entry.Retention),
                $entry.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'),
                ($entry.SizeBytes / 1MB)
        ))
    }
}
$markdown.Add('')
$markdown.Add('## Execution records')
$markdown.Add('')
$runEntries = @($allRunSummaries | Sort-Object RunLastWriteTime -Descending)
if ($runEntries.Count -eq 0) {
    $markdown.Add('No run summaries found.')
}
else {
    $markdown.Add('| Run record | Status | Exit | Output | Source config | Time |')
    $markdown.Add('| --- | --- | ---: | --- | --- | --- |')
    foreach ($runEntry in $runEntries) {
        $runSourceName = if ([string]::IsNullOrWhiteSpace($runEntry.SourceConfig)) {
            ''
        }
        else {
            Split-Path -Leaf $runEntry.SourceConfig
        }
        $markdown.Add((
            '| `{0}` | {1} | {2} | `{3}` | {4} | {5} |' -f
                (Format-TableText $runEntry.RunRelativePath),
                (Format-TableText $runEntry.Status),
                $(if ($null -eq $runEntry.ExitCode) { '' } else { $runEntry.ExitCode }),
                (Format-TableText $runEntry.OutputRelativePath),
                (Format-TableText $runSourceName),
                $runEntry.RunLastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')
        ))
    }
}
$markdown.Add('')
$markdown.Add('## Cleanup guidance')
$markdown.Add('')
$markdown.Add('| Category | Count | Meaning |')
$markdown.Add('| --- | ---: | --- |')
$markdown.Add("| KEEP | $($keepEntries.Count) | Current formal result or required input provenance. |")
$markdown.Add("| REVIEW | $($reviewEntries.Count) | Calibration, validation, or experiment evidence; delete only after confirmation. |")
$markdown.Add("| DELETE-CANDIDATE | $($cleanupEntries.Count) | Historical navigation or probe output that can be cleaned first. |")
$markdown.Add('')
if ($cleanupEntries.Count -gt 0) {
    $markdown.Add('Current cleanup candidates:')
    $markdown.Add('')
    foreach ($entry in $cleanupEntries) {
        $markdown.Add("- ``$($entry.RelativePath)``: $($entry.Kind)")
    }
}
else {
    $markdown.Add('No automatic delete candidates were found.')
}

$readmePath = Join-Path $root 'README.md'
$indexJsonPath = Join-Path $root 'output-index.json'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText(
    $readmePath,
    (($markdown -join "`n") + "`n"),
    $utf8NoBom
)
$indexObject = [pscustomobject]@{
    GeneratedAt = $generatedAt.ToString('o')
    Root = $root
    TriggerPath = if ([string]::IsNullOrWhiteSpace($TriggerPath)) { $null } else { [System.IO.Path]::GetFullPath($TriggerPath) }
    Outputs = $entries
    Runs = $runEntries
}
[System.IO.File]::WriteAllText(
    $indexJsonPath,
    (($indexObject | ConvertTo-Json -Depth 8) + "`n"),
    $utf8NoBom
)

[pscustomobject]@{
    Status = 'success'
    Root = $root
    Readme = $readmePath
    Json = $indexJsonPath
    OutputCount = $entries.Count
    RunCount = $runEntries.Count
    OfficialCount = $officialEntries.Count
    ReviewCount = $reviewEntries.Count
    CleanupCandidateCount = $cleanupEntries.Count
}
