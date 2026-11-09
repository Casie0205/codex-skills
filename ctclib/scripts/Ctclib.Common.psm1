Set-StrictMode -Version 2.0

$script:DefaultCtclibHome = 'D:\Code\ctclib_exe'

function Get-CtclibSafeName {
    param([Parameter(Mandatory)][string]$Value)

    $name = $Value -replace '[<>:"/\\|?*\x00-\x1F]', '_'
    $name = $name.Trim().TrimEnd('.')
    if ([string]::IsNullOrWhiteSpace($name)) {
        return 'ctclib'
    }
    return $name
}

function Resolve-CtclibEnvironment {
    [CmdletBinding()]
    param([string]$CtclibHome)

    $candidate = $CtclibHome
    if ([string]::IsNullOrWhiteSpace($candidate)) {
        $candidate = $env:CTCLIB_HOME
    }
    if ([string]::IsNullOrWhiteSpace($candidate)) {
        $candidate = $script:DefaultCtclibHome
    }
    if (-not [System.IO.Path]::IsPathRooted($candidate)) {
        $candidate = Join-Path (Get-Location).Path $candidate
    }
    if (-not (Test-Path -LiteralPath $candidate -PathType Container)) {
        throw "ctclib home directory not found: $candidate"
    }

    $homePath = (Resolve-Path -LiteralPath $candidate).Path
    $decodeExe = Join-Path $homePath 'ctclib_decode.exe'
    $appExe = Join-Path $homePath 'ctclib_app.exe'
    $decrypterDll = Join-Path $homePath 'Decrypter.dll'

    foreach ($path in @($decodeExe, $appExe, $decrypterDll)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Required ctclib file not found: $path"
        }
    }

    [pscustomobject]@{
        Home         = $homePath
        DecodeExe    = $decodeExe
        AppExe       = $appExe
        DecrypterDll = $decrypterDll
    }
}

function Import-CtclibInput {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$InputFile,
        [Parameter(Mandatory)][string]$Workspace,
        [switch]$NoStage
    )

    $sourcePath = (Resolve-Path -LiteralPath $InputFile).Path
    if ($NoStage) {
        return [pscustomobject]@{
            ExecutionPath = $sourcePath
            SourcePath    = $sourcePath
            Mode          = 'in-place'
        }
    }

    $sourceDir = Join-Path $Workspace 'source'
    New-Item -ItemType Directory -Force -Path $sourceDir | Out-Null
    $targetPath = Join-Path $sourceDir (Split-Path -Leaf $sourcePath)
    $targetPath = [System.IO.Path]::GetFullPath($targetPath)

    if ($sourcePath -eq $targetPath) {
        return [pscustomobject]@{
            ExecutionPath = $sourcePath
            SourcePath    = $sourcePath
            Mode          = 'in-place'
        }
    }

    if (Test-Path -LiteralPath $targetPath -PathType Leaf) {
        $sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $sourcePath).Hash
        $targetHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $targetPath).Hash
        if ($sourceHash -ne $targetHash) {
            Copy-Item -LiteralPath $sourcePath -Destination $targetPath -Force
            return [pscustomobject]@{
                ExecutionPath = $targetPath
                SourcePath    = $sourcePath
                Mode          = 'replaced'
            }
        }
        return [pscustomobject]@{
            ExecutionPath = $targetPath
            SourcePath    = $sourcePath
            Mode          = 'staged-existing'
        }
    }

    $sourceRoot = [System.IO.Path]::GetPathRoot($sourcePath)
    $targetRoot = [System.IO.Path]::GetPathRoot($targetPath)
    $mode = 'copied'

    if ($sourceRoot -eq $targetRoot) {
        try {
            New-Item -ItemType HardLink -Path $targetPath -Target $sourcePath -ErrorAction Stop | Out-Null
            $mode = 'hardlink'
        }
        catch {
            Copy-Item -LiteralPath $sourcePath -Destination $targetPath -Force
        }
    }
    else {
        Copy-Item -LiteralPath $sourcePath -Destination $targetPath -Force
    }

    [pscustomobject]@{
        ExecutionPath = $targetPath
        SourcePath    = $sourcePath
        Mode          = $mode
    }
}

