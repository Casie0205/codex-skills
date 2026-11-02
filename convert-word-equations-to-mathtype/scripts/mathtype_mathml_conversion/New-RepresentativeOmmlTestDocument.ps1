[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SourcePath,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [Parameter(Mandatory = $true)]
    [int[]]$SourceIndices
)

$ErrorActionPreference = 'Stop'

if ($SourceIndices.Count -eq 0) {
    throw 'SourceIndices must contain at least one formula index.'
}
if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf)) {
    throw "Source document does not exist: $SourcePath"
}

$sourceFullPath = [System.IO.Path]::GetFullPath($SourcePath)
$outputFullPath = [System.IO.Path]::GetFullPath($OutputPath)
$outputDirectory = Split-Path -Parent $outputFullPath
if (-not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}
if (Test-Path -LiteralPath $outputFullPath) {
    throw (
        'Refusing to overwrite an existing representative test document: ' +
        $outputFullPath
    )
}

$word = $null
$sourceDocument = $null
$testDocument = $null
$testTable = $null
$saved = $false

try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.AutomationSecurity = 3

    $sourceDocument = $word.Documents.Open(
        $sourceFullPath,
        $false,
        $true,
        $false)
    $sourceCount = $sourceDocument.OMaths.Count

    $invalid = @(
        $SourceIndices |
            Where-Object { $_ -lt 1 -or $_ -gt $sourceCount }
    )
    if ($invalid.Count -gt 0) {
        throw (
            'Representative source indices are outside the valid range ' +
            "1..$sourceCount`: " +
            ($invalid -join ', ')
        )
    }

    $testDocument = $word.Documents.Add()
    $testDocument.TrackRevisions = $false

    $titleRange = $testDocument.Range(0, 0)
    $titleRange.Text = (
        "MathType V2 代表公式验证`r" +
        "源文档 SHA-256 另见 Markdown 验证报告。`r`r"
    )
    [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject(
        $titleRange)

    $tablePosition = $testDocument.Content.End - 1
    $tableRange = $testDocument.Range($tablePosition, $tablePosition)
    $testTable = $testDocument.Tables.Add(
        $tableRange,
        $SourceIndices.Count,
        2)
    [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject(
        $tableRange)

    for ($sample = 0; $sample -lt $SourceIndices.Count; $sample++) {
        $sourceIndex = $SourceIndices[$sample]
        $labelCell = $testTable.Cell($sample + 1, 1)
        $labelCellRange = $labelCell.Range
        $labelCellRange.Text = (
            ('样本 {0:D2}，源公式序号 {1}' -f ($sample + 1), $sourceIndex) +
            ''
        )
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject(
            $labelCellRange)
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject(
            $labelCell)

        $sourceEquation = $null
        $sourceRange = $null
        $targetRange = $null
        $formulaCell = $null
        try {
            $sourceEquation = $sourceDocument.OMaths.Item($sourceIndex)
            $sourceRange = $sourceEquation.Range.Duplicate
            $formulaCell = $testTable.Cell($sample + 1, 2)
            $targetRange = $formulaCell.Range.Duplicate
            $targetRange.End = $targetRange.End - 1
            $targetRange.FormattedText = $sourceRange.FormattedText
        }
        finally {
            foreach ($item in @(
                $targetRange,
                $formulaCell,
                $sourceRange,
                $sourceEquation
            )) {
                if ($null -ne $item) {
                    [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject(
                        $item)
                }
            }
        }
    }

    if ($testDocument.OMaths.Count -ne $SourceIndices.Count) {
        throw (
            'Representative test document formula-count mismatch: expected=' +
            $SourceIndices.Count +
            '; actual=' +
            $testDocument.OMaths.Count
        )
    }

    $testDocument.SaveAs2($outputFullPath, 12)
    $saved = $true

    [pscustomobject]@{
        SourcePath = $sourceFullPath
        OutputPath = $outputFullPath
        SourceFormulaCount = $sourceCount
        RepresentativeFormulaCount = $SourceIndices.Count
        SourceIndices = $SourceIndices
    } | ConvertTo-Json -Depth 4
}
finally {
    if ($null -ne $testTable) {
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject(
            $testTable)
    }
    if ($null -ne $testDocument) {
        $testDocument.Close($saved)
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject(
            $testDocument)
    }
    if ($null -ne $sourceDocument) {
        $sourceDocument.Close($false)
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject(
            $sourceDocument)
    }
    if ($null -ne $word) {
        $word.Quit()
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($word)
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
