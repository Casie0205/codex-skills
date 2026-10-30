# Demo Script

This script is designed for a 10 to 15 minute live demo using the current sample data and the current implementation.

## Goal

Show that the Skill does three things:

1. Understands GNSS artifacts
2. Routes to the correct `AnalysisHub` or `AnalysisHub-cli` workflow
3. Explains outputs in human terms

## Recommended sample

Use this sample folder:

`D:\市场问题\MARKET-322\Sourcefile_9999323_20260420165032`

It contains:

- `_QC.html`
- `_DF.html`
- `_TF.html`
- `DataList.log`
- `.DF`
- `.TF`

## Demo flow

### Part 1: Recognize artifacts

Prompt:

```text
先识别这个目录里有哪些 GNSS 分析产物，告诉我能走哪些 AnalysisHub / AnalysisHub-cli 流程。
```

Expected talking point:

- The Skill should identify QC, DF, TF, `DataList.log`, `.DF`, and `.TF`
- It should distinguish:
  - `cli-qc-health`
  - `gui-df-health`
  - `gui-tf-health`

Supporting script:

```powershell
powershell -ExecutionPolicy Bypass -File D:\AnalysisHUB_v2\build\src\gui\Release\codex-skills\gnss-analysishub\scripts\find_gnss_artifacts.ps1 -Path D:\市场问题\MARKET-322\Sourcefile_9999323_20260420165032 -AsJson
```

### Part 2: Show CLI health route

Prompt:

```text
基于这个 _QC.html 和 DataList.log，生成数据体检报表，并总结最主要的异常项。
```

Talking point:

- Current CLI `report health` is valid for QC-style health generation
- This is the headless and batchable path

Command example:

```powershell
AnalysisHub-cli.exe --output-dir D:\市场问题\MARKET-322\Sourcefile_9999323_20260420165032\9999323_20260420165032_obs_health report health D:\市场问题\MARKET-322\Sourcefile_9999323_20260420165032\9999323_20260420165032_QC.html D:\市场问题\MARKET-322\Sourcefile_9999323_20260420165032\9999323_20260420165032_DataList.log
```

Output to mention:

- `health.html`
- `health_report.html`
- overview PNGs
- anomaly CSVs

### Part 3: Show GUI mode-following difference

Prompt:

```text
如果我切到 DF 模式再点体检报表，现在工具会走什么逻辑？和 CLI 的 report health 有什么区别？
```

Talking point:

- Current GUI follows the active result mode
- GUI can switch with `QC / DF / TF`
- DF / TF health adds precision anomaly tables for:
  - carrier precision abnormal satellite-frequency summary
  - pseudorange precision abnormal satellite-frequency summary
- Current CLI surface does not expose the same current-mode routing contract

### Part 4: Show batch merge value

Prompt:

```text
把这个目录下所有 QC HTML 合并成一张汇总表，并告诉我最适合先看的系统和频点。
```

Talking point:

- This shows the Skill is not only a command launcher
- It can also explain what to look at first

Command example:

```powershell
AnalysisHub-cli.exe qc merge-reports --dir D:\some\qc\folder -o D:\some\qc\folder\merged.xlsx
```

## Key phrases for the talk

- `算法没有变，变的是入口。`
- `GUI 解决探索，CLI 解决批量，Skill 解决可用性。`
- `AI 不是替代 GNSS 分析逻辑，而是替代人工串流程。`

## What not to claim

- Do not say current CLI fully reproduces GUI mode-following DF / TF health logic
- Do not say CLI skyplot is a true skyplot in headless mode
- Do not imply the Skill is doing GNSS computation itself
