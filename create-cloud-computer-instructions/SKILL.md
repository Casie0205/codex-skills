---
name: create-cloud-computer-instructions
description: Create and maintain standalone instruction documents for an external offline cloud computer, stored under D:\DOC rather than in the local Codex commands or skills directories.
---

# Create Cloud Computer Instructions

A cloud computer is an external AI environment that receives files by copying and is
usually offline. A cloud-computer Markdown file is a standalone instruction deliverable,
not a local Codex skill, command, or project document.

## Storage Rules

- Store cloud-computer instructions under `D:\DOC\<project>\`.
- Use lowercase English, digits, and hyphens in file names.
- Do not create cloud-computer instructions under `C:\Users\<user>\.codex\commands`.
- Do not create cloud-computer instructions under `C:\Users\<user>\.codex\skills`.
- A local Codex skill may define how to author these documents, but it does not replace
  the external instruction itself.
- Cloud-computer instructions must be self-contained. Do not assume access to local
  Codex skills, conversation history, command menus, or the `~/.codex` directory.

## Workflow

1. Confirm the task, cloud-computer environment, input paths, output paths, executable
   programs, and offline dependencies.
2. Inspect existing instructions for the same topic and update the canonical file
   instead of creating a duplicate.
3. Read [references/instruction-template.md](references/instruction-template.md) and
   use its document structure.
4. State prerequisites, version checks, the main execution flow, success conditions,
   failure handling, and the required completion report.
5. Make commands, paths, and code copyable. When a package is required, specify its
   copied location and integrity check.
6. Run testable code locally before delivery. Mark any unverified part explicitly.
7. Audit the Markdown for table-of-contents anchors, links, placeholders, code fences,
   and final newline.
8. Report the absolute instruction path and every adjacent package or resource.

## Boundaries

- Do not write project documentation, design notes, or work logs as cloud-computer
  instructions.
- Do not use local `$skill-name` invocation syntax in a cloud-computer document.
- Do not rely on local Codex command discovery.
- Do not reference local-only paths that the cloud computer cannot access.
- Prefer a separate copyable script or package over embedding a large algorithm in the
  instruction.

## Reference

- [references/instruction-template.md](references/instruction-template.md): required
  structure, storage rules, and delivery checklist.
