#!/usr/bin/env python3
"""Plot INS status trajectories and compare INS against gnss_rtkplot."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

from standard_plot_bridge import load_figure_core


GPS_EPOCH = datetime(1980, 1, 6)
SECONDS_PER_WEEK = 604800.0
STATUS_ORDER = ("Fix", "Float", "Diff", "Single", "INS", "Other")
STATUS_COLORS = {
    "Fix": "#1b9e77",
    "Float": "#d95f02",
    "Diff": "#1f77b4",
    "Single": "#e7298a",
    "INS": "#7570b3",
    "Other": "#777777",
}
STATUS_DISPLAY = {
    "Fix": "固定解",
    "Float": "浮点解",
    "Diff": "差分",
    "Single": "单点",
    "INS": "INS",
    "Other": "其他",
}
INS_STATUS_TO_CLASS = {
    1: "Fix",
    2: "Float",
    3: "Diff",
    4: "Diff",
    5: "Single",
    6: "INS",
}
METRIC_LABELS = (
    ("mean", "均值"),
    ("std", "标准差"),
    ("rms", "均方根"),
    ("max", "极大值"),
    ("min", "极小值"),
    ("range", "极差"),
    ("cep68", "CEP68"),
    ("cep95", "CEP95"),
    ("cep99", "CEP99"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot NavPlot trajectory status and compare INS position/velocity with RTKPlot."
    )
    parser.add_argument("--ins-insplot", type=Path, required=True)
    parser.add_argument("--gnss-rtkplot", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-match-gap", type=float, default=0.30)
    parser.add_argument("--max-rtk-gap", type=float, default=0.50)
    parser.add_argument("--max-rtk-speed", type=float, default=50.0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def load_ins_insplot(path: Path) -> dict[str, np.ndarray | int]:
    rows: list[list[float]] = []
    malformed = 0
    widths: dict[int, int] = {}
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            tokens = stripped.split()
            widths[len(tokens)] = widths.get(len(tokens), 0) + 1
            if len(tokens) < 18:
                malformed += 1
                continue
            try:
                rows.append([float(value) for value in tokens])
            except ValueError:
                malformed += 1
    if not rows:
        raise ValueError(f"No usable rows in ins_insplot: {path}")
    data = np.asarray(rows, dtype=float)
    order = np.argsort(data[:, 0] * SECONDS_PER_WEEK + data[:, 1], kind="stable")
    data = data[order]
    time = data[:, 0] * SECONDS_PER_WEEK + data[:, 1]
    keep = np.r_[np.diff(time) > 1e-7, True]
    return {
        "data": data[keep],
        "time": time[keep],
        "malformed": malformed,
        "widths": widths,
    }


def parse_gps_datetime(date_value: str, time_value: str) -> float:
    parsed = datetime.strptime(f"{date_value} {time_value}", "%Y/%m/%d %H:%M:%S.%f")
    return (parsed - GPS_EPOCH).total_seconds()


def load_gnss_rtkplot(path: Path) -> dict[str, np.ndarray | int]:
    rows: list[list[float]] = []
    malformed = 0
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("%"):
                continue
            tokens = stripped.replace(",", " ").split()
            if len(tokens) < 7:
                malformed += 1
                continue
            try:
                time_s = parse_gps_datetime(tokens[0], tokens[1])
                x, y, z = (float(tokens[index]) for index in (2, 3, 4))
                quality = int(float(tokens[5]))
                satellites = int(float(tokens[6]))
                rows.append([time_s, x, y, z, quality, satellites])
            except ValueError:
                malformed += 1
    if not rows:
        raise ValueError(f"No usable rows in gnss_rtkplot: {path}")
    data = np.asarray(rows, dtype=float)
    order = np.argsort(data[:, 0], kind="stable")
    data = data[order]
    keep = np.r_[np.diff(data[:, 0]) > 1e-7, True]
    data = data[keep]
    return {"data": data, "malformed": malformed}


def geodetic_to_ecef(
    latitude_deg: np.ndarray,
    longitude_deg: np.ndarray,
    height_m: np.ndarray,
) -> np.ndarray:
    a = 6378137.0
    f = 1.0 / 298.257223563
    e2 = f * (2.0 - f)
    lat = np.deg2rad(np.asarray(latitude_deg, dtype=float))
    lon = np.deg2rad(np.asarray(longitude_deg, dtype=float))
    h = np.asarray(height_m, dtype=float)
    sin_lat = np.sin(lat)
    cos_lat = np.cos(lat)
    sin_lon = np.sin(lon)
    cos_lon = np.cos(lon)
    n = a / np.sqrt(1.0 - e2 * sin_lat * sin_lat)
    return np.column_stack(
        (
            (n + h) * cos_lat * cos_lon,
            (n + h) * cos_lat * sin_lon,
            (n * (1.0 - e2) + h) * sin_lat,
        )
    )


def ecef_to_geodetic(ecef: np.ndarray) -> np.ndarray:
    a = 6378137.0
    f = 1.0 / 298.257223563
    e2 = f * (2.0 - f)
    b = a * (1.0 - f)
    ep2 = (a * a - b * b) / (b * b)
    result = np.empty_like(ecef, dtype=float)
    for index, (x, y, z) in enumerate(ecef):
        p = math.hypot(x, y)
        if p < 1e-9:
            latitude = math.copysign(math.pi / 2.0, z)
            longitude = 0.0
            height = abs(z) - b
        else:
            theta = math.atan2(z * a, p * b)
            sin_theta = math.sin(theta)
            cos_theta = math.cos(theta)
            latitude = math.atan2(
                z + ep2 * b * sin_theta**3,
                p - e2 * a * cos_theta**3,
            )
            longitude = math.atan2(y, x)
            n = a / math.sqrt(1.0 - e2 * math.sin(latitude) ** 2)
            height = p / math.cos(latitude) - n
        result[index] = (
            math.degrees(latitude),
            math.degrees(longitude),
            height,
        )
    return result


def enu_rotation(latitude_deg: float, longitude_deg: float) -> np.ndarray:
    lat = math.radians(latitude_deg)
    lon = math.radians(longitude_deg)
    sin_lat, cos_lat = math.sin(lat), math.cos(lat)
    sin_lon, cos_lon = math.sin(lon), math.cos(lon)
    return np.array(
        [
            [-sin_lon, cos_lon, 0.0],
            [-sin_lat * cos_lon, -sin_lat * sin_lon, cos_lat],
            [cos_lat * cos_lon, cos_lat * sin_lon, sin_lat],
        ],
        dtype=float,
    )


def segmented_ecef_velocity(
    time_s: np.ndarray,
    ecef: np.ndarray,
    quality: np.ndarray,
    max_gap_s: float,
    max_speed_mps: float,
) -> tuple[np.ndarray, np.ndarray]:
    velocity = np.full_like(ecef, np.nan, dtype=float)
    valid = np.zeros(time_s.size, dtype=bool)
    start = 0
    while start < time_s.size:
        end = start + 1
        while end < time_s.size:
            same_quality = quality[end] == quality[start]
            continuous = (time_s[end] - time_s[end - 1]) <= max_gap_s
            if not (same_quality and continuous):
                break
            end += 1
        if end - start >= 3:
            segment_velocity = np.gradient(
                ecef[start:end],
                time_s[start:end],
                axis=0,
                edge_order=2,
            )
            speed = np.linalg.norm(segment_velocity, axis=1)
            segment_valid = np.isfinite(speed) & (speed <= max_speed_mps)
            velocity[start:end][segment_valid] = segment_velocity[segment_valid]
            valid[start:end] = segment_valid
        start = end
    return velocity, valid


def status_classes(codes: np.ndarray) -> np.ndarray:
    return np.array(
        [INS_STATUS_TO_CLASS.get(int(code), "Other") for code in codes],
        dtype=object,
    )


def category_handles(categories: list[str], figure_core) -> list:
    return [
        figure_core.Line2D(
            [0],
            [0],
            marker="o",
            linestyle="None",
            markersize=5,
            color=STATUS_COLORS[category],
            label=STATUS_DISPLAY[category],
        )
        for category in categories
    ]


def plot_status_scatter(
    axis,
    x_values: np.ndarray,
    y_values: np.ndarray,
    classes: np.ndarray,
    categories: list[str],
    marker_size: float = 4.0,
) -> None:
    for category in categories:
        mask = classes == category
        if np.any(mask):
            axis.scatter(
                x_values[mask],
                y_values[mask],
                s=marker_size,
                color=STATUS_COLORS[category],
                linewidths=0,
                alpha=0.9,
                rasterized=False,
            )


def plot_horizontal_trajectory(
    east: np.ndarray,
    north: np.ndarray,
    classes: np.ndarray,
    categories: list[str],
    output_base: Path,
    figure_core,
) -> list[Path]:
    fig, axes_grid = figure_core.create_figure(1)
    axis = axes_grid[0, 0]
    axis.plot(east, north, color="0.75", linewidth=0.45, zorder=1)
    plot_status_scatter(axis, east, north, classes, categories)
    axis.scatter([east[0]], [north[0]], marker="*", s=90, color="black", zorder=5)
    axis.set_aspect("equal", adjustable="box")
    figure_core.style_axis(
        axis,
        xlabel="东向 (m)",
        ylabel="北向 (m)",
        panel_letter="a",
    )
    figure_core.add_shared_legend(
        fig,
        category_handles(categories, figure_core),
        [STATUS_DISPLAY[category] for category in categories],
        legend_columns=6,
    )
    outputs = figure_core.save_figure(fig, output_base, include_pickle=True)
    figure_core.plt.close(fig)
    return outputs


def plot_position_time(
    elapsed_s: np.ndarray,
    east: np.ndarray,
    north: np.ndarray,
    up: np.ndarray,
    classes: np.ndarray,
    categories: list[str],
    output_base: Path,
    figure_core,
) -> list[Path]:
    fig, axes_grid = figure_core.create_figure(3, legend_scope="figure")
    axes = axes_grid[:, 0]
    values = (east, north, up)
    labels = ("东向位置 (m)", "北向位置 (m)", "天向位置 (m)")
    for index, (axis, values_for_axis, ylabel) in enumerate(zip(axes, values, labels)):
        plot_status_scatter(axis, elapsed_s, values_for_axis, classes, categories)
        figure_core.style_axis(
            axis,
            ylabel=ylabel,
            xlabel="时间 (s)" if index == len(axes) - 1 else None,
            panel_letter=chr(ord("a") + index),
        )
    figure_core.add_shared_legend(
        fig,
        category_handles(categories, figure_core),
        [STATUS_DISPLAY[category] for category in categories],
        legend_columns=6,
    )
    outputs = figure_core.save_figure(fig, output_base, include_pickle=True)
    figure_core.plt.close(fig)
    return outputs


def plot_error_time(
    elapsed_s: np.ndarray,
    position_errors: tuple[np.ndarray, np.ndarray, np.ndarray],
    velocity_errors: tuple[np.ndarray, np.ndarray, np.ndarray],
    classes: np.ndarray,
    categories: list[str],
    output_base: Path,
    figure_core,
) -> list[Path]:
    fig, axes = figure_core.create_figure(3, ncols=2, sharex=True)
    panel_labels = iter("abcdef")
    ylabels = (
        ("位置东向误差 (m)", "速度东向误差 (m/s)"),
        ("位置北向误差 (m)", "速度北向误差 (m/s)"),
        ("位置天向误差 (m)", "速度天向误差 (m/s)"),
    )
    for row in range(3):
        for column, error_values in enumerate(
            (position_errors[row], velocity_errors[row])
        ):
            axis = axes[row, column]
            plot_status_scatter(
                axis,
                elapsed_s,
                error_values,
                classes,
                categories,
                marker_size=3.0,
            )
            axis.axhline(0.0, color="0.55", linewidth=0.5)
            figure_core.style_axis(
                axis,
                ylabel=ylabels[row][column],
                xlabel="时间 (s)" if row == 2 else None,
                panel_letter=next(panel_labels),
            )
    figure_core.add_shared_legend(
        fig,
        category_handles(categories, figure_core),
        [STATUS_DISPLAY[category] for category in categories],
        legend_columns=6,
    )
    outputs = figure_core.save_figure(fig, output_base, include_pickle=True)
    figure_core.plt.close(fig)
    return outputs


def scalar_statistics(values: np.ndarray, magnitude: bool = False) -> dict[str, float]:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return {key: float("nan") for key, _ in METRIC_LABELS}
    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1)) if values.size > 1 else 0.0
    rms = float(np.sqrt(np.mean(values * values)))
    maximum = float(np.max(values))
    minimum = float(np.min(values))
    absolute = values if magnitude else np.abs(values)
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


def error_group(
    quantity: str,
    solution_set: str,
    east: np.ndarray,
    north: np.ndarray,
    up: np.ndarray,
) -> list[dict[str, object]]:
    two_d = np.sqrt(east * east + north * north)
    three_d = np.sqrt(east * east + north * north + up * up)
    axis_stats = {
        "E": scalar_statistics(east),
        "N": scalar_statistics(north),
        "U": scalar_statistics(up),
        "2D": scalar_statistics(two_d, magnitude=True),
        "3D": scalar_statistics(three_d, magnitude=True),
    }
    rows = []
    for metric, label in METRIC_LABELS:
        rows.append(
            {
                "quantity": quantity,
                "solution_set": solution_set,
                "count": int(east.size),
                "metric": label,
                "E": axis_stats["E"][metric],
                "N": axis_stats["N"][metric],
                "U": axis_stats["U"][metric],
                "2D": axis_stats["2D"][metric],
                "3D": axis_stats["3D"][metric],
            }
        )
    return rows


def write_error_statistics(
    output_dir: Path,
    groups: list[tuple[str, str, np.ndarray, np.ndarray, np.ndarray]],
) -> tuple[list[dict[str, object]], Path, Path]:
    rows: list[dict[str, object]] = []
    for quantity, solution_set, east, north, up in groups:
        rows.extend(error_group(quantity, solution_set, east, north, up))
    csv_path = output_dir / "navigation_error_statistics.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    md_path = output_dir / "navigation_error_statistics.md"
    headers = list(rows[0])
    display_headers = ["物理量", "解集", "数量", "指标", "东向", "北向", "天向", "2D", "3D"]
    quantity_display = {
        "position_m": "位置 (m)",
        "velocity_mps": "速度 (m/s)",
    }
    solution_display = {
        "fixed": "固定解",
        "all": "所有解",
    }
    lines = [
        "# 导航误差统计",
        "",
        "| " + " | ".join(display_headers) + " |",
        "| " + " | ".join(["---"] * 3 + ["---:"] * (len(display_headers) - 3)) + " |",
    ]
    for row in rows:
        display_row = dict(row)
        display_row["quantity"] = quantity_display.get(
            str(row["quantity"]), str(row["quantity"])
        )
        display_row["solution_set"] = solution_display.get(
            str(row["solution_set"]), str(row["solution_set"])
        )
        formatted = []
        for header in headers:
            value = display_row[header]
            if isinstance(value, float):
                formatted.append(f"{value:.6f}")
            else:
                formatted.append(str(value))
        lines.append("| " + " | ".join(formatted) + " |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rows, csv_path, md_path


def write_error_samples(
    output_dir: Path,
    matched: dict[str, np.ndarray],
) -> Path:
    path = output_dir / "navigation_error_samples.csv"
    fields = list(matched)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(fields)
        for index in range(matched[fields[0]].size):
            writer.writerow([matched[field][index] for field in fields])
    return path


def main() -> int:
    args = parse_args()
    try:
        ins_path = args.ins_insplot.resolve()
        rtk_path = args.gnss_rtkplot.resolve()
        output_dir = args.output_dir.resolve()
        if output_dir.exists() and any(output_dir.iterdir()) and not args.force:
            raise ValueError(
                f"Output directory is not empty: {output_dir}. Use --force to replace outputs."
            )
        figure_core = load_figure_core()
        figure_core.configure_style()
        ins = load_ins_insplot(ins_path)
        rtk = load_gnss_rtkplot(rtk_path)
        ins_data = ins["data"]
        rtk_data = rtk["data"]
        assert isinstance(ins_data, np.ndarray)
        assert isinstance(rtk_data, np.ndarray)
        ins_time = np.asarray(ins["time"], dtype=float)
        rtk_time = rtk_data[:, 0]
        ins_lat = ins_data[:, 2]
        ins_lon = ins_data[:, 3]
        ins_height = ins_data[:, 4]
        ins_status = ins_data[:, 5].astype(int)
        classes = status_classes(ins_status)
        categories = [
            category
            for category in STATUS_ORDER
            if np.any(classes == category)
        ]

        finite_origin = np.flatnonzero(
            np.isfinite(ins_lat) & np.isfinite(ins_lon) & np.isfinite(ins_height)
        )
        if finite_origin.size == 0:
            raise ValueError("ins_insplot has no finite position")
        origin_index = int(finite_origin[0])
        origin_lat = float(ins_lat[origin_index])
        origin_lon = float(ins_lon[origin_index])
        origin_height = float(ins_height[origin_index])
        origin_ecef = geodetic_to_ecef(
            np.array([origin_lat]),
            np.array([origin_lon]),
            np.array([origin_height]),
        )[0]
        rotation = enu_rotation(origin_lat, origin_lon)

        ins_ecef = geodetic_to_ecef(ins_lat, ins_lon, ins_height)
        ins_enu = (ins_ecef - origin_ecef) @ rotation.T
        ins_velocity = ins_data[:, 15:18]

        rtk_xyz = rtk_data[:, 1:4]
        rtk_quality = rtk_data[:, 4].astype(int)
        rtk_velocity_ecef, rtk_velocity_valid = segmented_ecef_velocity(
            rtk_time,
            rtk_xyz,
            rtk_quality,
            args.max_rtk_gap,
            args.max_rtk_speed,
        )
        rtk_velocity_enu = rtk_velocity_ecef @ rotation.T
        rtk_speed = np.linalg.norm(rtk_velocity_ecef, axis=1)
        finite_speed = rtk_speed[np.isfinite(rtk_speed)]

        in_range = (ins_time >= rtk_time[0]) & (ins_time <= rtk_time[-1])
        right_raw = np.searchsorted(rtk_time, ins_time, side="left")
        right = np.clip(right_raw, 0, rtk_time.size - 1)
        left = np.clip(right_raw - 1, 0, rtk_time.size - 1)
        interpolation_gap = np.maximum(
            np.abs(ins_time - rtk_time[left]),
            np.abs(rtk_time[right] - ins_time),
        )
        matched_mask = in_range & (interpolation_gap <= args.max_match_gap)
        matched_mask &= np.isfinite(ins_enu).all(axis=1)
        matched_mask &= np.isfinite(rtk_xyz).all(axis=1)[left]
        matched_mask &= np.isfinite(rtk_xyz).all(axis=1)[right]
        if not np.any(matched_mask):
            raise ValueError(
                "No INS epochs fall inside the RTK time range within --max-match-gap."
            )

        matched_time = ins_time[matched_mask]
        matched_classes = classes[matched_mask]
        matched_status = ins_status[matched_mask]
        q_left = rtk_quality[left[matched_mask]]
        q_right = rtk_quality[right[matched_mask]]
        matched_gap = interpolation_gap[matched_mask]
        matched_east = ins_enu[matched_mask, 0]
        matched_north = ins_enu[matched_mask, 1]
        matched_up = ins_enu[matched_mask, 2]
        matched_velocity = ins_velocity[matched_mask]
        velocity_bracket_valid = (
            rtk_velocity_valid[left[matched_mask]]
            & rtk_velocity_valid[right[matched_mask]]
        )

        rtk_enu = (rtk_xyz - origin_ecef) @ rotation.T
        reference_east = np.interp(matched_time, rtk_time, rtk_enu[:, 0])
        reference_north = np.interp(matched_time, rtk_time, rtk_enu[:, 1])
        reference_up = np.interp(matched_time, rtk_time, rtk_enu[:, 2])
        reference_ve = np.interp(matched_time, rtk_time, rtk_velocity_enu[:, 0])
        reference_vn = np.interp(matched_time, rtk_time, rtk_velocity_enu[:, 1])
        reference_vu = np.interp(matched_time, rtk_time, rtk_velocity_enu[:, 2])
        reference_ve[~velocity_bracket_valid] = np.nan
        reference_vn[~velocity_bracket_valid] = np.nan
        reference_vu[~velocity_bracket_valid] = np.nan

        error_east = matched_east - reference_east
        error_north = matched_north - reference_north
        error_up = matched_up - reference_up
        error_ve = matched_velocity[:, 0] - reference_ve
        error_vn = matched_velocity[:, 1] - reference_vn
        error_vu = matched_velocity[:, 2] - reference_vu
        valid_position = np.isfinite(error_east + error_north + error_up)
        valid_velocity = np.isfinite(error_ve + error_vn + error_vu)
        valid_plot = valid_position | valid_velocity
        if not np.any(valid_plot):
            raise ValueError("No valid matched position or velocity errors were produced.")
        fixed_position = (
            valid_position
            & (matched_status == 1)
            & (q_left == 1)
            & (q_right == 1)
        )
        fixed_velocity = (
            valid_velocity
            & (matched_status == 1)
            & (q_left == 1)
            & (q_right == 1)
        )

        elapsed = matched_time - matched_time[0]
        groups = [
            ("position_m", "fixed", error_east[fixed_position], error_north[fixed_position], error_up[fixed_position]),
            ("position_m", "all", error_east[valid_position], error_north[valid_position], error_up[valid_position]),
            ("velocity_mps", "fixed", error_ve[fixed_velocity], error_vn[fixed_velocity], error_vu[fixed_velocity]),
            ("velocity_mps", "all", error_ve[valid_velocity], error_vn[valid_velocity], error_vu[valid_velocity]),
        ]

        output_dir.mkdir(parents=True, exist_ok=True)
        trajectory_outputs = plot_horizontal_trajectory(
            ins_enu[:, 0],
            ins_enu[:, 1],
            classes,
            categories,
            output_dir / "navigation_trajectory_by_status",
            figure_core,
        )
        time_outputs = plot_position_time(
            (ins_time - ins_time[0]),
            ins_enu[:, 0],
            ins_enu[:, 1],
            ins_enu[:, 2],
            classes,
            categories,
            output_dir / "navigation_time_by_status",
            figure_core,
        )
        error_outputs = plot_error_time(
            elapsed[valid_plot],
            (
                error_east[valid_plot],
                error_north[valid_plot],
                error_up[valid_plot],
            ),
            (
                error_ve[valid_plot],
                error_vn[valid_plot],
                error_vu[valid_plot],
            ),
            matched_classes[valid_plot],
            categories,
            output_dir / "navigation_error_time",
            figure_core,
        )

        statistics_rows, statistics_csv, statistics_md = write_error_statistics(
            output_dir, groups
        )
        sample_data = {
            "elapsed_s": elapsed[valid_plot],
            "gps_week": ins_data[matched_mask, 0][valid_plot].astype(int),
            "sow_s": ins_data[matched_mask, 1][valid_plot],
            "ins_status": matched_status[valid_plot],
            "rtk_q_left": q_left[valid_plot],
            "rtk_q_right": q_right[valid_plot],
            "rtk_match_gap_s": matched_gap[valid_plot],
            "error_east_m": error_east[valid_plot],
            "error_north_m": error_north[valid_plot],
            "error_up_m": error_up[valid_plot],
            "error_2d_m": np.sqrt(
                error_east[valid_plot] ** 2 + error_north[valid_plot] ** 2
            ),
            "error_3d_m": np.sqrt(
                error_east[valid_plot] ** 2
                + error_north[valid_plot] ** 2
                + error_up[valid_plot] ** 2
            ),
            "error_ve_mps": error_ve[valid_plot],
            "error_vn_mps": error_vn[valid_plot],
            "error_vu_mps": error_vu[valid_plot],
            "error_v2d_mps": np.sqrt(
                error_ve[valid_plot] ** 2 + error_vn[valid_plot] ** 2
            ),
            "error_v3d_mps": np.sqrt(
                error_ve[valid_plot] ** 2
                + error_vn[valid_plot] ** 2
                + error_vu[valid_plot] ** 2
            ),
        }
        samples_csv = write_error_samples(output_dir, sample_data)

        status_counts = {
            category: int(np.count_nonzero(classes == category))
            for category in categories
        }
        summary = {
            "status": "success",
            "ins_insplot": str(ins_path),
            "gnss_rtkplot": str(rtk_path),
            "output_dir": str(output_dir),
            "origin": {
                "latitude_deg": origin_lat,
                "longitude_deg": origin_lon,
                "height_m": origin_height,
            },
            "ins_rows": int(ins_data.shape[0]),
            "rtk_rows": int(rtk_data.shape[0]),
            "matched_rows": int(np.count_nonzero(valid_plot)),
            "position_matched_rows": int(np.count_nonzero(valid_position)),
            "velocity_matched_rows": int(np.count_nonzero(valid_velocity)),
            "fixed_matched_rows": int(np.count_nonzero(fixed_position | fixed_velocity)),
            "fixed_position_rows": int(np.count_nonzero(fixed_position)),
            "fixed_velocity_rows": int(np.count_nonzero(fixed_velocity)),
            "max_match_gap_seconds": args.max_match_gap,
            "max_rtk_gap_seconds": args.max_rtk_gap,
            "max_rtk_speed_mps": args.max_rtk_speed,
            "rtk_velocity_median_mps": (
                float(np.median(finite_speed)) if finite_speed.size else None
            ),
            "rtk_velocity_peak_mps": (
                float(np.max(finite_speed)) if finite_speed.size else None
            ),
            "velocity_reference": "RTK ECEF position differentiated within same-Q continuous segments and rotated to ENU",
            "error_sign": "INS minus RTK",
            "status_counts": status_counts,
            "malformed": {
                "ins_insplot": int(ins["malformed"]),
                "gnss_rtkplot": int(rtk["malformed"]),
            },
            "outputs": {
                "trajectory": [str(path) for path in trajectory_outputs],
                "position_time": [str(path) for path in time_outputs],
                "error_time": [str(path) for path in error_outputs],
                "error_statistics_csv": str(statistics_csv),
                "error_statistics_markdown": str(statistics_md),
                "error_samples_csv": str(samples_csv),
            },
            "statistics_rows": statistics_rows,
        }
        summary_path = output_dir / "navigation_analysis_summary.json"
        summary_path.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(json.dumps({"status": "success", "summary": str(summary_path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
