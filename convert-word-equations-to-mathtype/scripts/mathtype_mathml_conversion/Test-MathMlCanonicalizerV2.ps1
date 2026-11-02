[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Xml

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$canonicalizerPath = Join-Path $scriptRoot 'MathMlCanonicalizer.cs'
$references = @(
    [System.Xml.XmlDocument].Assembly.Location,
    [System.Uri].Assembly.Location
)
Add-Type -Path $canonicalizerPath -ReferencedAssemblies $references

function Get-CanonicalForm {
    param([Parameter(Mandatory = $true)][string]$MathMl)

    return [ThesisMathTypeConversionV2.MathMlCanonicalizer]::Canonicalize(
        $MathMl)
}

function Assert-True {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )

    if (-not $Condition) {
        throw $Message
    }
}

$ns = 'http://www.w3.org/1998/Math/MathML'
$leftNested = Get-CanonicalForm (
    "<math xmlns='$ns'><mfrac><mi>a</mi><mfrac><mi>b</mi><mi>c</mi></mfrac></mfrac></math>"
)
$rightNested = Get-CanonicalForm (
    "<math xmlns='$ns'><mfrac><mfrac><mi>a</mi><mi>b</mi></mfrac><mi>c</mi></mfrac></math>"
)
Assert-True (
    $leftNested.StructureSignature -ne $rightNested.StructureSignature
) 'Tree signatures did not distinguish different fraction nesting.'

$attachedScript = Get-CanonicalForm (
    "<math xmlns='$ns'><msup><mi>x</mi><mi mathvariant='normal'>T</mi></msup></math>"
)
$detachedScript = Get-CanonicalForm (
    "<math xmlns='$ns'><mrow><mi>x</mi><msup><mrow/><mtext>T</mtext></msup></mrow></math>"
)
Assert-True (
    $attachedScript.StructureSignature -eq
        $detachedScript.StructureSignature
) 'Equivalent attached and detached MathType scripts did not normalize.'

$normalFunction = Get-CanonicalForm (
    "<math xmlns='$ns'><mrow><mi mathvariant='normal'>s</mi><mi mathvariant='normal'>i</mi><mi mathvariant='normal'>n</mi></mrow></math>"
)
$textFunction = Get-CanonicalForm (
    "<math xmlns='$ns'><mtext>sin</mtext></math>"
)
Assert-True (
    $normalFunction.TokenSequence -eq $textFunction.TokenSequence -and
    [ThesisMathTypeConversionV2.MathMlCanonicalizer]::
        AreStyleSequencesEquivalent(
            $normalFunction.StyleSequence,
            $textFunction.StyleSequence)
) 'Equivalent upright function spellings did not normalize.'

$italicFunction = Get-CanonicalForm (
    "<math xmlns='$ns'><mi mathvariant='italic'>sin</mi></math>"
)
Assert-True (
    $normalFunction.TokenSequence -eq $italicFunction.TokenSequence -and
    -not [ThesisMathTypeConversionV2.MathMlCanonicalizer]::
        AreStyleSequencesEquivalent(
            $normalFunction.StyleSequence,
            $italicFunction.StyleSequence)
) 'The typography gate did not reject an italicized function name.'

$textUnit = Get-CanonicalForm (
    "<math xmlns='$ns'><mtext>kg</mtext></math>"
)
$normalUnit = Get-CanonicalForm (
    "<math xmlns='$ns'><mi mathvariant='normal'>kg</mi></math>"
)
Assert-True (
    [ThesisMathTypeConversionV2.MathMlCanonicalizer]::
        AreStyleSequencesEquivalent(
            $textUnit.StyleSequence,
            $normalUnit.StyleSequence)
) 'Equivalent upright unit spellings did not normalize.'

$starIdentifier = Get-CanonicalForm (
    "<math xmlns='$ns'><msup><mi>X</mi><mi>*</mi></msup></math>"
)
$starOperator = Get-CanonicalForm (
    "<math xmlns='$ns'><msup><mi>X</mi><mo>*</mo></msup></math>"
)
$starText = Get-CanonicalForm (
    "<math xmlns='$ns'><msup><mi>X</mi><mtext>*</mtext></msup></math>"
)
Assert-True (
    $starIdentifier.TokenSequence -eq $starOperator.TokenSequence -and
    $starIdentifier.TokenSequence -eq $starText.TokenSequence -and
    [ThesisMathTypeConversionV2.MathMlCanonicalizer]::
        AreStyleSequencesEquivalent(
            $starIdentifier.StyleSequence,
            $starOperator.StyleSequence) -and
    [ThesisMathTypeConversionV2.MathMlCanonicalizer]::
        AreStyleSequencesEquivalent(
            $starIdentifier.StyleSequence,
            $starText.StyleSequence)
) 'Equivalent superscript star spellings did not normalize.'

