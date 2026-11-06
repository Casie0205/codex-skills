from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from rtkplot_data import (
    RtkDataset,
    RtkPlotError,
    choose_origin,
    enu_from_llh,
    plottable_samples,
)

PLOT_TYPES = ("trajectory", "position", "sigma", "quality")
COLORS = (
    "#0072B2",
    "#D55E00",
    "#009E73",
    "#CC79A7",
    "#E69F00",
    "#56B4E9",
    "#F0E442",
    "#000000",
)


def _relative_time(time_s: float, common_start_s: float) -> float:
    return time_s - common_start_s


def _configure_figure(fig: plt.Figure, title: str | None) -> None:
    fig.subplots_adjust(top=0.90, bottom=0.09, left=0.10, right=0.97, hspace=0.34)
    if title:
        fig.text(0.5, 0.975, title, ha="center", va="top", fontsize=12)


def _place_legend(fig: plt.Figure, handles: Sequence[Line2D], labels: Sequence[str]) -> None:
    if not handles:
        return
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.005),
        ncol=min(4, len(handles)),
        frameon=False,
        fontsize=9,
    )


def _set_time_axis(ax: Axes) -> None:
    ax.set_xlabel("Time since common start [s]")
    ax.grid(True, alpha=0.25, linewidth=0.6)


def _plot_trajectory(
    datasets: Sequence[RtkDataset],
    origin: tuple[float, float, float],
    title: str | None,
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(9.2, 7.2))
    handles: list[Line2D] = []
    labels: list[str] = []

    for index, dataset in enumerate(datasets):
        samples = plottable_samples(dataset)
        if not samples:
            continue
        points = [
            enu_from_llh(
                sample.lat_rad,
                sample.lon_rad,
                sample.h_m,
                origin[0],
                origin[1],
                origin[2],
            )
            for sample in samples
        ]
        color = COLORS[index % len(COLORS)]
        ax.plot(
            [point.east_m for point in points],
            [point.north_m for point in points],
            color=color,
            linewidth=1.2,
            label=dataset.name,
        )
        ax.scatter(
            [points[0].east_m],
            [points[0].north_m],
            color=color,
            marker="o",
            s=20,
            zorder=3,
        )
        handles.append(Line2D([0], [0], color=color, linewidth=1.2))
        labels.append(dataset.name)

    if not handles:
        plt.close(fig)
        raise RtkPlotError("no plottable RTKFIX/RTKFLOAT/SINGLE positions")

    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("East [m]")
    ax.set_ylabel("North [m]")
    ax.grid(True, alpha=0.25, linewidth=0.6)
    _configure_figure(fig, title)
    _place_legend(fig, handles, labels)
    return fig


def _position_series(
    dataset: RtkDataset,
    origin: tuple[float, float, float],
) -> tuple[list[float], list[float], list[float], list[float]]:
    samples = plottable_samples(dataset)
    times = [sample.time_s for sample in samples]
    points = [
        enu_from_llh(
            sample.lat_rad,
            sample.lon_rad,
            sample.h_m,
            origin[0],
            origin[1],
            origin[2],
        )
        for sample in samples
    ]
    return (
        times,
        [point.east_m for point in points],
        [point.north_m for point in points],
        [point.up_m for point in points],
    )


def _plot_position(
    datasets: Sequence[RtkDataset],
    origin: tuple[float, float, float],
    common_start_s: float,
    title: str | None,
) -> plt.Figure:
    fig, axes = plt.subplots(3, 1, figsize=(10.0, 9.0), sharex=True)
    handles: list[Line2D] = []
    labels: list[str] = []
    labels_y = ("East [m]", "North [m]", "Up [m]")

    for dataset_index, dataset in enumerate(datasets):
        times, east, north, up = _position_series(dataset, origin)
        if not times:
            continue
        values = (east, north, up)
        color = COLORS[dataset_index % len(COLORS)]
        relative_times = [_relative_time(value, common_start_s) for value in times]
        for axis, series in zip(axes, values):
            axis.plot(relative_times, series, color=color, linewidth=1.0)
        handles.append(Line2D([0], [0], color=color, linewidth=1.1))
        labels.append(dataset.name)

    if not handles:
        plt.close(fig)
        raise RtkPlotError("no plottable RTKFIX/RTKFLOAT/SINGLE positions")

    for axis, ylabel in zip(axes, labels_y):
        axis.set_ylabel(ylabel)
        axis.grid(True, alpha=0.25, linewidth=0.6)
    _set_time_axis(axes[-1])
    _configure_figure(fig, title)
    _place_legend(fig, handles, labels)
    return fig


