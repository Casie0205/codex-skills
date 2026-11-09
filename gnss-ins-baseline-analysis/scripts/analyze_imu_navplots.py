#!/usr/bin/env python3
"""Analyze CTCLib split IMU NavPlot files without reinterpreting columns."""

from __future__ import annotations

import argparse
import csv
import json
import math
import pickle
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


WEEK_COLUMN = 0
SOW_COLUMN = 1
TEMPERATURE_COLUMN = 14
ACC_COLUMNS = (15, 16, 17)
GYRO_COLUMNS = (18, 19, 20)
MIN_COLUMNS = 21
SECONDS_PER_WEEK = 604800.0


@dataclass
class Segment:
    path: Path
    data: np.ndarray
    absolute_time: np.ndarray


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze CTCLib imu_*.navplot segments and generate raw IMU figures and statistics."
    )
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--input-dir", type=Path, help="Directory containing imu_*.navplot files")
    inputs.add_argument(
        "--input",
        type=Path,
        action="append",
        help="Explicit imu_*.navplot path; repeat for multiple files",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--title-prefix", default="CTCLib IMU")
    parser.add_argument("--force", action="store_true", help="Allow writing into a non-empty output directory")
    parser.add_argument("--json", action="store_true", help="Print the summary JSON")
    return parser.parse_args()


def discover_inputs(args: argparse.Namespace) -> list[Path]:
    if args.input_dir:
        if not args.input_dir.is_dir():
            raise ValueError(f"Input directory not found: {args.input_dir}")
        paths = sorted(args.input_dir.glob("imu_*.navplot"))
    else:
        paths = list(args.input or [])
    paths = [path.resolve() for path in paths]
    if not paths:
        raise ValueError("No imu_*.navplot files were found")
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise ValueError("Input files not found: " + ", ".join(missing))
    return sorted(paths)


def load_segment(path: Path) -> Segment:
    data = np.loadtxt(path, ndmin=2)
    if data.ndim != 2 or data.shape[0] == 0 or data.shape[1] < MIN_COLUMNS:
        raise ValueError(
            f"{path} must contain at least {MIN_COLUMNS} columns and one data row"
        )
    if not np.isfinite(data).all():
        raise ValueError(f"{path} contains non-finite values")
    absolute_time = data[:, WEEK_COLUMN] * SECONDS_PER_WEEK + data[:, SOW_COLUMN]
    order = np.argsort(absolute_time, kind="stable")
    return Segment(path=path, data=data[order], absolute_time=absolute_time[order])


def statistics(values: np.ndarray) -> dict[str, float]:
    finite = np.asarray(values, dtype=float)
    mean = float(np.mean(finite))
    std = float(np.std(finite, ddof=1)) if finite.size > 1 else 0.0
    rms = float(math.sqrt(float(np.mean(finite * finite))))
    minimum = float(np.min(finite))
    maximum = float(np.max(finite))
    absolute = np.abs(finite)
    cep68, cep95, cep99 = np.percentile(absolute, [68.0, 95.0, 99.0])
    return {
        "mean": mean,
        "std": std,
        "rms": rms,
        "max": maximum,
        "min": minimum,
        "range": maximum - minimum,
        "cep68": float(cep68),
        "cep95": float(cep95),
        "cep99": float(cep99),
    }


def format_value(value: float) -> str:
    return f"{value:.6f}"


def write_statistics(
    output_dir: Path,
    accelerometer: dict[str, dict[str, float]],
    gyroscope: dict[str, dict[str, float]],
) -> tuple[Path, Path]:
    headers = [
        "Metric",
        "Acc X (g)",
        "Acc Y (g)",
        "Acc Z (g)",
        "Gyro X (deg/s)",
        "Gyro Y (deg/s)",
        "Gyro Z (deg/s)",
    ]
    keys = [
        ("mean", "均值"),
        ("std", "标准差"),
        ("rms", "均方根"),
        ("max", "极大值"),
        ("min", "极小值"),
        ("range", "极差"),
        ("cep68", "CEP68"),
        ("cep95", "CEP95"),
        ("cep99", "CEP99"),
    ]
    rows: list[list[str]] = []
    for key, label in keys:
        rows.append(
            [
                label,
                format_value(accelerometer["x"][key]),
                format_value(accelerometer["y"][key]),
                format_value(accelerometer["z"][key]),
                format_value(gyroscope["x"][key]),
                format_value(gyroscope["y"][key]),
                format_value(gyroscope["z"][key]),
            ]
        )

    csv_path = output_dir / "imu_statistics.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)

    md_path = output_dir / "imu_statistics.md"
    md_lines = [
        "# CTCLib IMU Statistics",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] + ["---:"] * (len(headers) - 1)) + " |",
    ]
    md_lines.extend("| " + " | ".join(row) + " |" for row in rows)
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return csv_path, md_path