function Invoke-CtclibExecutable {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Executable,
        [Parameter(Mandatory)][string[]]$Arguments,
        [Parameter(Mandatory)][string]$WorkingDirectory,
        [Parameter(Mandatory)][string]$RunRoot,
        [ValidateRange(0, 86400)]
        [int]$TimeoutSeconds = 900
    )

    New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null
    $stdoutPath = Join-Path $RunRoot 'stdout.log'
    $stderrPath = Join-Path $RunRoot 'stderr.log'
    $quotedArguments = foreach ($argument in $Arguments) {
        if ($argument -match '[\s"]') {
            '"' + $argument.Replace('"', '\"') + '"'
        }
        else {
            $argument
        }
    }
    $argumentLine = $quotedArguments -join ' '
    $commandLine = '"{0}" {1}' -f $Executable, $argumentLine
    [System.IO.File]::WriteAllText(
        (Join-Path $RunRoot 'command.txt'),
        $commandLine,
        (New-Object System.Text.UTF8Encoding($false))
    )

    $startedAt = Get-Date
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $Executable
    $startInfo.Arguments = $argumentLine
    $startInfo.WorkingDirectory = $WorkingDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    if (-not $process.Start()) {
        throw "Failed to start ctclib process: $Executable"
    }
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()

    $exited = if ($TimeoutSeconds -gt 0) {
        $process.WaitForExit($TimeoutSeconds * 1000)
    }
    else {
        $process.WaitForExit()
        $true
    }
    $timedOut = -not $exited
    if ($timedOut) {
        try {
            $process.Kill()
            $process.WaitForExit(5000) | Out-Null
        }
        catch {
        }
    }
    $process.Refresh()
    $duration = ((Get-Date) - $startedAt).TotalSeconds

    $stdoutDrained = $stdoutTask.Wait(5000)
    $stderrDrained = $stderrTask.Wait(5000)
    $stdout = '[stdout was not fully drained]'
    $stderr = '[stderr was not fully drained]'
    if ($stdoutDrained) {
        try {
            $stdout = $stdoutTask.GetAwaiter().GetResult()
        }
        catch {
            $stdoutDrained = $false
        }
    }
    if ($stderrDrained) {
        try {
            $stderr = $stderrTask.GetAwaiter().GetResult()
        }
        catch {
            $stderrDrained = $false
        }
    }
    if (-not $stdoutDrained) {
        try {
            $process.StandardOutput.Close()
        }
        catch {
        }
    }
    if (-not $stderrDrained) {
        try {
            $process.StandardError.Close()
        }
        catch {
        }
    }
    $outputDrainTimedOut = -not ($stdoutDrained -and $stderrDrained)
    [System.IO.File]::WriteAllText($stdoutPath, $stdout, (New-Object System.Text.UTF8Encoding($false)))
    [System.IO.File]::WriteAllText($stderrPath, $stderr, (New-Object System.Text.UTF8Encoding($false)))

    $licensePromptDetected = ($stdout + "`n" + $stderr) -match 'Please send Serial Number|attempts remaining'
    $exitCode = $null
    if (-not $timedOut) {
        try {
            $exitCode = $process.ExitCode
        }
        catch {
        }
    }

    $result = [pscustomobject]@{
        ExitCode              = $exitCode
        DurationSeconds       = [math]::Round($duration, 3)
        TimedOut              = $timedOut
        OutputDrainTimedOut   = $outputDrainTimedOut
        LicensePromptDetected = $licensePromptDetected
        CommandLine           = $commandLine
        StdoutPath            = $stdoutPath
        StderrPath            = $stderrPath
        Stdout                = $stdout
        Stderr                = $stderr
    }
    try {
        $process.Dispose()
    }
    catch {
    }
    return $result
}

function Test-CtclibRegistrationAvailable {
    [CmdletBinding()]
    param()

    $registryPath = 'HKCU:\SOFTWARE\WOW6432Node\CTCLib4.0\Decrypt'
    if (-not (Test-Path -LiteralPath $registryPath)) {
        return $false
    }
    try {
        $properties = Get-ItemProperty -LiteralPath $registryPath -ErrorAction Stop
    }
    catch {
        return $false
    }
    $names = @($properties.PSObject.Properties.Name)
    if (($names -notcontains 'regCode') -or ($names -notcontains 'reqCode')) {
        return $false
    }
    $regCode = [string]$properties.regCode
    $reqCode = $properties.reqCode
    return (
        (-not [string]::IsNullOrWhiteSpace($regCode)) -and
        ($null -ne $reqCode) -and
        ([string]$reqCode -ne '0')
    )
}

function Get-CtclibConfigValue {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$ConfigFile,
        [Parameter(Mandatory)][string]$Section,
        [Parameter(Mandatory)][string]$Key
    )

    $currentSection = ''
    foreach ($line in [System.IO.File]::ReadLines($ConfigFile)) {
        $sectionMatch = [regex]::Match($line, '^\s*\[([^\]]+)\]\s*$')
        if ($sectionMatch.Success) {
            $currentSection = $sectionMatch.Groups[1].Value.Trim()
            continue
        }
        if ($currentSection -ne $Section) {
            continue
        }

        $keyMatch = [regex]::Match(
            $line,
            ('^\s*' + [regex]::Escape($Key) + '\s*=\s*(.*?)\s*$'),
            [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
        )
        if ($keyMatch.Success) {
            $value = [regex]::Replace($keyMatch.Groups[1].Value, '\s+#.*$', '')
            return $value.Trim()
        }
    }
    return $null
}

