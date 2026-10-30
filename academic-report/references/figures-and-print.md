# Figures and Print

Use this reference when selecting charts, generating figures, placing screenshots, or preparing the A4 print version.

## Source Selection

Prefer the latest processed output over an older screenshot. Confirm that the asset hash, timestamp, and metric labels match the current result.

Store copied web assets under the report's `assets/` directory. Keep original outputs in the project output directory. If a plot must be regenerated, keep the plotting script in the report project or the relevant analysis project.

Use separate output files for separate plots. Do not build a single plotting function that only works when every figure is emitted together unless the workflow genuinely requires it.

## Plot Standards

- Put the legend outside the axes, normally above the plotting area.
- Include units in axes and legends.
- Use consistent font sizes large enough for A4 printing.
- Prefer vector outputs for line plots when available; export PNG when the web page needs it.
- For SVG charts, keep the canvas background transparent. Remove full-size white or paper-colored background rectangles before embedding the file.
- Avoid unnecessary chart titles when the figure caption already names the plot.
- Keep axis scales honest. Label logarithmic scales.
- State duration, sample count, and selection rules in the caption.
- Use color to separate methods only when the mapping remains clear.

## Multi-Panel Figures

Combine plots into one figure when they answer one technical question:

- overview plus one representative event;
- global context plus local detail;
- original signal plus corrected signal plus residual;
- related comparisons that must be read together.

Use `(a)`, `(b)`, `(c)` labels and one figure caption. Keep labels large enough after A4 scaling. The combined figure should fit one printed page whenever possible.

Do not combine unrelated metrics merely to reduce figure count.

## Figure HTML

```html
<figure class="figure-card is-full">
  <div class="figure-media">
    <img src="../assets/result.png" alt="结果图的准确描述">
  </div>
  <figcaption>
    <strong>图题</strong>
    <span>样本量、时间范围、关键数值和必要的限制。</span>
  </figcaption>
</figure>
```

Do not add a fixed height to `.figure-media` or the image. Use `width: 100%; height: auto`.

## Table HTML

```html
<div class="table-wrap" data-title="精度统计">
  <table class="data-table">
    <thead>
      <tr><th>指标</th><th class="num">结果</th><th>说明</th></tr>
    </thead>
    <tbody>
      <tr><td>水平 RMS</td><td class="num">2.126 mm</td><td>固定解，10 h 静态数据。</td></tr>
    </tbody>
  </table>
</div>
```

The `data-title` value becomes the table title. Numeric columns use `.num` so decimal alignment and whitespace remain stable.

## A4 Print Rules

- Page: A4 portrait.
- Content width: about 170 mm with 20 mm side margins.
- Body text: normally 9.5-10.5 pt.
- Single-column layout.
- Screen navigation, print buttons, copy controls, and screen-only notes are hidden.
- Figures preserve their aspect ratio.
- Avoid an image that prints taller than 245 mm at the content width; the caption and page spacing also need room.
- Keep figure captions with their images and table titles with their tables.
- Do not rely on horizontal scrolling in print.
- Do not edit the generated PDF to fix clipping. Correct the HTML/CSS and print again.

## Visual QA

Check all three views:

1. Desktop: structure, figure resolution, caption placement.
2. Narrow screen: text wrapping, table overflow, title fit.
3. Print media or A4 preview: hidden controls, page breaks, figure scale, table width.

Use screenshots or a PDF page render for inspection. Do not assume that a successful page load means the printed layout is correct.