def plot_sensor(
    segments: list[Segment],
    columns: tuple[int, int, int],
    labels: tuple[str, str, str],
    unit: str,
    title: str,
    output_base: Path,
) -> list[Path]:
    global_start = min(float(segment.absolute_time[0]) for segment in segments)
    fig, axes = plt.subplots(3, 1, figsize=(15.5, 10.5), sharex=True)
    legend_handles = []
    legend_labels = []

    for segment in segments:
        elapsed_minutes = (segment.absolute_time - global_start) / 60.0
        for axis_index, column in enumerate(columns):
            line = axes[axis_index].plot(
                elapsed_minutes,
                segment.data[:, column],
                linewidth=0.7,
                label=segment.path.name,
            )[0]
            if axis_index == 0:
                legend_handles.append(line)
                legend_labels.append(segment.path.name)

    for axis, label in zip(axes, labels):
        axis.set_ylabel(label)
        axis.grid(True, alpha=0.25)
    axes[-1].set_xlabel("Elapsed time (min)")

    legend_columns = min(6, max(1, len(legend_labels)))
    fig.legend(
        legend_handles,
        legend_labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.995),
        ncol=legend_columns,
        frameon=True,
    )
    fig.subplots_adjust(top=0.90, hspace=0.20, left=0.08, right=0.985, bottom=0.07)
    axes[0].set_title(f"{title} ({unit})", pad=10)

    outputs: list[Path] = []
    for suffix, kwargs in (
        (".svg", {"format": "svg"}),
        (".png", {"format": "png", "dpi": 300}),
    ):
        path = output_base.with_suffix(suffix)
        fig.set_visible(True)
        fig.savefig(path, bbox_inches="tight", **kwargs)
        outputs.append(path)
    figure_path = output_base.with_suffix(".fig")
    fig.set_visible(True)
    with figure_path.open("wb") as handle:
        pickle.dump(fig, handle)
    outputs.append(figure_path)
    plt.close(fig)
    return outputs


def main() -> int:
    args = parse_args()
    try:
        paths = discover_inputs(args)
        output_dir = args.output_dir.resolve()
        if output_dir.exists() and any(output_dir.iterdir()) and not args.force:
            raise ValueError(f"Output directory is not empty: {output_dir}. Use --force to replace outputs.")
        output_dir.mkdir(parents=True, exist_ok=True)
        segments = [load_segment(path) for path in paths]
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    merged_data = np.concatenate([segment.data for segment in segments], axis=0)
    merged_time = np.concatenate([segment.absolute_time for segment in segments], axis=0)
    order = np.argsort(merged_time, kind="stable")
    merged_data = merged_data[order]
    merged_time = merged_time[order]

    accelerometer = {
        axis: statistics(merged_data[:, column])
        for axis, column in zip(("x", "y", "z"), ACC_COLUMNS)
    }
    gyroscope = {
        axis: statistics(merged_data[:, column])
        for axis, column in zip(("x", "y", "z"), GYRO_COLUMNS)
    }
    statistics_csv, statistics_md = write_statistics(
        output_dir, accelerometer, gyroscope
    )

    accel_figures = plot_sensor(
        segments,
        ACC_COLUMNS,
        ("Acc X", "Acc Y", "Acc Z"),
        "g",
        f"{args.title_prefix} accelerometer",
        output_dir / "imu_accelerometer_all_segments",
    )
    gyro_figures = plot_sensor(
        segments,
        GYRO_COLUMNS,
        ("Gyro X", "Gyro Y", "Gyro Z"),
        "deg/s",
        f"{args.title_prefix} gyroscope",
        output_dir / "imu_gyroscope_all_segments",
    )

    deltas = np.diff(merged_time)
    positive_deltas = deltas[deltas > 0]
    rounded_positive_deltas = np.round(positive_deltas, 6)
    median_dt = float(np.median(positive_deltas)) if positive_deltas.size else 0.0
    duration = float(merged_time[-1] - merged_time[0]) if merged_time.size > 1 else 0.0
    sample_rate = (merged_time.size - 1) / duration if duration > 0 else 0.0
    segment_summaries = []
    for segment in segments:
        segment_duration = (
            float(segment.absolute_time[-1] - segment.absolute_time[0])
            if segment.absolute_time.size > 1
            else 0.0
        )
        segment_summaries.append(
            {
                "path": str(segment.path),
                "rows": int(segment.data.shape[0]),
                "first_sow": float(segment.data[0, SOW_COLUMN]),
                "last_sow": float(segment.data[-1, SOW_COLUMN]),
                "duration_seconds": segment_duration,
            }
        )

    summary = {
        "status": "success",
        "input_files": [str(path) for path in paths],
        "output_dir": str(output_dir),
        "rows": int(merged_data.shape[0]),
        "segments": segment_summaries,
        "time": {
            "first_sow": float(merged_data[0, SOW_COLUMN]),
            "last_sow": float(merged_data[-1, SOW_COLUMN]),
            "duration_seconds": duration,
            "median_sample_interval_seconds": median_dt,
            "estimated_rate_hz": sample_rate,
            "duplicate_timestamps": int(np.count_nonzero(deltas == 0)),
            "gaps_gt_20ms": int(np.count_nonzero(rounded_positive_deltas > 0.020)),
            "gaps_gt_100ms": int(np.count_nonzero(rounded_positive_deltas > 0.100)),
        },
        "temperature_c": {
            "min": float(np.min(merged_data[:, TEMPERATURE_COLUMN])),
            "mean": float(np.mean(merged_data[:, TEMPERATURE_COLUMN])),
            "max": float(np.max(merged_data[:, TEMPERATURE_COLUMN])),
        },
        "column_mapping": {
            "week": WEEK_COLUMN,
            "sow": SOW_COLUMN,
            "temperature": TEMPERATURE_COLUMN,
            "accelerometer_g": list(ACC_COLUMNS),
            "gyroscope_deg_s": list(GYRO_COLUMNS),
        },
        "statistics": {
            "accelerometer": accelerometer,
            "gyroscope": gyroscope,
        },
        "outputs": {
            "statistics_csv": str(statistics_csv),
            "statistics_markdown": str(statistics_md),
            "accelerometer_figures": [str(path) for path in accel_figures],
            "gyroscope_figures": [str(path) for path in gyro_figures],
        },
    }
    summary_path = output_dir / "imu_analysis_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(json.dumps({"status": "success", "summary": str(summary_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
