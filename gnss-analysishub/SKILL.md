---
name: gnss-analysishub
description: Use when the user wants GNSS conversion, QC, existing-result recovery, AnalysisHub observation-score or fixed-coordinate report interpretation, auto processing, ionosphere or PPP-SSR analysis, plotting, report generation, or support-facing diagnosis based on AnalysisHub and AnalysisHub-cli.
---

# GNSS AnalysisHub

Use this skill for GNSS analysis workflows built on the current `AnalysisHub.exe` and `AnalysisHub-cli.exe` in the release bundle.

## Scope

- Folder-first artifact recognition
- Raw-message pre-analysis with message type, protocol, format, count, unit, and selection key inventory: `convert analyze`
- Batch selected-message-to-ASCII, binary, and RINEX conversion: `convert run`
- Single-station QC: `qc obscheck`
- Diff-epoch and triple-epoch QC
- Zero-baseline and short-baseline residual analysis
- One-click auto process + combined report: `ctclib auto`
- One-click combined-report rebuild from existing artifacts: `report auto-combined`
- ObsQc MP aligned one-click workflow: `ctclib auto --obsqcmp-mp`
- Ionosphere analysis: `iono`
- Ionosphere HTML report generation from `IonosphereIndex_Ant0.txt/.log` or `Ionosatinfodatalist.log/.txt`
- PPP-SSR packet-loss analysis: `ssr`
- QC-style health report generation from `_QC.html` and `DataList.log`
- RTK report generation from `_QC.html` and `DataList.log`
- Observation-quality compare reports from multiple `DataList.log`
- Evidence-based interpretation of observation-quality score reports
- Evidence-based interpretation of fixed-coordinate and auto-process combined reports
- CLI batch orchestration patterns built above leaf commands and report aggregators
- Headless plot export to PNG
- Interactive compare plotting guidance from processed result nodes
- Batch merge of QC HTML reports into Excel
- GUI recovery of QC and plot artifacts from an adjacent `Sourcefile_<input completeBaseName>` folder without rerunning QC
- GUI handoff for `Residual / Ionosphere...`, `PPP-SSR...`, and `GNSS Accuracy Tool...`
- The Pro source retains a `GNSS Accuracy Advanced...` label path, but no verified action wiring is present in the current build; do not promise it as a separate production workflow.
- Awareness that `Survey Points...` and `ADR Compare...` remain stubs, while `RAWIMUXA...` parses ASCII logs and plots acceleration, gyro rate, gravity tilt, and relative yaw
- Explanation of QC, report, and plot outputs for support or review

## Load Only What You Need

- Read [references/file-patterns.md](references/file-patterns.md) first when the task starts from a folder or a loose set of files.
- Read [references/cli-capabilities.md](references/cli-capabilities.md) before building commands.
- Read [references/interactive-flow.md](references/interactive-flow.md) when the user gives only a data path or a vague request.
- Read [references/analysis-playbook.md](references/analysis-playbook.md) when the user wants diagnosis, interpretation, or a support-facing summary.
- Read [references/observation-score-report.md](references/observation-score-report.md) before interpreting an observation-quality score or compare report, including any pseudorange/carrier count comparison.
- Read [references/fixed-coordinate-report.md](references/fixed-coordinate-report.md) before interpreting a fixed-coordinate report or the fixed-coordinate section of an auto-process combined report.
- Read [references/cli-batch-workflows.md](references/cli-batch-workflows.md) when the user asks how to batch CLI commands, scan many folders, rebuild many reports, archive scene reports, or package report bundles.
- Read [references/cli-batch-recipes-zh.md](references/cli-batch-recipes-zh.md) when the user asks in Chinese how to explain or present batch CLI workflows to users, support, or field teams.
- Read [references/conversation-templates.md](references/conversation-templates.md) when the user wants a more assistant-like conversation flow with fewer questions.
- Read [references/gui-handoff.md](references/gui-handoff.md) when abnormal plots, PPP-SSR review, residual/ionosphere interaction, or GUI-only tool dialogs should continue in the GUI.
- Read [references/gui-plotting.md](references/gui-plotting.md) when the user asks how to draw observation-series, time-series, compare plots, or system/frequency plots in the GUI.

## Routing Rules

