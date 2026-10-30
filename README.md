# Codex Skills

Custom Codex skills maintained in this repository.

## Skills

| Skill | Purpose |
| --- | --- |
| [`academic-report`](academic-report/SKILL.md) | Create and revise print-ready academic-style HTML progress reports with figures, tables, and A4 print output. |
| [`gnss-analysishub`](gnss-analysishub/SKILL.md) | Support GNSS conversion, QC, AnalysisHub processing, plotting, reports, and troubleshooting. |
| [`humanizer`](humanizer/SKILL.md) | Rewrite AI-sounding prose while preserving facts, data, and the writer's intended meaning. |

## Installation

Copy the required skill directory into the local Codex skills directory:

```powershell
Copy-Item -Recurse .\academic-report "$HOME\.codex\skills\academic-report"
```

Keep the `SKILL.md` file in each skill root. Optional `agents`, `assets`, `references`, and `scripts` directories should remain beside it.

## Validation

Use the skill-creator validator for each skill:

```powershell
python "$HOME\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .\academic-report
```

The `humanizer` directory includes its own MIT license. Other skills do not declare a separate license.
