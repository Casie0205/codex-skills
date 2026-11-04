---
name: navigation-output-analysis
description: Analyze NavPlot navigation output in ins_insplot.txt, including file discovery, fixed column interpretation, solution-status checks, missing-column limits, and concise evidence reporting.
---

# Navigation Output Analysis

Use this skill when the user asks to inspect or analyze a navigation run whose primary
result is `ins_insplot.txt`.

## Workflow

1. Use the user's explicit `ins_insplot.txt` path when provided. If the user gives an
   output directory, read `<output-directory>\ins_insplot.txt`.
2. If the path is unknown, check the task directory and its direct subdirectories. If
   several files match, list them and stop for confirmation.
3. Read [references/navplot-columns.md](references/navplot-columns.md) before
   interpreting values.
4. Validate the file:
   - at least seven usable columns;
   - non-empty data;
   - consistent row width;
   - valid latitude/longitude ranges;
   - non-negative and ordered GPS time after sorting.
5. Report the file path, row count, column count, time range, status distribution,
   satellite range, and missing optional columns.
6. Answer only from measured columns. If metric movement is requested, use
   `navplot-coordinate-conversion` when available instead of treating latitude and
   longitude as metres.

## Boundaries

- Do not replace `ins_insplot.txt` with `.pos`, `.navplot`, or another file unless the
  user explicitly requests it.
- Do not infer columns by value range.
- Do not treat missing optional columns as measured zeroes.
- Do not describe standard deviations as truth-referenced positioning errors.
- Do not claim velocity or attitude data from a 15-column file.
