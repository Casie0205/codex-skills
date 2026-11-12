#!/usr/bin/env python3
"""Apply observable DR calibration states as priors and preserve estimation."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class ParameterGroup:
    config_key: str
    columns: tuple[str, ...]
    circular_degrees: bool = False
    state_to_config_axes: tuple[int, ...] | None = None
    state_to_config_signs: tuple[float, ...] | None = None


GROUPS = (
    ParameterGroup(
        "lever_imu2gnss",
        (
            "LeverImu2Gnss X(m)",
            "LeverImu2Gnss Y(m)",
            "LeverImu2Gnss Z(m)",
        ),
    ),
    ParameterGroup(
        "lever_imu2car",
        (
            "leverImu2Car X(m)",
            "LeverImu2Car Y(m)",
            "LeverImu2Car Z(m)",
        ),
    ),
    ParameterGroup(
        "install_imu2car",
        (
            "AngleImu2Car X(deg)",
            "AngleImu2Car Y(deg)",
            "AngleImu2Car Z(deg)",
        ),
        circular_degrees=True,
    ),
    ParameterGroup(
        "install_gnss2car",
        (
            "AngleGnss2Car X(deg)",
            "AngleGnss2Car Y(deg)",
            "AngleGnss2Car Z(deg)",
        ),
        circular_degrees=True,
    ),
    ParameterGroup(
        "lever_imu2vio",
        (
            "LeverImu2Vio X(m)",
            "LeverImu2Vio Y(m)",
            "LeverImu2Vio Z(m)",
        ),
        state_to_config_axes=(1, 0, 2),
        state_to_config_signs=(1.0, 1.0, -1.0),
    ),
    ParameterGroup(
        "install_car2vio",
        (
            "AngleCar2Vio X(deg)",
            "AngleCar2Vio Y(deg)",
            "AngleCar2Vio Z(deg)",
        ),
        circular_degrees=True,
        state_to_config_signs=(1.0, 1.0, -1.0),
    ),
    ParameterGroup(
        "gyo_sf",
        (
            "GyoSf X(persent)",
            "GyoSf Y(persent)",
            "GyoSf Z(persent)",
        ),
    ),
    ParameterGroup(
        "acc_sf",
        (
            "AccSf X(persent)",
            "AccSf Y(persent)",
            "AccSf Z(persent)",
        ),
    ),
    ParameterGroup(
        "gyo_cross",
        (
            "GyoCross XY(deg)",
            "GyoCross XZ(deg)",
            "GyoCross YZ(deg)",
            "GyoCross YX(deg)",
            "GyoCross ZX(deg)",
            "GyoCross ZY(deg)",
        ),
    ),
    ParameterGroup(
        "acc_cross",
        (
            "AccCross XY(deg)",
            "AccCross XZ(deg)",
            "AccCross YZ(deg)",
            "AccCross YX(deg)",
            "AccCross ZX(deg)",
            "AccCross ZY(deg)",
        ),
    ),
)

COMMENTS = {
    "ins_mode": "# [enum] 0:NAV, 1:CALIB, 2:NAVLC, 3:STATICCALIB",
    "method_adaptive_calib": "# [bool] enable adaptive calibration",
    "method_vio_yaw": "# [bool] use VIO yaw update only with VIO rows",
    "lever_imu2gnss": "# [m] IMU-to-GNSS lever arm X,Y,Z",
    "lever_imu2gnss_std": "# [m] IMU-to-GNSS lever-arm prior std X,Y,Z",
    "lever_imu2car": "# [m] IMU-to-vehicle lever arm X,Y,Z",
    "lever_imu2car_std": "# [m] IMU-to-vehicle lever-arm prior std X,Y,Z",
    "install_imu2car": "# [deg] IMU-to-vehicle installation angle X,Y,Z",
    "install_imu2car_std": "# [deg] IMU-to-vehicle angle prior std X,Y,Z",
    "install_gnss2car": "# [deg] GNSS-to-vehicle installation angle X,Y,Z",
    "install_gnss2car_std": "# [deg] GNSS-to-vehicle angle prior std X,Y,Z",
    "lever_imu2vio": "# [m] IMU-to-VIO lever arm X,Y,Z",
    "lever_imu2vio_std": "# [m] IMU-to-VIO lever-arm prior std X,Y,Z",
    "install_car2vio": "# [deg] vehicle-to-VIO installation angle X,Y,Z",
    "install_car2vio_std": "# [deg] vehicle-to-VIO angle prior std X,Y,Z",
    "gyo_sf": "# [percent] gyro scale factor X,Y,Z",
    "gyo_sf_std": "# [percent] gyro scale-factor prior std X,Y,Z",
    "acc_sf": "# [percent] accelerometer scale factor X,Y,Z",
    "acc_sf_std": "# [percent] accelerometer scale-factor prior std X,Y,Z",
    "gyo_cross": "# [deg] gyro cross coupling XY,XZ,YZ,YX,ZX,ZY",
    "gyo_cross_std": "# [deg] gyro cross-coupling prior std XY,XZ,YZ,YX,ZX,ZY",
    "acc_cross": "# [deg] accelerometer cross coupling XY,XZ,YZ,YX,ZX,ZY",
    "acc_cross_std": (
        "# [deg] accelerometer cross-coupling prior std XY,XZ,YZ,YX,ZX,ZY"
    ),
    "est_lever_imu2gnss": "# [bool] estimate IMU-to-GNSS lever arm",
    "est_lever_imu2car": "# [bool] estimate IMU-to-vehicle lever arm",
    "est_install_imu2car": "# [bool] estimate IMU-to-vehicle installation angle",
    "est_install_gnss2car": "# [bool] estimate GNSS-to-vehicle installation angle",
    "est_lever_imu2vio": "# [bool] estimate IMU-to-VIO lever arm",
    "est_install_car2vio": "# [bool] estimate vehicle-to-VIO installation angle",
    "est_gyo_sf": "# [bool] estimate gyro scale factors X,Y,Z",
    "est_acc_sf": "# [bool] estimate accelerometer scale factors X,Y,Z",
    "est_gyo_cross": "# [bool] estimate gyro cross coupling XY,XZ,YZ,YX,ZX,ZY",
    "est_acc_cross": (
        "# [bool] estimate accelerometer cross coupling XY,XZ,YZ,YX,ZX,ZY"
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Identify observable calibration states, write their last-window "
            "value/std as priors, and preserve estimation switches."
        )
    )
    parser.add_argument("--dr-est", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-config", type=Path, required=True)
    parser.add_argument("--vio-prodef", type=Path)
    parser.add_argument("--window-seconds", type=float, default=30.0)
    parser.add_argument("--min-window-samples", type=int, default=10)
    parser.add_argument("--tolerance", type=float, default=1e-6)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def parse_vector(value: str, expected_count: int) -> np.ndarray:
    clean = value.split("#", 1)[0].strip()
    parts = [part.strip() for part in clean.split(",")]
    if len(parts) != expected_count:
        raise ValueError(
            f"Expected {expected_count} values, got {len(parts)}: {value}"
        )
    return np.array([float(part) for part in parts], dtype=float)


def format_vector(values: np.ndarray) -> str:
    return ",".join(f"{float(value):.8g}" for value in values)


def transform_definition(
    group: ParameterGroup,
) -> tuple[tuple[int, ...], tuple[float, ...]]:
    count = len(group.columns)
    axes = group.state_to_config_axes or tuple(range(count))
    signs = group.state_to_config_signs or tuple(1.0 for _ in range(count))
    if len(axes) != count or len(signs) != count:
        raise ValueError(f"Invalid axis transform for {group.config_key}")
    if sorted(axes) != list(range(count)):
        raise ValueError(f"Incomplete axis transform for {group.config_key}")
    return axes, signs


def state_to_config(values: np.ndarray, group: ParameterGroup) -> np.ndarray:
    axes, signs = transform_definition(group)
    return np.array(
        [signs[axis] * values[axes[axis]] for axis in range(len(axes))],
        dtype=float,
    )


def config_to_state(values: np.ndarray, group: ParameterGroup) -> np.ndarray:
    axes, signs = transform_definition(group)
    result = np.zeros(len(axes), dtype=float)
    for config_axis, state_axis in enumerate(axes):
        result[state_axis] = signs[config_axis] * values[config_axis]
    return result


def std_to_config(values: np.ndarray, group: ParameterGroup) -> np.ndarray:
    axes, _ = transform_definition(group)
    return np.array([values[axis] for axis in axes], dtype=float)


def section_bounds(lines: list[str], section: str) -> tuple[int, int]:
    matches = [
        index
        for index, line in enumerate(lines)
        if re.match(rf"^\s*\[{re.escape(section)}\]\s*$", line)
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Config must contain exactly one [{section}] section, found {len(matches)}"
        )
    start = matches[0]
    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].strip()
        if re.match(r"^\[.+\]$", stripped) or stripped.startswith(">"):
            end = index
            break
    return start, end


def active_entries(lines: list[str], start: int, end: int) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {}
    for index in range(start + 1, end):
        match = re.match(r"^\s*([A-Za-z0-9_\[\]]+)\s*=\s*(.*)$", lines[index])
        if not match:
            continue
        key = match.group(1)
        result.setdefault(key, []).append(index)
    return result


def read_config_value(lines: list[str], entries: dict[str, list[int]], key: str) -> str | None:
    indexes = entries.get(key, [])
    if not indexes:
        return None
    if len(indexes) > 1:
        raise ValueError(f"Config contains duplicate active key in [ctclib_ins]: {key}")
    value = lines[indexes[0]].split("=", 1)[1]
    return value.split("#", 1)[0].strip()


def set_config_value(
    lines: list[str],
    entries: dict[str, list[int]],
    section_end: int,
    key: str,
    value: str,
) -> None:
    indexes = entries.get(key, [])
    if len(indexes) > 1:
        raise ValueError(f"Config contains duplicate active key in [ctclib_ins]: {key}")
    if indexes:
        index = indexes[0]
        original = lines[index]
        comment_match = re.search(r"\s+#.*$", original)
        comment = comment_match.group(0) if comment_match else ""
        lines[index] = f"{key} = {value}{comment}"
        return
    comment = COMMENTS.get(key, "")
    insertion = f"{key} = {value}"
    if comment:
        insertion = f"{insertion} {comment}"
    lines.insert(section_end, insertion)
    for indexes_for_key in entries.values():
        for index_position, line_index in enumerate(indexes_for_key):
            if line_index >= section_end:
                indexes_for_key[index_position] = line_index + 1
    entries[key] = [section_end]


def load_dr_est(path: Path) -> tuple[dict[str, int], np.ndarray, np.ndarray]:
    with path.open("r", encoding="utf-8-sig") as handle:
        header = handle.readline().strip()
        rows = []
        for line in handle:
            line = line.strip()
            if line.startswith("INS_EST_STATE,"):
                rows.append([float(value) for value in line.split(",")[1:]])
    if not rows:
        raise ValueError(f"No INS_EST_STATE rows found in {path}")
    prefix = "#PROTOCOL_DEFINE0,V1,{INS_EST_STATE},"
    if not header.startswith(prefix):
        raise ValueError(f"Unexpected dr_est header: {header[:80]}")
    names = header[len(prefix) :].removesuffix("*ff").split(",")
    normalized_names = []
    for name in names:
        clean = name.strip().replace("{", "").replace("}", "")
        if clean.startswith("[") and clean.endswith("]"):
            clean = clean[1:-1]
        normalized_names.append(clean)
    names = normalized_names
    column_index = {name.casefold(): index for index, name in enumerate(names)}
    data = np.asarray(rows, dtype=float)
    if data.shape[1] != len(names):
        raise ValueError(
            f"dr_est column mismatch: header={len(names)}, data={data.shape[1]}"
        )
    if "week" not in column_index or "sow" not in column_index:
        raise ValueError("dr_est header must define WEEK and SOW")
    absolute_time = (
        data[:, column_index["week"]] * 604800.0
        + data[:, column_index["sow"]]
    )
    if np.any(np.diff(absolute_time) < 0):
        raise ValueError("dr_est rows are not ordered by GPS week and SOW")
    for group in GROUPS:
        for column in group.columns + tuple(f"{name}[STD]" for name in group.columns):
            if column.casefold() not in column_index:
                raise ValueError(f"Missing dr_est column: {column}")
    return column_index, data, absolute_time


def count_vio_rows(path: Path | None) -> int:
    if path is None:
        return 0
    if not path.is_file():
        raise ValueError(f"VIO file not found: {path}")
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        return sum(1 for line in handle if line.startswith("VIO,"))


def circular_median_degrees(values: np.ndarray) -> float:
    radians = np.deg2rad(values)
    unwrapped = np.unwrap(radians)
    result = math.degrees(np.median(unwrapped)) % 360.0
    return float((result + 180.0) % 360.0 - 180.0)


def diagnostic_values(
    raw_values: np.ndarray,
    group: ParameterGroup,
    initial: np.ndarray,
) -> np.ndarray:
    if not group.circular_degrees:
        return raw_values
    result = np.empty_like(raw_values)
    for axis in range(raw_values.shape[1]):
        unwrapped = np.rad2deg(np.unwrap(np.deg2rad(raw_values[:, axis])))
        offset = 360.0 * np.round((initial[axis] - unwrapped[0]) / 360.0)
        result[:, axis] = unwrapped + offset
    return result


def main() -> int:
    args = parse_args()
    try:
        dr_est_path = args.dr_est.resolve()
        config_path = args.config.resolve()
        output_path = args.output_config.resolve()
        vio_path = args.vio_prodef.resolve() if args.vio_prodef else None
        if output_path in {config_path, dr_est_path, vio_path}:
            raise ValueError("Output config must differ from all input files.")
        if output_path.exists() and not args.force:
            raise ValueError(f"Output config exists: {output_path}. Use --force to replace it.")
        if args.window_seconds <= 0:
            raise ValueError("--window-seconds must be positive")
        if args.min_window_samples < 2:
            raise ValueError("--min-window-samples must be at least 2")

        column_index, data, absolute_time = load_dr_est(dr_est_path)
        if absolute_time.size < 2:
            raise ValueError("dr_est must contain at least two INS_EST_STATE rows.")
        last_time = float(absolute_time[-1])
        window_mask = absolute_time >= last_time - args.window_seconds
        window_samples = int(np.count_nonzero(window_mask))
        if window_samples < args.min_window_samples:
            raise ValueError(
                "Calibration window contains "
                f"{window_samples} samples; minimum is {args.min_window_samples}."
            )
        vio_rows = count_vio_rows(vio_path)

        lines = config_path.read_text(encoding="utf-8-sig").splitlines()
        section_start, section_end = section_bounds(lines, "ctclib_ins")
        entries = active_entries(lines, section_start, section_end)
        ins_mode_raw = read_config_value(lines, entries, "ins_mode")
        if ins_mode_raw != "1":
            raise ValueError(
                f"Source config must be a CALIB config with ins_mode=1, got {ins_mode_raw!r}."
            )

        report_rows = []
        group_results = {}
        observable_groups = set()
        for group in GROUPS:
            value_indexes = [column_index[name.casefold()] for name in group.columns]
            std_indexes = [
                column_index[f"{name}[STD]".casefold()] for name in group.columns
            ]
            raw_values = data[:, value_indexes]
            raw_stds = data[:, std_indexes]
            last_values = raw_values[window_mask]
            last_stds = raw_stds[window_mask]

            config_raw = read_config_value(lines, entries, group.config_key)
            expected_count = len(group.columns)
            config_initial = (
                parse_vector(config_raw, expected_count)
                if config_raw
                else np.zeros(expected_count)
            )
            config_std_raw = read_config_value(
                lines, entries, f"{group.config_key}_std"
            )
            config_initial_std = (
                parse_vector(config_std_raw, expected_count)
                if config_std_raw
                else np.zeros(expected_count)
            )
            initial = config_to_state(config_initial, group)
            estimate_raw = read_config_value(
                lines, entries, f"est_{group.config_key}"
            )
            estimate_mask = (
                parse_vector(estimate_raw, expected_count)
                if estimate_raw is not None
                else np.zeros(expected_count)
            )
            enabled_config_axes = estimate_mask > 0
            enabled_state_axes = np.abs(
                config_to_state(estimate_mask, group)
            ) > 0.5
            estimate_enabled = bool(np.any(enabled_config_axes))
            if group.circular_degrees:
                final = np.array(
                    [
                        circular_median_degrees(last_values[:, axis])
                        for axis in range(last_values.shape[1])
                    ]
                )
            else:
                final = np.median(last_values, axis=0)
            final_std = np.median(last_stds, axis=0)
            diagnostics = diagnostic_values(raw_values, group, initial)
            axis_delta = np.max(np.abs(diagnostics - initial), axis=0)
            axis_range = np.ptp(diagnostics, axis=0)
            axis_observable = (
                (axis_delta > args.tolerance) | (axis_range > args.tolerance)
            )
            if np.any(enabled_state_axes):
                max_delta = float(np.max(axis_delta[enabled_state_axes]))
                max_range = float(np.max(axis_range[enabled_state_axes]))
            else:
                max_delta = 0.0
                max_range = 0.0
            observable_config_axes = np.abs(
                state_to_config(axis_observable.astype(float), group)
            ) > 0.5
            selected_observable_axes = (
                enabled_config_axes & observable_config_axes
            )
            is_vio_group = group.config_key in {"lever_imu2vio", "install_car2vio"}
            if is_vio_group and vio_rows == 0:
                observable = False
                status = "missing_vio_input"
            elif not estimate_enabled:
                observable = False
                status = "estimation_disabled"
            else:
                observable = bool(np.any(selected_observable_axes))
                status = "observable" if observable else "not_observable"
            if observable:
                observable_groups.add(group.config_key)
                config_value = np.where(
                    selected_observable_axes,
                    state_to_config(final, group),
                    config_initial,
                )
                config_std = np.where(
                    selected_observable_axes,
                    std_to_config(final_std, group),
                    config_initial_std,
                )
                set_config_value(
                    lines,
                    entries,
                    section_end,
                    group.config_key,
                    format_vector(config_value),
                )
                set_config_value(
                    lines,
                    entries,
                    section_end,
                    f"{group.config_key}_std",
                    format_vector(config_std),
                )
            else:
                config_value = config_initial.copy()
                config_std = config_initial_std.copy()
            result = {
                "group": group.config_key,
                "status": status,
                "initial": initial.tolist(),
                "estimate_enabled": bool(estimate_enabled),
                "last_value": final.tolist(),
                "last_std": final_std.tolist(),
                "config_value": config_value.tolist(),
                "config_std": config_std.tolist(),
                "last_window_samples": window_samples,
                "max_deviation_from_initial": max_delta,
                "max_range": max_range,
            }
            group_results[group.config_key] = result
            report_rows.append(
                {
                    "group": group.config_key,
                    "status": status,
                    "estimate_enabled": str(bool(estimate_enabled)).lower(),
                    "initial": format_vector(initial),
                    "last_value": format_vector(final),
                    "last_std": format_vector(final_std),
                    "config_value": format_vector(config_value),
                    "config_std": format_vector(config_std),
                    "last_window_samples": window_samples,
                    "max_deviation_from_initial": f"{max_delta:.8g}",
                    "max_range": f"{max_range:.8g}",
                }
            )

        set_config_value(lines, entries, section_end, "ins_mode", "0")
        vio_observable = bool(observable_groups & {"lever_imu2vio", "install_car2vio"})
        if not vio_observable:
            set_config_value(lines, entries, section_end, "method_vio_yaw", "0")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path = output_path.with_name(output_path.stem + "_calibration_report.csv")
        json_path = output_path.with_name(output_path.stem + "_calibration_report.json")
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(report_rows[0]))
            writer.writeheader()
            writer.writerows(report_rows)
        status = "success" if observable_groups else "no_observable_states"
        report = {
            "status": status,
            "dr_est": str(dr_est_path),
            "source_config": str(config_path),
            "output_config": str(output_path) if observable_groups else None,
            "vio_prodef": str(vio_path) if vio_path else None,
            "vio_rows": vio_rows,
            "window_seconds": args.window_seconds,
            "window_samples": window_samples,
            "observable_groups": sorted(observable_groups),
            "estimation_policy": "preserve_source_switches",
            "groups": group_results,
            "outputs": {"csv": str(csv_path), "json": str(json_path)},
        }
        json_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        if not observable_groups:
            if args.json:
                print(json.dumps(report, indent=2, ensure_ascii=False))
            else:
                print(json.dumps({"status": status, "report": str(json_path)}))
            return 3
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(
            json.dumps(
                {
                    "status": "success",
                    "observable_groups": report["observable_groups"],
                    "output_config": str(output_path),
                },
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
