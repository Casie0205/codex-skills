# Outline and document splitting

## 目录

- [1. Structure snapshot](#1-structure-snapshot)
- [2. Table-of-contents convention](#2-table-of-contents-convention)
- [3. Placement decision](#3-placement-decision)
- [4. Structural recalculation](#4-structural-recalculation)
- [5. Document splitting](#5-document-splitting)
- [6. Merge and cross-reference rules](#6-merge-and-cross-reference-rules)
- [7. Anti-patterns](#7-anti-patterns)

## 1. Structure snapshot

Before editing a maintained document, identify:

- the document purpose in one sentence;
- its primary reader and use case;
- the existing title hierarchy;
- sections that duplicate or overlap;
- sections that no longer fit the title;
- unresolved or draft markers;
- inbound links and the nearest project index when one exists.

Read the entire document when practical. For a very large file, at minimum read the
title, status block, table of contents, every heading, and the sections adjacent to the
change.

## 2. Table-of-contents convention

Place the table of contents after the title and a short status or metadata block, and
before the first introductory paragraph:

```markdown
# Document title

状态：初稿。

## 目录

- [1. Current problem](#1-current-problem)
- [2. Investigation](#2-investigation)
  - [2.1 Environment](#21-environment)
- [3. Results](#3-results)
- [4. Open issues](#4-open-issues)
```

Rules:

- Every top-level content section must appear in the table of contents.
- Keep the material between the title and the table of contents to at most six
  nonblank lines in no more than two short blocks.
- A title-to-TOC metadata block may use a recognized status, date, update, version,
  scope, or author prefix, or a blockquote.
- Lower-level sections should appear when readers need them for navigation.
- Omit code fences, status blocks, and the table-of-contents heading itself.
- Keep wording identical to the heading.
- Renaming a heading requires updating every internal link to its anchor.
- Use explicit HTML anchors only when the target renderer does not generate stable
  anchors from the headings.
- When a section moves to another document, replace its old entry with a pointer to the
  canonical document.

## 3. Placement decision

Choose one placement before editing:

| Relationship to existing content | Preferred action |
|---|---|
| Same question, additional evidence or detail | Add a subsection under the existing topic |
| Same topic, but the current order obscures the work | Merge related fragments and redesign that topic |
| Related topic with an independent workflow, reader, or lifecycle | Recommend a separate document and ask before splitting |
| Unrelated topic | Ask the author whether to create a new document |
| A new section would make the current document serve two unrelated purposes | Recommend a split |

Placement is not determined by the bottom of the file or the most recent edit. Search
the heading tree for the existing topic first.

## 4. Structural recalculation

Reconsider the structure whenever an addition introduces any of these conditions:

- a second independent problem or workflow;
- content that answers a different reader question;
- repeated explanations of the same mechanism;
- a section that is now larger than its parent topic;
- headings whose order no longer reflects the reading sequence;
- links that require readers to jump repeatedly between distant sections;
- unrelated update histories mixed into technical sections.

Prefer a small local reorganization when it restores a clear reading order. Rebuild the
top-level framework only when local changes cannot make the document coherent.

Do not use a fixed line count as the split criterion. Topic independence, reader goal,
ownership, update cadence, and navigation cost are stronger signals.

## 5. Document splitting

Recommend a split when:

- the proposed content can stand alone as a complete topic;
- different sections serve different readers or decisions;
- the sections change for different reasons or at different times;
- one section has become a reusable reference while another remains chronological;
- keeping the material together creates duplicated explanations or unstable links.

Before creating a separate document, ask the author unless the author already requested
the split. This includes related material that introduces an independent workflow,
reader, or maintenance lifecycle. State the proposed title, purpose, and boundary in one
short question.

When splitting:

1. Define the new document's single purpose and title.
2. Identify the exact sections that belong to it.
3. Preserve all source facts and status information during the move.
4. Add a table of contents to the new maintained document.
5. Leave a short pointer in the old document at the previous location.
6. Update the nearest documentation index when one exists; otherwise update the project
   entrypoint link.
7. Search for inbound links and update them.
8. Re-run the Markdown audit on the affected documents and any updated index or
   entrypoint.

A split is incomplete if the old document, new document, project entrypoint, and any
existing index disagree about where the canonical content lives.

## 6. Merge and cross-reference rules

- Merge duplicate material into the section that best answers the reader's question.
- Keep unique evidence, limitations, and history from each source.
- Preserve the source location when chronology or provenance matters.
- Use relative links inside a project unless an absolute path is required.
- Link to a canonical section instead of copying the same instructions again.
- When replacing a section with a pointer, state what moved and where.

## 7. Anti-patterns

Avoid these patterns:

- appending each update at the end regardless of topic;
- maintaining a table of contents that omits existing top-level sections;
- creating a new top-level section for every small note;
- nesting headings beyond the level needed by the reader;
- using duplicate headings without distinguishing anchors;
- copying the same procedure into several documents;
- splitting a document without leaving a pointer or updating the entrypoint or index
  that links to it;
- retaining dozens of stale links after renaming sections.