def _plot_sigma(
    datasets: Sequence[RtkDataset],
    common_start_s: float,
    title: str | None,
) -> plt.Figure:
    fig, axes = plt.subplots(3, 1, figsize=(10.0, 9.0), sharex=True)
    handles: list[Line2D] = []
    labels: list[str] = []
    labels_y = ("Latitude sigma [m]", "Longitude sigma [m]", "Height sigma [m]")
    value_getters = (
        lambda sample: sample.sigma_lat_m,
        lambda sample: sample.sigma_lon_m,
        lambda sample: sample.sigma_h_m,
    )

    for dataset_index, dataset in enumerate(datasets):
        samples = plottable_samples(dataset)
        if not samples:
            continue
        color = COLORS[dataset_index % len(COLORS)]
        relative_times = [_relative_time(sample.time_s, common_start_s) for sample in samples]
        for axis, getter in zip(axes, value_getters):
            values = [getter(sample) for sample in samples]
            axis.plot(relative_times, values, color=color, linewidth=1.0)
        handles.append(Line2D([0], [0], color=color, linewidth=1.1))
        labels.append(dataset.name)

    if not handles:
        plt.close(fig)
        raise RtkPlotError("no plottable solution samples")

    for axis, ylabel in zip(axes, labels_y):
        axis.set_ylabel(ylabel)
        axis.grid(True, alpha=0.25, linewidth=0.6)
    _set_time_axis(axes[-1])
    _configure_figure(fig, title)
    _place_legend(fig, handles, labels)
    return fig


def _plot_quality(
    datasets: Sequence[RtkDataset],
    common_start_s: float,
    title: str | None,
) -> plt.Figure:
    fig, axes = plt.subplots(3, 1, figsize=(10.0, 9.0), sharex=True)
    handles: list[Line2D] = []
    labels: list[str] = []
    labels_y = ("Satellites", "Differential age [s]", "PDOP")
    value_getters = (
        lambda sample: sample.num_svs,
        lambda sample: sample.diff_age_s,
        lambda sample: sample.pdop,
    )

    for dataset_index, dataset in enumerate(datasets):
        samples = dataset.samples
        color = COLORS[dataset_index % len(COLORS)]
        relative_times = [_relative_time(sample.time_s, common_start_s) for sample in samples]
        for axis, getter in zip(axes, value_getters):
            values = [getter(sample) for sample in samples]
            axis.plot(relative_times, values, color=color, linewidth=0.9)
        handles.append(Line2D([0], [0], color=color, linewidth=1.1))
        labels.append(dataset.name)

    for axis, ylabel in zip(axes, labels_y):
        axis.set_ylabel(ylabel)
        axis.grid(True, alpha=0.25, linewidth=0.6)
    _set_time_axis(axes[-1])
    _configure_figure(fig, title)
    _place_legend(fig, handles, labels)
    return fig


def output_paths(output_base: Path, formats: Sequence[str]) -> list[Path]:
    stem = output_base
    if stem.suffix.lower() in {".svg", ".png"}:
        stem = stem.with_suffix("")
    return [Path(f"{stem}.{extension}") for extension in formats]


def render_plot(
    datasets: Sequence[RtkDataset],
    plot_type: str,
    output_base: Path,
    formats: Sequence[str],
    title: str | None,
    overwrite: bool,
) -> list[Path]:
    if plot_type not in PLOT_TYPES:
        raise RtkPlotError(f"unsupported plot type: {plot_type}")

    targets = output_paths(output_base, formats)
    existing = [path for path in targets if path.exists()]
    if existing and not overwrite:
        joined = ", ".join(str(path) for path in existing)
        raise RtkPlotError(f"output already exists; pass --overwrite to replace: {joined}")

    origin_sample = choose_origin(datasets[0])
    origin = (origin_sample.lat_rad, origin_sample.lon_rad, origin_sample.h_m)
    common_start_s = min(dataset.samples[0].time_s for dataset in datasets)

    if plot_type == "trajectory":
        fig = _plot_trajectory(datasets, origin, title)
    elif plot_type == "position":
        fig = _plot_position(datasets, origin, common_start_s, title)
    elif plot_type == "sigma":
        fig = _plot_sigma(datasets, common_start_s, title)
    else:
        fig = _plot_quality(datasets, common_start_s, title)

    created: list[Path] = []
    try:
        for path in targets:
            path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(path, dpi=180, bbox_inches="tight")
            if not path.exists() or path.stat().st_size == 0:
                raise RtkPlotError(f"failed to create non-empty output: {path}")
            created.append(path)
    finally:
        plt.close(fig)
    return created