- Prefer CLI when the task is batch, headless, and already supported by the current command surface.
- Prefer the GUI workflow when the task depends on the current page, current mode, or interactive comparison.
- If the user already processed an observation file and the adjacent `Sourcefile_<input completeBaseName>` directory exists, prefer the GUI station-settings option `Load existing QC results and plot options from the adjacent Sourcefile_ folder` when they want to resume rather than rerun QC.
- For RINEX observation import, the station-settings dialog appears only when the adjacent history directory is detected; without one, RINEX keeps the fast-import path. For an already imported RINEX file, use its Data Manager context menu and open `Current Station Settings...` to load history.
- Treat `AnalysisHub-cli convert analyze <input...>` as the preprocessing entrypoint before selecting message names or exact keys.
- Treat `AnalysisHub-cli convert run <input...> --to ascii ...` as the batch selected-message-to-ASCII entrypoint.
- Treat `AnalysisHub-cli convert run <input...> --to rinex --rinex-version <version>` as the RINEX conversion entrypoint.
- Prefer the GUI `Tools -> Data Conversion...` workflow when the user needs interactive per-file message checkboxes; prefer CLI for repeatable directory batches.
- When the user asks `how do we batch this`, separate `leaf CLI commands` from `script-level orchestration`; explain both instead of presenting one giant shell loop.
- When the user asks in Chinese how to batch or how to explain batch workflows to field/support teams, prefer the Chinese batch-recipes framing before listing commands.
- Start folder-based work by running `scripts/find_gnss_artifacts.ps1 -Path <path> -AsJson`.
- Do not claim that the current CLI supports full mode-following `DF` or `TF` health behavior.
- Treat `AnalysisHub-cli report health <qc_html> <datalist>` as the current CLI QC-style health entrypoint.
- Treat `AnalysisHub-cli report rtk <qc_html> <datalist>` as the current CLI RTK diagnosis report entrypoint.
- Treat `AnalysisHub-cli report obs-compare <datalist...>` as the current CLI observation-quality compare entrypoint.
- Treat `AnalysisHub-cli ctclib auto <rover_or_raw_file> ...` as the current CLI one-click auto-process entrypoint; it runs fixed-coordinate residual, QC, and the combined report in one workflow.
- Treat `AnalysisHub-cli report auto-combined ...` as the current CLI combined-report rebuild entrypoint; it consumes existing `DataList/QC/MP/MPresult/arlog/pos` artifacts and regenerates the fixed + combined report without rerunning CTCLib or QC.
- Treat `AnalysisHub-cli iono <input> ...` as the current CLI ionosphere entrypoint.
- Treat `AnalysisHub-cli iono <input>` with `--base` as rover+base RINEX ionosphere processing.
- Treat `AnalysisHub-cli iono <input>` without `--base` as single-file raw / decoder-style ionosphere processing.
- Treat `AnalysisHub-cli report iono <input> ...` as the current CLI ionosphere HTML report entrypoint.
- Treat `AnalysisHub-cli ssr <log_file> ...` as the current CLI PPP-SSR loss-analysis entrypoint.
- Treat `--obsqcmp-mp` as the current CLI switch for the GUI `ObsQc MP mode`, which routes QC to `CHCQC2.0_obsqcmp.exe`.
- For CLI plotting, `skyplot` is not a true headless sky plot in the current implementation; it currently falls back to a `cn0` plot.
- For GUI plotting, distinguish `importing observation files` from `plotting plot-data files`.
- For the current source-backed GUI path, plotting is driven by plot-data files such as `*_DataList.log`, `.DD`, `.DF`, `.TF`, `.MP`, `.GF`, `.MW`, and `.PsrCompare`.
- The current GUI has both `Plot` and `Compare Plot` docks.
- The current GUI `Analysis` menu contains `Residual / Ionosphere...`, `GNSS Accuracy Tool...`, and `PPP-SSR...`.
- The current GUI `Tools` menu contains `Survey Points...` and `ADR Compare...` as stubs. `RAWIMUXA...` is available for ASCII RAWIMUXA attitude plots; its yaw is relative gyro integration, not absolute heading.
- The current top-level CLI commands `accuracy`, `survey`, and `tool` are reserved/help-only entries; do not promise full headless support for them yet.
- For compare plotting in the current GUI, prefer the processed-result-node workflow over asking the user to manually browse for plot files first.
- The current GUI compare workflow defaults to only two comparison slots.
- Do not promise that an arbitrary raw observation file can be plotted directly unless that behavior was verified on the running build.

## Observable Identity Rules

These rules are correctness invariants. Do not infer observable identity from chart color, curve order, relative magnitude, or an unlabeled screenshot.

- In `*_DataList.log`, carrier availability comes from the `L_*` field group. A carrier item is valid when it parses and is not `0.0`.
- In `*_DataList.log`, pseudorange availability comes from the `P_*` field group. A pseudorange item is valid when it parses and is greater than `0.0`.
- Observation-report `pseudorange count` and `carrier count` are per-epoch counts of valid satellite-frequency observation items. They are not satellite counts and not DataList row counts.
- The observation-report timeline order is pseudorange count, carrier count, high-elevation satellite count, slip-carrier ratio, and average CN0. Use labels or parsed field names, never position alone.
- In a fixed-coordinate report, carrier and pseudorange values come from `.arlog` double-difference residual records: `carrPhase` and `pseudorange`. Do not transfer DataList count semantics to this report without saying the source changed.
- The current fixed-coordinate time-series gallery contains `double-difference carrier observation count`, not a pseudorange-count chart.
- If labels, headers, or source artifacts are unavailable, state that observable identity is unverified and do not publish a carrier-versus-pseudorange conclusion.

