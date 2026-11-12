[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)]
    [string]$ConfigFile,
    [string]$OutputDir,
    [string]$RunRoot,
    [string]$CtclibHome = $env:CTCLIB_HOME,
    [ValidateRange(0, 86400)]
    [int]$TimeoutSeconds = 900,
    [switch]$UseConfigOutput,
    [switch]$Force,
    [switch]$PlanOnly,
    [switch]$Json
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'Ctclib.Common.psm1') -Force

$environment = Resolve-CtclibEnvironment -CtclibHome $CtclibHome
$configPath = (Resolve-Path -LiteralPath $ConfigFile).Path
$configStem = [System.IO.Path]::GetFileNameWithoutExtension($configPath)
$safeStem = Get-CtclibSafeName $configStem
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
$inputValue = Get-CtclibConfigValue -ConfigFile $configPath -Section 'ctclib' -Key 'file_input_obs_rover'
if ([string]::IsNullOrWhiteSpace($inputValue)) {
    throw "Config does not define [ctclib] file_input_obs_rover: $configPath"
}
$inputPath = Resolve-CtclibConfigPath -ConfigFile $configPath -Value $inputValue
if (-not (Test-Path -LiteralPath $inputPath -PathType Leaf)) {
    throw "Navigation input file not found: $inputPath"
}

if ($UseConfigOutput) {
    if (-not [string]::IsNullOrWhiteSpace($OutputDir)) {
        throw 'Use either -OutputDir or -UseConfigOutput, not both.'
    }
    $configOutput = Get-CtclibConfigValue -ConfigFile $configPath -Section 'ctclib' -Key 'dir_output'
    if (-not [string]::IsNullOrWhiteSpace($configOutput)) {
        $OutputDir = Resolve-CtclibConfigPath -ConfigFile $configPath -Value $configOutput
    }
}
else {
    if ([string]::IsNullOrWhiteSpace($OutputDir)) {
        throw (
            'OutputDir is required. Use ' +
            'D:\Output\<dataset-root>\ctclib\<run-name>.'
        )
    }
}

$OutputDir = Resolve-CtclibDatasetOutputPath -Path $OutputDir -ParameterName 'OutputDir'

if ([string]::IsNullOrWhiteSpace($RunRoot)) {
    $runParent = Join-Path (Split-Path -Parent $OutputDir) 'runs'
    $RunRoot = Join-Path $runParent ($timestamp + '_solve_' + $safeStem)
}
$RunRoot = Resolve-CtclibDatasetOutputPath -Path $RunRoot -ParameterName 'RunRoot'

if (-not [string]::IsNullOrWhiteSpace($OutputDir) -and (Test-Path -LiteralPath $OutputDir -PathType Container)) {
    $existing = @(Get-ChildItem -LiteralPath $OutputDir -Force)
    if (($existing.Count -gt 0) -and -not $Force) {
        throw "Navigation output directory is not empty. Choose another -OutputDir or pass -Force: $OutputDir"
    }
}

$derivedConfig = Join-Path $RunRoot 'ctclib.derived.ctccfg'

if ($PlanOnly) {
    $summary = [pscustomobject]@{
        Status          = 'planned'
        CtclibInstallDir = $environment.Home
        CtclibVersion   = $environment.Version
        CtclibCandidateCount = $environment.CandidateCount
        AppExe          = $environment.AppExe
        SourceConfig    = $configPath
        NavigationInput = $inputPath
        OutputDir       = $OutputDir
        DerivedConfig   = $derivedConfig
        RunRoot         = $RunRoot
        UseConfigOutput = [bool]$UseConfigOutput
        RegistrationAvailable = Test-CtclibRegistrationAvailable
        TimeoutSeconds  = $TimeoutSeconds
        Command         = ('"{0}" "{1}"' -f $environment.AppExe, $derivedConfig)
    }
    if ($Json) {
        $summary | ConvertTo-Json -Depth 6
    }
    else {
        $summary
    }
    exit 0
}

