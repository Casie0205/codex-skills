---
name: gnss-ins-baseline-analysis
description: Use when analyzing CTCLib GNSS/INS data end to end, including split IMU figures, navigation calibration and writeback, status-colored trajectories, and INS-versus-RTK error statistics.
---

# GNSS/INS Baseline Analysis

Status: workflow and helper scripts verified on Windows on 2026-11-09.

## Contents

- [Purpose](#purpose)
- [Use CTCLib first](#use-ctclib-first)
- [Required sequence](#required-sequence)
- [IMU analysis](#imu-analysis)
- [Calibration](#calibration)
- [Apply calibration and rerun](#apply-calibration-and-rerun)
- [Navigation result plots](#navigation-result-plots)
- [Output naming](#output-naming)
- [Resume without repeating](#resume-without-repeating)
- [Output layout](#output-layout)
- [Validation rules](#validation-rules)

## Purpose

Run a repeatable baseline analysis for CTCLib raw GNSS/INS data:

1. decode raw data;
2. analyze all split IMU NavPlot files;
3. run a calibration solve;
4. copy only observable calibration states into a new config;
5. run the final navigation solve with estimation disabled.

Do not use this skill for RINEX-only positioning, RTKPlot files, or general
NavPlot plotting that does not involve CTCLib GNSS/INS processing.

## Use CTCLib first

Load and follow the `ctclib` skill before running either executable. Use its
packaged decode and solve scripts with absolute paths:

- `run-decode.ps1` for raw `ctclib_decode.exe` work;
- `run-solve.ps1` for `ctclib_app.exe` calibration or navigation.

Do not reproduce CTCLib command construction in this skill. If CTCLib scripts
or executables are unavailable, stop and report the missing dependency.

## Required sequence

1. Decode and validate the raw input.
2. Analyze the split `ctclibdec_imu_navplot\imu_*.navplot` files.
3. Confirm ARW and VRW with the user.
4. Build a CALIB config and run `ins_mode=1`.
5. Inspect `dr_est.prodef`; treat states that never update as unobservable.
6. Write observable final values and their last-window STD into a new config.
7. Disable estimation and run `ins_mode=0`.
8. Generate trajectory, position-time, and INS-versus-RTK error outputs.
9. Validate the produced navigation rows and update the project Markdown report.

Do not skip from calibration directly to a deliverable navigation result
without checking that estimated values actually changed.

## IMU analysis

Read [references/imu-analysis.md](references/imu-analysis.md) before
interpreting the split IMU files.

Run:

```powershell
python "<skill-root>\scripts\analyze_imu_navplots.py" `
  --input-dir "D:\Output\<project>\ctclib\<decode>\source\<stem>_ctclibdec\ctclibdec_imu_navplot" `
  --output-dir "D:\Output\<project>\analysis\<data-time>_imu" `
  --json
```

The script must produce:

- one gyroscope figure containing all segments and X/Y/Z subplots;
- one accelerometer figure containing all segments and X/Y/Z subplots;
- one six-axis statistics table in CSV and Markdown form;
- `imu_analysis_summary.json` with segment, time, rate, gap, and temperature
  evidence.

Each figure must be saved as `.svg`, `.png`, and `.fig`; set
`figure.set_visible(True)` before saving `.fig`. Keep the legend outside the
plot area at the top, below the figure title. Put the unit in each y-axis
label, not in the figure title.

## Calibration

Read [references/navigation-calibration.md](references/navigation-calibration.md)
before creating a calibration config.

Ask the user to confirm `gyo_arw` and `acc_vrw` before running the calibration.
Do not silently reuse another project's noise values.

Start from
[assets/navigation-calibration.ctccfg](assets/navigation-calibration.ctccfg).
Preserve the template defaults `log_level=0,5`,
`method_align_velyaw=1`, and `method_align_velyaw_min=0.2` unless the data's
speed profile requires a different minimum yaw-alignment speed.

Every active parameter line in the generated input config must keep an ASCII
English inline `#` comment. Do not put Chinese text in an inline parameter
comment; some CTCLib builds fail to parse a single parameter line containing
Chinese text.

Select only sensor relationships supported by the decoded records:

- IMU to vehicle: `lever_imu2car`, `install_imu2car`;
- IMU to GNSS lever arm: `lever_imu2gnss`;
- GNSS to vehicle installation: `install_gnss2car`;
- VIO relationships only when `ctclibdec_vio.prodef` contains `VIO,` rows.

Run CALIB with `ins_mode=1`. A CALIB run may leave `ins_novatel.ASC` empty;
that alone is not a failure. Validate `dr_est.prodef`, run status, row count,
and the absence of structured `ERROR/FATAL` records.

`ins_mode` is defined in `[ctclib_ins]`:

| Value | Meaning |
| ---: | --- |
| 0 | NAV |
| 1 | CALIB |
| 2 | NAVLC |
| 3 | STATICCALIB |

`ins_mode=0` means normal navigation, not "disable navigation."

## Apply calibration and rerun

Apply only states that changed or moved away from their configured initial
values:

```powershell
python "<skill-root>\scripts\apply_calibration.py" `
  --dr-est "D:\Output\<project>\ctclib\<calibration>\dr_est.prodef" `
  --config "D:\DatasetParameters\<project>\<data-time-tag>_gnss-ins-calibration.ctccfg" `
  --output-config "D:\DatasetParameters\<project>\<data-time-tag>_gnss-ins-final.ctccfg" `
  --vio-prodef "D:\Output\<project>\ctclib\<decode>\source\<stem>_ctclibdec\ctclibdec_vio.prodef" `
  --window-seconds 30 `
  --json
```

The script:

- reads the fixed `INS_EST_STATE` columns;
- requires the source config to be `ins_mode=1`;
- checks each group's `est_*` switch and VIO input availability;
- uses the last 30 seconds by default;
- writes the median final value and median final STD for observable groups;
- leaves unobservable values unchanged;
- turns all related `est_*` switches off;
- sets `ins_mode=0` and `method_adaptive_calib=0`;
- writes CSV and JSON application reports beside the output config.

Review the report before running the final solve. A value that remains at its
initial value is not a successful calibration.

The script exits with status `3` and does not write the final config when no
observable groups are found. Some CTCLib builds may rewrite
`method_adaptive_calib` in their generated `ctclib.ctccfg`; in that case verify
that all related `est_*` switches are still zero and that the calibrated values
remain constant in `dr_est.prodef`.

## Navigation result plots

Read [references/navigation-plots.md](references/navigation-plots.md) before
interpreting solution colors, error signs, or error statistics.

Run:

```powershell
python "<skill-root>\scripts\plot_navigation_results.py" `
  --ins-insplot "<run>\ins_insplot.txt" `
  --gnss-rtkplot "<run>\gnss_rtkplot.txt" `
  --output-dir "<stable-analysis-directory>" `
  --data-label "<dataset label>" `
  --json
```

The script produces:

- one horizontal trajectory colored by solution class;
- one E/N/U time-series figure colored by solution class;
- one position and velocity error figure, defined as INS minus RTK;
- one fixed/all error statistics table in CSV and Markdown;
- matched error samples and a JSON summary.

Every figure is written as SVG, PNG, and pickle-backed FIG. Keep the title
above the legend and put units in each y-axis label.

The current CTCLib `gnss_rtkplot.txt` ECEF format is parsed directly. Do not send
it to the separate 18-column relative-time RTKPlot workflow.

## Output naming

Use data time and meaningful parameter variants, never the current wall-clock
time of the run:

```text
<data-time>_<flavor>
<data-time>_<flavor>_<parameter-tags>
```

Examples:

```text
20261109T160537_navigation
20261109T160537_navigation_arw_x0p1
20261109T160537_navigation_arw_x0p1_vrw_x0p5
20261109T160537_calibration
20261109T160537_imu
20261109T160537_decode
```

Use `scripts/resolve_output_path.py`:

```powershell
python "<skill-root>\scripts\resolve_output_path.py" `
  --root "D:\Output\<project>\ctclib" `
  --data-time "2026-11-09T16:05:37" `
  --mode navigation `
  --variant "arw=0.1" `
  --json
```

Rules:

- Reuse the same path when data time, mode, and parameter variant are the same.
- Do not add a run timestamp to avoid a new directory for every execution.
- Create a different variant only when an important parameter differs from the
  standard template.
- Encode decimals as `p`, for example `0.1` becomes `0p1` in a path token.
- If an identical path already exists, overwrite only after an explicit user
  request to rerun that variant.

## Resume without repeating

Reuse earlier work only after validating its contents:

- decode step complete: decoded directory, nonzero post-process config, and
  IMU rows exist;
- IMU analysis complete: summary JSON has the expected segment count and both
  figure pairs exist;
- calibration complete: `dr_est.prodef` has usable rows and the application
  report identifies observable groups;
- final navigation complete: the primary output has valid navigation rows and
  status values.

Do not skip based only on file existence. If the user asks to rerun the same
data and parameter variant, reuse the same canonical directory after explicit
approval to overwrite. Create a different suffix only when an important
parameter changes.

## Output layout

Use the project paths required by the workspace:

```text
D:\Dataset\<project>\raw\
D:\DatasetParameters\<project>\<YYMMDDHH_data>_gnss-ins-calibration.ctccfg
D:\DatasetParameters\<project>\<YYMMDDHH_data>_gnss-ins-final.ctccfg
D:\Output\<project>\ctclib\<data-time>_<flavor>[_<parameter-tags>]\
D:\Output\<project>\analysis\<data-time>_decode[_<parameter-tags>]\
D:\Output\<project>\analysis\<data-time>_imu[_<parameter-tags>]\
D:\Output\<project>\analysis\<data-time>_calibration[_<parameter-tags>]\
D:\Output\<project>\analysis\<data-time>_navigation[_<parameter-tags>]\
D:\DOC\<project>\
```

Keep parameters only in `D:\DatasetParameters`, generated results only in
`D:\Output`, and the project summary in `D:\DOC`. Use normal text, CSV, SVG,
PNG, and visible `.fig` artifacts.

## Validation rules

- Confirm sample count, time range, median interval, duplicate timestamps, and
  gaps before interpreting IMU statistics.
- Do not treat CEP or standard deviation as a truth-referenced error.
- Do not call a calibration successful when the estimated state stayed at
  zero for the full run.
- Do not enable VIO estimation without actual `VIO,` records.
- A `run-solve.ps1` status of `failed` can be a file-name check failure; inspect
  the actual `#INSPVAXA` rows in `ins_novatel.ASC` or the build-equivalent
  `gnss_novatel.ASC` before concluding that the solver failed.
- Update the project Markdown report with decoded data, analysis outputs,
  calibration observability, final config, and navigation validation.
