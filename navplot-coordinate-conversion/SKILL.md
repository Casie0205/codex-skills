---
name: navplot-coordinate-conversion
description: Convert NavPlot latitude, longitude, and height into local ENU metre displacements, cumulative travel distances, and a summary JSON for navigation analysis and plotting.
---

# Navplot Coordinate Conversion

Use this skill when NavPlot position fields must be converted from geodetic coordinates
to metric local movement before analysis or plotting.

## Input Contract

The first seven whitespace-separated NavPlot columns are:

```text
1 GPS week
2 GPS seconds-of-week
3 latitude (deg)
4 longitude (deg)
5 height (m)
6 position status
7 satellite count
```

Treat the latitude and longitude as WGS84 degrees. Treat height as WGS84 ellipsoidal
height unless the user explicitly states another vertical datum.

## Workflow

1. Locate `ins_insplot.txt` or use the file path provided by the user.
2. Check that the file exists, is non-empty, and has at least seven usable columns.
3. Run:

   ```powershell
   python scripts/convert_navplot_enu.py `
     --input "<ins_insplot.txt>" `
     --output-csv "<ins_insplot_enu.csv>" `
     --summary-json "<ins_insplot_enu_summary.json>"
   ```

4. Use `--origin-mode fixed --origin-lat ... --origin-lon ... --origin-height ...`
   when several runs must share one reference origin. Otherwise use the default
   `first` origin.
5. Read the summary JSON and verify retained rows, removed duplicates, maximum time
   gap, horizontal path length, 3D path length, and net displacement.
6. Use the output CSV columns `elapsed_s`, `east_m`, `north_m`, and `up_m` for
   subsequent metric plots.

## Rules

- Do not treat latitude/longitude columns as metres.
- Do not overwrite the input file.
- Do not overwrite existing outputs without explicit approval and `--overwrite`.
- Sort by GPS week and seconds. For duplicate epochs, keep the last record.
- Check `max_dt_s`; do not describe a path across a long outage as continuous motion.
- The local ENU tangent plane is intended for local and regional trajectories.
- Preserve the original NavPlot file.

## Script Output

The CSV contains elapsed time, original coordinates and status, ENU displacement,
per-step 2D/3D distance, and cumulative 2D/3D distance.

The JSON summary contains input/output paths, row counts, duplicate and invalid-row
counts, origin coordinates, time range, maximum time gap, path lengths, and net
displacement.
