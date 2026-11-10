from __future__ import annotations

from pathlib import Path

import numpy as np
from matplotlib.lines import Line2D

from figure_core import (
    add_aligned_ylabels,
    add_shared_legend,
    add_subplot_legend,
    configure_style,
    create_figure,
    save_figure,
    style_axis,
)

import matplotlib.pyplot as plt


def draw_with_subplot_legends(output_dir: Path) -> list[Path]:
    configure_style()
    time_s = np.linspace(0.0, 120.0, 240)
    figure, axes = create_figure(
        3,
        legend_scope="subplot",
        external_ylabels=True,
    )
    axes = axes[:, 0]

    panel_series = [
        [
            ("东向位置", "#1f77b4", 2.0 * np.sin(time_s / 18.0)),
            ("北向位置", "#d95f02", 1.4 * np.cos(time_s / 22.0)),
        ],
        [
            ("东向速度", "#1b9e77", 0.20 * np.sin(time_s / 15.0)),
            ("北向速度", "#7570b3", 0.15 * np.cos(time_s / 17.0)),
        ],
        [
            ("横滚角", "#e7298a", 0.8 * np.sin(time_s / 20.0)),
            ("俯仰角", "#66a61e", 0.5 * np.cos(time_s / 24.0)),
        ],
    ]
    ylabels = ["位置 (m)", "速度 (m/s)", "姿态 (deg)"]

    for index, (axis, series, _) in enumerate(
        zip(axes, panel_series, ylabels, strict=True)
    ):
        for label, color, values in series:
            axis.plot(time_s, values, color=color, linewidth=1.2, label=label)
        style_axis(
            axis,
            panel_letter=chr(ord("a") + index),
            xlabel="时间 (s)" if index == len(axes) - 1 else None,
        )
        add_subplot_legend(axis, legend_columns=2)

    add_aligned_ylabels(figure, axes, ylabels)
    outputs = save_figure(figure, output_dir / "subplot_legends")
    plt.close(figure)
    return outputs


def draw_with_figure_legend(output_dir: Path) -> list[Path]:
    configure_style()
    time_s = np.linspace(0.0, 120.0, 240)
    figure, axes = create_figure(
        2,
        legend_scope="figure",
        external_ylabels=True,
    )
    axes = axes[:, 0]
    entries = [
        ("主天线", "#1f77b4"),
        ("副天线", "#d95f02"),
    ]
    series = [
        [0.9 * np.sin(time_s / 19.0), 0.7 * np.cos(time_s / 23.0)],
        [0.18 * np.sin(time_s / 14.0), 0.13 * np.cos(time_s / 16.0)],
    ]
    ylabels = ["位置 (m)", "速度 (m/s)"]

    for index, (axis, panel_values) in enumerate(
        zip(axes, series, strict=True)
    ):
        for value, (_, color) in zip(panel_values, entries, strict=True):
            axis.plot(time_s, value, color=color, linewidth=1.2)
        style_axis(
            axis,
            panel_letter=chr(ord("a") + index),
            xlabel="时间 (s)" if index == len(axes) - 1 else None,
        )

    handles = [
        Line2D([0], [0], color=color, linewidth=1.2, label=label)
        for label, color in entries
    ]
    add_shared_legend(
        figure,
        handles,
        [label for label, _ in entries],
        legend_columns=2,
    )
    add_aligned_ylabels(figure, axes, ylabels)
    outputs = save_figure(figure, output_dir / "figure_legend")
    plt.close(figure)
    return outputs


def main() -> int:
    output_dir = Path(__file__).resolve().parent / "output"
    outputs = [
        *draw_with_subplot_legends(output_dir),
        *draw_with_figure_legend(output_dir),
    ]
    for path in outputs:
        if not path.exists() or path.stat().st_size == 0:
            raise RuntimeError(f"Invalid output: {path}")
        print(f"{path} ({path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
