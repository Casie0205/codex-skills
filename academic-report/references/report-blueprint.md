# Report Blueprint

Use this reference to decide the report structure before drafting or substantially revising a page.

## 1. Unit of Delivery

Create one self-contained HTML report for each evaluation item, project milestone, or technical topic that the audience needs to review independently.

Do not split a report merely because the evidence came from several files or tools. Group evidence by the question it answers.

When two evaluation categories overlap heavily, keep the report structure technical and avoid repeating the same achievement under multiple headings.

## 2. Default Page Order

1. Screen-only navigation
2. Report title block
3. Quantitative completion summary
4. Four key metrics
5. Two to four numbered main sections
6. Concise source footer

Use a new printed page for each main section when the evidence is long. A short report may use fewer page breaks.

## 3. Title Block

The title block contains:

- report category and period;
- a real technical title, not a slogan;
- one sentence describing the evaluated scope;
- reporting date;
- optional substantive work state only when it changes how the result should be read.

Do not show implementation or page-verification state such as “页面已验证” or “页面已完成”.

Avoid a decorative cover page for a normal progress report. The title block should begin on the first content page.

## 4. Summary

The summary states what was done, on what data, with what key measurements, and what remains.

Useful pattern:

1. Name the technical tasks.
2. Give sample counts, durations, rates, error values, and verified outputs.
3. State the result or validation status.
4. Mention unfinished work or external dependencies only when they affect interpretation.

Do not restate assessment weights, target thresholds, or known administrative metadata. Do not write copy instructions for another system.

## 5. Main Section Patterns

Choose the pattern that matches the work:

### Performance Characterization

Use for sensor noise, precision, correlation, latency, or other measured properties.

- Explain the measured quantity and evaluation basis.
- Show the primary evidence figure.
- Add a compact statistics table.
- End with an interpretation that affects later engineering decisions.

### Comparative Evaluation

Use for methods, versions, parameter sets, or baseline comparisons.

- State all compared options and the common inputs.
- Give a summary metric table.
- Use plots only when each adds a distinct view, such as overall accuracy, tail behavior, temporal error, and robustness.
- Keep an offline or oracle baseline explicitly labeled.

### Data Pipeline and Quality Audit

Use for parsing, decoding, timestamping, synchronization, and integrity checks.

- Start with an input and output manifest table.
- Show one representative visual for format or layout when it helps interpretation.
- Report validation failures and denominators.
- End with the usable output and any remaining receiver-side or environmental checks.

### Event Processing and Repair

Use for timestamp resets, outages, dropout recovery, or other short anomalies.

- Give the number of events and the overall sample range first.
- Use an overview plot for the whole timeline.
- Use a representative or maximum-severity event plot for detail.
- Add before/after metrics.
- Verify that ordering, counts, payloads, hashes, and required anchors were retained.
- If several event plots answer the same question, combine them into one multi-panel figure.

## 6. GNSS/INS Reference Structure

The validated GNSS/INS page follows this technical order:

1. **M720 IMU baseline performance**
   - Allan deviation
   - axis-level noise and grouped stability statistics
   - temperature and duration limitations

2. **M720 single-point and fixed RTK precision**
   - data profile and precision table
   - error time series
   - single-point horizontal scatter and RMS circle
   - fixed-solution horizontal scatter and RMS circle
   - cumulative error distribution
   - autocorrelation and correlation time

3. **Mova 2026-09-23 data**
   - bag, camera, RTCM3, HCNav DAT and decoded frame inventory
   - camera layout evidence
   - RTK and odometry trajectory quality
   - ctclib GNSS result

4. **Mova 2026-10-27 data**
   - IMU timestamp rollback and compensation
   - IMU before/after re-encoding verification
   - VIO/VINSOBS timestamp audit and maximum rollback event
   - VIO correction and GNSS/IMU/VIO merge verification
   - ctclib GNSS/IMU result

This is an example of grouping by technical question. It is not a requirement that every future report use the same section titles or number of sections.

## 7. Figure and Table Selection

Include an object when it adds a measurement, comparison, validation, or spatial relationship that prose alone cannot convey.

Delete or merge:

- screenshots that only confirm an application opened;
- duplicate plots using the same metric and same conclusion;
- enlarged thumbnails whose labels remain unreadable;
- tables that repeat the summary or another table;
- plots showing only one trivially constant value when a sentence is clearer.

When the user references old figure numbers, map them to the source images or results first. Renumber the final report in reading order.

## 8. Completeness Check

Before delivery, verify that the report:

- covers every requested work item;
- includes quantitative evidence for each major claim;
- states the sample size or duration behind every aggregate metric;
- distinguishes current results from future work;
- contains no unrelated legacy sections;
- has no orphan figures or unexplained tables;
- ends on a concrete result, validation boundary, or next action.