## Batch Orchestration Rules

- Model batch workflows as `scan -> normalize -> leaf command -> archive -> package`.
- Model data conversion as `analyze -> select names or exact keys -> convert -> verify per-file outputs`.
- Prefer existing helper scripts or their structure over ad-hoc shell loops when the workflow spans many scenes.
- Keep scene-local outputs in stable subdirectories beside the source data.
- Keep root-level archives in named directories so HTML and CSV links stay stable.
- Reuse existing outputs unless the user asks to rerun; mention `force` behavior explicitly when relevant.
- Remove stale generated summaries before rerun if the current generator is known not to overwrite them safely.
- Use the smallest workable flow:
  - if the user only wants merged QC HTML, prefer `qc merge-reports`
  - if the user wants batch message conversion, run `convert analyze` first and then `convert run`
  - if the user wants full one-click processing, prefer `ctclib auto`
  - if the user already has `DataList/QC/arlog/pos` artifacts and only wants the report refreshed, prefer `report auto-combined`
  - if the user wants scene ranking, archive browsing, or bundle delivery, use a multi-stage archive workflow
- Be explicit when a helper flow is current script practice rather than a native `AnalysisHub-cli` subcommand.

## Standard Workflow

1. Inspect inputs with `scripts/find_gnss_artifacts.ps1` when the task starts from a folder or report directory.
2. Identify the user intent:
   - `qc`
   - `convert analyze`
   - `convert run`
   - `ctclib auto`
   - `report auto-combined`
   - `iono`
   - `report iono`
   - `ssr`
   - `report health`
   - `report rtk`
   - `report obs-compare`
   - batch orchestration
   - `plot`
   - `compare plot`
   - `merge-reports`
   - residual analysis
   - GUI-only tool handoff
3. Choose GUI or CLI using the routing rules.
4. Run the selected workflow.
5. For interpretation, verify metric identity and denominator before comparing values, then separate direct evidence from inference.
6. Return results in this shape:
   - recognized inputs
   - selected route and why
   - command or GUI handoff
   - output paths
   - key findings
   - next recommended step

## Interactive Behavior

If the user gives only a path or says `analyze this data first`, do not jump straight to a command.

Use this interaction order:

1. Inspect the path and identify what artifacts exist.
2. Recommend one default route if there is an obvious first-pass path.
3. Ask concise follow-up questions only for information that cannot be reliably inferred.
4. Run the selected workflow.
5. Return the result and the next-step option.

Minimum-question rule:

- Do not ask for mode if only one valid route exists.
- Do not ask for decode type again when the user already provided `_QC.html`, `_DF.html`, `_TF.html`, a report directory, or a scene folder that already implies the route.
- If several routes exist, recommend one default route first instead of asking an open-ended question.
- If the user already has `DataList/QC/arlog/pos` artifacts and asks for a refreshed one-click report, recommend `report auto-combined` first.
- If the file is not clearly a supported observation input, stop before `obscheck` and ask the user to choose the supported input type.

## QC Presets

- `fast`: default QC path; the current default seed uses CTCLib slip check with standard thresholds
- `doppler-assisted`: use when Doppler is available and the user wants stronger slip confirmation
- `strict`: use when the user wants a heavier slip investigation and can tolerate more follow-up or GUI review

Interpretation rule:

- carrier phase and code are the baseline QC observables
- Doppler is an optional aid for slip detection
- SNR helps explain signal quality, but it is not the primary slip observable

## Route Names Used By This Skill

- `cli-qc-health`: QC-style first-pass health report is ready in CLI.
- `cli-convert-analyze`: raw files can be pre-analyzed into message types, counts, and exact selection keys.
- `cli-convert-run`: selected messages can be batch converted to ASCII, binary, or RINEX in CLI.
- `cli-auto-process`: one-click auto processing and combined report can be handled in CLI.
- `cli-auto-combined-report`: an existing one-click artifact set can be rebuilt into a fresh combined report in CLI.
- `cli-iono`: ionosphere analysis can be handled in CLI.
- `cli-ssr-loss`: PPP-SSR loss analysis can be handled in CLI.
- `cli-obs-compare-report`: multi-DataList observation-quality compare can be handled in CLI.
- `cli-rtk-report`: RTK report is ready from `_QC.html` and `DataList.log`.
- `gui-df-health`: DF health should continue in GUI because current-mode behavior matters.
- `gui-tf-health`: TF health should continue in GUI because current-mode behavior matters.
- `gui-ppp-ssr`: PPP-SSR should continue in the GUI when interactive chart review matters.
- `gui-residual-iono`: residual and ionosphere should continue in the shared GUI tool when page switching matters.
- `cli-plot-cn0`: `DataList.log` can be plotted as `cn0`.
- `cli-plot-df-residual`: `.DF` data can be plotted as `residual`.
- `cli-plot-tf-residual`: `.TF` data can be plotted as `residual`.
- `cli-merge-qc-html`: `_QC.html` can participate in batch merge.
- `gui-compare-plot`: compare plotting should continue in GUI because shared mode selection and interactive overlays matter.

