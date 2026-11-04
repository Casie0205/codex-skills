from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


WGS84_A = 6378137.0
WGS84_F = 1.0 / 298.257223563
WGS84_E2 = WGS84_F * (2.0 - WGS84_F)
SECONDS_PER_WEEK = 604800.0


class ConversionError(RuntimeError):
    pass


@dataclass(frozen=True)
class NavRow:
    gps_week: int
    gps_seconds: float
    latitude_deg: float
    longitude_deg: float
    height_m: float
    position_status: str
    satellites: str
    source_line: int


@dataclass(frozen=True)
class Origin:
    latitude_deg: float
    longitude_deg: float
    height_m: float
    ecef_x_m: float
    ecef_y_m: float
    ecef_z_m: float
    mode: str


def geodetic_to_ecef(
    latitude_deg: float,
    longitude_deg: float,
    height_m: float,
) -> tuple[float, float, float]:
    latitude = math.radians(latitude_deg)
    longitude = math.radians(longitude_deg)
    sin_lat = math.sin(latitude)
    cos_lat = math.cos(latitude)
    sin_lon = math.sin(longitude)
    cos_lon = math.cos(longitude)

    prime_vertical_radius = WGS84_A / math.sqrt(
        1.0 - WGS84_E2 * sin_lat * sin_lat
    )
    x_m = (prime_vertical_radius + height_m) * cos_lat * cos_lon
    y_m = (prime_vertical_radius + height_m) * cos_lat * sin_lon
    z_m = (
        prime_vertical_radius * (1.0 - WGS84_E2) + height_m
    ) * sin_lat
    return x_m, y_m, z_m


def ecef_delta_to_enu(
    delta_x_m: float,
    delta_y_m: float,
    delta_z_m: float,
    origin_latitude_deg: float,
    origin_longitude_deg: float,
) -> tuple[float, float, float]:
    latitude = math.radians(origin_latitude_deg)
    longitude = math.radians(origin_longitude_deg)
    sin_lat = math.sin(latitude)
    cos_lat = math.cos(latitude)
    sin_lon = math.sin(longitude)
    cos_lon = math.cos(longitude)

    east_m = -sin_lon * delta_x_m + cos_lon * delta_y_m
    north_m = (
        -sin_lat * cos_lon * delta_x_m
        - sin_lat * sin_lon * delta_y_m
        + cos_lat * delta_z_m
    )
    up_m = (
        cos_lat * cos_lon * delta_x_m
        + cos_lat * sin_lon * delta_y_m
        + sin_lat * delta_z_m
    )
    return east_m, north_m, up_m


def make_origin(
    mode: str,
    rows: list[NavRow],
    fixed_latitude_deg: float | None,
    fixed_longitude_deg: float | None,
    fixed_height_m: float | None,
) -> Origin:
    if mode == "fixed":
        if (
            fixed_latitude_deg is None
            or fixed_longitude_deg is None
            or fixed_height_m is None
        ):
            raise ConversionError(
                "origin-mode fixed requires --origin-lat, --origin-lon and "
                "--origin-height"
            )
        latitude_deg = fixed_latitude_deg
        longitude_deg = fixed_longitude_deg
        height_m = fixed_height_m
    elif mode == "first":
        first = rows[0]
        latitude_deg = first.latitude_deg
        longitude_deg = first.longitude_deg
        height_m = first.height_m
    else:
        raise ConversionError(f"unsupported origin mode: {mode}")

    if not -90.0 <= latitude_deg <= 90.0:
        raise ConversionError(f"invalid origin latitude: {latitude_deg}")
    if not -180.0 <= longitude_deg <= 180.0:
        raise ConversionError(f"invalid origin longitude: {longitude_deg}")
    if not math.isfinite(height_m):
        raise ConversionError(f"invalid origin height: {height_m}")

    ecef_x_m, ecef_y_m, ecef_z_m = geodetic_to_ecef(
        latitude_deg,
        longitude_deg,
        height_m,
    )
    return Origin(
        latitude_deg=latitude_deg,
        longitude_deg=longitude_deg,
        height_m=height_m,
        ecef_x_m=ecef_x_m,
        ecef_y_m=ecef_y_m,
        ecef_z_m=ecef_z_m,
        mode=mode,
    )


def parse_float(value: str, field_name: str, line_no: int) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"line {line_no}: invalid {field_name}: {value!r}") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"line {line_no}: non-finite {field_name}: {value!r}")
    return parsed


