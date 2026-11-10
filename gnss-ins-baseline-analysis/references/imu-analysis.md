# CTCLib Split IMU Analysis

## Contents

- [Column contract](#column-contract)
- [Statistics table](#statistics-table)
- [Figures](#figures)
- [Quality checks](#quality-checks)
- [Known interpretation boundary](#known-interpretation-boundary)

## Column contract

CTCLib writes the split IMU files as NavPlot-shaped text, but the payload is
raw IMU data:

| Zero-based column | Meaning | Unit |
| ---: | --- | --- |
| 0 | GPS week | week |
| 1 | seconds of week | s |
| 2-13 | NavPlot packaging fields | not used here |
| 14 | temperature | deg C |
| 15-17 | accelerometer X/Y/Z | g |
| 18-20 | gyroscope X/Y/Z | deg/s |

All files matching `imu_*.navplot` belong to one IMU stream and must be sorted
by `week * 604800 + SOW` before combining.

## Statistics table

Produce one table with six data columns:

- `Acc X/Y/Z (g)`;
- `Gyro X/Y/Z (deg/s)`.

Rows must follow the reference format:

| Row | Definition |
| --- | --- |
| Mean | arithmetic mean |
| Standard deviation | sample standard deviation |
| RMS | `sqrt(mean(x^2))` |
| Maximum | signed maximum |
| Minimum | signed minimum |
| Range | maximum minus minimum |
| CEP68 | 68th percentile of `abs(x)` |
| CEP95 | 95th percentile of `abs(x)` |
| CEP99 | 99th percentile of `abs(x)` |

The reference screenshots show a separate velocity table and attitude table.
For raw IMU analysis, combine both sensor groups into one table with six
columns and keep the units in the headers.

## Figures

Create two independent figures:

1. gyroscope X/Y/Z over elapsed time;
2. accelerometer X/Y/Z over elapsed time.

Every input segment must be present in each figure. The plotted values and axis
semantics are defined above; layout and export are delegated to
`python-publication-figures`.

## Quality checks

Report:

- number of input files;
- total rows;
- first and last SOW;
- duration;
- median sampling interval;
- estimated sampling rate;
- duplicate timestamps;
- gaps greater than 20 ms and 100 ms;
- temperature minimum, mean, and maximum.

Do not silently discard duplicate time stamps. Keep them in the raw statistics
and report their count.

## Known interpretation boundary

The file extension is `.navplot`, but columns 15-20 are not navigation velocity
and attitude. Do not apply NavPlot navigation column semantics to these files.
Do not use NavPlotStudio position or attitude interpretations for this payload.
