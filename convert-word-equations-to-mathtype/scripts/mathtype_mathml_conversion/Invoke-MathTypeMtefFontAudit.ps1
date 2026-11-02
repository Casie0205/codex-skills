[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$DocumentPath,

    [Parameter(Mandatory = $true)]
    [string]$ReportPath,

    [ValidateRange(0, [int]::MaxValue)]
    [int]$ExpectedMathTypeObjectCount = 0
)

$ErrorActionPreference = 'Stop'
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sharedRoot = Join-Path $scriptRoot '..\mathtype_tex_conversion'

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.Xml
$references = @(
    [System.IO.Compression.ZipArchive].Assembly.Location,
    [System.IO.Compression.ZipFile].Assembly.Location,
    [System.Xml.XmlDocument].Assembly.Location,
    [System.Uri].Assembly.Location
)
Add-Type -Path @(
    (Join-Path $sharedRoot 'MathTypeOleMtef.cs'),
    (Join-Path $scriptRoot 'MtefFontProfileAudit.cs'),
    (Join-Path $scriptRoot 'OpcRelationshipTargetResolver.cs')
) -ReferencedAssemblies $references

$documentPath = [System.IO.Path]::GetFullPath($DocumentPath)
$reportPath = [System.IO.Path]::GetFullPath($ReportPath)
if (-not [System.IO.File]::Exists($documentPath)) {
    throw "DOCX not found: $documentPath"
}
if ([string]::Equals(
    $documentPath,
    $reportPath,
    [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'The report path must differ from the DOCX path.'
}
if ([System.IO.File]::Exists($reportPath)) {
    throw "Report already exists: $reportPath"
}

$sourceStream = [System.IO.File]::Open(
    $documentPath,
    [System.IO.FileMode]::Open,
    [System.IO.FileAccess]::Read,
    [System.IO.FileShare]::ReadWrite
)
$snapshotStream = [System.IO.MemoryStream]::new()
try {
    $sourceStream.CopyTo($snapshotStream)
}
finally {
    $sourceStream.Dispose()
}
$documentSizeBytes = $snapshotStream.Length
$documentBytes = $snapshotStream.ToArray()
$sha256 = [System.Security.Cryptography.SHA256]::Create()
try {
    $documentSha256 = [System.BitConverter]::ToString(
        $sha256.ComputeHash($documentBytes)
    ).Replace('-', '')
}
finally {
    $sha256.Dispose()
}
$snapshotStream.Position = 0
$archive = $null
try {
    $archive = [System.IO.Compression.ZipArchive]::new(
        $snapshotStream,
        [System.IO.Compression.ZipArchiveMode]::Read,
        $false
    )
    $documentEntry = $archive.GetEntry('word/document.xml')
    $relationshipsEntry =
        $archive.GetEntry('word/_rels/document.xml.rels')
    if ($null -eq $documentEntry -or
        $null -eq $relationshipsEntry) {
        throw 'DOCX is missing document.xml or its relationships part.'
    }

    $documentXml = [System.Xml.XmlDocument]::new()
    $documentXml.PreserveWhitespace = $true
    $documentStream = $documentEntry.Open()
    try {
        $documentXml.Load($documentStream)
    }
    finally {
        $documentStream.Dispose()
    }

    $relationshipsXml = [System.Xml.XmlDocument]::new()
    $relationshipsStream = $relationshipsEntry.Open()
    try {
        $relationshipsXml.Load($relationshipsStream)
    }
    finally {
        $relationshipsStream.Dispose()
    }

    $documentNamespaces =
        [System.Xml.XmlNamespaceManager]::new(
            $documentXml.NameTable
        )
    $documentNamespaces.AddNamespace(
        'o',
        'urn:schemas-microsoft-com:office:office'
    )
    $documentNamespaces.AddNamespace(
        'r',
        'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    )
    $relationshipNamespaces =
        [System.Xml.XmlNamespaceManager]::new(
            $relationshipsXml.NameTable
        )
    $relationshipNamespaces.AddNamespace(
        'p',
        'http://schemas.openxmlformats.org/package/2006/relationships'
    )

    $results = [System.Collections.Generic.List[object]]::new()
    $objects = $documentXml.SelectNodes(
        "//o:OLEObject[@ProgID='Equation.DSMT4']",
        $documentNamespaces
    )
    if ($objects.Count -eq 0) {
        throw 'DOCX contains no inline Equation.DSMT4 objects.'
    }
    $index = 0
    foreach ($object in $objects) {
        $index++
        $relationId = $object.GetAttribute(
            'id',
            'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
        )
        $relationship = $relationshipsXml.SelectSingleNode(
            "//p:Relationship[@Id='$relationId']",
            $relationshipNamespaces
        )
        if ($null -eq $relationship) {
            throw "Missing relationship $relationId for MathType object $index."
        }
        $target = $relationship.GetAttribute('Target')
        $targetMode = $relationship.GetAttribute('TargetMode')
        $relationshipType = $relationship.GetAttribute('Type')
        $target =
            [ThesisMathTypeConversionV2.OpcRelationshipTargetResolver]::
                ResolveOleObjectPart(
                    'word/document.xml',
                    $target,
                    $targetMode,
                    $relationshipType
                )
        $entry = $archive.GetEntry($target)
        if ($null -eq $entry) {
            throw "Missing MathType OLE part: $target"
        }

        $entryStream = $entry.Open()
        $buffer = [System.IO.MemoryStream]::new()
        try {
            $entryStream.CopyTo($buffer)
            $mtef =
                [ThesisMathTypeConversion.MathTypeOleMtef]::
                    ReadEquationMtefFromOlePackage($buffer.ToArray())
        }
        finally {
            $buffer.Dispose()
            $entryStream.Dispose()
        }

        $fontAudit =
            [ThesisMathTypeConversionV2.MtefFontProfileAudit]::
                Inspect($mtef)
        $results.Add(
            [pscustomobject]@{
                objectIndex = $index
                relationId = $relationId
                olePart = $target
                mtefLength = $mtef.Length
                hasTimesNewRoman = $fontAudit.HasTimesNewRoman
                hasEuclidExtra = $fontAudit.HasEuclidExtra
                hasLegacyMtExtra = $fontAudit.HasLegacyMtExtra
                requiredStylesUseTimesNewRoman =
                    $fontAudit.RequiredStylesUseTimesNewRoman
                mathExtraStyleUsesEuclidExtra =
                    $fontAudit.MathExtraStyleUsesEuclidExtra
                accepted = $fontAudit.Accepted
            }
        )
    }
}
finally {
    if ($null -ne $archive) {
        $archive.Dispose()
    }
    $snapshotStream.Dispose()
}

$countMatchesExpectation =
    $ExpectedMathTypeObjectCount -eq 0 -or
    $results.Count -eq $ExpectedMathTypeObjectCount
$rejectedCount =
    @($results | Where-Object { -not $_.accepted }).Count
$summary = [pscustomobject]@{
    documentPath = $documentPath
    documentSizeBytes = $documentSizeBytes
    documentSha256 = $documentSha256
    mathTypeObjectCount = $results.Count
    expectedMathTypeObjectCount =
        if ($ExpectedMathTypeObjectCount -gt 0) {
            $ExpectedMathTypeObjectCount
        }
        else {
            $null
        }
    countMatchesExpectation = $countMatchesExpectation
    acceptedCount = @($results | Where-Object accepted).Count
    timesNewRomanCount =
        @($results | Where-Object hasTimesNewRoman).Count
    euclidExtraCount =
        @($results | Where-Object hasEuclidExtra).Count
    legacyMtExtraCount =
        @($results | Where-Object hasLegacyMtExtra).Count
    requiredStylesUseTimesNewRomanCount =
        @(
            $results |
                Where-Object requiredStylesUseTimesNewRoman
        ).Count
    mathExtraStyleUsesEuclidExtraCount =
        @(
            $results |
                Where-Object mathExtraStyleUsesEuclidExtra
        ).Count
    rejectedCount = $rejectedCount
    hardGateAccepted =
        $rejectedCount -eq 0 -and $countMatchesExpectation
}
$payload = [pscustomobject]@{
    summary = $summary
    equations = $results
}

$parent = [System.IO.Path]::GetDirectoryName($reportPath)
if (-not [string]::IsNullOrWhiteSpace($parent)) {
    [System.IO.Directory]::CreateDirectory($parent) | Out-Null
}
$temporaryReport =
    $reportPath +
    '.tmp-' +
    [System.Guid]::NewGuid().ToString('N')
try {
    [System.IO.File]::WriteAllText(
        $temporaryReport,
        ($payload | ConvertTo-Json -Depth 5),
        [System.Text.UTF8Encoding]::new($false)
    )
    [System.IO.File]::Move($temporaryReport, $reportPath)
}
finally {
    if ([System.IO.File]::Exists($temporaryReport)) {
        [System.IO.File]::Delete($temporaryReport)
    }
}
$summary | ConvertTo-Json -Depth 3
if (-not $summary.hardGateAccepted) {
    throw (
        "MTEF font profile audit failed. Report: " +
        $reportPath
    )
}
