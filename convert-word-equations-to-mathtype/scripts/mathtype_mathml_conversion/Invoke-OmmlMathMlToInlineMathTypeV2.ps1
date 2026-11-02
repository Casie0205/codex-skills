[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Preflight', 'Convert')]
    [string]$Mode,

    [Parameter(Mandatory = $true)]
    [string]$SourcePath,

    [string]$OutputPath,
    [string]$BackupPath,
    [Parameter(Mandatory = $true)]
    [string]$ManifestPath,
    [Parameter(Mandatory = $true)]
    [string]$ProgressPath,

    [string]$OfficeOmmlToMathMlXsltPath =
        'C:\Program Files\Microsoft Office\root\Office16\OMML2MML.XSL',
    [string]$BlankEquationPath =
        'C:\Program Files (x86)\MathType\Office Support\BlankEqn.doc',
    [string]$PreferencePath,
    [string]$MathPageDirectory =
        'C:\Program Files (x86)\MathType\MathPage\64',

    [ValidateSet('ReviewQueue', 'Strict')]
    [string]$ConversionPolicy = 'ReviewQueue'
)

$ErrorActionPreference = 'Stop'

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($scriptRoot)) {
    throw 'Cannot resolve the V2 converter script directory.'
}
if ([string]::IsNullOrWhiteSpace($PreferencePath)) {
    $PreferencePath = Join-Path $scriptRoot '..\mathtype_tex_conversion\preferences\TimesNewRoman-EuclidExtra-10.eqp'
}

Add-Type -AssemblyName Microsoft.Office.Interop.Word
Add-Type -AssemblyName office
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.Xml

$v1Root = Join-Path $scriptRoot '..\mathtype_tex_conversion'
$sources = @(
    (Join-Path $v1Root 'MathTypeNativeApi.cs'),
    (Join-Path $v1Root 'MathTypeOleMtef.cs'),
    (Join-Path $scriptRoot 'V2Models.cs'),
    (Join-Path $scriptRoot 'MathMlCanonicalizer.cs'),
    (Join-Path $scriptRoot 'OmmlMathMlTransformer.cs'),
    (Join-Path $scriptRoot 'MtefStyleAudit.cs'),
    (Join-Path $scriptRoot 'MtefFontProfileAudit.cs'),
    (Join-Path $scriptRoot 'MathTypeMathMlNativeBridge.cs'),
    (Join-Path $scriptRoot 'MathTypeOleDataObject.cs'),
    (Join-Path $scriptRoot 'MathTypeDiagnosticPolicy.cs'),
    (Join-Path $scriptRoot 'MathTypeReviewClassifier.cs'),
    (Join-Path $scriptRoot 'OleMessageFilter.cs'),
    (Join-Path $scriptRoot 'WordV2Interop.cs'),
    (Join-Path $scriptRoot 'WordMathTypeV2Converter.cs')
)
$references = @(
    [Microsoft.Office.Interop.Word.ApplicationClass].Assembly.Location,
    [Microsoft.Office.Core.MsoAutomationSecurity].Assembly.Location,
    [System.IO.Compression.ZipArchive].Assembly.Location,
    [System.IO.Compression.ZipFile].Assembly.Location,
    [System.Xml.XmlDocument].Assembly.Location,
    [System.Uri].Assembly.Location
)
Add-Type -Path $sources -ReferencedAssemblies $references

switch ($Mode) {
    'Preflight' {
        $result = [ThesisMathTypeConversionV2.WordMathTypeV2Converter]::Preflight(
            $SourcePath,
            $ManifestPath,
            $ProgressPath,
            $OfficeOmmlToMathMlXsltPath)
    }
    'Convert' {
        $result = [ThesisMathTypeConversionV2.WordMathTypeV2Converter]::Convert(
            $SourcePath,
            $OutputPath,
            $BackupPath,
            $ManifestPath,
            $ProgressPath,
            $OfficeOmmlToMathMlXsltPath,
            $BlankEquationPath,
            $PreferencePath,
            $MathPageDirectory,
            [ThesisMathTypeConversionV2.V2ConversionPolicy]$ConversionPolicy)
    }
}

$result | ConvertTo-Json -Depth 5
