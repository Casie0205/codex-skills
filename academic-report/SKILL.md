---
name: academic-report
description: "Create and revise print-ready academic-style HTML progress reports and PPT-conversion reports, with quantitative figures and tables, consistent layouts, and A4 or slide output."
---

# Academic Report

Build reports as complete, evidence-led documents. The default deliverable is a static HTML report that reads like an academic paper and prints cleanly to A4. Use this design unless the user explicitly asks for a different visual system.

## Outcome

A finished report should:

- present the actual work, measurements, outputs, and remaining risks;
- use one clear technical narrative rather than a dashboard or slide deck;
- place complete figures and useful tables in reading order;
- remain readable on desktop, narrow screens, and A4 paper;
- separate confirmed results from pending validation;
- be ready to print without editing the PDF afterward.

## Workflow

1. **Audit the evidence.** Read the supplied work records, logs, output files, code paths, figures, and existing notes. Record exact counts, units, time ranges, denominators, rates, and validation status.
2. **Define the technical structure.** Group work by question or result, not by file count or the order in which files were produced. Use two to four main sections. Read [references/report-blueprint.md](references/report-blueprint.md) before drafting a new report.
3. **Create the page.** For a new report, run:

   ```bash
   python scripts/init_report.py <output-directory> \
     --title "<report title>" \
     --subtitle "<one-sentence scope>" \
     --author "<author>" \
     --period "<YYYY-MM>"
   ```

   The starter copies the validated report CSS, print script, and generic HTML shell. Do not initialize over an existing report unless replacement is explicitly requested.
4. **Build the evidence set.** Reuse existing outputs first. If a required plot is missing, regenerate it from the checked data with a separate reproducible script. Follow [references/figures-and-print.md](references/figures-and-print.md).
5. **Write the report.** Lead with quantitative findings. Keep background short and keep the current work dominant. Follow [references/writing-and-delivery.md](references/writing-and-delivery.md).
6. **Validate.** Run:

   ```bash
   python scripts/validate_report.py <report-directory>/index.html
   ```

   Resolve missing references, duplicate IDs, unresolved placeholders, omitted alt text, and images that cannot fit the intended print width.
7. **Inspect rendered output.** Check desktop, a narrow viewport, and print media or an A4 preview. Confirm that images are uncropped, tables remain aligned, captions follow their objects, and screen-only controls disappear in print.
8. **Deliver only what was requested.** Publish the HTML and supporting assets first. Generate the PDF when the user asks for it or after the page version is approved.

## Design Invariants

- Use a white paper surface inside a restrained surrounding page, with one centered content column.
- Use serif type for body text and report titles; reserve sans-serif for navigation, labels, code, and numeric callouts.
- Use numbered main sections and, when needed, descriptive subsections. Do not mix multiple competing section systems.
- Do not show implementation or page-verification status in report metadata. Include work status only when it changes how the reader should interpret the results.
- Keep figures single-column and full-width. Preserve the original aspect ratio; never place a graph inside a fixed-height viewport that clips it.
- Do not create a figure for a few simple counts or a single scalar when prose or a table communicates the result more directly. Use figures when the visual reveals a trend, distribution, relationship, spatial pattern, or nontrivial comparison.
- Put figure captions below the image and table titles above the table. Let the CSS number them automatically.
- Give a figure caption title and its explanatory text the same font family, size, and color. Keep only the title bold; use regular weight for the explanation.
- Put figure legends outside the plot area, normally above it.
- When several event plots answer the same question, combine them into one multi-panel figure with `(a)`, `(b)`, `(c)` labels and one caption.
- Keep captions quantitative. State what is shown, the sample size or duration, the key result, and any limitation needed to interpret it.
- Use one compact key-metrics row near the summary. The metrics must be outputs, not restated targets.
- Use screen-only navigation and print controls. They must be hidden by `@media print`.
- Do not present the page as a collection of floating cards. Use prose, rules, tables, and uninterrupted figure bands.
- Do not use direct PDF editing to repair layout. Fix the HTML/CSS and print again.

## PPT Conversion

When the report will be converted into PPT or shown as slides:

- Omit slide numbers, page counters, footer labels, source paths, generation dates, validation records, and other production metadata from every slide.
- Keep provenance, data paths, collection dates, and caveats in an accompanying Markdown file, README, or speaker notes instead of visible slide text.
- Use one idea per 16:9 page and keep content inside the page without relying on browser navigation, footers, or hover states.
- Inspect the print export page by page and confirm that no footer labels, page numbers, paths, or metadata remain.
- Do not treat a paper-style report page as a PPT cover. Use the supplied presentation template or a dedicated slide cover when one is available.

## Writing Rules

- State the main result early. Every paragraph after that must add a fact, interpretation, or limitation.
- Use active, concrete language. Prefer direct verbs such as completed, checked, corrected, generated, and verified.
- Include units and the measurement basis whenever a number appears.
- Explain why an analysis was performed and what decision it supports.
- Mark incomplete work plainly, including who has been informed and what remains.
- Do not include assessment weights, bottom lines, target thresholds, or other information already fixed in an external form unless the user explicitly asks to discuss them.
- Do not write submission instructions such as "paste directly into the progress tracker".
- Do not describe the document itself or how the page was assembled.
- Do not use decorative bold labels, forced triads, one-line summary closers, or em dashes.
- When existing figures use old numbers, use those numbers only to identify the source object. Renumber the final report in reading order.

## Resources

- [references/report-blueprint.md](references/report-blueprint.md): section design, evidence mapping, and the GNSS/INS-derived page blueprint.
- [references/figures-and-print.md](references/figures-and-print.md): plotting, subfigure, table, screenshot, and A4 rules.
- [references/writing-and-delivery.md](references/writing-and-delivery.md): summary and caption wording, status handling, validation, and delivery.
- `assets/report-starter/`: self-contained HTML/CSS/JS starter.
- `scripts/init_report.py`: copy and initialize the starter.
- `scripts/validate_report.py`: validate references, IDs, placeholders, figure count, and print image height.