function Resolve-CtclibConfigPath {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$ConfigFile,
        [Parameter(Mandatory)][string]$Value
    )

    if ([System.IO.Path]::IsPathRooted($Value)) {
        return [System.IO.Path]::GetFullPath($Value)
    }
    $configDir = Split-Path -Parent (Resolve-Path -LiteralPath $ConfigFile).Path
    return [System.IO.Path]::GetFullPath((Join-Path $configDir $Value))
}

function New-CtclibDerivedConfig {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$ConfigFile,
        [Parameter(Mandatory)][string]$Destination,
        [Parameter(Mandatory)][string]$InputFile,
        [string]$OutputDir,
        [switch]$UseConfigOutput
    )

    $sourceLines = [System.IO.File]::ReadAllLines($ConfigFile)
    $managed = [ordered]@{
        file_input_obs_rover = ($InputFile -replace '\\', '/')
    }
    if (-not $UseConfigOutput) {
        if ([string]::IsNullOrWhiteSpace($OutputDir)) {
            throw 'OutputDir is required unless UseConfigOutput is set.'
        }
        $managed.selfoutput = '0'
        $managed.dir_output = ($OutputDir -replace '\\', '/')
    }

    $found = @{}
    $currentSection = ''
    $hasTopLevelSection = $false
    $outputLines = New-Object System.Collections.Generic.List[string]

    foreach ($line in $sourceLines) {
        $sectionMatch = [regex]::Match($line, '^\s*\[([^\]]+)\]\s*$')
        if ($sectionMatch.Success) {
            $currentSection = $sectionMatch.Groups[1].Value.Trim()
            if ($currentSection -eq 'ctclib') {
                $hasTopLevelSection = $true
            }
            $outputLines.Add($line)
            continue
        }

        $replaced = $false
        if ($currentSection -eq 'ctclib') {
            foreach ($key in $managed.Keys) {
                if ($line -imatch ('^\s*' + [regex]::Escape($key) + '\s*=')) {
                    $outputLines.Add(('{0} = {1}' -f $key, $managed[$key]))
                    $found[$key] = $true
                    $replaced = $true
                    break
                }
            }
        }
        if (-not $replaced) {
            $outputLines.Add($line)
        }
    }

    if (-not $hasTopLevelSection) {
        throw "The config does not contain a [ctclib] section: $ConfigFile"
    }

    $sectionIndex = -1
    for ($i = 0; $i -lt $outputLines.Count; $i++) {
        if ($outputLines[$i] -match '^\s*\[ctclib\]\s*$') {
            $sectionIndex = $i
            break
        }
    }

    $missingKeys = @($managed.Keys | Where-Object { -not $found.ContainsKey($_) })
    for ($i = $missingKeys.Count - 1; $i -ge 0; $i--) {
        $key = $missingKeys[$i]
        $outputLines.Insert($sectionIndex + 1, ('{0} = {1}' -f $key, $managed[$key]))
    }

    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Destination) | Out-Null
    [System.IO.File]::WriteAllLines(
        $Destination,
        $outputLines.ToArray(),
        (New-Object System.Text.UTF8Encoding($false))
    )
    return $Destination
}

function Get-CtclibFileInventory {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        return @()
    }
    $rootPath = (Resolve-Path -LiteralPath $Path).Path
    return @(
        Get-ChildItem -LiteralPath $rootPath -Recurse -File |
            Sort-Object FullName |
            ForEach-Object {
                [pscustomobject]@{
                    Path             = $_.FullName
                    RelativePath     = $_.FullName.Substring($rootPath.Length + 1)
                    Length           = $_.Length
                    LastWriteTimeUtc = $_.LastWriteTimeUtc
                }
            }
    )
}

function Write-CtclibSummary {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Summary,
        [Parameter(Mandatory)][string]$Path
    )

    $json = $Summary | ConvertTo-Json -Depth 8
    [System.IO.File]::WriteAllText(
        $Path,
        $json,
        (New-Object System.Text.UTF8Encoding($false))
    )
}

Export-ModuleMember -Function @(
    'Get-CtclibSafeName',
    'Resolve-CtclibEnvironment',
    'Import-CtclibInput',
    'Invoke-CtclibExecutable',
    'Test-CtclibRegistrationAvailable',
    'Get-CtclibConfigValue',
    'Resolve-CtclibConfigPath',
    'New-CtclibDerivedConfig',
    'Get-CtclibFileInventory',
    'Write-CtclibSummary'
)
