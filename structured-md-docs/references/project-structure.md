# Project documentation structure

## 目录

- [1. Entry points](#1-entry-points)
- [2. Index maintenance](#2-index-maintenance)
- [3. Creating and naming documents](#3-creating-and-naming-documents)
- [4. Cross-links and canonical locations](#4-cross-links-and-canonical-locations)
- [5. Status and history](#5-status-and-history)
- [6. Personal and evolving notes](#6-personal-and-evolving-notes)

## 1. Entry points

Use a root `AGENTS.md` when the project needs a stable instruction and navigation
entrypoint. Keep it concise and point to the documents that matter.

A common structure is:

```text
AGENTS.md
docs/
|-- README.md
|-- architecture.md
|-- debugging/
|   |-- README.md
|   `-- issue-001.md
`-- reports/
    `-- README.md
```

This is not a required tree. A small project can use a root entrypoint and a few direct
links. Add `docs/README.md` and nested indexes when they reduce lookup cost.

For project-level work, read in this order:

```text
AGENTS.md -> nearest documentation index, if any -> target document -> linked evidence
```

If the project has no index, follow direct links from `AGENTS.md` or the documented
project entrypoint.

## 2. Index maintenance

If the project has an index, update it when a document is added, renamed, split,
archived, or moved. Create an index when the number of maintained documents makes direct
links from the entrypoint difficult to navigate.

An index should state:

- its scope;
- the documents it contains;
- the recommended reading order;
- current status when statuses exist;
- links to parent and child indexes.

Do not list empty or planned documents as if they already contain information.

## 3. Creating and naming documents

- Give each document one primary purpose.
- Prefer a name that states the topic rather than the edit date.
- Follow the project's existing date, language, and directory conventions.
- Keep raw source records separate from synthesized conclusions.
- Ask before creating a new document when the connection to existing content is weak,
  or when the split would change the current document's reader goal or lifecycle.
- Do not create a new file for a small subsection that fits an existing topic.

## 4. Cross-links and canonical locations

- Maintain one canonical section for each fact, procedure, or decision.
- Link from related documents instead of duplicating substantial content.
- Use relative links for project files.
- Update inbound links after a rename or split.
- Leave a short pointer when content moves.
- Check the old path, new path, project entrypoint or index, and table of contents
  together.

The audit script verifies local link targets, but only the author can decide whether the
linked content is semantically correct.

## 5. Status and history

Preserve any existing document status system. If none exists, use only the minimum
needed to avoid confusion, such as draft, active, or superseded.

Do not turn a draft into a final document without explicit evidence or author approval.
Do not rewrite historical decisions to match a later state. Supersede and link instead.

## 6. Personal and evolving notes

For personal logs, temporary records, and project diaries:

- keep the raw chronological record;
- create synthesized summaries separately;
- preserve source paths, dates, parameters, and open questions;
- use a table of contents in every maintained document;
- promote a recurring or independently useful topic into a dedicated document;
- leave a link from the summary to the source record when traceability matters.

The existence of an empty source folder or missing local session record does not prove
that no work occurred.