def read_navplot(path: Path) -> tuple[list[NavRow], dict[str, int]]:
    if not path.is_file():
        raise ConversionError(f"input file not found: {path}")

    rows: list[NavRow] = []
    nonempty_lines = 0
    invalid_rows = 0
    header_lines = 0

    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            nonempty_lines += 1
            fields = line.split()

            if len(fields) < 7:
                invalid_rows += 1
                continue

            try:
                gps_week = int(round(parse_float(fields[0], "GPS week", line_no)))
                gps_seconds = parse_float(fields[1], "GPS seconds", line_no)
                latitude_deg = parse_float(fields[2], "latitude", line_no)
                longitude_deg = parse_float(fields[3], "longitude", line_no)
                height_m = parse_float(fields[4], "height", line_no)
            except ValueError:
                if not rows:
                    header_lines += 1
                else:
                    invalid_rows += 1
                continue

            if not -90.0 <= latitude_deg <= 90.0:
                invalid_rows += 1
                continue
            if not -180.0 <= longitude_deg <= 180.0:
                invalid_rows += 1
                continue

            rows.append(
                NavRow(
                    gps_week=gps_week,
                    gps_seconds=gps_seconds,
                    latitude_deg=latitude_deg,
                    longitude_deg=longitude_deg,
                    height_m=height_m,
                    position_status=fields[5],
                    satellites=fields[6],
                    source_line=line_no,
                )
            )

    stats = {
        "nonempty_lines": nonempty_lines,
        "header_lines_skipped": header_lines,
        "invalid_rows_skipped": invalid_rows,
    }
    if not rows:
        raise ConversionError(f"no usable NavPlot rows found in: {path}")
    return rows, stats


def sort_and_deduplicate(
    rows: Iterable[NavRow],
) -> tuple[list[NavRow], int]:
    ordered = sorted(
        rows,
        key=lambda row: (row.gps_week, row.gps_seconds, row.source_line),
    )
    retained: list[NavRow] = []
    duplicate_count = 0

    for row in ordered:
        if (
            retained
            and retained[-1].gps_week == row.gps_week
            and retained[-1].gps_seconds == row.gps_seconds
        ):
            retained[-1] = row
            duplicate_count += 1
        else:
            retained.append(row)
    return retained, duplicate_count


def elapsed_seconds(start: NavRow, current: NavRow) -> float:
    return (
        (current.gps_week - start.gps_week) * SECONDS_PER_WEEK
        + current.gps_seconds
        - start.gps_seconds
    )


def convert_rows(
    rows: list[NavRow],
    origin: Origin,
) -> tuple[list[dict[str, float | int | str]], dict[str, float]]:
    output_rows: list[dict[str, float | int | str]] = []
    first = rows[0]
    previous: NavRow | None = None
    previous_east_m = 0.0
    previous_north_m = 0.0
    previous_up_m = 0.0
    cumulative_2d_m = 0.0
    cumulative_3d_m = 0.0
    vertical_path_m = 0.0
    max_step_2d_m = 0.0
    max_step_3d_m = 0.0
    max_dt_s = 0.0
    last_east_m = 0.0
    last_north_m = 0.0
    last_up_m = 0.0

    for index, row in enumerate(rows):
        ecef_x_m, ecef_y_m, ecef_z_m = geodetic_to_ecef(
            row.latitude_deg,
            row.longitude_deg,
            row.height_m,
        )
        east_m, north_m, up_m = ecef_delta_to_enu(
            ecef_x_m - origin.ecef_x_m,
            ecef_y_m - origin.ecef_y_m,
            ecef_z_m - origin.ecef_z_m,
            origin.latitude_deg,
            origin.longitude_deg,
        )

        if previous is None:
            dt_s = 0.0
            step_2d_m = 0.0
            step_3d_m = 0.0
        else:
            dt_s = elapsed_seconds(previous, row)
            if dt_s < -1.0e-6:
                raise ConversionError(
                    f"time decreased at source line {row.source_line}"
                )
            delta_east_m = east_m - previous_east_m
            delta_north_m = north_m - previous_north_m
            delta_up_m = up_m - previous_up_m
            step_2d_m = math.hypot(delta_east_m, delta_north_m)
            step_3d_m = math.sqrt(
                delta_east_m * delta_east_m
                + delta_north_m * delta_north_m
                + delta_up_m * delta_up_m
            )
            cumulative_2d_m += step_2d_m
            cumulative_3d_m += step_3d_m
            vertical_path_m += abs(delta_up_m)
            max_step_2d_m = max(max_step_2d_m, step_2d_m)
            max_step_3d_m = max(max_step_3d_m, step_3d_m)
            max_dt_s = max(max_dt_s, dt_s)

        elapsed_s = elapsed_seconds(first, row)
        output_rows.append(
            {
                "gps_week": row.gps_week,
                "gps_seconds": row.gps_seconds,
                "elapsed_s": elapsed_s,
                "latitude_deg": row.latitude_deg,
                "longitude_deg": row.longitude_deg,
                "height_m": row.height_m,
                "position_status": row.position_status,
                "satellites": row.satellites,
                "east_m": east_m,
                "north_m": north_m,
                "up_m": up_m,
                "dt_s": dt_s,
                "step_2d_m": step_2d_m,
                "step_3d_m": step_3d_m,
                "cumulative_2d_m": cumulative_2d_m,
                "cumulative_3d_m": cumulative_3d_m,
            }
        )

        previous = row
        previous_east_m = east_m
        previous_north_m = north_m
        previous_up_m = up_m
        last_east_m = east_m
        last_north_m = north_m
        last_up_m = up_m

    metrics = {
        "total_horizontal_distance_m": cumulative_2d_m,
        "total_3d_path_length_m": cumulative_3d_m,
        "vertical_path_length_m": vertical_path_m,
        "net_displacement_horizontal_m": math.hypot(last_east_m, last_north_m),
        "net_displacement_3d_m": math.sqrt(
            last_east_m * last_east_m
            + last_north_m * last_north_m
            + last_up_m * last_up_m
        ),
        "net_vertical_change_m": last_up_m,
        "max_step_2d_m": max_step_2d_m,
        "max_step_3d_m": max_step_3d_m,
        "max_dt_s": max_dt_s,
    }
    return output_rows, metrics


