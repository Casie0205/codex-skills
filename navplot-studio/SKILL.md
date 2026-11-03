---
name: navplot-studio
description: Use when the user wants to inspect or plot NavPlot files, export position/velocity/attitude figures, difference two NavPlot sources A-B, or operate NavPlotStudio.exe on Windows through its GUI or headless CLI.
---

# NavPlot Studio

## Contents

- [Locate the executable](#locate-the-executable)
- [Mandatory workflow](#mandatory-workflow)
- [Plot selection](#plot-selection)
- [Command rules](#command-rules)
- [GUI handoff](#gui-handoff)
- [Correctness boundaries](#correctness-boundaries)
- [Command reference](#command-reference)

Use the packaged `NavPlotStudio.exe` as the only data-processing entrypoint on
cloud computers. Do not call the source Python modules directly and do not
reimplement parsing, interpolation, or plotting.

## Locate the executable

Resolve the executable in this order:

1. The path in environment variable `NAVPLOT_STUDIO_EXE`.
2. `NavPlotStudio.exe` in the current task directory or its direct subdirectories.
3. `D:\Output\NavPlotStudio\NavPlotStudio.exe`.

If none exists, ask the user for the copied executable path. Do not scan every
drive.

Run `& $exe --version` once after locating a new executable. If it fails, treat
the executable as unavailable and report the exact error.

## Mandatory workflow

1. Quote the exe path, every input path, and the output base path.
2. Run `inspect --input "<file>" --json` before the first plot from a new data
   set. Confirm the sample count is nonzero and note skipped rows.
3. Map the request to one canonical plot value: `position`, `velocity`, or
   `attitude`.
4. Build exactly one `render` command for a normal plot. Use one `diff` command
   for one A-B plot type.
5. Check whether both `<output>.svg` and `<output>.png` already exist. If yes,
   ask before overwriting unless the user explicitly approved replacement.
6. Run the command with `--json` and verify exit code 0.
7. Verify both output files exist and are nonzero before reporting success.
8. Report the exact output paths and the relevant JSON fields. Do not invent
   values or visual conclusions that were not inspected.

Read [references/commands.md](references/commands.md) for exact command forms,
JSON fields, exit codes, and examples.

## Plot selection

| User wording | `--plot` |
| --- | --- |
| Position, E/N/U, position | `position` |
| Velocity, Ve/Vn/Vu, velocity | `velocity` |
| Attitude, Roll/Pitch/Yaw, attitude | `attitude` |
| A minus B, difference, compare | Use `diff --input-a A --input-b B` |

Each output figure has three stacked subplots for the three axes. `position`
means East/North/Up component time series, not an E-N plane trajectory map.

## Command rules

- Use `render` for one source or for overlaying multiple sources.
- Use `diff` only for exactly two sources. Preserve the user's A-B order.
- Treat `--output` as a file base name, not a directory.
- Include `--formats svg,png` so both formats are explicit.
- Keep `--json` for machine-readable output.
- Do not add `--max-gap` unless the user asks to change interpolation behavior.
  A `diff` success result reports `max_gap_seconds`; `inspect` does not.
- If the user wants several plot types, run separate commands. Do not combine
  all plot types into one image.

Default output naming when the user gives no path:

```text
D:\Output\NavPlotStudio\<project>\<source_stem>_<plot>
```

Use that default only when `D:\Output` exists. Otherwise ask for the destination
or use a writable directory supplied by the user.

## GUI handoff

Use GUI mode when the user wants to inspect, manually choose two sources, or
interactively save:

1. Start `NavPlotStudio.exe` with no arguments.
2. Use the Open Files action or drag files into the window.
3. Use data-source checkboxes to include or exclude overlays.
4. Right-click one source and set it as difference source A.
5. Right-click the second source and set it as difference source B.
6. Choose Generate Difference Figure and then position, velocity, or attitude.
7. In the target tab, use Save SVG/PNG.

## Correctness boundaries

- The first 7 NavPlot columns are required. Optional columns 8-27 may be absent.
- A 15-column source can be plotted for position. Do not claim velocity or
  attitude data unless columns 16-21 actually contain values.
- Position differencing uses a common origin from source A and A-source epochs
  as interpolation targets.
- Multiple position sources in one render share the ENU origin of the first
  input source, preserving inter-source offsets.
- Repeated GPS epochs within each source are reduced to the last record before
  differencing.
- Yaw differences are wrapped to `[-180, 180)` degrees.
- A "no overlap" or "no sample pair" error means the inputs cannot be compared
  under the current time or gap constraints. Report it; do not bypass the check.
- The tool writes SVG and PNG. Do not claim PDF, FIG, CSV, or E-N trajectory
  export support.

## Command reference

Load [references/commands.md](references/commands.md) whenever constructing or
debugging a CLI command.
