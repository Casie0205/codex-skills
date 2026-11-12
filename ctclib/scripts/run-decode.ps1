[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)]
    [string]$InputFile,
    [string]$Workspace,
    [string]$CtclibHome = $env:CTCLIB_HOME,
    [ValidateRange(0, 86400)]
    [int]$TimeoutSeconds = 900,
    [switch]$NoStage,
    [switch]$Force,
    [switch]$PlanOnly,
    [switch]$Json
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'Ctclib.Common.psm1') -Force

$environment = Resolve-CtclibEnvironment -CtclibHome $CtclibHome
$inputPath = (Resolve-Path -LiteralPath $InputFile).Path
$inputItem = Get-Item -LiteralPath $inputPath
$stem = [System.IO.Path]::GetFileNameWithoutExtension($inputItem.Name)

if ([string]::IsNullOrWhiteSpace($Workspace)) {
    throw (
        'Workspace is required. Use ' +
        'D:\Output\<dataset-root>\ctclib\decode_<timestamp>.'
    )
}
$Workspace = Resolve-CtclibDatasetOutputPath -Path $Workspace -ParameterName 'Workspace'
$runRoot = Join-Path $Workspace '_run'
$plannedExecutionInput = if ($NoStage) {
    $inputPath
}
else {
    Join-Path (Join-Path $Workspace 'source') $inputItem.Name
}
$expectedOutput = Join-Path (Split-Path -Parent $plannedExecutionInput) ($stem + '_ctclibdec')

if ((Test-Path -LiteralPath $expectedOutput) -and -not $Force) {
    throw "Decode output already exists. Choose a new workspace or pass -Force: $expectedOutput"
}

if ($PlanOnly) {
    $summary = [pscustomobject]@{
        Status         = 'planned'
        CtclibInstallDir = $environment.Home
        CtclibVersion  = $environment.Version
        CtclibCandidateCount = $environment.CandidateCount
        DecodeExe      = $environment.DecodeExe
        InputFile      = $inputPath
        Workspace      = $Workspace
        ExecutionInput = $plannedExecutionInput
        StageMode      = if ($NoStage) { 'in-place' } else { 'planned' }
        ExpectedOutput = $expectedOutput
        Command        = ('"{0}" -b "{1}"' -f $environment.DecodeExe, $plannedExecutionInput)
        TimeoutSeconds = $TimeoutSeconds
        RunRoot        = $runRoot
    }
    if ($Json) {
        $summary | ConvertTo-Json -Depth 6
    }
    else {
        $summary
    }
    exit 0
}

New-Item -ItemType Directory -Force -Path $Workspace | Out-Null
$staged = Import-CtclibInput -InputFile $inputPath -Workspace $Workspace -NoStage:$NoStage
$expectedOutput = Join-Path (Split-Path -Parent $staged.ExecutionPath) ($stem + '_ctclibdec')
$baseline = @{}
if (Test-Path -LiteralPath $expectedOutput -PathType Container) {
    foreach ($entry in @(Get-CtclibFileInventory -Path $expectedOutput)) {
        $baseline[$entry.Path] = $entry
    }
}
$result = Invoke-CtclibExecutable `
    -Executable $environment.DecodeExe `
    -Arguments @('-b', $staged.ExecutionPath) `
    -WorkingDirectory $Workspace `
    -RunRoot $runRoot `
    -TimeoutSeconds $TimeoutSeconds

$inventory = @(Get-CtclibFileInventory -Path $expectedOutput)
$assessedInventory = @(
    foreach ($entry in $inventory) {
        $previous = $baseline[$entry.Path]
        $fresh = ($null -eq $previous) -or
            ($previous.Length -ne $entry.Length) -or
            ($previous.LastWriteTimeUtc -ne $entry.LastWriteTimeUtc)
        [pscustomobject]@{
            Path             = $entry.Path
            RelativePath     = $entry.RelativePath
            Length           = $entry.Length
            LastWriteTimeUtc = $entry.LastWriteTimeUtc
            Fresh            = $fresh
        }
    }
)
$dataNames = @(
    'ctclibdec_imu.txt',
    'ctclibdec_vio.prodef',
    'ctclibdec_base.rtcm3',
    'ctclibdec_rover.rtcm3',
    'ctclibdec_rover2.rtcm3',
    'ctclibdec_rover.novatel',
    'ctclibdec_gpgga.txt',
    'ctclibdec_gpgga2.txt',
    'ctclibdec_rtkplot.txt',
    'ctclibdec_rtkplot_2ant.txt',
    'ctclibdec_rtkplot_origin.navplot',
    'ctclibdec_origin_2ant.navplot'
)
$keyNames = @(
    'ctclibdec_forpost.ctccfg',
    'ctclibdec_log.txt'
) + $dataNames
$keyFiles = @(
    $assessedInventory |
        Where-Object {
            ($_.Length -gt 0) -and ($keyNames -contains (Split-Path -Leaf $_.Path))
        }
)
$freshKeyFiles = @($keyFiles | Where-Object { $_.Fresh })
$configFiles = @(
    $freshKeyFiles |
        Where-Object { (Split-Path -Leaf $_.Path) -eq 'ctclibdec_forpost.ctccfg' }
)
$dataFiles = @(
    $freshKeyFiles |
        Where-Object { $dataNames -contains (Split-Path -Leaf $_.Path) }
)
$success = (
    ($result.ExitCode -eq 0) -and
    (-not $result.TimedOut) -and
    (-not $result.OutputDrainTimedOut) -and
    (Test-Path -LiteralPath $expectedOutput -PathType Container) -and
    ($configFiles.Count -gt 0) -and
    ($dataFiles.Count -gt 0)
)
$summary = [pscustomobject]@{
    Status          = if ($success) { 'success' } elseif ($result.TimedOut) { 'timed_out' } elseif ($result.OutputDrainTimedOut) { 'output_drain_timed_out' } else { 'failed' }
    CtclibInstallDir = $environment.Home
    CtclibVersion   = $environment.Version
    CtclibCandidateCount = $environment.CandidateCount
    DecodeExe       = $environment.DecodeExe
    InputFile       = $inputPath
    ExecutionInput  = $staged.ExecutionPath
    StageMode       = $staged.Mode
    Workspace       = $Workspace
    DecodeOutput    = $expectedOutput
    ExitCode        = $result.ExitCode
    DurationSeconds = $result.DurationSeconds
    TimedOut        = $result.TimedOut
    OutputDrainTimedOut = $result.OutputDrainTimedOut
    CommandLine     = $result.CommandLine
    StdoutLog       = $result.StdoutPath
    StderrLog       = $result.StderrPath
    FileCount       = $inventory.Count
    KeyFiles        = $keyFiles
    FreshKeyFiles   = $freshKeyFiles
    ConfigFile      = $configFiles
    DataFiles       = $dataFiles
    Files           = $assessedInventory
}
Write-CtclibSummary -Summary $summary -Path (Join-Path $runRoot 'summary.json')

if ($Json) {
    $summary | ConvertTo-Json -Depth 8
}
else {
    $summary
}
if (-not $success) {
    exit 1
}
