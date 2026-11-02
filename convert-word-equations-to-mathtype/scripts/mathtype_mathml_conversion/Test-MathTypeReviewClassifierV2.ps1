[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Add-Type -AssemblyName System.Xml
$references = @(
    [System.Xml.XmlDocument].Assembly.Location,
    [System.Uri].Assembly.Location
)
Add-Type -Path @(
    (Join-Path $scriptRoot 'V2Models.cs'),
    (Join-Path $scriptRoot 'MathMlCanonicalizer.cs'),
    (Join-Path $scriptRoot 'MtefFontProfileAudit.cs'),
    (Join-Path $scriptRoot 'MathTypeDiagnosticPolicy.cs'),
    (Join-Path $scriptRoot 'MathTypeReviewClassifier.cs')
) -ReferencedAssemblies $references

$source = [ThesisMathTypeConversionV2.MathMlSnapshot]::new()
$source.SourceIndex = 27
$roundTrip = [ThesisMathTypeConversionV2.MathMlRoundTripResult]::new()
$roundTrip.ReadbackMathMl =
    '<math><mi>' + [char]0xFFFD + '</mi></math>'
$roundTrip.TokenSequenceEqual = $false
$roundTrip.StructureSignatureEqual = $false
$roundTrip.StyleSequenceEqual = $true
$roundTrip.MtefStyleEqual = $true
$roundTrip.MtefFontProfileAccepted = $true

$codes = [ThesisMathTypeConversionV2.MathTypeReviewClassifier]::Classify(
    $source,
    $roundTrip,
    [string[]]@(
        [ThesisMathTypeConversionV2.MathTypeReviewClassifier]::AccentScriptUnsupported,
        [ThesisMathTypeConversionV2.MathTypeReviewClassifier]::AccentScriptUnsupported
    )
)

$expected = @(
    'SPECIAL_ACCENT_SCRIPT_UNSUPPORTED',
    'RT_TOKEN',
    'RT_STRUCTURE',
    'READBACK_REPLACEMENT_CHAR'
)
if (($codes -join ',') -ne ($expected -join ',')) {
    throw "Unexpected review classification: $($codes -join ',')"
}

$periodAccentSource =
    [ThesisMathTypeConversionV2.MathMlSnapshot]::new()
$periodAccentSource.NormalizedMathMl = @'
<math xmlns="http://www.w3.org/1998/Math/MathML">
  <mover><mi>q</mi><mrow><mo>.</mo></mrow></mover>
</math>
'@
if (-not [ThesisMathTypeConversionV2.MathTypeDiagnosticPolicy]::
    ShouldSkipTexReadback($periodAccentSource)) {
    throw 'Ordinary-period mover was not excluded from TeX readback.'
}

foreach ($unsafeBar in @([char]0x02C9, [char]0x00AF)) {
    $barAccentSource =
        [ThesisMathTypeConversionV2.MathMlSnapshot]::new()
    $barAccentSource.NormalizedMathMl =
        "<math xmlns='http://www.w3.org/1998/Math/MathML'>" +
        "<mover accent='true'><mi>q</mi><mi>" +
        $unsafeBar +
        "</mi></mover></math>"
    if (-not [ThesisMathTypeConversionV2.MathTypeDiagnosticPolicy]::
        ShouldSkipTexReadback($barAccentSource)) {
        throw (
            'Unsafe bar mover was not excluded from TeX readback: U+' +
            ([int]$unsafeBar).ToString('X4')
        )
    }
}

$ordinarySource =
    [ThesisMathTypeConversionV2.MathMlSnapshot]::new()
$ordinarySource.NormalizedMathMl = @'
<math xmlns="http://www.w3.org/1998/Math/MathML">
  <mi>q</mi>
</math>
'@
if ([ThesisMathTypeConversionV2.MathTypeDiagnosticPolicy]::
    ShouldSkipTexReadback($ordinarySource)) {
    throw 'Ordinary formula was incorrectly excluded from TeX readback.'
}

$fontMismatchRoundTrip =
    [ThesisMathTypeConversionV2.MathMlRoundTripResult]::new()
$fontMismatchRoundTrip.TokenSequenceEqual = $true
$fontMismatchRoundTrip.StructureSignatureEqual = $true
$fontMismatchRoundTrip.StyleSequenceEqual = $true
$fontMismatchRoundTrip.MtefStyleEqual = $true
$fontMismatchRoundTrip.MtefFontProfileAccepted = $false
$fontMismatchCodes =
    [ThesisMathTypeConversionV2.MathTypeReviewClassifier]::Classify(
        $source,
        $fontMismatchRoundTrip,
        [string[]]@()
    )
if (($fontMismatchCodes -join ',') -ne 'RT_MTEF_FONT_PROFILE') {
    throw "Unexpected font-profile classification: $($fontMismatchCodes -join ',')"
}

[pscustomobject]@{
    TestCount = 6
    Passed = 6
    Codes = $codes
} | ConvertTo-Json -Depth 3
