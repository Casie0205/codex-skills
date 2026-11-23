---
name: chcnav-slidev-report
description: Create or edit CHCNAV internal presentations as Slidev Markdown using the packaged CHCNAV internal-report template. Use for Slidev reports, technical reviews, and internal briefings. Do not use for PowerPoint-native editing or when the user explicitly requires PPTX, PDF, or HTML deliverables.
metadata:
  short-description: Create CHCNAV Slidev reports in Markdown
---

# CHCNAV Slidev Report

Create and maintain CHCNAV internal presentations as Slidev Markdown.

## Default Output Contract

Unless the user explicitly requests another format:

- Produce or edit `slides.md`.
- Copy the packaged `theme/` directory beside it when starting a new deck.
- Keep referenced figures under the deck's `assets/` directory.
- Do not run `slidev export`, `slidev build`, or any command that writes PPTX, PDF, HTML, PNG, or another deliverable format.
- Do not add npm scripts whose purpose is exporting those formats.
- Validate by inspecting the Markdown and, when useful, starting the Slidev preview server. Do not leave the server running.

Markdown is the deliverable. Exported formats require an explicit user request.

## New Deck

Create a new deck with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\scaffold_report.ps1 `
  -Destination D:\DOC\Project\26123112_report-name
```

The script copies:

```text
slides.md
theme/
assets/
```

If either `slides.md` or `theme/` already exists, the script refuses to modify the destination. Back up or move the existing deck before scaffolding again.

## Authoring

Start from `assets/slides-template.md`. It contains the approved page patterns:

- cover
- report overview
- contents
- section divider
- default content
- two-column content
- figure-led content
- formula content
- table content
- evidence grading
- closing

Replace the sample copy and placeholder figures with user-provided facts. Keep every number, unit, status, and caveat from the source material.

Prefer native Markdown tables and KaTeX formulas. Use the theme classes already present in the template instead of inline positioning.

## Theme Changes

Read [references/design-contract.md](references/design-contract.md) before changing:

- canvas size
- title or subtitle coordinates
- fonts or colors
- background assets
- page layout geometry

Do not modify individual slides with ad hoc pixel offsets when the change belongs in the theme.

## Validation

1. Run the Markdown audit when editing long supporting Markdown:

```powershell
python "$HOME\.codex\skills\structured-md-docs\scripts\audit_markdown.py" <file>
```

2. Check that every referenced image exists.
3. Start the Slidev preview only when visual inspection is needed.
4. Confirm the final deck remains Markdown-first and no export files were created.
