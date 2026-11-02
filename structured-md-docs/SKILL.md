---
name: structured-md-docs
description: "Create, revise, restructure, audit, and maintain Markdown documentation for software and data projects, especially documents that grow incrementally. Use when table-of-contents design, placement of new material, section reorganization, document splitting, cross-links, AGENTS.md, or docs indexes matter. Do not use for generic prose polishing or non-Markdown office documents."
metadata:
  short-description: "Structure-first Markdown documentation maintenance"
---

# Structured Markdown docs

## 目录

- [Core rule](#core-rule)
- [Workflow](#workflow)
- [Placement and splitting](#placement-and-splitting)
- [Evidence and preservation](#evidence-and-preservation)
- [Document types](#document-types)
- [Project documentation](#project-documentation)
- [Validation](#validation)
- [Final response](#final-response)

Build and maintain Markdown documents as navigable structures, not append-only text
collections. Preserve the author's facts and intent while choosing where new material
belongs.

## Core rule

Before editing, inspect the complete heading tree and table of contents. Re-evaluate
the document framework for every substantive addition. Do not append new material
without deciding whether it belongs in an existing section, requires reorganization,
or should become a separate document.

Every maintained document must have a table of contents:

- Put a table of contents immediately after the title and any short metadata or status
  block.
- Put it before the first introductory content paragraph.
- Link every top-level content section. Include lower-level sections when they help
  navigation.
- Update the table of contents whenever headings are added, removed, renamed, moved,
  or split into another document.
- Keep the table of contents synchronized with the actual heading anchors.

Auto-generated or disposable scratch documents may skip the table of contents. Do not
manually maintain generated documents; edit their source instead.

## Workflow

1. Identify the operation: create, update, reorganize, split, audit, or synchronize
   project documentation.
2. Read the target document and, for project-level work, the nearest `AGENTS.md` and
   documentation index when one exists. Use the project entrypoint when no index exists.
   Read only files relevant to the task.
3. Record the existing title hierarchy, table of contents, section scope, links, and
   document status before editing.
4. Build a short placement decision: existing subsection, new subsection, structural
   reorganization, or separate document.
5. Edit with the smallest change that keeps one subject in one canonical location.
6. Update the table of contents, cross-links, and the nearest index when the project
   uses one before validation.
7. Run the audit script from [scripts/audit_markdown.py](scripts/audit_markdown.py).
8. Review the result manually for factual accuracy, structural fit, and unsupported
   claims.

## Placement and splitting

Use [references/outline-and-split.md](references/outline-and-split.md) before adding a
substantive section, merging scattered material, or splitting a document.

- Put new content in the existing section that answers the same question.
- Reorganize when the current hierarchy no longer makes the document easy to navigate.
- Keep one canonical copy of a fact, procedure, or decision. Link to it from related
  sections instead of repeating it.
- If the new material has little meaningful connection to the current document, ask
  the author whether to create a new document.
- If the content is related but would give the document a second reader goal,
  maintenance lifecycle, or independent workflow, recommend a split and ask before
  creating the new document unless the author already requested that split.
- After an approved split, preserve the original material, leave a pointer in the old
  location, and update all indexes and inbound links.

## Evidence and preservation

- Read logs, code, data descriptions, outputs, and prior notes before drafting factual
  content. Do not invent results, completion states, paths, commands, versions, or
  citations.
- Distinguish confirmed results, observations, inference, drafts, and unresolved work.
- Preserve code fences, commands, identifiers, paths, numbers, units, and link targets
  unless the user asks to change them.
- Prefer merging and relocating existing content over rewriting it. Never silently
  discard historical evidence or unresolved issues.
- Match the language of the user and the existing document. For Chinese technical
  writing, use direct statements and concrete evidence; avoid decorative headings,
  inflated conclusions, and generic summary language.

## Document types

Use [references/document-types.md](references/document-types.md) when choosing the
structure for a new document or when an existing document no longer matches its type.
It covers technical notes, debug records, work summaries, design documents, decisions,
README files, API references, and release notes.

Do not force a template when the document already has a coherent purpose-specific
structure.

## Project documentation

Use [references/project-structure.md](references/project-structure.md) when creating or
changing `AGENTS.md`, `docs/README.md`, topic indexes, cross-document links, or a
multi-document knowledge base.

For simple personal or single-file projects, a root entrypoint and direct links are
enough. Update an existing index whenever its documents move or split. Create a new
index only when multi-document navigation needs one.

## Validation

Read [references/validation.md](references/validation.md) before finalizing substantial
new or reorganized documentation.

Run:

```bash
python "<absolute-path-to-skill>/scripts/audit_markdown.py" <file-or-directory>
```

Resolve `<absolute-path-to-skill>` from the location of this `SKILL.md`, not from the
target project's working directory. Use `--strict` when warnings should fail the check.
Use `--no-require-toc` only for generated or disposable documents. The script performs
deterministic checks; it does not prove factual correctness or good topic boundaries.

## Final response

Briefly report:

- files changed;
- the structural decision and any document split;
- validation commands and results;
- unresolved evidence, links, or structural questions.

Do not describe routine tool usage or paste the entire document back to the user.
