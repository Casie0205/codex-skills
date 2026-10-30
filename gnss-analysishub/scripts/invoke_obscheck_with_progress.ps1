param(
    [Parameter(Mandatory = $true)]
    [string]$CliPath,

    [Parameter(Mandatory = $true)]
    [string]$InputFile,

    [Parameter(Mandatory = $true)]
    [string]$OutputDir,

    [int]$DataType,

    [double]$EleDeg = 7,

    [string]$Systems,

    [switch]$PassThru
)

$ErrorActionPreference = 'Stop'

function Get-ArtifactPaths {
    param(
        [string]$Dir,
        [string]$Stem
    )

    return [ordered]@{
        QC       = Join-Path $Dir "${Stem}_QC.html"
        DataList = Join-Path $Dir "${Stem}_DataList.log"
        MP       = Join-Path $Dir "${Stem}.MP"
        GF       = Join-Path $Dir "${Stem}.GF"
        MW       = Join-Path $Dir "${Stem}.MW"
        Psr      = Join-Path $Dir "${Stem}.PsrCompare"
        CS       = Join-Path $Dir "${Stem}.CS"
    }
}

function Get-ProgressState {
    param(
        [hashtable]$Artifacts,
        [datetime]$StartedAt
    )

    $elapsed = [int]((Get-Date) - $StartedAt).TotalSeconds
    $existing = @{}

    foreach ($key in $Artifacts.Keys) {
        if (Test-Path -LiteralPath $Artifacts[$key]) {
            $item = Get-Item -LiteralPath $Artifacts[$key]
            $existing[$key] = $item.Length
        }
    }

    $floor = 5
    $status = 'Process started, waiting for first QC artifacts...'

    if ($existing.Count -gt 0) {
        $floor = 30
        $status = "QC artifacts are being generated ($($existing.Count) files detected)..."
    }

    if ($existing.ContainsKey('DataList')) {
        $sizeMb = [math]::Round($existing['DataList'] / 1MB, 1)
        $floor = 70
        $status = "Generating DataList and QC evidence (${sizeMb} MB written)..."
    }

    if ($existing.ContainsKey('QC')) {
        $floor = 90
        $status = 'QC HTML has been created, finalizing remaining outputs...'
    }

    $timePercent = [math]::Min(92, 5 + [int]($elapsed / 2))
    $percent = [math]::Max($floor, $timePercent)

    return [pscustomobject]@{
        Percent  = $percent
        Status   = $status
        Existing = $existing
        Elapsed  = $elapsed
    }
}

$cliResolved = (Resolve-Path -LiteralPath $CliPath).Path
$inputResolved = (Resolve-Path -LiteralPath $InputFile).Path
$outputResolved = [System.IO.Path]::GetFullPath($OutputDir)
$stem = [System.IO.Path]::GetFileNameWithoutExtension($inputResolved)
$artifacts = Get-ArtifactPaths -Dir $outputResolved -Stem $stem

New-Item -ItemType Directory -Force -Path $outputResolved | Out-Null

$stdoutPath = Join-Path $outputResolved '_obscheck_stdout.log'
$stderrPath = Join-Path $outputResolved '_obscheck_stderr.log'

if (Test-Path -LiteralPath $stdoutPath) { Remove-Item -LiteralPath $stdoutPath -Force }
if (Test-Path -LiteralPath $stderrPath) { Remove-Item -LiteralPath $stderrPath -Force }

$args = New-Object System.Collections.Generic.List[string]
$args.Add('qc')
$args.Add('obscheck')
$args.Add($inputResolved)
$args.Add('--out-dir')
$args.Add($outputResolved)
$args.Add('--ele-deg')
$args.Add(([string]$EleDeg))

if ($PSBoundParameters.ContainsKey('DataType')) {
    $args.Add('--data-type')
    $args.Add(([string]$DataType))
}

if (-not [string]::IsNullOrWhiteSpace($Systems)) {
    $args.Add('--sys')
    $args.Add($Systems)
}

Write-Host "Starting GNSS QC with progress..."
Write-Host "CLI:      $cliResolved"
Write-Host "Input:    $inputResolved"
Write-Host "Output:   $outputResolved"
Write-Host "EleDeg:   $EleDeg"
if ($PSBoundParameters.ContainsKey('DataType')) {
    Write-Host "DataType: $DataType"
}
if (-not [string]::IsNullOrWhiteSpace($Systems)) {
    Write-Host "Systems:  $Systems"
}

$startedAt = Get-Date
$process = Start-Process -FilePath $cliResolved `
    -ArgumentList $args `
    -WorkingDirectory (Split-Path -Parent $cliResolved) `
    -RedirectStandardOutput $stdoutPath `
    -RedirectStandardError $stderrPath `
    -PassThru

$lastPrintedStatus = ''

while (-not $process.HasExited) {
    $process.Refresh()
    $state = Get-ProgressState -Artifacts $artifacts -StartedAt $startedAt
    $elapsedText = [TimeSpan]::FromSeconds($state.Elapsed).ToString()

    Write-Progress -Activity 'GNSS QC ObsCheck' -Status "$($state.Status) Elapsed: $elapsedText" -PercentComplete $state.Percent

    if ($state.Status -ne $lastPrintedStatus) {
        Write-Host ("[{0}] {1} ({2}%)" -f (Get-Date -Format 'HH:mm:ss'), $state.Status, $state.Percent)
        $lastPrintedStatus = $state.Status
    }

    Start-Sleep -Seconds 1
}

$process.WaitForExit()
$exitCode = $process.ExitCode

if ($exitCode -ne 0) {
    Write-Progress -Activity 'GNSS QC ObsCheck' -Completed -Status 'Failed'
    $stderrText = if (Test-Path -LiteralPath $stderrPath) {
        (Get-Content -LiteralPath $stderrPath -Raw)
    } else {
        ''
    }
    throw "ObsCheck failed with exit code $exitCode. $stderrText"
}

Write-Progress -Activity 'GNSS QC ObsCheck' -Completed -Status 'Completed'

$summary = [pscustomobject]@{
    InputFile       = $inputResolved
    OutputDir       = $outputResolved
    QCHtml          = $artifacts.QC
    DataList        = $artifacts.DataList
    MPFile          = $artifacts.MP
    GFFile          = $artifacts.GF
    MWFile          = $artifacts.MW
    PsrCompareFile  = $artifacts.Psr
    CSFile          = $artifacts.CS
    StdoutLog       = $stdoutPath
    StderrLog       = $stderrPath
    ElapsedSeconds  = [int]((Get-Date) - $startedAt).TotalSeconds
}

Write-Host "GNSS QC completed."
Write-Host "QC HTML:  $($summary.QCHtml)"
Write-Host "DataList: $($summary.DataList)"
Write-Host "Elapsed:  $($summary.ElapsedSeconds)s"

if ($PassThru) {
    $summary
}
