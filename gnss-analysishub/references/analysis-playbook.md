# Analysis Playbook

Use this reference when the task requires diagnosis or explanation, not only command execution.

## Evidence Contract

Before interpreting a number or curve, identify all of the following:

1. Source artifact and report section.
2. Exact metric label and unit.
3. Population and denominator, if it is a count, ratio, average, or score.
4. Time range, station role, system, frequency, and satellite scope.
5. Whether the statement is direct evidence, an inference, or a hypothesis that needs another artifact.

Never infer carrier versus pseudorange from line color, curve height, series order, or an unlabeled screenshot. For these observables, use the identity rules in `SKILL.md` and the relevant report reference.

When evidence is incomplete, say what is missing and reduce confidence. Do not silently convert `not reported` into zero or normal.

## Analysis Order

Use the smallest sequence that can answer the request:

1. Verify inputs, provenance, time span, and whether compared files are commensurate.
2. Read the report's core metrics before the total score or generated narrative.
3. Find the dominant shortfall and its exact time window.
4. Align independent evidence in that window, such as counts, high-elevation satellites, GF, CN0, multipath, regularity, and residuals.
5. Drill down by station, system, frequency, and satellite only where the aggregate evidence points.
6. State direct findings first, then causal interpretation, confidence, and the next discriminating check.

Do not use a global average to dismiss short severe windows, spatially concentrated problems, or one poor station in a rover/base pair.

## Intent To Workflow Mapping

### Quick quality check

- Route to `qc obscheck`.
- If the file is not clearly a supported observation input, identify the format before running QC.
- Ask only for missing high-value settings: elevation mask (default `7 deg`) and slip strategy (default `fast`).
- Return the output HTML, DataList path, and whether score or health reporting is possible.

The current default QC seed uses CTCLib slip check.

### Slip strategy

- `fast`: default QC path.
- `doppler-assisted`: use when Doppler exists and stronger slip confirmation is needed.
- `strict`: use for a heavier slip investigation when additional follow-up is acceptable.

Carrier phase and pseudorange are the baseline QC observables. Doppler can assist slip detection; SNR/CN0 is explanatory context, not the primary slip observable.

### Observation-quality score or compare report

- Read [observation-score-report.md](observation-score-report.md).
- For a report rebuild, use `report obs-compare` with two or more `DataList.log` files.
- Report the score and EPI only after the six core dimensions and their evidence.
- Align pseudorange/carrier count, high-elevation satellite, GF, slip, CN0, and multipath evidence before assigning a cause.

### Fixed-coordinate or combined report

- Read [fixed-coordinate-report.md](fixed-coordinate-report.md).
- Treat `.arlog` double-difference residuals as a different data domain from `_DataList.log` observation availability.
- Start with carrier regularity, `Delta vL`, residual amplitude, and carrier support.
- Use rover/base quality and common-view evidence only when those artifacts are actually available.

### Health report

- `_QC.html + DataList.log` is a valid CLI input pair.
- If the report must follow active GUI mode `QC / DF / TF`, use the GUI route.
- Summarize the overall conclusion, anomaly class, key window, and next inspection target.

### Ionosphere analysis

- Rover/base RINEX or one raw input: route to `iono`.
- `IonosphereIndex_Ant0.txt/.log` or `Ionosatinfodatalist.log/.txt`: route to `report iono`.
- Use `Residual / Ionosphere...` when interactive follow-up matters.
- State the result log, report path, and `auto`, `brdc`, `estimate`, or `off` mode.

### PPP-SSR analysis

- Route to `ssr` for headless packet-loss analysis.
- Use `PPP-SSR...` for interactive chart review or snapshot export.
- State the report path, worst packet types, and `csm` or `upbeat` mode.

### DF/TF precision anomaly

- Use the GUI for full current-mode behavior.
- Keep carrier precision and pseudorange precision tables separate and quote their exact labels.

### Plot evidence

- Use CLI `plot` when headless export is sufficient.
- State plot type, filters, and PNG path.
- Use the GUI references for interactive plots or restored history.

### Merge many results

- Use `qc merge-reports`.
- State the number merged, Excel path, and the first system/frequency requiring review.

### GUI-only tools

- `GNSS Accuracy Tool...` is available.
- `Survey Points...` and `ADR Compare...` are visible placeholders. `RAWIMUXA...` performs ASCII IMU conversion and plotting, but its gyro-integrated yaw is relative and may drift.

## Result Shape

For analytical work, return:

1. Inputs and provenance.
2. Metric definitions and scope.
3. Direct evidence, with values and time windows.
4. Interpretation and competing explanations.
5. Confidence and missing evidence.
6. Next check, prioritized by how well it separates the remaining explanations.

For support-facing summaries, compress this to one conclusion plus two to four concrete observations, but retain the distinction between evidence and inference.
