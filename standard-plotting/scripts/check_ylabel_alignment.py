#!/usr/bin/env python3
"""Verify that rendered y-axis labels are centered on their axes."""

from __future__ import annotations

import matplotlib.pyplot as plt

from figure_core import (
    add_aligned_ylabels,
    configure_style,
    create_figure,
    style_axis,
)


def check_rows(row_count: int) -> None:
    configure_style()
    figure, axes = create_figure(
        row_count,
        legend_scope="figure",
        external_ylabels=True,
    )
    labels = [f"North velocity error {index} (m/s)" for index in range(row_count)]
    for row, axis in enumerate(axes[:, 0]):
        style_axis(axis, panel_letter=chr(ord("a") + row))
    texts = add_aligned_ylabels(figure, axes, labels)
    renderer = figure.canvas.get_renderer()
    deltas = []
    for axis, text in zip(axes[:, 0], texts, strict=True):
        axes_box = axis.get_window_extent(renderer)
        text_box = text.get_window_extent(renderer)
        delta = (
            text_box.y0
            + 0.5 * text_box.height
            - axes_box.y0
            - 0.5 * axes_box.height
        )
        deltas.append(abs(delta))
    plt.close(figure)
    if max(deltas) > 0.5:
        raise RuntimeError(f"{row_count}-row y-label alignment failed: {deltas}")
    print(f"{row_count} rows: maximum vertical center error {max(deltas):.6f} px")


def main() -> int:
    check_rows(1)
    check_rows(2)
    check_rows(3)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