$scriptedNormBase = Get-CanonicalForm (
    "<math xmlns='$ns'><msubsup><mrow><mo>&#x2225;</mo><mi>r</mi><mo>&#x2225;</mo></mrow><mi>a</mi><mn>2</mn></msubsup></math>"
)
$scriptedNormClose = Get-CanonicalForm (
    "<math xmlns='$ns'><mrow><mo>&#x2225;</mo><mi>r</mi><msubsup><mo>&#x2225;</mo><mi>a</mi><mn>2</mn></msubsup></mrow></math>"
)
Assert-True (
    $scriptedNormBase.StructureSignature -eq
        $scriptedNormClose.StructureSignature
) 'Equivalent U+2225 norm-delimiter script placement did not normalize.'

$nestedClosingScript = Get-CanonicalForm (
    "<math xmlns='$ns'><mrow><mo>(</mo><mi>a</mi><mo>(</mo><mi>b</mi><mo>)</mo><mi>c</mi><msup><mo>)</mo><mi>T</mi></msup></mrow></math>"
)
$nestedGroupedScript = Get-CanonicalForm (
    "<math xmlns='$ns'><msup><mrow><mo>(</mo><mi>a</mi><mo>(</mo><mi>b</mi><mo>)</mo><mi>c</mi><mo>)</mo></mrow><mi>T</mi></msup></math>"
)
Assert-True (
    $nestedClosingScript.StructureSignature -eq
        $nestedGroupedScript.StructureSignature
) 'Nested paired fences were not matched before script normalization.'

$combinedNumericList = Get-CanonicalForm (
    "<math xmlns='$ns'><mrow><mn>1,2</mn><mo>,</mo><mo>&#x2026;</mo></mrow></math>"
)
$splitNumericList = Get-CanonicalForm (
    "<math xmlns='$ns'><mrow><mn>1</mn><mo>,</mo><mn>2</mn><mo>,</mo><mo>&#x2026;</mo></mrow></math>"
)
Assert-True (
    $combinedNumericList.TokenSequence -eq
        $splitNumericList.TokenSequence -and
    $combinedNumericList.StructureSignature -eq
        $splitNumericList.StructureSignature
) 'Comma-separated integer list tokens did not normalize.'

$decimalComma = Get-CanonicalForm (
    "<math xmlns='$ns'><mn>1,2</mn></math>"
)
$splitDecimalComma = Get-CanonicalForm (
    "<math xmlns='$ns'><mn>1</mn><mo>,</mo><mn>2</mn></math>"
)
Assert-True (
    $decimalComma.TokenSequence -ne
        $splitDecimalComma.TokenSequence
) 'An isolated decimal comma was incorrectly treated as a list.'

$zeroWidthBoundary = Get-CanonicalForm (
    "<math xmlns='$ns'><mi mathvariant='normal'>A</mi><mspace width='0em'/><msub><mi mathvariant='normal'>B</mi><mi>i</mi></msub></math>"
)
$boundaryReadback = Get-CanonicalForm (
    "<math xmlns='$ns'><mi mathvariant='normal'>A</mi><mtext>&#x200B;</mtext><msub><mi mathvariant='normal'>B</mi><mi>i</mi></msub></math>"
)
Assert-True (
    $zeroWidthBoundary.TokenSequence -eq
        $boundaryReadback.TokenSequence -and
    $zeroWidthBoundary.StructureSignature -eq
        $boundaryReadback.StructureSignature
) 'A zero-width MathType run boundary changed semantic structure.'

$combiningMacron = Get-CanonicalForm (
    "<math xmlns='$ns'><mover accent='true'><mi>u</mi><mo>&#x0304;</mo></mover></math>"
)
$spacingMacron = Get-CanonicalForm (
    "<math xmlns='$ns'><mover accent='true'><mi>u</mi><mi>&#x02C9;</mi></mover></math>"
)
Assert-True (
    $combiningMacron.TokenSequence -eq
        $spacingMacron.TokenSequence -and
    $combiningMacron.StructureSignature -eq
        $spacingMacron.StructureSignature
) 'Equivalent macron code points did not normalize.'

$groupedVariationScript = Get-CanonicalForm (
    "<math xmlns='$ns'><msub><mrow><mi>&#x03B4;</mi><mi>w</mi></mrow><mi>q</mi></msub></math>"
)
$splitVariationScript = Get-CanonicalForm (
    "<math xmlns='$ns'><mrow><mi>&#x03B4;</mi><msub><mi>w</mi><mi>q</mi></msub></mrow></math>"
)
Assert-True (
    $groupedVariationScript.StructureSignature -eq
        $splitVariationScript.StructureSignature
) 'A leading variation operator changed script attachment semantics.'

$doubleStruckAttribute = Get-CanonicalForm -MathMl (
    "<math xmlns='$ns'><mi mathvariant='double-struck'>R</mi></math>"
)
$doubleStruckUnicode = Get-CanonicalForm -MathMl (
    "<math xmlns='$ns'><mi>&#x211D;</mi></math>"
)
Assert-True (
    [ThesisMathTypeConversionV2.MathMlCanonicalizer]::
        AreStyleSequencesEquivalent(
            $doubleStruckAttribute.StyleSequence,
            $doubleStruckUnicode.StyleSequence)
) 'Legacy double-struck Unicode did not preserve its semantic style.'

[pscustomobject]@{
    Passed = 14
    Failed = 0
    TreeStructureGate = $true
    UprightTypographyGate = $true
    MathTypeEquivalenceNormalization = $true
} | ConvertTo-Json
