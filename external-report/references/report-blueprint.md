# External Report Blueprint

## 目录

- [1. Reader and decision](#1-reader-and-decision)
- [2. Default page order](#2-default-page-order)
- [3. Title block](#3-title-block)
- [4. Main section patterns](#4-main-section-patterns)
- [5. Evidence hierarchy](#5-evidence-hierarchy)
- [6. Completeness check](#6-completeness-check)

## 1. Reader and decision

Write for a reader who owns the product, data, or operational problem and needs to know:

1. what was wrong;
2. what effect it had;
3. what was changed;
4. how the result was verified;
5. what remains uncertain.

Do not organize the main narrative around files processed, tools used, meetings held, or the amount of analysis performed.

## 2. Default page order

1. Screen-only navigation.
2. Report title block.
3. Customer-facing summary of findings and resolution.
4. A compact row of result metrics.
5. Two to four sections built around problems, fixes, and verification.
6. Remaining risks and next checks.
7. Concise evidence footer.

The opening summary should stand alone. A reader who stops after it should still know the outcome.

Do not fill that summary with internal sample counts, event counts, or file counts. Use a qualitative scope statement and move detailed counts to the evidence sections.

## 3. Title block

Include:

- data date and report period;
- a technical title that names the subject;
- one sentence describing the evaluated scope;
- reporting date;
- data range when it differs from the reporting date.

Do not include page-verification status, internal task state, or decorative badges.

## 4. Main section patterns

### Anomaly found and resolved

- State the anomaly and visible symptom.
- Show one plot that exposes it.
- Show the original complete record row at the affected position.
- State the correction and the before/after validation.
- End with the effect on the customer workflow.

### Performance investigation

- State the measured limitation and the decision it affects.
- Use one figure that shows the trend or contrast.
- Keep exact confidential tuning values out. Use relative settings or ranges.
- Summarize the practical conclusion and residual uncertainty.

### Constraint or configuration selection

- State the selected configuration in the section heading or first sentence.
- Compare only options needed for the decision.
- Explain which observable each option constrains.
- End with the selected option and the reason.

## 5. Evidence hierarchy

Use evidence in this order:

1. A concise conclusion with the affected unit, time range, or data scope.
2. One or two intuitive figures that expose the problem or comparison.
3. A representative raw-data row or package excerpt that proves the source record was interpreted correctly.
4. A compact table for exact audit values or residual risks.

Do not replace a simple numeric result with a screenshot. Do not use a screenshot when a measured plot exists. When the reader may question data handling, provide both the diagnostic plot and the source record.

## 6. Completeness check

Before delivery, confirm that the report:

- leads with the customer-relevant result;
- contains no exact confidential parameters;
- shows the most direct evidence before detailed numbers;
- includes a complete original row when data integrity is in question;
- separates resolved items from remaining checks;
- avoids internal work narration and self-assessment;
- remains readable in desktop, mobile, and A4 print views.
