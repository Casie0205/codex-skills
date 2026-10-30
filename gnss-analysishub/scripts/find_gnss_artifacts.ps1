param(
    [Parameter(Mandatory = $true)]
    [string]$Path,

    [switch]$Recurse,

    [switch]$AsJson
)

$searchRoot = (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path
$items = Get-ChildItem -LiteralPath $searchRoot -File -Recurse:$Recurse

$groups = @{}
$orphanDataLists = New-Object System.Collections.Generic.List[System.IO.FileInfo]

function New-ArtifactGroup {
    param(
        [string]$Stem,
        [string]$Directory
    )

    return [ordered]@{
        stem                    = $Stem
        directory               = $Directory
        qc_html                 = $null
        df_html                 = $null
        tf_html                 = $null
        datalist_log            = $null
        df_data                 = $null
        tf_data                 = $null
        mp_result               = $null
        mp_data                 = $null
        gf_data                 = $null
        mw_data                 = $null
        psr_compare_data        = $null
        slip_ratio_log          = $null
        arlog_data              = $null
        history_restore_candidate = ((Split-Path -Path $Directory -Leaf) -like 'Sourcefile_*')
        available_health_routes = @()
        available_routes        = @()
        suggested_health_route  = $null
        suggested_route         = $null
        suggested_first_action  = $null
    }
}

function Get-ArtifactMatch {
    param([System.IO.FileInfo]$Item)

    switch -Regex ($Item.Name) {
        '^(.*)_QC\.html$' {
            return @{
                stem = $Matches[1]
                field = 'qc_html'
            }
        }
        '^(.*)_DF\.html$' {
            return @{
                stem = $Matches[1]
                field = 'df_html'
            }
        }
        '^(.*)_TF\.html$' {
            return @{
                stem = $Matches[1]
                field = 'tf_html'
            }
        }
        '^(.*)_DataList\.log$' {
            return @{
                stem = $Matches[1]
                field = 'datalist_log'
            }
        }
        '^(.*)\.DF$' {
            return @{
                stem = $Matches[1]
                field = 'df_data'
            }
        }
        '^(.*)\.TF$' {
            return @{
                stem = $Matches[1]
                field = 'tf_data'
            }
        }
        '^(.*)\.MPresult$' {
            return @{
                stem = $Matches[1]
                field = 'mp_result'
            }
        }
        '^(.*)\.MP$' {
            return @{
                stem = $Matches[1]
                field = 'mp_data'
            }
        }
        '^(.*)\.GF$' {
            return @{
                stem = $Matches[1]
                field = 'gf_data'
            }
        }
        '^(.*)\.MW$' {
            return @{
                stem = $Matches[1]
                field = 'mw_data'
            }
        }
        '^(.*)\.PsrCompare$' {
            return @{
                stem = $Matches[1]
                field = 'psr_compare_data'
            }
        }
        '^(.*)_SLIPRATIO\.log$' {
            return @{
                stem = $Matches[1]
                field = 'slip_ratio_log'
            }
        }
        '^(.*)\.arlog$' {
            return @{
                stem = $Matches[1]
                field = 'arlog_data'
            }
        }
        '^DataList\.log$' {
            return @{
                stem = $null
                field = 'orphan_datalist_log'
            }
        }
        default {
            return $null
        }
    }
}

foreach ($item in $items) {
    $match = Get-ArtifactMatch -Item $item
    if (-not $match) {
        continue
    }

    if ($match.field -eq 'orphan_datalist_log') {
        $orphanDataLists.Add($item)
        continue
    }

    $groupKey = '{0}|{1}' -f $item.Directory.FullName, $match.stem
    if (-not $groups.ContainsKey($groupKey)) {
        $groups[$groupKey] = New-ArtifactGroup -Stem $match.stem -Directory $item.Directory.FullName
    }

    $groups[$groupKey][$match.field] = $item.FullName
}

foreach ($item in $orphanDataLists) {
    $candidates = @(
        $groups.Values | Where-Object {
            $_.directory -eq $item.Directory.FullName
        }
    )

    if ($candidates.Count -eq 1 -and -not $candidates[0].datalist_log) {
        $candidates[0].datalist_log = $item.FullName
        continue
    }

    $fallbackStem = Split-Path -Path $item.Directory.FullName -Leaf
    $groupKey = '{0}|{1}' -f $item.Directory.FullName, $fallbackStem
    if (-not $groups.ContainsKey($groupKey)) {
        $groups[$groupKey] = New-ArtifactGroup -Stem $fallbackStem -Directory $item.Directory.FullName
    }

    if (-not $groups[$groupKey].datalist_log) {
        $groups[$groupKey].datalist_log = $item.FullName
    }
}

$result = foreach ($group in $groups.Values | Sort-Object directory, stem) {
    $healthRoutes = New-Object System.Collections.Generic.List[string]
    $routes = New-Object System.Collections.Generic.List[string]

    if ($group.qc_html) {
        $routes.Add('cli-merge-qc-html')
    }

    if ($group.datalist_log) {
        $routes.Add('cli-plot-cn0')
    }

    if ($group.history_restore_candidate) {
        $routes.Add('gui-restore-existing-results')
    }

    if ($group.qc_html -and $group.datalist_log) {
        $healthRoutes.Add('cli-qc-health')
        $routes.Add('cli-qc-health')
        $routes.Add('cli-rtk-report')
    }

    if ($group.df_html -and $group.datalist_log -and $group.df_data) {
        $healthRoutes.Add('gui-df-health')
        $routes.Add('gui-df-health')
        $routes.Add('cli-plot-df-residual')
    }

    if ($group.tf_html -and $group.datalist_log -and $group.tf_data) {
        $healthRoutes.Add('gui-tf-health')
        $routes.Add('gui-tf-health')
        $routes.Add('cli-plot-tf-residual')
    }

    if ($group.datalist_log -and $group.arlog_data) {
        $routes.Add('cli-auto-combined-report')
    }

    $group.available_health_routes = @($healthRoutes)
    $group.available_routes = @($routes | Select-Object -Unique)

    if ($group.available_health_routes -contains 'cli-qc-health') {
        $group.suggested_health_route = 'cli-qc-health'
        $group.suggested_route = 'cli-qc-health'
        $group.suggested_first_action = 'Generate a QC health report with AnalysisHub-cli report health.'
    } elseif ($group.available_health_routes -contains 'gui-df-health') {
        $group.suggested_health_route = 'gui-df-health'
        $group.suggested_route = 'gui-df-health'
        $group.suggested_first_action = 'Open AnalysisHub GUI and generate the DF health report from the current DF mode.'
    } elseif ($group.available_health_routes -contains 'gui-tf-health') {
        $group.suggested_health_route = 'gui-tf-health'
        $group.suggested_route = 'gui-tf-health'
        $group.suggested_first_action = 'Open AnalysisHub GUI and generate the TF health report from the current TF mode.'
    } elseif ($group.available_routes -contains 'cli-plot-cn0') {
        $group.suggested_health_route = 'incomplete'
        $group.suggested_route = 'cli-plot-cn0'
        $group.suggested_first_action = 'Use AnalysisHub-cli plot on the DataList log for a first-pass CN0 view.'
    } elseif ($group.available_routes -contains 'cli-merge-qc-html') {
        $group.suggested_health_route = 'incomplete'
        $group.suggested_route = 'cli-merge-qc-html'
        $group.suggested_first_action = 'Use AnalysisHub-cli qc merge-reports if the goal is batch summary.'
    } else {
        $group.suggested_health_route = 'incomplete'
        $group.suggested_route = 'incomplete'
        $group.suggested_first_action = 'More inputs are needed before a report workflow can be selected.'
    }

    [pscustomobject]$group
}

if ($AsJson) {
    $result | ConvertTo-Json -Depth 6
} else {
    $result
}
