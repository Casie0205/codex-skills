# RTKPlot Studio Commands

## Contents

- [Runtime selection](#runtime-selection)
- [Inspect](#inspect)
- [Render](#render)
- [Output rules](#output-rules)
- [Errors](#errors)

## Runtime selection

Set `$rtkRoot` to the copied skill directory and use Python 3.11 or newer with
Matplotlib available:

```powershell
$rtkRoot = "D:\DOC\cloud-skills\rtkplot-studio"
$py = "python"
$script = Join-Path $rtkRoot "scripts\rtkplot_studio.py"
& $py $script --version
```

Expected:

```text
RTKPlotStudio 0.1.0
```

## Inspect

Inspect one input:

```powershell
$source = "D:\Dataset\project\gnss_rtkplot.txt"
& $py $script inspect --input $source --json
```

Inspect multiple inputs in one call:

```powershell
& $py $script inspect `
  --input "D:\Dataset\project\run_a\gnss_rtkplot.txt" `
  --input "D:\Dataset\project\run_b\gnss_rtkplot.txt" `
  --json
```

The success object contains one item per input under `inputs`, including sample
counts, malformed rows, row widths, fix-type counts, status counts, time
statistics, ranges, and the first finite ENU origin.

## Render

One trajectory:

```powershell
& $py $script render `
  --input $source `
  --plot trajectory `
  --output "D:\Output\RTKPlotStudio\project\run_trajectory" `
  --formats svg,png `
  --json
```

One position component figure with East, North, and Up panels:

```powershell
& $py $script render `
  --input $source `
  --plot position `
  --output "D:\Output\RTKPlotStudio\project\run_position" `
  --formats svg,png `
  --json
```

One sigma figure:

```powershell
& $py $script render `
  --input $source `
  --plot sigma `
  --output "D:\Output\RTKPlotStudio\project\run_sigma" `
  --formats svg,png `
  --json
```

One quality figure:

```powershell
& $py $script render `
  --input $source `
  --plot quality `
  --output "D:\Output\RTKPlotStudio\project\run_quality" `
  --formats svg,png `
  --json
```

Overlay two sources:

```powershell
& $py $script render `
  --input "D:\Dataset\project\run_a\gnss_rtkplot.txt" `
  --input "D:\Dataset\project\run_b\gnss_rtkplot.txt" `
  --plot position `
  --output "D:\Output\RTKPlotStudio\project\run_a_vs_b_position" `
  --formats svg,png `
  --json
```

`--plot` accepts exactly one of `trajectory`, `position`, `sigma`, or `quality`.
Run separate commands when several figure types are required.

## Output rules

- `--output` is a file base name.
- `--formats svg,png` creates both `<base>.svg` and `<base>.png`.
- A `.svg` or `.png` suffix on `--output` is removed before writing both formats.
- Existing outputs are rejected unless `--overwrite` is supplied.
- Missing parent directories are created.
- Figure legends are placed outside and above the plotting area.
- `trajectory`, `position`, and `sigma` exclude NO_SOLUTION rows.
- `quality` includes every parsed row.

## Errors

Expected parsing, input, plotting, and output errors exit with code `2`.
With `--json`, failures return:

```json
{
  "ok": false,
  "command": "render",
  "error": "<exact error>"
}
```

Do not retry a failed command with guessed column order. Reinspect the source
row width and the 18-column contract first.
