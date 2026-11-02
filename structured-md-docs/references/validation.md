# Validation and final report

## 目录

- [1. Deterministic audit](#1-deterministic-audit)
- [2. Structural review](#2-structural-review)
- [3. Evidence review](#3-evidence-review)
- [4. Link and index review](#4-link-and-index-review)
- [5. Final report](#5-final-report)

## 1. Deterministic audit

Run the bundled script:

```bash
python "<absolute-path-to-skill>/scripts/audit_markdown.py" <file-or-directory>
python "<absolute-path-to-skill>/scripts/audit_markdown.py" <file-or-directory> --strict
```

Resolve the script path from this skill directory, not from the target project's
working directory.

The script checks:

- a missing or duplicated top-level title;
- missing tables of contents for maintained documents with content headings;
- stale table-of-contents anchors and omitted top-level headings;
- tables of contents placed after introductory content;
- heading-level jumps and excessive heading depth;
- unbalanced code fences and fences without a language;
- broken relative links and unresolved local anchors;
- trailing whitespace, tab indentation, repeated blank lines, and a missing final
  newline;
- common unfinished placeholders.

Use `--json` for machine-readable output. `--strict` treats warnings as failures.

## 2. Structural review

After the automated audit, confirm manually:

- the document has one clear purpose;
- every section belongs under its current parent;
- the table of contents is directly below the title or a short status block;
- the table of contents reflects the intended reading order, not the edit history;
- duplicate sections have been merged into a canonical location;
- unrelated material has not been hidden inside an existing topic;
- a split, if used, has a clear boundary and updated navigation.

## 3. Evidence review

Confirm that the final text does not invent or overstate:

- results and completion states;
- file, data, or output paths;
- versions, parameter values, units, and counts;
- causes, conclusions, or validation status;
- citations and ownership.

Keep direct observations separate from interpretation when the distinction affects the
decision. Preserve uncertainty where the source is incomplete.

## 4. Link and index review

Check:

- the target document is reachable from the nearest index when one exists, otherwise
  from the project entrypoint;
- links from indexes, entrypoints, and related documents reach the right section;
- renamed headings have no stale anchors;
- split documents point to each other;
- old locations retain a useful pointer;
- local paths use the project's existing convention.

## 5. Final report

Keep the report short:

- files changed;
- placement or split decision;
- audit command and result;
- unresolved evidence or structural decisions.

Do not claim the document is complete when the underlying evidence is still pending.
