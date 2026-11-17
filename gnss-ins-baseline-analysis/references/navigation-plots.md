# Navigation Result Analysis

## Contents

- [Source contracts](#source-contracts)
- [Solution classes](#solution-classes)
- [Plot handoff](#plot-handoff)
- [Error comparison](#error-comparison)
- [Statistics table](#statistics-table)
- [Validation](#validation)

## Source contracts

Use the current CTCLib outputs:

- `ins_insplot.txt`: NavPlot, GPS week/SOW, geodetic latitude/longitude/height,
  solution status, satellite count, velocity, and attitude.
- `gnss_rtkplot.txt`: header-commented ECEF RTKPlot text with GPST, ECEF X/Y/Z,
  Q, satellite count, and covariance/quality fields.

The current CTCLib `gnss_rtkplot.txt` is an ECEF variant with extra columns. It
is not the 18-column relative-time/radian format used by the separate
RTKPlotStudio skill. Parse the fields defined in these Wiki pages:

| Page ID | URL |
| --- | --- |
| `dev_cc:devresource:rtkplot_format` | `http://192.168.0.112:8800/doku.php?id=dev_cc%3Adevresource%3Artkplot_format` |
| `personal:yinfei:navplot` | `http://192.168.0.112:8800/doku.php?id=personal%3Ayinfei%3Anavplot` |
| `dev_cc:test:testtools:posvant_postype_mapping` | `http://192.168.0.112:8800/doku.php?id=dev_cc%3Atest%3Atesttools%3Aposvant_postype_mapping` |

## Solution classes

Use six stable solution classes:

| Internal class | Display label | NavPlot status |
| --- | --- | --- |
| Fix | 固定解 | 1 |
| Float | 浮点解 | 2 |
| Diff | 差分 | 3, 4 |
| Single | 单点 | 5 |
| INS | INS | 6 |
| Other | 其他 | other |

RTK Q mapping is:

- Q1: Fix
- Q2: Float
- Q3/Q4: Diff
- Q5: Single
- Q6: PPP in the current RTKPlot header/Wiki, but POSVANT mode mapping uses
  `6` for INS; do not use Q6 for class colors until the build-specific meaning
  is confirmed
- other: Other

For `ins_insplot.txt`, use the NavPlot status column for solution-class
classification. For the fixed comparison set, require both INS status `1` and
RTK Q `1`.

## Plot handoff

This reference defines data semantics, error signs, and required analysis
outputs only. Figure layout, styling, legends, panel labels, and export belong
to `standard-plotting`; do not maintain a second plotting specification here.

## Error comparison

Use a local ENU origin from the first finite INS position.

Position:

- convert INS geodetic coordinates to ECEF and ENU;
- convert RTK ECEF positions to the same ENU frame;
- interpolate RTK positions at INS epochs;
- reject matches farther than `--max-match-gap` from an RTK epoch.

Velocity:

- use INS velocity columns 16-18;
- derive RTK ECEF velocity only inside continuous same-Q segments;
- split segments when RTK Q changes or the sample gap exceeds
  `--max-rtk-gap` default `0.5 s`;
- reject derived samples above `--max-rtk-speed` default `50 m/s`;
- rotate RTK ECEF velocity into the same ENU frame;
- interpolate RTK velocity at INS epochs.

The Wiki-defined RTKPlot columns do not include a velocity field, so the RTK
velocity reference is a derived quantity and must be reported as such. Velocity
errors are excluded when either interpolation endpoint lacks a valid derived
velocity.

Error sign is always:

```text
INS - RTK
```

Report East, North, Up, horizontal 2D, and 3D errors.

## Statistics table

Create one long-form table with these dimensions:

- quantity: `position_m` or `velocity_mps`;
- solution set: `fixed` or `all`;
- metric: Mean, Standard deviation, RMS, Maximum, Minimum, Range,
  CEP68, CEP95, CEP99;
- components: E, N, U, 2D, 3D.

Definitions:

- axis CEP is the percentile of absolute axis error;
- 2D and 3D CEP are percentiles of the radial magnitude;
- fixed requires INS status 1 and both RTK interpolation endpoints Q1;
- all includes every finite matched epoch.

Also write matched samples with errors, statuses, RTK Q, and time-match gaps.

## Validation

Confirm:

- both source files are non-empty;
- malformed row counts;
- common time overlap;
- matched and fixed-matched row counts;
- statistics and sample CSVs are non-empty;
- solution-class assignments in the analysis outputs.

Do not claim a truth-referenced absolute accuracy from this comparison. It is an
internal INS-versus-RTK consistency check unless RTK is independently validated
as truth.
