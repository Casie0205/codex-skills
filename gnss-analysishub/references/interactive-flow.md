# Interactive Flow

Use this reference when the user does not give a full task, only a path or a vague request.

## Target experience

Desired user flow:

1. User gives a data path and says: `先分析下这个数据`
2. Skill inspects the directory
3. Skill asks only the missing high-value questions
4. Skill runs the right `AnalysisHub` or `AnalysisHub-cli` workflow
5. Skill returns:
   - report path
   - AI summary
   - suggestion to open abnormal plots in `AnalysisHub` GUI

## How to react to vague requests

### Case 1: user gives a folder path

First inspect the folder with `find_gnss_artifacts.ps1`.

Then respond in this order:

- say what artifacts were recognized
- say what workflows are available
- ask only the unresolved question

Recommended question pattern:

```text
这个目录里我已经识别到 QC / DF / TF / DataList 这些产物。你这次希望我先走哪条分析：
1. 快速 QC 体检
2. DF 模式分析
3. TF 模式分析
4. 先做结果判断和总结
```

If the user has not specified decode type and the workflow needs it, ask:

```text
这个数据你希望按什么解码类型处理？如果没有特殊要求，我默认按当前工具常用的 RINEX 数据流程走。
```

### Case 2: user gives a single file

If it is a raw observation or RINEX-like input:

- ask whether the user wants:
  - single-station QC
  - diff-epoch
  - triple-epoch
  - residual analysis if a baseline pair is involved
  - ionosphere analysis if the user is asking about ionosphere directly

Additional guardrails for single-file QC:

- If the file is not clearly a supported observation input, ask the user to choose the supported input type before `obscheck`.
- Ask only the missing high-value QC settings:
  - elevation mask, default `7°`
  - slip strategy: `fast`, `doppler-assisted`, or `strict`

English fallback question:

```text
Before I run single-file QC, please confirm the supported input type, the elevation mask in degrees, and the slip strategy. If you do not specify them, I will use single-station QC, 7 degrees, and the fast slip strategy.
```

Suggested question:

```text
这个文件可以走单站质检、历元间双差、历元间三差，或者电离层分析。你这次想先看哪种模式？如果只是先看整体质量，我建议先做单站质检。
```

### Case 3: user gives a QC HTML or report folder

Do not ask decode type again.

Ask only whether they want:

- a quick AI summary
- a health report
- a rebuilt one-click combined report if the folder already contains `DataList/QC/arlog/pos` artifacts
- GUI deep dive for abnormal plots

### Case 4: user asks for PPP-SSR, ionosphere, or observation compare

- If the user already asked for ionosphere and provided a rover file, route to `AnalysisHub-cli iono` unless they explicitly want GUI interaction.
- If the user provides an existing `IonosphereIndex_Ant0.txt/.log` or `Ionosatinfodatalist.log/.txt`, route to `AnalysisHub-cli report iono`.
- If the user already asked for PPP-SSR and provided a log file, route to `AnalysisHub-cli ssr` for headless loss analysis, or `PPP-SSR...` in the GUI when interactive chart review matters.
- If the user provides multiple `DataList.log` files and wants cross-file observation comparison, recommend `AnalysisHub-cli report obs-compare`.
- If the folder already contains a rover `DataList.log` plus `.arlog` and the user wants a refreshed one-click summary, recommend `AnalysisHub-cli report auto-combined`.

## Default recommendation logic

When several valid routes exist, use this recommendation order:

1. `QC health` for first-pass overview
2. `ctclib auto` when the user wants one-click combined output from rover/base or single-file raw input
3. `report auto-combined` when the required one-click artifacts already exist and only the report needs refresh
4. `iono` when the user explicitly asks for ionosphere analysis
5. `ssr` when the user explicitly asks for PPP-SSR / packet-loss analysis
6. `DF` when the user is focused on diff precision or epoch-to-epoch stability
7. `TF` when the user explicitly wants triple-epoch analysis

## Default deliverable after processing

After the workflow completes, always return these three layers:

### Layer 1: output

- report file path
- key PNG or CSV paths if they exist

### Layer 2: summary

- overall conclusion
- main anomaly category
- main time window
- suggested next inspection target

### Layer 3: handoff

If the user may want to inspect plots:

```text
如果你要继续看异常图、切 DF/TF、看 PPP-SSR 交互图，或者进入残差/电离层工具，我可以直接帮你转到 AnalysisHub GUI。
```

## Guardrails

- Ask fewer questions, not more
- Only ask what cannot be inferred
- If the folder already clearly supports a good default route, recommend it first
- Never pretend GUI-only behavior is already fully available in CLI
- Do not describe `survey` or `tool` as fully supported headless CLI commands in the current build
- After the first-pass analysis, always give the user a next-step option instead of stopping at the report path