## Current Command Families

- `AnalysisHub-cli qc obscheck <file> [options]`
- `AnalysisHub-cli convert analyze <input...> [options]`
- `AnalysisHub-cli convert run <input...> [options]`
- `AnalysisHub-cli qc diff-epoch <file> [options]`
- `AnalysisHub-cli qc triple-epoch <file> [options]`
- `AnalysisHub-cli qc residual <base-file> <rover-file> [options]`
- `AnalysisHub-cli qc short-residual <base-file> <rover-file> [options]`
- `AnalysisHub-cli qc merge-reports ...`
- `AnalysisHub-cli ctclib app <rover_file> [options]`
- `AnalysisHub-cli ctclib post <rover_file> [options]`
- `AnalysisHub-cli ctclib auto <rover_or_raw_file> [options]`
- `AnalysisHub-cli report auto-combined [options]`
- `AnalysisHub-cli report health <qc_html> <datalist> [options]`
- `AnalysisHub-cli report rtk <qc_html> <datalist> [options]`
- `AnalysisHub-cli report iono <input> [options]`
- `AnalysisHub-cli report obs-compare <datalist...> [options]`
- `AnalysisHub-cli iono <input> [options]`
- `AnalysisHub-cli ssr <log_file> [options]`
- `AnalysisHub-cli plot <file> [options]`
- Top-level `accuracy`, `survey`, and `tool` currently exist only as reserved CLI entries; do not describe them as production-ready headless workflows.

## Current GUI Tool Families

- `Analysis -> Residual / Ionosphere...`
- `Analysis -> GNSS Accuracy Tool...`
- `Analysis -> PPP-SSR...`
- `Tools -> Survey Points...`
- `Tools -> Data Conversion...`
- `Tools -> ADR Compare...`
- `Tools -> RAWIMUXA...`

`Survey Points...` and `ADR Compare...` are placeholders in this source-backed build. `RAWIMUXA...` accepts ASCII RAWIMUXA logs and plots XYZ acceleration, XYZ gyro rate, pitch, roll, Z tilt, and relative yaw.

## GUI Plotting Rules

- When the user asks how to use the GUI to plot, load [references/gui-plotting.md](references/gui-plotting.md) and answer with the verified control names.
- For the current source-backed GUI:
  - import observation files from `Data -> Import Rover File...` or `Import Base File...`
  - regular plotting can open plot data from the `Plot` dock using `Browse` + `Parse`
  - compare plotting can open files from the `Compare Plot` dock, but the preferred current workflow is to right-click processed result nodes and set them as compare plot file 1 and 2
  - use `Observation Series` for system-level observation-sequence plots
  - use `Time Series (LCT/CN0/Doppler/Elev)` for system-frequency time-series plots such as `GPS_L1`
  - use `Carrier / Pseudorange` only in observation-series mode
- If the user gives a processed output directory, first identify which files are plot-capable, then explain the GUI path for each file type instead of only listing filenames.
- If `*_DataList.log` and other plot artifacts already exist in the adjacent `Sourcefile_<stem>` directory, the user can restore them through station settings; do not tell them to rerun QC merely to plot them.
- If the user asks how compare plotting should be used in the current GUI, explain the right-click node flow first:
  - set one processed result as compare plot file 1
  - set another processed result as compare plot file 2
  - choose one shared compare mode
  - let the GUI switch into `Compare Plot`

## Output Discipline

- If the user writes in Chinese, answer in Chinese.
- Use exact filenames and exact mode names: `QC`, `DF`, `TF`.
- Distinguish `GUI-supported` from `CLI-supported`.
- Separate what the tool produced from what you infer from it.
- State the source artifact, metric definition or denominator, direct evidence, inference, and any missing evidence for analytical conclusions.
- Use the report's exact labels and units. If a field cannot be tied to a verified label or schema, mark it unverified instead of guessing.
- Keep support-facing summaries short and concrete.
- Do not invent CLI parity for GUI-only behavior.

Default result shape:

- `Recognized Inputs`
- `Recommended Route`
- `Command Or GUI Handoff`
- `Output Paths`
- `AI Summary`
- `Next Step`
