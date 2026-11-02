[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Add-Type -Path (
    Join-Path $scriptRoot 'OpcRelationshipTargetResolver.cs'
)

$type = [ThesisMathTypeConversionV2.OpcRelationshipTargetResolver]
$oleType = $type::OleObjectRelationshipType

$cases = @(
    @{
        target = 'embeddings/equation.bin'
        expected = 'word/embeddings/equation.bin'
    },
    @{
        target = '/word/embeddings/equation.bin'
        expected = 'word/embeddings/equation.bin'
    },
    @{
        target = '../embeddings/equation.bin'
        expected = 'embeddings/equation.bin'
    },
    @{
        target = 'embeddings/../media/equation.bin'
        expected = 'word/media/equation.bin'
    }
)
foreach ($case in $cases) {
    $actual = $type::ResolveOleObjectPart(
        'word/document.xml',
        $case.target,
        '',
        $oleType
    )
    if ($actual -ne $case.expected) {
        throw "Unexpected OPC resolution for $($case.target): $actual"
    }
}

$failureCases = @(
    @{
        target = 'embeddings/equation.bin'
        mode = 'External'
        relationType = $oleType
    },
    @{
        target = 'https://example.test/equation.bin'
        mode = ''
        relationType = $oleType
    },
    @{
        target = '../../equation.bin'
        mode = ''
        relationType = $oleType
    },
    @{
        target = 'embeddings/equation.bin'
        mode = ''
        relationType = 'wrong-type'
    }
)
foreach ($case in $failureCases) {
    $failed = $false
    try {
        [void]$type::ResolveOleObjectPart(
            'word/document.xml',
            $case.target,
            $case.mode,
            $case.relationType
        )
    }
    catch {
        $failed = $true
    }
    if (-not $failed) {
        throw "Expected OPC target to fail: $($case.target)"
    }
}

[pscustomobject]@{
    TestCount = $cases.Count + $failureCases.Count
    Passed = $cases.Count + $failureCases.Count
} | ConvertTo-Json
