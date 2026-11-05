# Writing and Delivery

Use this reference when drafting summaries, captions, validation notes, or the final delivery.

## Writing Priorities

The report is technical evidence, not promotional copy.

- Lead with the achieved result.
- Keep background only when it explains a decision or metric.
- Support each substantive claim with a number, output path, or validation result.
- Explain anomalies before interpreting downstream results.
- Distinguish “generated”, “structurally verified”, “numerically evaluated”, and “receiver-validated”.
- End unfinished items with a concrete remaining check.

## Summary Pattern

Write one dense paragraph or two short paragraphs with:

1. the work completed;
2. the datasets and their scale;
3. the key quantitative result;
4. the verification output;
5. the remaining work or boundary.

Avoid a list of task names without outcomes.

## Caption Pattern

Use:

> **对象名称**
> 数据范围或样本量；图中显示的指标；关键数值；解释时需注意的限制。

Examples of useful numbers:

- 93,862 frames, 7 events, maximum rollback 310.009 s;
- horizontal RMS 2.126 mm and P95 4.938 mm over 36,001 epochs;
- 17,833/17,976 valid RTCM3 frames;
- 42/42 anchors aligned and zero negative intervals after correction.

## Language Rules

- Use concrete Chinese verbs: 解析、对齐、修正、重建、比较、验证、归档.
- Prefer “结果经过本地结构校验” to “结果已完全验证”.
- Keep sentence lengths varied.
- Use a colon only when it introduces a real list or definition.
- Avoid em dashes.
- Avoid “不是……而是……” constructions that make an ordinary contrast sound larger.
- Avoid one-line closer paragraphs such as “这体现了工作价值”.
- Avoid decorative bold labels and forced triads.
- Do not talk about how the report was assembled.

When prose editing is substantial and the `humanizer` skill is available, apply it while preserving every factual number and qualification.

## Content Boundaries

- Do not reproduce assessment weights, minimum values, target levels, or challenge levels from an external form.
- Do not present the same achievement as several independent results because it supports several categories.
- Do not mention WIKI or other planned knowledge products when the user has asked to omit them.
- Do not imply that a class-group presentation occurred when only a mentor briefing occurred.
- Do not replace a numeric result with a screenshot when the screenshot does not show the measurement.
- Do not show page construction or implementation validation status such as “页面已验证” in the report metadata.

## Validation and Delivery

Before delivery:

1. Run `scripts/validate_report.py`.
2. Inspect desktop and narrow layouts.
3. Inspect A4 print media for hidden controls and page breaks.
4. Sync the final HTML, CSS, JS, assets and documentation to the agreed output directory.
5. Keep prior PDFs clearly identified as old versions when the new page has not been printed.
6. Generate the PDF only after the user asks or approves the page.

If the report lives in a Git repository, commit the source changes after verification. Preserve unrelated working-tree changes.
