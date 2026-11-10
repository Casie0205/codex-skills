---
name: standard-plotting
description: Default skill for all charts and figures unless the user explicitly requests another visual system. Creates stable Matplotlib layouts with fixed width, external legends, no titles, Chinese/English publication fonts, and SVG/PNG output.
---

# Standard Plotting

## Contents

- [Workflow](#workflow)
- [Invariants](#invariants)
- [Resources](#resources)

Use this skill as the default plotting workflow for every chart or figure request:
time series, diagnostics, comparison plots, multi-panel report figures, and
presentation-ready plots. Use another plotting system only when the user explicitly
requests it. The fixed layout, legends, typography, and export rules below remain in
force across report, paper, analysis, and presentation contexts.

## Workflow

1. Resolve the input data and confirm the plotted columns, units, and time basis. If
   NavPlot positions are stored as latitude/longitude/height and the requested plot is a
   metric displacement, run `scripts/convert_navplot_enu.py` first.
2. Read [references/figure-spec.md](references/figure-spec.md) before creating or
   changing a multi-panel figure.
3. Start from [scripts/plotting_template.py](scripts/plotting_template.py). Preserve its
   sizing, typography, legend placement, and panel-label helpers unless the user asks
   for a different visual system.
4. Do not add a figure-level title. Put units in the relevant axis labels.
5. Choose exactly one legend mode:
   - all panels share the same legend: one legend above the whole figure;
   - panels need different legends: one legend above each panel.
   Write legend labels in Chinese by default. Keep Latin text only for units,
   special symbols, or model and product names that should not be translated.
6. Export one SVG and one PNG per figure. Do not use `bbox_inches="tight"`.
7. Verify files, dimensions, fonts, clipping, legend placement, axis units, and panel labels before
   reporting success.

File names and directory structure identify the figure; do not repeat that information
as an in-figure title.

## Invariants

- Figure width is `2/3` of A4 width, exactly `140 mm`.
- Do not create a figure for a few simple counts or one scalar. Use prose or a table unless the visual reveals a trend, distribution, relationship, or another non-obvious pattern.
- Never use raw latitude/longitude columns as metric E/N coordinates.
- Panels stack vertically by default.
- Legends stay outside the axes and are the topmost visual element.
- Legend labels are Chinese by default; units, special symbols, and untranslated
  model or product names are the exceptions.
- Each panel has only an `(a)`, `(b)`, `(c)` label at its upper-left corner.
- Do not add figure-level titles or panel titles.
- Chinese text uses SimSun; Latin text, numbers, and panel labels use Times New Roman.
- Every y-axis label includes its unit, for example `位置 (m)`.
- Vertical y-axis labels are centered on the axes height.
- Horizontal y-label placement follows the leftmost rendered tick label with a
  small fixed gap; do not use a fixed figure-wide x coordinate.
- Each figure is an independent output with SVG and PNG variants.

## Resources

- [references/figure-spec.md](references/figure-spec.md): complete layout, typography,
  legend, axis-label, output, and validation contract.
- `scripts/figure_core.py`: shared implementation for size, style, panels, legends,
  and export.
- `scripts/plotting_template.py`: tested runnable template covering both legend modes.
- `scripts/convert_navplot_enu.py`: converts NavPlot latitude/longitude/height to local
  ENU metres and writes a CSV ready for plotting.
