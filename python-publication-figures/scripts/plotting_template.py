from __future__ import annotations

from pathlib import Path
from typing import Literal

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


MM_PER_INCH = 25.4
A4_WIDTH_MM = 210.0
FIGURE_WIDTH_IN = (A4_WIDTH_MM * 2.0 / 3.0) / MM_PER_INCH

PANEL_HEIGHT_IN = 1.62
PANEL_GAP_IN = 0.38
TOP_MARGIN_IN = 0.70
BOTTOM_MARGIN_IN = 0.62


def configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": ["Times New Roman", "SimSun"],
            "font.size": 9,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "axes.unicode_minus": False,
            "mathtext.fontset": "stix",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "axes.linewidth": 0.8,
        }
    )


def calculate_figure_height(
    nrows: int,
    legend_scope: Literal["figure", "subplot"],
) -> float:
    if nrows < 1:
        raise ValueError("nrows must be at least 1")

    gap_in = 0.58 if legend_scope == "subplot" else PANEL_GAP_IN
    height_in = (
        TOP_MARGIN_IN
        + BOTTOM_MARGIN_IN
        + nrows * PANEL_HEIGHT_IN
        + max(0, nrows - 1) * gap_in
    )
    return max(height_in, 3.4)


def create_figure(
    nrows: int,
    legend_scope: Literal["figure", "subplot"],
) -> tuple[plt.Figure, np.ndarray]:
    height_in = calculate_figure_height(nrows, legend_scope)
    fig, axes = plt.subplots(
        nrows=nrows,
        ncols=1,
        figsize=(FIGURE_WIDTH_IN, height_in),
        sharex=nrows > 1,
        squeeze=False,
    )
    axes = axes[:, 0]

    fig.subplots_adjust(
        left=0.225,
        right=0.975,
        bottom=0.095,
        top=0.935 if legend_scope == "subplot" else 0.92,
        hspace=0.88 if legend_scope == "subplot" else 0.42,
    )
    return fig, axes


def style_axis(
    ax: plt.Axes,
    panel_letter: str,
    xlabel: str | None,
) -> None:
    if xlabel:
        ax.set_xlabel(xlabel, labelpad=4)
    ax.tick_params(
        axis="both",
        which="major",
        direction="out",
        length=3.0,
        width=0.8,
        pad=3,
    )
    ax.grid(True, color="0.75", linewidth=0.45, alpha=0.45)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_linewidth(0.8)

    ax.text(
        0.012,
        0.982,
        f"({panel_letter})",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        fontfamily="Times New Roman",
        zorder=10,
    )


def add_aligned_ylabels(
    fig: plt.Figure,
    axes: np.ndarray,
    labels: list[str],
    x_position: float = 0.045,
) -> None:
    for ax, label in zip(axes, labels, strict=True):
        position = ax.get_position()
        fig.text(
            x_position,
            position.y1,
            label,
            rotation=90,
            ha="right",
            va="center",
            rotation_mode="anchor",
            fontsize=9,
        )


def add_subplot_legend(ax: plt.Axes, legend_columns: int) -> None:
    handles, labels = ax.get_legend_handles_labels()
    if not handles:
        return
    ax.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.015),
        ncol=min(legend_columns, len(handles)),
        frameon=False,
        borderaxespad=0,
        handlelength=2.4,
        columnspacing=1.3,
    )


def add_figure_legend(
    fig: plt.Figure,
    entries: list[tuple[str, str]],
    legend_columns: int,
) -> None:
    handles = [
        Line2D([0], [0], color=color, linewidth=1.2, label=label)
        for label, color in entries
    ]
    fig.legend(
        handles=handles,
        labels=[entry[0] for entry in entries],
        loc="lower center",
        bbox_to_anchor=(0.5, 0.962),
        ncol=min(legend_columns, len(handles)),
        frameon=False,
        borderaxespad=0,
        handlelength=2.4,
        columnspacing=1.3,
    )


def save_figure(
    fig: plt.Figure,
    output_base: Path,
    dpi: int = 300,
) -> list[Path]:
    output_base.parent.mkdir(parents=True, exist_ok=True)
    png_path = output_base.with_suffix(".png")
    svg_path = output_base.with_suffix(".svg")
    fig.savefig(png_path, dpi=dpi, bbox_inches=None, pad_inches=0)
    fig.savefig(svg_path, bbox_inches=None, pad_inches=0)
    return [png_path, svg_path]


def draw_with_subplot_legends(output_dir: Path) -> list[Path]:
    configure_style()
    time_s = np.linspace(0.0, 120.0, 240)
    figure, axes = create_figure(3, legend_scope="subplot")

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

    for index, (ax, series, ylabel) in enumerate(
        zip(axes, panel_series, ylabels, strict=True)
    ):
        for label, color, values in series:
            ax.plot(time_s, values, color=color, linewidth=1.2, label=label)
        style_axis(
            ax,
            panel_letter=chr(ord("a") + index),
            xlabel="时间 (s)" if index == len(axes) - 1 else None,
        )
        add_subplot_legend(ax, legend_columns=2)

    add_aligned_ylabels(figure, axes, ylabels)
    outputs = save_figure(figure, output_dir / "subplot_legends")
    plt.close(figure)
    return outputs


def draw_with_figure_legend(output_dir: Path) -> list[Path]:
    configure_style()
    time_s = np.linspace(0.0, 120.0, 240)
    figure, axes = create_figure(2, legend_scope="figure")
    entries = [
        ("主天线", "#1f77b4"),
        ("副天线", "#d95f02"),
    ]

    series = [
        [
            0.9 * np.sin(time_s / 19.0),
            0.7 * np.cos(time_s / 23.0),
        ],
        [
            0.18 * np.sin(time_s / 14.0),
            0.13 * np.cos(time_s / 16.0),
        ],
    ]
    ylabels = ["位置 (m)", "速度 (m/s)"]

    for index, (ax, panel_values, ylabel) in enumerate(
        zip(axes, series, ylabels, strict=True)
    ):
        for value, (_, color) in zip(panel_values, entries, strict=True):
            ax.plot(time_s, value, color=color, linewidth=1.2)
        style_axis(
            ax,
            panel_letter=chr(ord("a") + index),
            xlabel="时间 (s)" if index == len(axes) - 1 else None,
        )

    add_figure_legend(figure, entries, legend_columns=2)
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
