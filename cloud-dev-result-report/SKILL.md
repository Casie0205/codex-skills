---
name: cloud-dev-result-report
description: Generate a self-contained, screenshot-friendly HTML report from a verified cloud code-development result bundle. Use after result.md, changed files, verification logs, patch, and review evidence exist; do not use it to replace or invent raw evidence.
---

# Cloud Development Result Report

## Contents

- [Inputs](#inputs)
- [Workflow](#workflow)
- [Report Contract](#report-contract)
- [Status Rules](#status-rules)
- [Outputs](#outputs)

Create one readable HTML report from the completed `cloud-code-delivery` result bundle so a
user can inspect or screenshot the actual development outcome without copying text from the
cloud computer.

## Inputs

Read only from the task's `output_path` and the verified repository state:

- `result.md`
- `changed-files.txt`
- `verification.log`
- `cloud-code.patch` when `change_set: code`
- `review.md` when available
- `git show --stat`, selected `git diff`, and current `git status`

Do not use console claims that are absent from these artifacts. Redact secrets, tokens,
credentials, private keys, and unrelated user data.

## Workflow

Requires Python 3.8 or newer and uses only the standard library.

1. Read [report-schema.md](references/report-schema.md).
2. Build `<output_path>\development-result.json` from verified evidence. Use `unknown` or an
   empty list when a field cannot be established; do not guess.
3. Render the report:

```powershell
python "<skill-root>\scripts\render_result_report.py" `
  --input "<output_path>\development-result.json" `
  --output "<output_path>\development-result.html" `
  --output-root "<output_path>"
```

4. Confirm the HTML exists, is at least 5000 bytes, contains the task ID and status, and has
   no unresolved template markers.
5. Open `development-result.html` in a browser when available and check that tables, long
   paths, code blocks, and status badges do not overlap or clip.

When changing the renderer, run:

```powershell
python -B "<skill-root>\scripts\test_render_result_report.py"
```

## Report Contract

The HTML must show, in this order:

1. task ID, title, status, repository, branch, commits, and finish time;
2. requested outcome and implemented outcome;
3. data flow and module boundaries;
4. changed files, diff summary, removed obsolete paths, and selected key diffs;
5. acceptance criteria and build, test, and runtime verification with command, exit code,
   result, and evidence;
6. code-review findings and their resolution;
7. risks, not-verified items, next action, and document discrepancies;
8. source artifacts used to generate the report.

Keep the report self-contained. Do not add external CSS, JavaScript, fonts, images, iframes,
or network dependencies. Keep one report per task and write it only under `output_path`.

## Status Rules

- The report status must exactly match `result.md`.
- `DONE` requires committed task changes, at least one acceptance criterion and one
  verification record, and every acceptance/verification result must be `PASS` with exit
  code `0`.
- `PARTIAL` must name every failed or unverified acceptance item.
- `BLOCKED` must name the missing input, environment issue, unsafe Git state, or uncommitted
  code that caused the stop.
- A failed command must never be presented as passing. Preserve its actual exit code and key
  error text.

## Outputs

Required:

- `development-result.json`: evidence source for the report.
- `development-result.html`: self-contained screenshot-friendly report.

Optional:

- `development-result.png`: only when a local browser or rendering tool is already available.

Add generated files to the final `FILES` field. If report generation fails after the code and
result bundle are otherwise complete, report `PARTIAL`, omit only the files that were not
actually generated, and record the renderer command, error, and missing artifact in
`result.md`, `verification.log`, and the final `NOT VERIFIED` field.
