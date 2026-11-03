# NavPlot Studio CLI Reference

> Version: 0.1.0

## Contents

- [Executable selection](#executable-selection)
- [Inspect](#inspect)
- [Render](#render)
- [Difference](#difference)
- [Output contract](#output-contract)
- [Errors](#errors)
- [Verified examples](#verified-examples)

## Executable selection

Set a variable once in PowerShell:

```powershell
$exe = $env:NAVPLOT_STUDIO_EXE
if (-not $exe) {
    $exe = "D:\Output\NavPlotStudio\NavPlotStudio.exe"
}
```

Check the build:

```powershell
& $exe --version
& $exe --help
```

Expected version for this reference:

```text
NavPlotStudio 0.1.0
```

## Inspect

Use before plotting:

```powershell
& $exe inspect --input "C:\Data\run.navplot" --json
```

Multiple files:

```powershell
& $exe inspect `
  --input "C:\Data\a.navplot" `
  --input "C:\Data\b.navplot" `
  --json
```

Success shape:

```json
{
  "ok": true,
  "command": "inspect",
  "inputs": [
    {
      "path": "C:\\Data\\run.navplot",
      "samples": 91634,
      "unique_epochs": 91449,
      "duplicate_epochs": 185,
      "duration_seconds": 9163.4,
      "row_column_counts": [27],
      "skipped_rows": 0,
      "position_statuses": [
        "fixed solution",
        "float solution",
        "RTD",
        "SPP",
        "dead reckoning"
      ],
      "origin": {
        "latitude_deg": 31.15973417,
        "longitude_deg": 121.17913572,
        "height_m": 15.354
      }
    }
  ]
}
```

The actual state strings depend on the input language. The executable emits JSON
as ASCII Unicode escapes where needed. Parse JSON rather than matching rendered
glyphs.

## Render

One source:

```powershell
& $exe render `
  --input "C:\Data\run.navplot" `
  --plot position `
  --output "D:\Output\NavPlotStudio\project\run_position" `
  --formats svg,png `
  --json
```

Overlay multiple sources:

```powershell
& $exe render `
  --input "C:\Data\a.navplot" `
  --input "C:\Data\b.navplot" `
  --plot velocity `
  --output "D:\Output\NavPlotStudio\project\velocity_compare" `
  --formats svg,png `
  --json
```

Allowed `--plot` values:

- `position`
- `velocity`
- `attitude`

Optional title:

```powershell
--title "Survey run velocity"
```

## Difference

Position A-B:

```powershell
& $exe diff `
  --input-a "C:\Data\a.navplot" `
  --input-b "C:\Data\b.navplot" `
  --plot position `
  --output "D:\Output\NavPlotStudio\project\a_minus_b_position" `
  --formats svg,png `
  --json
```

Velocity B-A:

```powershell
& $exe diff `
  --input-a "C:\Data\b.navplot" `
  --input-b "C:\Data\a.navplot" `
  --plot velocity `
  --output "D:\Output\NavPlotStudio\project\b_minus_a_velocity" `
  --formats svg,png `
  --json
```

Optional gap override:

```powershell
--max-gap 0.3
```

The unit is seconds. Without an override, the tool uses:

```text
max(0.05, 5 * max(median_dt_A, median_dt_B))
```

Success shape:

```json
{
  "ok": true,
  "command": "diff",
  "inputs": ["C:\\Data\\a.navplot", "C:\\Data\\b.navplot"],
  "plot": "position",
  "outputs": [
    "D:\\Output\\NavPlotStudio\\project\\a_minus_b_position.svg",
    "D:\\Output\\NavPlotStudio\\project\\a_minus_b_position.png"
  ],
  "sample_pairs": 86377,
  "target_epochs": 86377,
  "max_gap_seconds": 5.0
}
```

## Output contract

`--output` is a base name:

```text
--output D:\Output\NavPlotStudio\result
```

Creates:

```text
D:\Output\NavPlotStudio\result.svg
D:\Output\NavPlotStudio\result.png
```

If the base already ends in `.svg` or `.png`, that suffix is removed before both
formats are written:

```text
--output D:\Output\NavPlotStudio\result.svg
```

Still creates both `result.svg` and `result.png`.

The tool creates missing parent directories. It does not prompt before overwrite.
Check both target paths first when replacement was not explicitly approved.

## Errors

Success exit code:

```text
0
```

Expected input, parsing, difference, save, or argument failure:

```text
2
```

With `--json`, failures are printed as:

```json
{
  "ok": false,
  "error": "<exact error text>"
}
```

Handle these error categories without retrying blindly:

- Missing file: verify the quoted path.
- No usable NavPlot rows: the file is not usable NavPlot text.
- No overlapping source time range: the GPS week/second ranges do not overlap.
- No sample pairs within the gap limit: do not hide this with a huge
  `--max-gap` unless the user explicitly accepts the interpolation risk.
- No three-axis velocity or attitude values: the file lacks optional columns
  16-21.

## Verified examples

The packaged exe was verified with:

```text
D:\Dataset\ctclib_learn_use\Geely-1000000-V1.1.43-V221.1698.1712-D1-T0-20250415_hcnav\hcnav_ins.navplot
```

Verified commands:

```powershell
& $exe inspect --input $sample --json
& $exe render --input $sample --plot position --output $out\position --json
& $exe render --input $sample --plot velocity --output $out\velocity --json
& $exe render --input $sample --plot attitude --output $out\attitude --json
& $exe diff --input-a $sample --input-b $origin `
  --plot position --output $out\position_diff --json
```

The sample inspection reported 91,634 rows, 91,449 unique epochs, 185 duplicate
epochs, and row width 27.