def format_value(value: float | int | str) -> str | int:
    if isinstance(value, float):
        return f"{value:.10f}"
    return value


def write_csv(path: Path, rows: list[dict[str, float | int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(path.name + ".tmp")
    fieldnames = list(rows[0].keys())
    with temporary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: format_value(value) for key, value in row.items()})
    temporary_path.replace(path)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(path.name + ".tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert NavPlot latitude/longitude/height to local ENU metres."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-csv", required=True, type=Path)
    parser.add_argument("--summary-json", type=Path)
    parser.add_argument(
        "--origin-mode",
        choices=("first", "fixed"),
        default="first",
        help="Use the first retained epoch or an explicit fixed origin.",
    )
    parser.add_argument("--origin-lat", type=float)
    parser.add_argument("--origin-lon", type=float)
    parser.add_argument("--origin-height", type=float)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacement of existing output files.",
    )
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> Path:
    summary_path = args.summary_json
    if summary_path is None:
        summary_path = args.output_csv.with_name(
            args.output_csv.stem + "_summary.json"
        )

    input_resolved = args.input.resolve()
    csv_resolved = args.output_csv.resolve()
    summary_resolved = summary_path.resolve()
    if csv_resolved == input_resolved or summary_resolved == input_resolved:
        raise ConversionError("output paths must not overwrite the input file")
    if csv_resolved == summary_resolved:
        raise ConversionError("output CSV and summary JSON must be different paths")

    if not args.overwrite:
        existing = [
            str(path)
            for path in (args.output_csv, summary_path)
            if path.exists()
        ]
        if existing:
            raise ConversionError(
                "output already exists; use --overwrite to replace: "
                + ", ".join(existing)
            )

    rows, read_stats = read_navplot(args.input)
    rows, duplicate_count = sort_and_deduplicate(rows)
    origin = make_origin(
        args.origin_mode,
        rows,
        args.origin_lat,
        args.origin_lon,
        args.origin_height,
    )
    converted_rows, metrics = convert_rows(rows, origin)
    write_csv(args.output_csv, converted_rows)

    first = rows[0]
    last = rows[-1]
    summary: dict[str, object] = {
        "input": str(args.input.resolve()),
        "output_csv": str(args.output_csv.resolve()),
        "rows_usable_before_deduplication": len(rows) + duplicate_count,
        "rows_retained": len(rows),
        "duplicate_epochs_removed": duplicate_count,
        **read_stats,
        "origin": {
            "mode": origin.mode,
            "latitude_deg": origin.latitude_deg,
            "longitude_deg": origin.longitude_deg,
            "height_m": origin.height_m,
            "ecef_x_m": origin.ecef_x_m,
            "ecef_y_m": origin.ecef_y_m,
            "ecef_z_m": origin.ecef_z_m,
        },
        "time_range": {
            "start_gps_week": first.gps_week,
            "start_gps_seconds": first.gps_seconds,
            "end_gps_week": last.gps_week,
            "end_gps_seconds": last.gps_seconds,
            "duration_s": elapsed_seconds(first, last),
        },
        **metrics,
        "coordinate_assumption": (
            "NavPlot latitude/longitude use WGS84 degrees; height is used "
            "directly as WGS84 ellipsoidal height."
        ),
    }
    write_json(summary_path, summary)
    return summary_path


def main(argv: list[str] | None = None) -> int:
    try:
        summary_path = run(parse_args(argv))
    except (ConversionError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"SUMMARY_JSON={summary_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
