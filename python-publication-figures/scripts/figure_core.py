"""Shared Matplotlib layout primitives for reusable figure workflows."""

from __future__ import annotations

import pickle
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


def create_figure(
    nrows: int,
    ncols: int = 1,
    *,
    sharex: bool = True,
    sharey: bool = False,
    legend_scope: Literal["figure", "subplot"] = "figure",
    panel_height_in: float = PANEL_HEIGHT_IN,
    external_ylabels: bool = False,
) -> tuple[plt.Figure, np.ndarray]:
    if nrows < 1 or ncols < 1:
        raise ValueError("nrows and ncols must be positive")
    gap_in = 0.58 if legend_scope == "subplot" else 0.38
    height_in = (
        TOP_MARGIN_IN
        + BOTTOM_MARGIN_IN
        + nrows * panel_height_in
        + max(0, nrows - 1) * gap_in
    )
    fig, axes = plt.subplots(
        nrows=nrows,
        ncols=ncols,
        figsize=(FIGURE_WIDTH_IN, max(height_in, 3.4)),
        sharex=sharex,
        sharey=sharey,
        squeeze=False,
    )
    if external_ylabels:
        left_margin = 0.225
    else:
        left_margin = 0.12 if ncols == 1 else 0.10
    fig.subplots_adjust(
        left=left_margin,
        right=0.975,
        bottom=0.16,
        top=0.88 if legend_scope == "figure" else 0.94,
        hspace=0.42,
        wspace=0.30,
    )
    return fig, axes


def style_axis(
    ax: plt.Axes,
    *,
    xlabel: str | None = None,
    ylabel: str | None = None,
    panel_letter: str | None = None,
) -> None:
    if xlabel:
        ax.set_xlabel(xlabel, labelpad=4)
    if ylabel:
        ax.set_ylabel(ylabel, labelpad=6)
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
    if panel_letter:
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


def add_shared_legend(
    fig: plt.Figure,
    handles: list[Line2D],
    labels: list[str],
    *,
    legend_columns: int | None = None,
) -> None:
    if not handles:
        return
    fig.legend(
        handles=handles,
        labels=labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.985),
        ncol=min(legend_columns or len(handles), len(handles)),
        frameon=False,
        borderaxespad=0,
        handlelength=2.4,
        columnspacing=1.3,
    )


def add_aligned_ylabels(
    fig: plt.Figure,
    axes: np.ndarray,
    labels: list[str],
    *,
    x_position: float = 0.045,
) -> None:
    for ax, label in zip(np.ravel(axes), labels, strict=True):
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


def save_figure(
    fig: plt.Figure,
    output_base: Path,
    *,
    dpi: int = 300,
    include_pickle: bool = False,
) -> list[Path]:
    output_base.parent.mkdir(parents=True, exist_ok=True)
    outputs = []
    for suffix, kwargs in (
        (".png", {"dpi": dpi}),
        (".svg", {}),
    ):
        path = output_base.with_suffix(suffix)
        fig.savefig(path, bbox_inches=None, pad_inches=0, **kwargs)
        outputs.append(path)
    if include_pickle:
        path = output_base.with_suffix(".fig")
        fig.set_visible(True)
        with path.open("wb") as handle:
            pickle.dump(fig, handle)
        outputs.append(path)
    return outputs
