# RTKPlot Text Format

## Scope

This skill handles the 18-column whitespace-separated RTKPlot solution text
produced by the GNSS/INS post-processing flow, commonly named
`gnss_rtkplot.txt`. It does not handle RTKLIB `.pos`, `.obs`, or `.nav` files.
Use RTKLIB's RTKPLOT application for those formats.

## Columns

Each usable data row contains at least 18 numeric tokens:

| Column | Field | Unit or meaning |
| ---: | --- | --- |
| 1 | `time_s` | relative time |
| 2 | `lat_rad` | latitude, radians |
| 3 | `lon_rad` | longitude, radians |
| 4 | `h_m` | ellipsoidal height, metres |
| 5 | `sigma_lat_m` | latitude standard deviation, metres |
| 6 | `sigma_lon_m` | longitude standard deviation, metres |
| 7 | `sigma_h_m` | height standard deviation, metres |
| 8 | `diff_age_s` | differential age, seconds |
| 9 | `sol_age_s` | solution age, seconds |
| 10 | `num_svs` | satellite count |
| 11 | `best_sol_status_code` | numeric solution status |
| 12 | `best_pos_type_code` | numeric best-position type |
| 13 | `gnssfgo_type_code` | 1 RTKFIX, 2 RTKFLOAT, 3 SINGLE, 4 NO_SOLUTION |
| 14 | `dop_pdop` | PDOP |
| 15 | `dop_hdop` | HDOP |
| 16 | `dop_vdop` | VDOP |
| 17 | `pos_source_code` | numeric position source |
| 18 | `hpd_status_code` | numeric HPD status |

Extra columns are ignored. Blank lines and lines beginning with `#` are skipped.
Rows with fewer than 18 tokens or nonnumeric required fields are reported as
malformed.

## Sampling Rules

- Latitude and longitude are radians. Do not reinterpret them as degrees.
- `NaN` is accepted for scalar quality fields.
- `trajectory`, `position`, and `sigma` use finite positions with fix codes
  1, 2, or 3. NO_SOLUTION rows are excluded from those figures.
- `quality` reads every parsed row and plots satellite count, differential age,
  and PDOP.
- Multiple inputs share the ENU origin of the first input, preserving relative
  offsets between sources.

## Sample

```text
# time_s lat_rad lon_rad h_m sigma_lat sigma_lon sigma_h diff_age sol_age svs status pos_type fix_type pdop hdop vdop pos_source hpd_status
0.0 0.548123 2.114832 12.34 0.012 0.010 0.025 1.0 2.0 24 1 1 1 1.2 0.8 0.9 1 1
0.2 0.548124 2.114833 12.36 0.013 0.011 0.026 1.1 2.1 23 1 1 1 1.3 0.9 1.0 1 1
```
