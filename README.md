# Codex Skills

## Contents

- [Skills](#skills)
- [Installation](#installation)
- [Validation](#validation)

Custom Codex skills maintained in this repository for company knowledge retrieval,
GNSS workflows, report generation, technical writing, Word equation conversion, and modular software development.

## Skills

| Skill | Purpose |
| --- | --- |
| [`academic-report`](academic-report/SKILL.md) | Create and revise print-ready academic-style HTML progress reports with figures, tables, and A4 print output. |
| [`build-modular-feature`](build-modular-feature/SKILL.md) | Extend existing codebases with clear module boundaries, thin entrypoints, and focused validation and review. |
| [`convert-word-equations-to-mathtype`](convert-word-equations-to-mathtype/SKILL.md) | Convert native Word OMML equations into editable inline MathType objects using a MathML-first workflow and preservation checks. |
| [`gnss-analysishub`](gnss-analysishub/SKILL.md) | Support GNSS conversion, QC, AnalysisHub processing, plotting, reports, and troubleshooting. |
| [`humanizer`](humanizer/SKILL.md) | Rewrite AI-sounding prose while preserving facts, data, and the writer's intended meaning. |
| [`starhub-mcp`](starhub-mcp/SKILL.md) | Operate CHC StarHub through MCP for connection reuse, device commands, raw saves, log inspection, and upgrade-state handling. |
| [`structured-md-docs`](structured-md-docs/SKILL.md) | Create and maintain structure-first Markdown documentation with synchronized tables of contents, deliberate content placement, and document-splitting checks. |
| [`yunxin-wiki`](yunxin-wiki/SKILL.md) | Search and read the authenticated internal Yunxin DokuWiki for company documentation, commands, message definitions, and technical references. |

## Installation

Copy the required skill directory into the local Codex skills directory:

```powershell
Copy-Item -Recurse .\academic-report "$HOME\.codex\skills\academic-report"
```

Keep the `SKILL.md` file in each skill root. Optional `agents`, `assets`, `references`, and `scripts` directories should remain beside it.

The MathType skill requires Windows, desktop Microsoft Word, and MathType 7. Its main entrypoint is `convert-word-equations-to-mathtype/scripts/mathtype_mathml_conversion/Invoke-OmmlMathMlToInlineMathTypeV2.ps1`; read its `SKILL.md` and `references/` before use. The modular-development skill provides instructions and reference checklists in `build-modular-feature/`; it has no runtime entrypoint.

## Validation

Use the skill-creator validator for each skill:

```powershell
python "$HOME\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .\academic-report
```

The `humanizer` directory includes its own MIT license. Other skills do not declare a separate license.