New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null
if (-not [string]::IsNullOrWhiteSpace($OutputDir)) {
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
}
New-CtclibDerivedConfig `
    -ConfigFile $configPath `
    -Destination $derivedConfig `
    -InputFile $inputPath `
    -OutputDir $OutputDir `
    -UseConfigOutput:$UseConfigOutput | Out-Null

$registrationAvailable = Test-CtclibRegistrationAvailable
$baseline = @{}
if ($registrationAvailable -and -not [string]::IsNullOrWhiteSpace($OutputDir)) {
    foreach ($entry in @(Get-CtclibFileInventory -Path $OutputDir)) {
        $baseline[$entry.Path] = $entry
    }
}

if ($registrationAvailable) {
    $result = Invoke-CtclibExecutable `
        -Executable $environment.AppExe `
        -Arguments @($derivedConfig) `
        -WorkingDirectory $RunRoot `
        -RunRoot $RunRoot `
        -TimeoutSeconds $TimeoutSeconds
}
else {
    $registrationLog = Join-Path $RunRoot 'registration_required.txt'
    [System.IO.File]::WriteAllText(
        $registrationLog,
        'ctclib_app.exe was not started because no CTCLib registration was found.',
        (New-Object System.Text.UTF8Encoding($false))
    )
    $result = [pscustomobject]@{
        ExitCode              = $null
        DurationSeconds       = 0
        TimedOut              = $false
        OutputDrainTimedOut   = $false
        LicensePromptDetected = $false
        CommandLine           = 'Not started: registration unavailable'
        StdoutPath            = $registrationLog
        StderrPath            = ''
        Stdout                = ''
        Stderr                = ''
    }
}

$combinedOutput = $result.Stdout + "`n" + $result.Stderr
$licenseRequired = (-not $registrationAvailable) -or
    $result.LicensePromptDetected -or
    ($combinedOutput -match 'Please send Serial Number|attempts remaining')
$inventory = if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    @()
}
else {
    @(Get-CtclibFileInventory -Path $OutputDir)
}
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
$keyNames = @(
    'ins_insplot.txt',
    'ins_novatel.ASC',
    'ins_fastsol.txt',
    'gnss_integsol.txt',
    'gnss_novatel.ASC',
    'ins_integsol.txt',
    'ctclib.ctccfg'
)
$keyFiles = @(
    $assessedInventory |
        Where-Object {
            ($_.Length -gt 0) -and ($keyNames -contains (Split-Path -Leaf $_.Path))
        }
)
$freshKeyFiles = @($keyFiles | Where-Object { $_.Fresh })
$primaryNames = @('ins_novatel.ASC', 'ins_insplot.txt', 'ins_fastsol.txt', 'gnss_integsol.txt')
$primaryFiles = @(
    $freshKeyFiles |
        Where-Object { $primaryNames -contains (Split-Path -Leaf $_.Path) }
)
$success = (
    ($result.ExitCode -eq 0) -and
    (-not $result.TimedOut) -and
    (-not $result.OutputDrainTimedOut) -and
    (-not $licenseRequired) -and
    ($primaryFiles.Count -gt 0)
)
$status = if ($success) {
    'success'
}
elseif ($licenseRequired) {
    'license_required'
}
elseif ($result.TimedOut) {
    'timed_out'
}
elseif ($result.OutputDrainTimedOut) {
    'output_drain_timed_out'
}
else {
    'failed'
}

$summary = [pscustomobject]@{
    Status          = $status
    CtclibInstallDir = $environment.Home
    CtclibVersion   = $environment.Version
    CtclibCandidateCount = $environment.CandidateCount
    AppExe          = $environment.AppExe
    SourceConfig    = $configPath
    DerivedConfig   = $derivedConfig
    NavigationInput = $inputPath
    OutputDir       = $OutputDir
    ExitCode        = $result.ExitCode
    DurationSeconds = $result.DurationSeconds
    TimedOut        = $result.TimedOut
    OutputDrainTimedOut = $result.OutputDrainTimedOut
    RegistrationAvailable = [bool]$registrationAvailable
    CommandLine     = $result.CommandLine
    StdoutLog       = $result.StdoutPath
    StderrLog       = $result.StderrPath
    LicenseRequired = [bool]$licenseRequired
    FileCount       = $inventory.Count
    KeyFiles        = $keyFiles
    FreshKeyFiles   = $freshKeyFiles
    PrimaryFiles    = $primaryFiles
    Files           = $assessedInventory
}
Write-CtclibSummary -Summary $summary -Path (Join-Path $RunRoot 'summary.json')

if ($Json) {
    $summary | ConvertTo-Json -Depth 8
}
else {
    $summary
}
if (-not $success) {
    exit 1
}
