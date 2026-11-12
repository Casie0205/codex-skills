---
name: create-cloud-computer-instructions
description: Create and maintain standalone instruction documents for an external offline cloud computer, stored under D:\DOC rather than in the local Codex commands or skills directories.
---

# Create Cloud Computer Instructions

## Contents

- [Storage Rules](#storage-rules)
- [Workflow](#workflow)
- [Boundaries](#boundaries)
- [Reference](#reference)

A cloud computer is an external AI environment that receives files by copying and is
usually offline. A cloud-computer Markdown file is a standalone instruction deliverable,
not a local Codex skill, command, or project document.

## Storage Rules

- When the cloud computer supports skills, prefer a reusable skill package for any
  workflow that will be used repeatedly. Use a command-style Markdown document only for
  a one-off task.
- Store cloud-computer instructions under `D:\DOC\<project>\`.
- Store reusable cloud-computer skill packages under `D:\DOC\cloud-skills\<skill-name>\`.
- The standard cloud-computer skill directory is
  `C:\Users\liuziao\lingma\skills`. Copy the complete `<skill-name>` folder there
  without repacking it.
- A cloud-computer skill must contain `SKILL.md` at its root and any scripts or agents
  directories beside it.
- Skill directory names use the canonical names from the maintained skill library. When
  canonical names share a word stem, keep a unique short prefix (typically three to six
  characters) in `display_name` so the user can narrow the skill list quickly.
- Use lowercase English, digits, and hyphens in file names.
- Keep every Markdown file below 10,000 characters. Start splitting when a file exceeds
  roughly 8,000 characters.
- For a multi-file command, keep the entry file and all referenced files in the same
  cloud-computer `commands` directory. The current standard target is
  `C:\Users\liuziao\lingma\commands`.
- The entry file must list every required sibling file in read order and use relative
  links such as `[plot_style.md](plot_style.md)`.
- Do not split by arbitrary chunks. Separate purpose, style, code template, and
  validation into documents with clear responsibilities.
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
4. Check the character count of every deliverable. Split long instructions into an
   entry document plus purpose-specific referenced files before copying to the cloud
   computer.
5. State prerequisites, version checks, the main execution flow, success conditions,
   failure handling, and the required completion report.
6. Make commands, paths, and code copyable. When a package is required, specify its
   copied location and integrity check.
7. Run testable code locally before delivery. Mark any unverified part explicitly.
8. Audit the Markdown for table-of-contents anchors, links, placeholders, code fences,
   and final newline.
9. Report the absolute instruction paths and every adjacent package or resource.

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
