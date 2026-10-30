# Observation-Quality Score Report

Read this reference before interpreting an AnalysisHub observation-quality score or compare report.

## Source Hierarchy

- `*_DataList.log` is the primary source for observation availability, carrier continuity, GF risk, high-elevation satellites, CN0, spatial coverage, and system/frequency balance.
- `.MPresult` is preferred for multipath scoring; `.MP` is the fallback.
- `_QC.html` supplies RTK, PPPAR, and PPPRTK support indicators. It is not a mandatory source for the observation-quality main score.
- A generated HTML narrative is a summary of these artifacts, not independent evidence. When possible, trace a claim to the named table, metric, and source file.

Do not compare files as receiver performance unless their time range, sampling interval, station role, enabled systems/frequencies, elevation mask, and processing configuration are sufficiently comparable.

## Carrier And Pseudorange Identity

This distinction is mandatory:

| Report concept | DataList source | Validity rule | Count meaning |
| --- | --- | --- | --- |
| Carrier availability/count | `L_*` field group | parses and value `!= 0.0` | valid satellite-frequency carrier items in the epoch |
| Pseudorange availability/count | `P_*` field group | parses and value `> 0.0` | valid satellite-frequency pseudorange items in the epoch |

Consequences:

- Neither count is a satellite count. One satellite can contribute multiple frequency items.
- Neither count is the number of DataList rows.
- Do not decide identity from which curve is larger. Valid carrier and pseudorange populations can differ.
- Do not decide identity from color or display order. Require the label, table header, exported field name, or source schema.
- In the observation overview timeline, the metric sequence is `pseudorange count`, `carrier count`, `high-elevation satellite count`, `slip-carrier ratio`, then `average CN0`. Quote labels in the result so the sequence cannot be confused with identity.

`Pseudorange completeness` and `carrier availability ratio` are not the same as the raw epoch counts. Their denominator is the theoretical observation population, derived from each satellite's first/last epoch and sampling interval and then expanded by frequency. State that denominator whenever quoting a ratio.

## Six Core Dimensions

Analyze the core dimensions before relying on the final score:

| Dimension | Primary evidence | Direction and caution |
| --- | --- | --- |
| Observation completeness | pseudorange completeness, carrier availability, multi-frequency availability | higher is better; distinguish ratios from raw counts |
| Carrier continuity | single-frequency continuity, multi-frequency continuity, reacquisition, reliable locktime support | higher continuity and lower reacquisition/reset risk are better |
| GF cycle-slip risk | GF epoch ratio, event density, burst ratio, frequency spread | lower is better; persistent high-elevation bursts are stronger evidence than low-elevation isolated events |
| Multipath environment | carrier multipath quality, pseudorange multipath quality | higher quality is better; carrier has greater diagnostic weight in the current report |
| High-elevation signal quality | trimmed CN0 mean, P90-P10 spread, low-CN0 tail | stronger, tighter, and less low-tail behavior is better |
| Spatial and system robustness | high-elevation coverage, high-elevation satellite median, largest empty sector, system/frequency balance CV | broad stable coverage is better; averages can hide a bad sector or system |

Current dimension weights are: completeness `15`, carrier continuity `20`, GF risk `20`, multipath `25`, high-elevation signal quality `12`, and spatial/system robustness `8`. The report calculates an absolute aggregate and an environment-adjusted aggregate, then uses `final score = 0.55 * absolute aggregate + 0.45 * environment-adjusted aggregate`. These weights explain ranking; they do not turn the score into a root-cause classifier.

The final score is useful for ranking but does not identify the cause by itself. A close score can hide different failure modes, and a high score does not rule out short severe windows.

## EPI

Environment Pressure Index is:

```text
EPI = 100 * (0.45 * E_occ + 0.30 * E_dyn + 0.25 * E_mp)
```

- `E_occ`: spatial obstruction pressure.
- `E_dyn`: dynamic fluctuation pressure.
- `E_mp`: multipath pressure.
- Lower EPI is closer to an open, stable environment.

EPI is an environment-pressure index, not a receiver capability score. Use it to describe scene difficulty and to understand the report's limited environment adjustment. Do not use it alone to declare one receiver better or worse.

## Diagnostic Sequence

1. Confirm input comparability and artifact availability.
2. Read the six core dimensions and identify the largest shortfall.
3. Check final score and EPI as summaries, not as substitutes for the core metrics.
4. Align the exact time windows for pseudorange count, carrier count, high-elevation satellite count, slip/GF behavior, CN0, and multipath evidence.
5. Drill down into the implicated system, frequency, and satellite.
6. Test at least one competing explanation before assigning a cause.

Useful combinations:

| Synchronized evidence | Supported interpretation |
| --- | --- |
| pseudorange and carrier counts fall with high-elevation satellite count and CN0 | obstruction, weak signal, or tracking support loss is plausible |
| carrier count/continuity worsens while pseudorange remains relatively stable | carrier tracking or phase continuity deserves priority; do not call it a code-availability failure |
| CN0 remains strong but GF, regularity, or multipath evidence worsens | strong signal does not rule out reflection or persistent phase bias |
| counts remain stable but GF bursts or continuity deteriorate | stable quantity does not imply stable carrier quality |
| one system/frequency degrades while others stay stable | inspect configuration, signal-specific tracking, interference, or constellation geometry before a global device conclusion |

These are interpretations, not proofs. A root-cause statement should cite at least two independent aligned indicators or be marked as a hypothesis.

## Reporting Guardrails

- Keep `satellite count`, `satellite-frequency observation count`, `valid epoch count`, and `theoretical observation count` distinct.
- Keep `availability`, `continuity`, `GF risk`, `CN0`, and `multipath` distinct. One cannot stand in for another.
- High CN0 does not prove carrier stability.
- Stable carrier count does not prove continuity, regularity, or low GF risk.
- Averages do not override time-window, low-tail, or spatial-sector evidence.
- Missing `.MPresult/.MP` means multipath evidence is unavailable, not normal.
- If a screenshot lacks labels, ask for the HTML table/export or source artifacts before naming carrier and pseudorange series.

## Recommended Output

State:

1. Files, station roles, time spans, and processing comparability.
2. Exact metric labels, definitions, denominators, and values.
3. Direct evidence and synchronized abnormal windows.
4. Most likely interpretation plus alternatives.
5. Confidence and missing artifacts.
6. The next system/frequency/satellite or time window to inspect.
