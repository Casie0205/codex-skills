#!/usr/bin/env python3
"""Summarize observability and step behavior across calibration runs."""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class ParameterGroup:
    name: str
    columns: tuple[str, ...]
    circular_degrees: bool = False


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
    ),
    ParameterGroup(
        "install_car2vio",
        (
            "AngleCar2Vio X(deg)",
            "AngleCar2Vio Y(deg)",
            "AngleCar2Vio Z(deg)",
        ),
        circular_degrees=True,
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

GROUP_BY_NAME = {group.name: group for group in GROUPS}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize calibration state observability and maximum steps."
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--window-seconds", type=float, default=30.0)
    parser.add_argument("--tolerance", type=float, default=1e-6)
    return parser.parse_args()


def normalize_name(value: str) -> str:
    clean = value.strip().replace("{", "").replace("}", "")
    if clean.startswith("[") and clean.endswith("]"):
        clean = clean[1:-1]
    return clean.casefold()


def load_dr_est(path: Path) -> tuple[dict[str, int], np.ndarray, np.ndarray]:
    with path.open("r", encoding="utf-8-sig") as handle:
        header = handle.readline().strip()
        rows = [
            [float(value) for value in line.strip().split(",")[1:]]
            for line in handle
            if line.startswith("INS_EST_STATE,")
        ]
    if not rows:
        raise ValueError(f"No INS_EST_STATE rows found in {path}")
    prefix = "#PROTOCOL_DEFINE0,V1,{INS_EST_STATE},"
    if not header.startswith(prefix):
        raise ValueError(f"Unexpected dr_est header: {path}")
    names = header[len(prefix) :].removesuffix("*ff").split(",")
    index = {normalize_name(name): position for position, name in enumerate(names)}
    data = np.asarray(rows, dtype=float)
    if data.shape[1] != len(names):
        raise ValueError(
            f"dr_est column mismatch in {path}: "
            f"header={len(names)}, data={data.shape[1]}"
        )
    elapsed = (
        (data[:, index["week"]] - data[0, index["week"]]) * 604800.0
        + data[:, index["sow"]]
        - data[0, index["sow"]]
    )
    return index, data, elapsed


def unwrap_degrees(values: np.ndarray) -> np.ndarray:
    return np.rad2deg(np.unwrap(np.deg2rad(values)))


def circular_median_degrees(values: np.ndarray) -> float:
    unwrapped = unwrap_degrees(values)
    return float((np.median(unwrapped) + 180.0) % 360.0 - 180.0)


def first_change_elapsed(
    changes: np.ndarray, elapsed: np.ndarray, tolerance: float
) -> float | None:
    changed = np.any(np.abs(changes) > tolerance, axis=1)
    if not np.any(changed):
        return None
    return float(elapsed[np.flatnonzero(changed)[0]])


def summarize_group(
    experiment: str,
    target_group: str,
    group: ParameterGroup,
    index: dict[str, int],
    data: np.ndarray,
    elapsed: np.ndarray,
    window_seconds: float,
    tolerance: float,
) -> dict[str, object]:
    value_indexes = [index[column.casefold()] for column in group.columns]
    std_indexes = [
        index[f"{column}[STD]".casefold()] for column in group.columns
    ]
    raw_values = data[:, value_indexes]
    values = (
        np.column_stack(
            [unwrap_degrees(raw_values[:, axis]) for axis in range(raw_values.shape[1])]
        )
        if group.circular_degrees
        else raw_values
    )
    raw_stds = data[:, std_indexes]
    final_mask = elapsed >= elapsed[-1] - window_seconds
    if group.circular_degrees:
        final = np.array(
            [
                circular_median_degrees(raw_values[final_mask, axis])
                for axis in range(raw_values.shape[1])
            ]
        )
    else:
        final = np.median(values[final_mask], axis=0)
    final_std = np.median(raw_stds[final_mask], axis=0)
    initial = values[0]
    deltas = values - initial
    steps = np.diff(values, axis=0)
    abs_steps = np.abs(steps)
    step_indexes = np.argmax(abs_steps, axis=0)
    ranges = np.ptp(values, axis=0)
    max_steps = np.max(abs_steps, axis=0)
    step_fractions = np.divide(
        max_steps,
        ranges,
        out=np.zeros_like(max_steps),
        where=ranges > tolerance,
    )
    changed = np.any(np.abs(values - values[0]) > tolerance, axis=1)
    first_change = first_change_elapsed(deltas, elapsed, tolerance)
    observable = bool(
        np.max(np.abs(deltas)) > tolerance or np.max(ranges) > tolerance
    )
    axis_results = []
    for axis, column in enumerate(group.columns):
        axis_results.append(
            {
                "axis": column,
                "initial": float(initial[axis]),
                "final_median": float(final[axis]),
                "final_std_median": float(final_std[axis]),
                "min": float(np.min(values[:, axis])),
                "max": float(np.max(values[:, axis])),
                "max_abs_change": float(np.max(np.abs(deltas[:, axis]))),
                "max_range": float(ranges[axis]),
                "max_step_abs": float(max_steps[axis]),
                "max_step_elapsed_s": float(
                    elapsed[step_indexes[axis] + 1]
                ),
                "max_step_fraction_of_range": float(step_fractions[axis]),
            }
        )
    largest_axis = int(np.argmax(max_steps))
    return {
        "experiment": experiment,
        "target_group": target_group,
        "group": group.name,
        "observable": observable,
        "changed_samples": int(np.count_nonzero(changed)),
        "first_change_elapsed_s": first_change,
        "largest_step_axis": group.columns[largest_axis],
        "largest_step_abs": float(max_steps[largest_axis]),
        "largest_step_elapsed_s": float(
            elapsed[step_indexes[largest_axis] + 1]
        ),
        "largest_step_fraction_of_range": float(step_fractions[largest_axis]),
        "axes": axis_results,
    }


def main() -> int:
    args = parse_args()
    manifest_path = args.manifest.resolve()
    output_dir = args.output_dir.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    missing = []
    for experiment in manifest["experiments"]:
        target_group = experiment["group"]
        selected_groups = experiment.get("groups")
        if not selected_groups:
            selected_groups = [target_group, "install_car2vio"]
        dr_est = Path(experiment["output_dir"]) / "dr_est.prodef"
        if not dr_est.is_file():
            missing.append(str(dr_est))
            continue
        index, data, elapsed = load_dr_est(dr_est)
        for group in GROUPS:
            if group.name not in selected_groups:
                continue
            result = summarize_group(
                experiment=target_group,
                target_group=target_group,
                group=group,
                index=index,
                data=data,
                elapsed=elapsed,
                window_seconds=args.window_seconds,
                tolerance=args.tolerance,
            )
            result["dr_est"] = str(dr_est)
            results.append(result)
    if missing:
        raise ValueError("Missing dr_est outputs: " + ", ".join(missing))

    json_path = output_dir / "calibration_observability_summary.json"
    csv_path = output_dir / "calibration_observability_summary.csv"
    json_path.write_text(
        json.dumps(
            {
                "manifest": str(manifest_path),
                "window_seconds": args.window_seconds,
                "tolerance": args.tolerance,
                "experiments": results,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        fields = (
            "experiment",
            "target_group",
            "group",
            "axis",
            "observable",
            "initial",
            "final_median",
            "final_std_median",
            "min",
            "max",
            "max_abs_change",
            "max_range",
            "max_step_abs",
            "max_step_elapsed_s",
            "max_step_fraction_of_range",
            "first_change_elapsed_s",
            "changed_samples",
        )
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            for axis in result["axes"]:
                writer.writerow(
                    {
                        "experiment": result["experiment"],
                        "target_group": result["target_group"],
                        "group": result["group"],
                        "axis": axis["axis"],
                        "observable": str(result["observable"]).lower(),
                        "initial": f"{axis['initial']:.9g}",
                        "final_median": f"{axis['final_median']:.9g}",
                        "final_std_median": f"{axis['final_std_median']:.9g}",
                        "min": f"{axis['min']:.9g}",
                        "max": f"{axis['max']:.9g}",
                        "max_abs_change": f"{axis['max_abs_change']:.9g}",
                        "max_range": f"{axis['max_range']:.9g}",
                        "max_step_abs": f"{axis['max_step_abs']:.9g}",
                        "max_step_elapsed_s": f"{axis['max_step_elapsed_s']:.9g}",
                        "max_step_fraction_of_range": (
                            f"{axis['max_step_fraction_of_range']:.9g}"
                        ),
                        "first_change_elapsed_s": (
                            ""
                            if result["first_change_elapsed_s"] is None
                            else f"{result['first_change_elapsed_s']:.9g}"
                        ),
                        "changed_samples": result["changed_samples"],
                    }
                )
    print(
        json.dumps(
            {
                "status": "success",
                "experiments": len(manifest["experiments"]),
                "groups": len(results),
                "json": str(json_path),
                "csv": str(csv_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
