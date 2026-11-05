# Client Report Delivery

## 目录

- [1. Writing stance](#1-writing-stance)
- [2. Parameter confidentiality](#2-parameter-confidentiality)
- [3. Raw-data evidence](#3-raw-data-evidence)
- [4. Intuitive figures](#4-intuitive-figures)
- [5. Default humanizer pass](#5-default-humanizer-pass)
- [6. Final checks](#6-final-checks)

## 1. Writing stance

Write from the customer's decision point. A useful section answers:

- What problem existed?
- What did it affect?
- What did we determine?
- What changed?
- How do we know it worked?
- What remains open?

Avoid narrating the internal sequence of investigation. Remove tool lists, internal folder inventories, rejected branches, and "we analyzed..." openings unless they change the conclusion.

Use concrete outcomes. "The timestamp rollback was removed from all 93,862 records" is more useful than "we performed a detailed timestamp audit."

## 2. Parameter confidentiality

Do not place exact proprietary or customer-specific parameters in an external report. This includes noise densities, covariance values, scale factors, tuning grids, thresholds, and full configuration files.

Use relative language that preserves the engineering meaning:

- "about 50-100 times the common configuration";
- "a high-noise setting relative to the baseline";
- "the selected weights are in the upper range of the tested set".

Explain what the relative setting implies. For example: "The accelerometer random-walk setting had to reach roughly 50-100 times the common configuration before navigation performance became stable. This indicates that the measured IMU jitter is much larger than the downstream filter originally assumed."

Keep exact values in internal records only unless the customer explicitly approves disclosure.

## 3. Raw-data evidence

When claiming a data-quality issue, show both:

1. one or two plots that make the issue immediately visible;
2. the original packaged data at the affected location.

The raw-data screenshot must show the complete original row for the selected frame, including every field in that record. A cropped timestamp or isolated payload is insufficient because it leaves room to question how adjacent fields were interpreted.

For a time-rollback issue, a useful pair is:

- a before/after timestamp-difference plot showing negative intervals;
- a raw package excerpt centered on the rollback row, with the full frame and nearby rows visible.

Redact only sensitive fields that are unrelated to the claim. State the file name, record index or timestamp, and field meanings in the caption.

## 4. Intuitive figures

Prefer one direct diagnostic view over a collection of exploratory plots. A figure should answer the customer's question without reading the surrounding method.

Remove:

- plots that show only a handful of simple counts;
- duplicate charts that support the same statement;
- analysis dashboards with several unrelated panels;
- screenshots that only prove software was opened.

Keep:

- a time-difference plot that visibly crosses zero;
- a trajectory or error plot that exposes divergence;
- a before/after comparison tied to the selected solution;
- a complete raw-data row needed for auditability.

## 5. Default humanizer pass

Read and apply `$humanizer:humanizer` to all customer-facing prose before final validation. Use file mode when editing a report file and embedded mode when drafting in a larger workflow.

Preserve every technical number, limitation, and selected configuration. Remove staged openers, forced contrasts, inflated significance, decorative bold labels, and analysis narration.

## 6. Final checks

1. The first screen states the finding and current outcome.
2. No exact confidential parameters remain.
3. Each major claim has direct evidence.
4. Data-integrity claims include a complete raw row.
5. Figure captions state scope, record count, and the conclusion.
6. The selected solution is explicit.
7. Remaining checks are concrete and brief.
8. A4 printing hides navigation and preserves all figures and tables.
