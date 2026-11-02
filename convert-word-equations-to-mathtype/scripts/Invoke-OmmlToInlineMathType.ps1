[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Preflight', 'Convert', 'BuildTest', 'Validate', 'Readback')]
    [string]$Mode,

    [string]$SourcePath,
    [string]$OutputPath,
    [string]$BackupPath,
    [string]$ManifestPath,
    [string]$ProgressPath,
    [string]$NativeTestPath,
    [string]$ReadbackManifestPath,
    [int]$ExpectedMathTypeCount = -1,
    [switch]$AllowAccentScriptRisks,

    [string]$MathPageDirectory = 'C:\Program Files (x86)\MathType\MathPage\64',
    [string]$BlankEquationPath = 'C:\Program Files (x86)\MathType\Office Support\BlankEqn.doc',
    [string]$PreferencePath
)

$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName Microsoft.Office.Interop.Word
Add-Type -AssemblyName office
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.Xml

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($PreferencePath)) {
    $PreferencePath = Join-Path $scriptRoot 'preferences\TimesNewRoman-EuclidExtra-10.eqp'
}
$sourceFiles = @(
    (Join-Path $scriptRoot 'MathTypeNativeApi.cs'),
    (Join-Path $scriptRoot 'AccentScriptRiskDetector.cs'),
    (Join-Path $scriptRoot 'MathTypeOleMtef.cs'),
    (Join-Path $scriptRoot 'TexNormalization.cs'),
    (Join-Path $scriptRoot 'WordMathTypeReadbackVerifier.cs'),
    (Join-Path $scriptRoot 'WordOmmlMathTypeConverter.cs')
)
$references = @(
    [Microsoft.Office.Interop.Word.ApplicationClass].Assembly.Location,
    [Microsoft.Office.Core.MsoAutomationSecurity].Assembly.Location,
    [System.IO.Compression.ZipArchive].Assembly.Location,
    [System.Xml.XmlDocument].Assembly.Location,
    [System.Uri].Assembly.Location
)

Add-Type -Path $sourceFiles -ReferencedAssemblies $references

switch ($Mode) {
    'Preflight' {
        $result = [ThesisMathTypeConversion.WordOmmlMathTypeConverter]::Preflight(
            $SourcePath,
            $ManifestPath,
            $ProgressPath)
    }
    'Convert' {
        $result = [ThesisMathTypeConversion.WordOmmlMathTypeConverter]::Convert(
            $SourcePath,
            $OutputPath,
            $BackupPath,
            $ManifestPath,
            $ProgressPath,
            $MathPageDirectory,
            $BlankEquationPath,
            $PreferencePath,
            $AllowAccentScriptRisks.IsPresent)
    }
    'BuildTest' {
        $result = [ThesisMathTypeConversion.WordOmmlMathTypeConverter]::BuildRepresentativeTest(
            $NativeTestPath,
            $OutputPath,
            $ManifestPath,
            $ProgressPath,
            $MathPageDirectory,
            $BlankEquationPath,
            $PreferencePath)
    }
    'Validate' {
        $result = [ThesisMathTypeConversion.WordOmmlMathTypeConverter]::Validate(
            $SourcePath,
            $ExpectedMathTypeCount,
            $ProgressPath)
    }
    'Readback' {
        $result = [ThesisMathTypeConversion.WordMathTypeReadbackVerifier]::Readback(
            $SourcePath,
            $ReadbackManifestPath,
            $ProgressPath,
            $MathPageDirectory,
            $ExpectedMathTypeCount)
    }
}

$result | ConvertTo-Json -Depth 4
