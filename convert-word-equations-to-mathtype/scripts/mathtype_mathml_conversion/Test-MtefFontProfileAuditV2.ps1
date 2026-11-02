[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Add-Type -Path (Join-Path $scriptRoot 'MtefFontProfileAudit.cs')

function New-TestMtef {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Fonts,

        [byte[]]$IncidentalBytes = @(),

        [string]$MathExtraFont,

        [string]$RequiredTimesFont = 'Times New Roman',

        [byte]$EquationPreferencesOptions = 0,

        [switch]$MalformedLastFont
    )

    $bytes = [System.Collections.Generic.List[byte]]::new()
    $bytes.AddRange([byte[]](5, 1, 0, 7, 8))
    $bytes.AddRange([System.Text.Encoding]::ASCII.GetBytes('DSMT7'))
    $bytes.Add(0)
    $bytes.Add(1)
    $bytes.Add(19)
    $bytes.AddRange(
        [System.Text.Encoding]::ASCII.GetBytes('WinAllBasicCodePages')
    )
    $bytes.Add(0)
    for ($index = 0; $index -lt $Fonts.Count; $index++) {
        $font = $Fonts[$index]
        $bytes.Add(17)
        $bytes.Add(5)
        $bytes.AddRange(
            [System.Text.Encoding]::ASCII.GetBytes($font)
        )
        if (-not (
            $MalformedLastFont -and
            $index -eq $Fonts.Count - 1
        )) {
            $bytes.Add(0)
        }
    }
    if (-not $MalformedLastFont) {
        $bytes.Add(18)
        $bytes.Add($EquationPreferencesOptions)
        $bytes.Add(0)
        $bytes.Add(0)
        $bytes.Add(11)
        $requiredTimesIndex =
            [Array]::IndexOf($Fonts, $RequiredTimesFont)
        for ($styleIndex = 0; $styleIndex -lt 10; $styleIndex++) {
            if ($styleIndex -in @(0, 1, 2, 6, 7, 9) -and
                $requiredTimesIndex -ge 0) {
                $bytes.Add($requiredTimesIndex + 1)
                if ($styleIndex -eq 2) {
                    $bytes.Add(2)
                }
                elseif ($styleIndex -eq 6) {
                    $bytes.Add(1)
                }
                else {
                    $bytes.Add(0)
                }
            }
            else {
                $bytes.Add(0)
            }
        }
        if ([string]::IsNullOrWhiteSpace($MathExtraFont)) {
            if ($Fonts -contains 'Euclid Extra') {
                $MathExtraFont = 'Euclid Extra'
            }
            elseif ($Fonts -contains 'MT Extra') {
                $MathExtraFont = 'MT Extra'
            }
        }
        $mathExtraIndex = [Array]::IndexOf($Fonts, $MathExtraFont)
        if ($mathExtraIndex -lt 0) {
            $bytes.Add(0)
        }
        else {
            $bytes.Add($mathExtraIndex + 1)
            $bytes.Add(0)
        }
        $bytes.AddRange($IncidentalBytes)
    }
    return $bytes.ToArray()
}

$accepted = [ThesisMathTypeConversionV2.MtefFontProfileAudit]::Inspect(
    (New-TestMtef -Fonts @('Times New Roman', 'Euclid Extra'))
)
if (-not $accepted.Accepted) {
    throw 'Expected Times New Roman/Euclid Extra profile to pass.'
}

$legacy = [ThesisMathTypeConversionV2.MtefFontProfileAudit]::Inspect(
    (New-TestMtef -Fonts @('Times New Roman', 'MT Extra'))
)
if ($legacy.Accepted -or -not $legacy.HasLegacyMtExtra) {
    throw 'Expected legacy MT Extra profile to fail.'
}

$substring = [ThesisMathTypeConversionV2.MtefFontProfileAudit]::Inspect(
    (New-TestMtef -Fonts @(
        'Times New Roman',
        'Euclid Extra',
        'MT Extra Tiger'
    ))
)
if (-not $substring.Accepted -or $substring.HasLegacyMtExtra) {
    throw 'MT Extra Tiger must not be treated as exact legacy MT Extra.'
}

$prefixed = [ThesisMathTypeConversionV2.MtefFontProfileAudit]::Inspect(
    (New-TestMtef -Fonts @(
        'Foo Times New Roman',
        'Foo Euclid Extra'
    ))
)
if ($prefixed.Accepted -or
    $prefixed.HasTimesNewRoman -or
    $prefixed.HasEuclidExtra) {
    throw 'Prefixed font names must not pass exact FONT_DEF matching.'
}

$incidentalValue = [System.Text.Encoding]::ASCII.GetBytes(
    "Times New Roman`0Euclid Extra`0"
)
$incidental = [ThesisMathTypeConversionV2.MtefFontProfileAudit]::Inspect(
    (New-TestMtef -Fonts @('Symbol') -IncidentalBytes $incidentalValue)
)
if ($incidental.Accepted -or
    $incidental.HasTimesNewRoman -or
    $incidental.HasEuclidExtra) {
    throw 'Strings outside FONT_DEF records must not pass the profile.'
}

$wrongMapping =
    [ThesisMathTypeConversionV2.MtefFontProfileAudit]::Inspect(
        (New-TestMtef `
            -Fonts @('Times New Roman', 'Euclid Extra') `
            -MathExtraFont 'Times New Roman')
    )
if ($wrongMapping.Accepted -or
    $wrongMapping.MathExtraStyleUsesEuclidExtra) {
    throw 'Euclid Extra must be the font mapped by the Math Extra style.'
}

$wrongTimesMapping =
    [ThesisMathTypeConversionV2.MtefFontProfileAudit]::Inspect(
        (New-TestMtef `
            -Fonts @(
                'Times New Roman',
                'Arial',
                'Euclid Extra'
            ) `
            -RequiredTimesFont 'Arial')
    )
if ($wrongTimesMapping.Accepted -or
    $wrongTimesMapping.RequiredStylesUseTimesNewRoman) {
    throw 'Required ordinary style slots must map to Times New Roman.'
}

$invalidOptionsFailed = $false
try {
    [void][ThesisMathTypeConversionV2.MtefFontProfileAudit]::Inspect(
        (New-TestMtef `
            -Fonts @('Times New Roman', 'Euclid Extra') `
            -EquationPreferencesOptions 1)
    )
}
catch {
    $invalidOptionsFailed = $true
}
if (-not $invalidOptionsFailed) {
    throw 'Nonzero EQN_PREFS options must fail parsing.'
}

$malformedFailed = $false
try {
    [void][ThesisMathTypeConversionV2.MtefFontProfileAudit]::Inspect(
        (New-TestMtef `
            -Fonts @('Times New Roman', 'Euclid Extra') `
            -MalformedLastFont)
    )
}
catch {
    $malformedFailed = $true
}
if (-not $malformedFailed) {
    throw 'An unterminated FONT_DEF must fail parsing.'
}

[pscustomobject]@{
    TestCount = 9
    Passed = 9
    AcceptedProfile = $accepted.Accepted
    LegacyProfile = $legacy.Accepted
} | ConvertTo-Json -Depth 3
