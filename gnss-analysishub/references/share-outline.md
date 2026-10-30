# Share Outline

Use this outline for a 20 to 30 minute internal sharing session.

## Title

`基于 AnalysisHub 与 AnalysisHub-CLI 的 GNSS 原始数据分析 Skill`

## Slide 1: Why this matters

- GNSS analysis workflows are fragmented
- GUI is strong for exploration but weak for standardization
- CLI is strong for automation but hard for non-experts
- We need an AI entry layer that understands the workflow

## Slide 2: What problem the Skill solves

- Input recognition
- Workflow routing
- Command assembly
- Output interpretation
- Support-facing summary generation

## Slide 3: Architecture

User request -> Skill -> AnalysisHub / AnalysisHub-cli -> report / plot / table -> AI explanation

## Slide 4: Current tool capability map

- `qc obscheck`
- `qc diff-epoch`
- `qc triple-epoch`
- `qc residual`
- `qc short-residual`
- `qc merge-reports`
- `report health`
- `report rtk`
- `plot`

Also highlight:

- GUI path supports current-mode `QC / DF / TF` health report behavior
- CLI health path is currently QC-style on the exposed command surface

## Slide 5: Skill design

- file pattern recognition
- route selection
- tool execution
- result explanation

## Slide 6: Demo 1

- recognize artifacts in a real sample folder
- decide valid routes

## Slide 7: Demo 2

- use CLI to generate a QC health report
- explain the result like a human analyst

## Slide 8: Demo 3

- explain why GUI mode-following DF / TF health matters
- show that the Skill knows the difference between GUI and CLI capabilities

## Slide 9: Packaging and release

- Skill source is maintained separately
- release bundle is published under `Release\codex-skills`
- installer script updates the local Codex skill directory
- later versions can be upgraded with the same entrypoint

## Slide 10: Takeaway

- This is not a new GNSS algorithm
- This is a new usability layer over existing GNSS capability
- The result is faster onboarding, more standard operation, and more reusable expertise

## Closing line

`把会用 AnalysisHub 的个人经验，沉淀成所有人都能调用的 Skill。`
