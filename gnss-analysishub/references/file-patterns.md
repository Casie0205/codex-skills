# File Patterns

Use these patterns to map files and result directories to AnalysisHub workflows.

## Observation And QC Artifacts

- `*_QC.html`: single-station QC result report.
- `*_DF.html`: diff-epoch report.
- `*_TF.html`: triple-epoch report.
- `*_DataList.log` or `DataList.log`: epoch, satellite, frequency observation and slip data.
- `*.DF`: diff-epoch numeric plot data.
- `*.TF`: triple-epoch numeric plot data.
- `*.MPresult` / `*.MP`: multipath statistics or plot data.
- `*.GF`, `*.MW`, `*.PsrCompare`: derived plot data.
- `*.arlog`: double-difference residual data used by fixed-coordinate analysis.
- `*_obs_health\`: generated health or observation-quality report folder.

Use the shared stem before the mode suffix where possible. Example set:

```text
9999323_20260420165032_QC.html
9999323_20260420165032_DF.html
9999323_20260420165032_TF.html
9999323_20260420165032_DataList.log
9999323_20260420165032.DF
9999323_20260420165032.TF
```

## Adjacent History Directory

QC creates an adjacent directory named:

```text
Sourcefile_<input completeBaseName>
```

Example:

```text
Input:  E:\data\site01.24o
Folder: E:\data\Sourcefile_site01\
```

The GUI can restore existing results and plot choices from this directory without rerunning QC. It recognizes the matching-stem artifacts including `_QC.html`, `_DataList.log`, `.MPresult`, `.MP`, `.DF`, `_DF.html`, `.TF`, `_TF.html`, `_SLIPRATIO.log`, `.GF`, `.MW`, `.PsrCompare`, and `.arlog` when present.

Directory existence means history is available for inspection, not that every expected artifact is valid. Confirm files exist and match the input stem before claiming restoration succeeded.

## GUI History Routing

- Non-RINEX observation import opens station settings; select `Load existing QC results and plot options from the adjacent Sourcefile_ folder` to restore history.
- RINEX import opens station settings only when the matching adjacent history directory is detected. With no history directory it retains the fast-import path.
- For an already imported observation, right-click it in Data Manager, open `Current Station Settings...`, select the same history option, and confirm.
- If the directory exists but contains no recognized matching-stem artifacts, report that the folder was detected but no loadable result was found. Do not claim the QC result was restored.

## Health Report Mapping

### QC health

- Required: `_QC.html`.
- Required: `DataList.log`.
- Optional: original observation file for naming.

### DF/TF health in the current GUI

- Required: current `_DF.html` or `_TF.html`.
- Required: `DataList.log`.
- Required for precision anomaly summaries: matching `.DF` or `.TF` numeric data.

The GUI can follow the active `QC / DF / TF` result context. CLI `report health` does not expose the same mode-following surface.

## Typical Generated Outputs

The usual health output folder is `<stem>_obs_health`. It may contain:

- `health.html` or `health_report.html`;
- `obsnum_cn0_overview.png`;
- `slip_ratio_overview.png`;
- CSV summaries for slips, rates, multipath, and precision abnormalities.
