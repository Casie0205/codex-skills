---
name: rtkplot-studio
description: Use when the user wants to inspect or plot 18-column RTKPlot solution text, including the common gnss_rtkplot.txt trajectory, position, sigma, and quality figures. Do not use for RTKLIB .pos, .obs, or .nav files.
---

# RTKPlot Studio

## Contents

- [Format boundary](#format-boundary)
- [Locate the runtime](#locate-the-runtime)
- [Mandatory workflow](#mandatory-workflow)
- [Plot selection](#plot-selection)
- [Command rules](#command-rules)
- [Correctness boundaries](#correctness-boundaries)
- [References](#references)

Inspect and plot the 18-column whitespace-separated RTKPlot solution text used
by the GNSS/INS post-processing flow, commonly `gnss_rtkplot.txt`.

## Format boundary

Use this skill only when the source follows the 18-column RTKPlot text contract
described in [references/format.md](references/format.md). The required fields
include relative time, latitude/longitude in radians, height, three position
sigmas, ages, satellite count, solution codes, DOP values, and source status.

Do not use this skill for RTKLIB `.pos`, `.obs`, or `.nav` files. Those belong
to the RTKLIB RTKPLOT application. Do not infer columns from the RTKLIB GUI.

## Locate the runtime

Resolve the Python runtime in this order:

1. The path in environment variable `RTKPLOT_STUDIO_PY`.
2. `python` on `PATH`, provided it is Python 3.11 or newer.
3. The runtime supplied by the current task environment.

Resolve the entrypoint as `<skill-directory>\scripts\rtkplot_studio.py`. Run
`--version` once before the first use in a new environment. If Matplotlib is
missing, report the exact import error; do not reimplement plotting with a
different stack.

## Mandatory workflow

1. Quote every input path, output base, Python path, and script path.
2. Run `inspect --input "<file>" --json` before the first plot from a new data
   set. Confirm `samples > 0`, review `malformed_rows`, and confirm the expected
   fix-type counts.
3. Map the request to exactly one plot type: `trajectory`, `position`, `sigma`,
   or `quality`.
4. Build one `render` command for that plot type. Use multiple `--input` values
   only for overlays that belong in the same figure.
5. Check the two intended output paths before overwriting. Ask the user unless
   replacement was explicitly approved; use `--overwrite` only after approval.
6. Run with `--formats svg,png --json` and verify exit code 0.
7. Verify both files exist and are nonzero before reporting success.
8. Report the exact outputs, sample counts, malformed-row count, and fix-type
   counts relevant to the request.

## Plot selection

| User wording | `--plot` |
| --- | --- |
| Track, map, E-N trajectory, route | `trajectory` |
| E/N/U time series, position history | `position` |
| Sigma, standard deviation, uncertainty | `sigma` |
| Satellites, differential age, PDOP, quality | `quality` |

Each command creates exactly one figure. Do not combine multiple requested plot
types into one image.

## Command rules

- Use `trajectory` for the East-North plane. Use `position` for three time-series
  panels.
- Multiple inputs in `render` are overlays. They share the first input's ENU
  origin.
- Treat `--output` as a file base name, not a directory.
- Include `--formats svg,png` explicitly.
- Use `--json` for machine-readable results.
- Keep the user's input order in overlays and reports.
- Default output naming when no path is supplied:

```text
D:\Output\RTKPlotStudio\<project>\<source_stem>_<plot>
```

Use that default only when `D:\Output` exists. Otherwise ask for a destination
or use a writable directory supplied by the user.

## Correctness boundaries

- Latitude and longitude are radians. Never silently treat them as degrees.
- `trajectory`, `position`, and `sigma` include fix codes 1, 2, and 3 only.
  NO_SOLUTION rows are excluded to avoid false jumps to an invalid coordinate.
- `quality` includes all parsed rows and plots satellite count, differential
  age, and PDOP.
- Extra columns are ignored; fewer than 18 required columns are malformed.
- The tool supports overlay rendering but does not compute an A-B solution
  difference.
- The tool writes SVG and PNG. Do not claim FIG, PDF, CSV, or RTKLIB-native
  export support.
- A "no usable 18-column RTKPlot rows" error usually means the input is an
  RTKLIB solution file or a different text format. Reinspect the source instead
  of guessing a conversion.

## References

- [references/format.md](references/format.md): exact 18-column contract,
  filtering rules, and a sample row.
- [references/commands.md](references/commands.md): runtime selection, inspect
  and render commands, output behavior, JSON, and errors.
