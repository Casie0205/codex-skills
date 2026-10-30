# Fixed-Coordinate Report

Read this reference before interpreting a fixed-coordinate report or the fixed-coordinate section of an auto-process combined report.

## Data Domain

The fixed-coordinate report is driven primarily by `.arlog` double-difference residual records. This is not the same domain as `_DataList.log` observation availability.

| Fixed-coordinate concept | `.arlog` field or derivation | Unit |
| --- | --- | --- |
| carrier residual | `DiffRecord.carrPhase[frequency]` | cycles |
| pseudorange residual | `DiffRecord.pseudorange[frequency]` | metres |
| carrier observation count | valid double-difference carrier items per epoch | items |
| pseudorange observation count | valid double-difference pseudorange items per epoch | items |
| carrier regularity delta | fractional-cycle change between adjacent valid carrier residuals within the allowed gap | cycles |

Do not transfer the DataList `L_*`/`P_*` availability interpretation into this report without stating that the source and meaning have changed.

The current time-series gallery includes:

- carrier regularity timeline;
- **double-difference carrier observation count timeline**;
- average CN0 timeline.

It does not provide a pseudorange-count timeline. If a chart is the current count chart, call it carrier count; do not rename it based on visual magnitude.

## Primary And Supporting Evidence

Interpret in this order:

1. Carrier regularity ratio.
2. Mean and maximum `Delta vL`.
3. Carrier residual amplitude and the share with `|vL| < 0.20 cycles`.
4. Carrier observation support and its low windows.
5. Pseudorange residual mean/maximum and CN0 as explanatory evidence.
6. Optional position deviation as a result-layer cross-check.

The fixed-coordinate residual report's overall grade is based on residual regularity, amplitude, and observation support. Position deviation is not part of that residual overall grade. If position data exists, use it only as an additional result-layer check and say so explicitly.

## Current Thresholds

The maintained source of truth is `src/core/DiagnosisThresholdSpec.h`. The key current thresholds are:

| Metric | Attention | High risk |
| --- | --- | --- |
| carrier regularity ratio | `<= 92%` | `<= 82%` |
| mean `Delta vL` | `>= 0.035 cycles` | `>= 0.070 cycles` |
| maximum `Delta vL` | `>= 0.080 cycles` | `>= 0.150 cycles` |
| mean absolute carrier residual | `>= 0.10 cycles` | `>= 0.18 cycles` |
| carrier residual pass ratio | `<= 92%` | `<= 80%` |
| mean absolute pseudorange residual | `>= 1.5 m` | `>= 3.0 m` |
| maximum absolute pseudorange residual | `>= 6.0 m` | `>= 12.0 m` |
| average CN0 | `<= 35 dB-Hz` | `<= 30 dB-Hz` |
| carrier support floor / peak | `<= 0.70` | `<= 0.50` |

Regularity pairs require an adjacent gap of at most `1.5 s`; a pair passes when its fractional-cycle delta is at most `0.05 cycles`. An isolated sample pass or a high overall regularity ratio does not prove the entire interval is smooth. Mean and maximum delta still matter.

Use report-provided thresholds when analyzing a report produced by another build. Do not overwrite its historical judgment with current thresholds without identifying the version difference.

## Single-Report Diagnostic Sequence

1. Confirm `.arlog`, report version, analyzed time range, and whether optional position data was supplied.
2. Read overall carrier regularity, mean/max `Delta vL`, residual pass ratio, and carrier support.
3. Locate aligned windows where regularity falls, carrier count drops, CN0 drops, or residuals expand.
4. Inspect the highest-risk system/frequency and satellite rows that meet evidence-count thresholds.
5. Use pseudorange residual and CN0 to distinguish likely weak-signal/obstruction behavior from strong-signal bias or multipath behavior.
6. Use position deviation only to check whether observation-layer problems propagated to the result layer.

Useful combinations:

| Synchronized evidence | More plausible interpretation |
| --- | --- |
| low regularity + low CN0 + carrier count drop | obstruction, weak signal, or tracking loss |
| low regularity + normal/strong CN0 + persistent residual increase | reflection, multipath, or persistent phase bias |
| stable regularity + large position deviation | reference coordinate, antenna height, model, or solution configuration needs review |
| short isolated max `Delta vL` spike with otherwise stable evidence | local satellite/frequency or transient event, not automatically a scene-wide failure |

## Rover/Base Combined Diagnosis

When the combined report includes both station score results and fixed-coordinate results:

1. Determine the double-end common-view candidate set before drawing conclusions from single-station visible-satellite totals.
2. Compare the same satellite/frequency on rover and base; do not mix rows across signals.
3. Separate rover-side, base-side, and shared risk.
4. Give priority to windows where regularity degradation, CN0 degradation, and double-difference carrier support loss align.
5. Use high-elevation coverage, empty sectors, GF, and multipath evidence to explain spatial or environmental structure.

Single-side visible satellite count is not common-view support. Many visible satellites do not imply many stable double-difference carrier constraints.

When actual common-view, rover/base, skyplot, or site evidence is absent, do not invent it. Describe only the fixed residual evidence and list the missing data needed for joint attribution.

## Fixing Claims

Observation and residual evidence can support statements such as:

- `fixed-solution support is weakened`;
- `stable ambiguity constraints appear insufficient`;
- `the observed carrier behavior is consistent with reduced fixing capability`.

Do not state that WL, NL, or the final solution failed unless the report or solver output contains direct fixing-state evidence. Without it, the causal chain remains an engineering inference:

```text
obstruction / multipath / persistent bias
-> carrier continuity or consistency degrades
-> stable ambiguity constraints weaken
-> fixing capability may decline
```

## Reporting Guardrails

- Use exact labels and units: carrier in cycles, pseudorange and position in metres, CN0 in dB-Hz.
- Keep observation count, satellite count, residual sample count, and regularity-pair count distinct.
- High CN0 does not prove a carrier residual is unbiased.
- A stable carrier count does not prove regularity or residual quality.
- A high regularity ratio does not cancel a large mean/max delta.
- Missing position data means propagation to coordinates is unknown, not absent.
- Separate direct report evidence, joint interpretation, and solver-state claims.

## Recommended Output

State:

1. Source artifacts, report version, stations, and time range.
2. Primary carrier regularity and support evidence.
3. Pseudorange, CN0, station-quality, and position cross-checks.
4. Aligned abnormal windows and implicated system/frequency/satellites.
5. Interpretation, alternatives, confidence, and missing evidence.
6. The next check most likely to distinguish environment, station-side, and configuration causes.
