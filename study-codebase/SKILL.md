---
name: study-codebase
description: Create read-only code-understanding materials for a large codebase, including a screenshot-friendly HTML study report, copy-friendly Markdown notes, a symbol index, and open questions. Use when the user wants to learn or explain one code flow rather than edit, refactor, build, or commit code.
---

# Study Codebase

## Contents

- [Purpose](#purpose)
- [Hard Boundaries](#hard-boundaries)
- [Inputs](#inputs)
- [Workflow](#workflow)
- [Evidence Rules](#evidence-rules)
- [Required Outputs](#required-outputs)
- [Report Design](#report-design)
- [Validation](#validation)
- [Completion Response](#completion-response)
- [Reference](#reference)

## Purpose

Turn one code flow into study material that a user can read, screenshot, and copy to
another computer. Optimize for understanding, not implementation. The primary reader is
the user who wants to trace the code manually after receiving the report.

Use this skill for:

- a main execution path from entrypoint to output;
- one module, subsystem, protocol decoder, or data flow;
- symbol, structure, and configuration mapping;
- onboarding notes for a large C, C++, or mixed-language repository.

Do not use it for code changes, refactoring, bug fixing, or repository-wide development.

## Hard Boundaries

- Treat the repository and all project-context paths as read-only.
- Do not create a branch, modify source, stage files, or commit.
- Write only below the task's `output_path`.
- Do not present name-based inference as source-confirmed behavior.
- Use a language service, compiler database, or build evidence for C/C++ symbols when
  available. Text search only locates candidates.
- Keep one topic per output bundle. Do not combine several independent flows into one
  long report.

## Inputs

Establish before reading code:

- repository root;
- topic name and the observable flow to explain;
- relevant entrypoint and stopping point;
- project-context documents already available;
- writable `output_path`;
- source commit or revision identifier when available.

If the repository root, topic, or output path is missing, stop and report `BLOCKED`.
If a context document conflicts with source, source wins and the difference is recorded
as `DOC-DISCREPANCY`.

## Workflow

1. Read the project entrypoint and the documents relevant to the selected flow.
2. Treat those documents as reading hypotheses. Verify behavior against the current
   source, using `cpp-code-navigation` semantics when installed.
3. Build `study-result.json` from [study-schema.md](references/study-schema.md).
4. Render the complete bundle:

```powershell
python "<skill-root>\scripts\render_study_bundle.py" `
  --input "<output_path>\study-result.json" `
  --output-root "<output_path>"
```

5. Inspect the generated HTML and Markdown. Confirm that paths, line references, and
   open questions agree with the source.
6. Report the artifacts and any unresolved evidence gap.

## Evidence Rules

Use exactly three confidence values:

| Value | Meaning |
| --- | --- |
| `confirmed` | Current source path and line identify the behavior. |
| `inferred` | Evidence supports the statement, but the exact control path is not proven. |
| `open` | Source, configuration, runtime data, or semantic evidence is missing. |

For every material step:

- cite repository-relative `path:line`;
- state caller, callee, inputs, outputs, and externally visible state changes;
- record normal and error branches when present;
- identify the next function or file the user should read;
- keep uncertain claims out of the `confirmed` section.

Do not dump whole source files. Quote only the minimum line or expression needed to
explain the behavior.

## Required Outputs

The renderer writes these files under `output_path`:

```text
study-result.json
study-report.html
study-note.md
symbol-index.csv
questions.md
```

`study-result.json` is the structured evidence source. The other four files are
generated from it and must not contain independent facts.

## Report Design

The HTML is for browser screenshots:

- one self-contained file with no external CSS, JavaScript, fonts, images, or network
  dependency;
- page width around 1120 pixels;
- selectable text and wrapped code blocks;
- no horizontal scrolling;
- primary content expanded by default;
- each flow step kept in one screenshot-sized block where practical;
- separate flows and diagrams; do not combine all topics into one visual.

The Markdown is for copying:

- table of contents immediately after the title;
- stable numbered headings;
- paths and line references kept as plain text;
- no content hidden only in the HTML.

## Validation

Run the bundled renderer tests after changing the renderer:

```powershell
python -B "<skill-root>\scripts\test_render_study_bundle.py"
```

Before completion, verify:

- all five required files exist;
- the HTML contains the topic ID and source revision;
- the HTML is at least 5000 bytes;
- there are no unresolved template markers;
- no `http://` or `https://` asset dependency exists;
- Markdown table-of-contents links resolve;
- every `confirmed` item has a source location.

The report is `DONE` only when the source flow and evidence are complete enough to read.
Use `PARTIAL` when the report is usable but named evidence, semantic navigation, or
runtime confirmation is missing. Use `BLOCKED` when the source or required output path
cannot be accessed.

## Completion Response

```text
STATUS: DONE | PARTIAL | BLOCKED
TOPIC: <topic_id>
SOURCE: <repository and revision>
OUTPUT: <output_path>
FILES: <generated files>
EVIDENCE: <main verified reading path>
OPEN: <open evidence gaps or none>
NEXT: <one concrete code location to read next or none>
DOC-DISCREPANCY: none | <confirmed difference>
```

## Reference

- [study-schema.md](references/study-schema.md): required JSON fields, optional
  sections, evidence rules, and a complete example.
