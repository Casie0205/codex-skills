---
name: python-publication-figures
description: Create publication-ready Matplotlib figures for reports and papers, especially A4 two-thirds-width vertical panels with external legends, Chinese/English publication fonts, and SVG/PNG output.
---

# Python Publication Figures

Use Matplotlib for report and paper figures when layout, typography, legends, and panel
labels must remain stable after export.

## Workflow

1. Resolve the input data and confirm the plotted columns, units, and time basis. If
   NavPlot positions are stored as latitude/longitude/height and the requested plot is a
   metric displacement, run `scripts/convert_navplot_enu.py` first.
2. Read [references/figure-spec.md](references/figure-spec.md) before creating or
   changing a multi-panel figure.
3. Start from [scripts/plotting_template.py](scripts/plotting_template.py). Preserve its
   sizing, typography, legend placement, and panel-label helpers unless the user asks
   for a different visual system.
4. Choose exactly one legend mode:
   - all panels share the same legend: one legend above the whole figure;
   - panels need different legends: one legend above each panel.
5. Export one SVG and one PNG per figure. Do not use `bbox_inches="tight"`.
6. Verify files, dimensions, fonts, clipping, legend placement, and panel labels before
   reporting success.

## Invariants

- Figure width is `2/3` of A4 width, exactly `140 mm`.
- Do not create a figure for a few simple counts or one scalar. Use prose or a table unless the visual reveals a trend, distribution, relationship, or another non-obvious pattern.
- Never use raw latitude/longitude columns as metric E/N coordinates.
- Panels stack vertically by default.
- Legends stay outside the axes.
- Each panel has only an `(a)`, `(b)`, `(c)` label at its upper-left corner.
- Do not add a figure-level title or panel titles.
- Chinese text uses SimSun; Latin text, numbers, and panel labels use Times New Roman.
- Vertical y-axis labels are top-aligned and must not overlap tick labels.
- Each figure is an independent output with SVG and PNG variants.

## Resources

- [references/figure-spec.md](references/figure-spec.md): complete layout, typography,
  legend, axis-label, output, and validation contract.
- `scripts/plotting_template.py`: tested runnable template covering both legend modes.
- `scripts/convert_navplot_enu.py`: converts NavPlot latitude/longitude/height to local
  ENU metres and writes a CSV ready for plotting.
