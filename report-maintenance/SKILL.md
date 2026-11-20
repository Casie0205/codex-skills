---
name: report-maintenance
description: "Modify existing technical reports while preserving user edits and Git history. Use for report content, structure, formula, table, or image changes. Default to Markdown-only output; create or update HTML/PDF only when the user explicitly requests those formats."
---

# Report Maintenance

Use this skill when changing an existing report. The current Markdown file is the
source of truth. Treat older HTML or PDF exports as read-only evidence unless the user
explicitly requests a synchronized or regenerated export.

## Output Contract

- Default to producing or editing only `.md` files and the assets they reference.
- Do not create, compile, refresh, or overwrite HTML or PDF as a side effect of a
  Markdown edit.
- If the user asks for a report update without naming a format, edit Markdown only.
- Generate HTML or PDF only after an explicit request naming that format. Do not infer
  that a preview, print check, or HTML/PDF export is wanted.
- When an explicit HTML or PDF request is made, generate that requested artifact
  without replacing the Markdown source.
- Use `$structured-md-docs` for maintained Markdown structure, table-of-contents
  synchronization, placement decisions, and strict auditing.
- Put display equations in LaTeX math blocks using `$$...$$`; use `$...$` for inline
  mathematics. Do not put formulas in `text` code fences unless the user asks for raw
  source.
- Embed report figures with Markdown image syntax such as
  `![caption](assets/figure.png)`. Keep referenced assets beside the report or at a
  stable relative path. A compiled preview must contain actual images, not only links.

## Preserve User Edits

The user may edit the Markdown at any time. On every report task:

1. Locate the containing Git repository. If none exists, initialize one at the report root before editing.
2. Record the current branch, status, staged changes, and task-file diff before
   editing.
3. Re-read the current Markdown file immediately before patching it.
4. Treat uncommitted and recently edited content as user work. Preserve unrelated
   hunks and integrate with the current text rather than replacing whole files from an
   older export.
5. If the target changed unexpectedly during the task, re-read and merge carefully
   instead of overwriting it.

Use `git diff -- <report-path>` to understand current edits. Never reconstruct a
report from memory, a stale conversion, or a clean `HEAD` version when the worktree
contains newer content.

## Git Workflow

- If the report is in a Git repository, make the requested edit, verify the current
  diff, and commit only the task files after successful validation.
- If no repository exists, run `git init -b main` in the report root. Verify that the
  repository top level is the intended report directory, not a filesystem root or a
  broader unrelated folder.
- For a newly initialized repository, commit the current report state as a baseline
  before changing report content. Include the Markdown source and the assets it needs;
  include existing HTML/CSS/scripts when they are part of the report directory and are
  needed to reproduce or inspect it.
- Stage explicit paths only with `git add -- <paths>`. Do not use `git add -A`,
  `git add .`, forced pushes, resets, clean operations, or history rewrites.
- Keep unrelated user changes unstaged and untouched.
- Do not create numbered backup copies when Git can preserve history.

## Validation

- Run the `$structured-md-docs` strict audit for every maintained Markdown report.
- If formulas changed, verify their syntax with KaTeX, MathJax, or the renderer used by
  the recipient.
- Verify that every referenced image exists. If the user explicitly asks for a compiled
  format, also verify that the rendered output contains actual `<img>` elements.
- Check the final Git diff for accidental HTML/PDF generation, unrelated formatting,
  and lost user edits.
