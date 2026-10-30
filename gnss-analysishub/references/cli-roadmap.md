# CLI Roadmap

Use this reference when discussing how to reduce the barrier further by enriching `AnalysisHub-cli`.

## Design goal

The current CLI already exposes professional commands such as:

- `qc obscheck`
- `qc diff-epoch`
- `qc triple-epoch`
- `qc residual`
- `qc short-residual`
- `qc merge-reports`
- `ctclib app`
- `ctclib post`
- `ctclib auto`
- `iono`
- `ssr`
- `report health`
- `report rtk`
- `report obs-compare`
- `plot`

These are good building blocks, but they are still expert-facing. To lower the barrier, add task-level wrappers above them.

## Recommended next commands

### `analyse <path>`

Purpose:

- Accept a folder or file path
- Detect available artifacts
- Recommend the best first-pass route
- Optionally run the route directly

Suggested output:

- recognized artifacts
- available routes
- recommended route
- missing prerequisites

### `doctor <path>`

Purpose:

- Explain what can be done with the path
- Explain what is missing
- Stop before running analysis

Suggested use:

- first-touch triage
- novice-facing diagnosis
- skill follow-up questions

### `health <path>`

Purpose:

- Accept a path instead of forcing the caller to pass `qc_html` and `datalist` manually
- Resolve `_QC.html`, `_DF.html`, `_TF.html`, `DataList.log`, `.DF`, `.TF` when possible
- Route to `current` CLI behavior or `future` richer behavior

Important:

- In the current implementation, full DF/TF mode-following health is still GUI-led.
- This wrapper should be explicit about `current` vs `future`.

### `summarize <report>`

Purpose:

- Convert generated report artifacts into a normalized summary
- Return machine-friendly text or JSON for Skill consumption

Suggested summary fields:

- overall conclusion
- major anomalies
- affected systems / satellites / frequencies
- suggested next action

### `plot-hints <path-or-report>`

Purpose:

- Recommend which abnormal plots should be checked next
- Map anomalies to likely plot files and GUI modes

Suggested output:

- anomaly type
- recommended file
- recommended mode
- recommended chart focus

## Output shape recommendation

For all future task-level commands, prefer a stable structured output with these fields:

- `status`
- `recognized_inputs`
- `available_routes`
- `selected_route`
- `outputs`
- `summary`
- `next_step`

## Skill alignment

These wrappers matter because they let the Skill stay simple:

- the CLI decides what is technically possible
- the Skill decides how to ask, explain, and hand off

That split keeps the logic easier to maintain across future releases.
