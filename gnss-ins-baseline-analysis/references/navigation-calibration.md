# CTCLib Navigation Calibration

## Contents

- [Calibration inputs](#calibration-inputs)
- [ARW and VRW confirmation](#arw-and-vrw-confirmation)
- [Sensor relationships](#sensor-relationships)
- [CALIB run](#calib-run)
- [Observability](#observability)
- [Writeback](#writeback)
- [Final navigation](#final-navigation)
- [Resume rules](#resume-rules)

## Calibration inputs

Use the decode-generated config to obtain:

- input file path;
- device name;
- IMU frequency;
- GNSS navigation frequency;
- dual-antenna availability;
- receiver-side calibration settings.

Create a normalized calibration config from
`assets/navigation-calibration.ctccfg`. Store it under
`D:\DatasetParameters\<project>` and do not modify the decode-generated source
config.

## ARW and VRW confirmation

Before every new calibration run, ask the user to confirm:

- `gyo_arw`, unit `deg/sqrt(h)`;
- `acc_vrw`, unit `ug/sqrt(Hz)`.

You may propose existing device or project values, but do not silently copy
values from a different receiver or IMU. Record the confirmed values in the
project parameter file.

## Sensor relationships

Enable calibration only for relationships supported by data and installation:

| Relationship | Value keys | Estimate keys |
| --- | --- | --- |
| IMU to GNSS | `lever_imu2gnss` | `est_lever_imu2gnss` |
| IMU to vehicle | `lever_imu2car`, `install_imu2car` | `est_lever_imu2car`, `est_install_imu2car` |
| GNSS to vehicle | `install_gnss2car` | `est_install_gnss2car` |
| IMU to VIO | `lever_imu2vio` | `est_lever_imu2vio` |
| Vehicle to VIO | `install_car2vio` | `est_install_car2vio` |

If `ctclibdec_vio.prodef` has no `VIO,` data rows, set VIO estimate switches to
`0,0,0` and set `method_vio_yaw=0`. Do not report a VIO angle from an
unobservable run.

## CALIB run

Use the `ctclib` solve workflow with `ins_mode=1`. The expected calibration
stream is:

```text
<output-dir>\dr_est.prodef
```

`ins_adaptive_calib_ready.prodef` may contain only a header. Do not treat that
header alone as proof that calibration is complete. Inspect the actual
`INS_EST_STATE` trajectory.

## Observability

Read the fixed header of `dr_est.prodef`; column positions must be resolved by
name, not guessed by value range.

Classify a three-axis group as observable when its values:

- changed from the configured initial value; or
- vary across the run by more than the configured tolerance.

Classify it as unobservable when it stays exactly at its initial value for the
entire run. A value that remains zero is not a calibrated zero.

## Writeback

Use `scripts/apply_calibration.py`.

- the source config must contain `ins_mode=1`;
- each relationship must have its corresponding `est_*` switch enabled;
- VIO relationships require `VIO,` rows in the supplied VIO file;
- default window is the last 30 seconds;
- final value is the median of the window;
- final STD is the median of the per-sample STD columns in the same window;
- angle groups use a wrapped circular median;
- only observable groups are written back;
- unobservable values remain unchanged;
- all corresponding `est_*` switches are disabled;
- the output config uses `ins_mode=0`.

Review the generated application CSV and JSON before running navigation.
If no group is observable, the report status is `no_observable_states`, the
script exits non-zero, and no final config is written.

Some CTCLib builds rewrite `method_adaptive_calib=0` back to `1` in their
generated output config. Verify that all `est_*` switches remain zero and that
the selected values are constant in `dr_est.prodef`; otherwise do not treat the
navigation config as fixed-parameter.

## Final navigation

Run the output config through the `ctclib` solve workflow. Validate:

- exit code;
- structured errors;
- primary result rows;
- first and last SOW;
- status distribution;
- valid latitude/longitude/height;
- actual config values and disabled estimate flags.

Some CTCLib builds leave `ins_novatel.ASC` empty and write valid
`#INSPVAXA` navigation rows to `gnss_novatel.ASC`. Inspect the data rather than
accepting the wrapper filename check as the sole result.

## Resume rules

If a previous run already contains validated outputs:

- skip decode when the decoded directory and IMU rows are valid;
- skip IMU analysis when the summary and all figure/table outputs exist;
- skip calibration when `dr_est.prodef` and its application report are valid;
- skip final navigation when a valid primary result exists.

Do not skip because a file merely exists. If any content check fails, rerun
that step in a new timestamped directory.
