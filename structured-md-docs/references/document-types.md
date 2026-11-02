# Document types and structures

## 目录

- [1. Selection rule](#1-selection-rule)
- [2. Technical note](#2-technical-note)
- [3. Debug or investigation record](#3-debug-or-investigation-record)
- [4. Work summary](#4-work-summary)
- [5. Design or architecture document](#5-design-or-architecture-document)
- [6. Decision record](#6-decision-record)
- [7. Project guide or README](#7-project-guide-or-readme)
- [8. API or interface reference](#8-api-or-interface-reference)
- [9. Release notes and changelogs](#9-release-notes-and-changelogs)
- [10. Incrementally extended documents](#10-incrementally-extended-documents)

## 1. Selection rule

Choose the structure from the reader's task. Do not combine several document types in
one file merely because they share a project.

If the content serves more than one reader goal, keep the primary goal in the current
document and recommend a linked document for the secondary material. Ask before creating
that document unless the author already requested it.

## 2. Technical note

Use for an explanation, experiment, format analysis, or implementation note.

Typical order:

1. question or purpose;
2. inputs, environment, and assumptions;
3. observations or implementation;
4. result and evidence;
5. limitations and open questions;
6. related paths and references.

Keep the conclusion tied to the evidence that supports it.

## 3. Debug or investigation record

Use for a live problem or a sequence of diagnostic decisions.

Typical order:

1. observed symptom;
2. scope and data;
3. hypotheses;
4. tests and parameter changes;
5. current result;
6. unresolved questions and next check.

Distinguish symptom, observation, inference, and confirmed cause. Preserve failed
attempts when they explain later decisions.

## 4. Work summary

Use for daily, weekly, monthly, or project summaries.

Typical order:

1. scope and period;
2. main workstreams;
3. measurable results;
4. problems and decisions;
5. remaining work;
6. source paths.

Group by workstream rather than by file or command. Keep raw chronological material in
the source log and link to it when provenance matters.

## 5. Design or architecture document

Use when the document defines boundaries, data flow, ownership, interfaces, or a target
implementation.

Typical order:

1. problem and scope;
2. constraints and non-goals;
3. architecture or data flow;
4. module responsibilities;
5. interfaces and data contracts;
6. failure handling;
7. validation plan;
8. migration and open decisions.

Keep the main path visible. Move historical alternatives and rejected branches into a
dedicated decision or appendix section.

## 6. Decision record

Use when the important artifact is the reason for a choice.

Typical order:

1. status and date;
2. context;
3. decision;
4. alternatives considered;
5. consequences;
6. affected paths and follow-up.

Do not rewrite a decided record to match a later implementation. Supersede it with a
new record and link both directions.

## 7. Project guide or README

Use for orientation and the shortest successful path through a project.

Typical order:

1. project purpose;
2. prerequisites;
3. install or setup;
4. primary workflow;
5. commands;
6. outputs;
7. tests and verification;
8. related docs.

Keep deep explanations in linked documents. Do not add badges, diagrams, or marketing
copy unless the author requests them.

## 8. API or interface reference

Use when readers need exact contracts.

Typical order:

1. scope and version;
2. shared types and conventions;
3. inputs;
4. outputs;
5. errors and edge cases;
6. examples;
7. compatibility notes.

Keep signatures, units, defaults, and error behavior exact.

## 9. Release notes and changelogs

Use for changes across versions or releases.

Typical order:

1. version and date;
2. user-visible changes;
3. fixes;
4. breaking changes and migration;
5. known issues.

Do not turn a changelog into a design document. Link to the design or decision when the
reason needs substantial explanation.

## 10. Incrementally extended documents

For a document that receives frequent additions:

- maintain a table of contents from the start;
- use stable, topic-specific headings;
- re-evaluate placement before every substantive addition;
- move or merge scattered fragments when a topic becomes clear;
- separate chronological evidence from synthesized conclusions;
- consider a split when a theme gains its own reader goal or maintenance lifecycle.

Do not let the physical order of edits become the reading order.
