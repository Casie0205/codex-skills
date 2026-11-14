---
name: external-report
description: Create client-ready technical reports with an academic paper layout, conclusion-first writing, protected parameter values, and direct raw-data evidence.
---

# External Report

Use this skill when the intended reader is a customer, partner, or other external stakeholder. The report explains what problem was found, how it was resolved, and what evidence supports the conclusion. It is not an internal work log.

## Workflow

1. **Establish the client decision.** Read the supplied records, outputs, screenshots, and acceptance criteria. State the problem, impact, current result, and remaining risk before drafting.
2. **Choose the report structure.** Read [references/report-blueprint.md](references/report-blueprint.md). Use two to four sections built around findings and outcomes.
3. **Create the page.** For a new report, run:

   ```bash
   python scripts/init_report.py <output-directory> \
     --title "<report title>" \
     --subtitle "<one-sentence client-facing scope>" \
     --author "<author>" \
     --period "<YYYY-MM>"
   ```

   Preserve the bundled paper layout, typography, responsive behavior, and A4 print rules.
4. **Select direct evidence.** Read [references/client-delivery.md](references/client-delivery.md) and [references/figures-and-print.md](references/figures-and-print.md). Show one or two figures that make the issue visible, then provide the original complete data row at the relevant location when data handling is questioned.
5. **Protect parameters.** Omit confidential or customer-specific parameter values. Replace tuning grids with relative ratios or ranges, such as "about 50-100 times the common configuration", unless exact values are explicitly approved for release.
6. **Write for the customer.** Lead with what was found and fixed. Keep internal work history, tool inventory, exploratory branches, and analysis narration out of the main text. Apply `$humanizer:humanizer` in embedded mode before final validation.
7. **Validate.** Run:

   ```bash
   python scripts/validate_report.py <report-directory>/index.html
   ```

   Inspect desktop, narrow screen, and A4 print output. Check that comparisons preserve proportions and the reader never has to zoom a figure to understand the claim.

## Non-Negotiables

- Keep the current academic paper layout: white surface, single content column, numbered sections, full-width figures, captions below figures, and print-safe tables.
- Default to the `humanizer:humanizer` skill for all report prose.
- State conclusions in customer terms. Describe what was found, its impact, what changed, and whether it is resolved.
- Keep the opening summary free of internal sample counts, event counts, file counts, and implementation metrics. Put exact audit counts in the evidence sections and retain only the few numbers needed for the customer decision.
- Do not expose exact proprietary tuning values, configuration snippets, tuning grids, or implementation-specific thresholds. Use relative ranges and the resulting behavior.
- Do not expose device brands or model names in customer-facing content or delivery assets unless release is explicitly approved. This includes headings, body text, captions, alt text, linked files, and image or data filenames. Use functional labels instead; in Chinese reports, use "参考 IMU" rather than a model identifier.
- Support data-quality conclusions with direct evidence: one or two intuitive plots plus a screenshot or excerpt of the complete original record row. Never show only a cropped field when the reader may question how the source record was interpreted.
- Use figures only when they reveal a pattern that prose or a table cannot express as clearly. Simple counts and single values remain in text or tables.
- For low-dimensional, discrete, or few-option comparisons, prefer a compact table. Do not use a simple bar chart when a heatmap, interval or dot plot, aligned time series, or table carries more information.
- Give every figure one explicit reader question. Remove figures that only restate a count, a small table, or another figure.
- Structure each conclusion summary as tiered points: core conclusion, supporting evidence, then limitations or exceptions. Keep confirmed evidence, reasonable inference, and unresolved questions separate.
- Keep residual risks and validation limits near the relevant conclusion.

## Resources

- [references/report-blueprint.md](references/report-blueprint.md): customer-facing section design and evidence order.
- [references/client-delivery.md](references/client-delivery.md): parameter confidentiality, source-data evidence, conclusion-first writing, and final checks.
- [references/figures-and-print.md](references/figures-and-print.md): figure selection, raw-data screenshots, captions, and A4 rules.
- `assets/report-starter/`: validated academic-style HTML, CSS, and print script.
- `scripts/init_report.py`: copy and initialize the report starter.
- `scripts/validate_report.py`: validate references, IDs, placeholders, alt text, and print image height.
