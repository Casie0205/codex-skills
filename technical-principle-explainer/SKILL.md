---
name: technical-principle-explainer
description: "Explain technical principles in conversation with layered intuition, formula anatomy, dimensions, worked numerical examples, geometric interpretation, and interpretation tables. Use when the user asks why or how a concept works. Do not modify documents unless the user separately requests an edit."
---

# Technical Principle Explainer

Explain the mechanism, not just the conclusion. The goal is to let the user predict how
the result changes, recognize common misunderstandings, and connect the formula to the
physical or statistical system.

## Response Shape

Use this order by default. Skip a stage only when it would add no information.

1. **Answer directly.** Start with one sentence that says what the concept is or what
   the formula does.
2. **Build a mental model.** Explain the process as a sequence of operations or a
   timeline before introducing the full formalism.
3. **Define objects and dimensions.** For vectors and matrices, give their meaning,
   dimensions, and the space they live in. State which quantity is a scalar, vector,
   covariance, transformation, or residual.
4. **Dissect each formula.** Explain what each term does, why it appears, and what
   would change if it were absent. Preserve the user's notation when possible.
5. **Work one concrete example.** Prefer a small scalar or 2D case first, then a
   correlated or matrix case when needed. Use one running example consistently rather
   than unrelated examples in every paragraph.
6. **Give a geometric or equivalent interpretation.** Use rotation, projection,
   whitening, Mahalanobis distance, ellipses, or another equivalent view when it makes
   the algebra legible.
7. **Compare related ideas.** Use a compact table for metrics such as NEES, ANEES, NIS,
   and NRC. Show what each metric reads, the covariance it normalizes by, and whether it
   needs truth.
8. **Explain interpretation.** State the ideal value, what greater and smaller values
   imply, and which observations support each interpretation.
9. **State assumptions and limits.** Separate mathematical identities from expected
   behavior in finite, correlated, linearized, or model-mismatched data.

## Explanation Rules

- Distinguish definitions, exact derivations, statistical expectations, typical
  magnitudes, and practical causes. Do not use "about" when an exact expectation is
  intended; explain the source of variation separately.
- Show the dimensions of all nontrivial matrix products.
- Explain why subtraction, inversion, normalization, division by dimension, or a
  covariance block is present.
- Call out common confusion pairs explicitly, such as marginal versus conditional,
  prefit versus posterior residual, state dimension versus measurement dimension, and
  covariance versus correlation.
- When using an eigenvalue decomposition, identify what the eigenvectors and
  eigenvalues mean geometrically.
- When using a numerical example, calculate at least one result directly and, when
  useful, through the alternative interpretation to show that they agree.
- If the user asks whether a value is "about 1" or "about 3," distinguish the ensemble
  expectation, the single-sample distribution, the finite-sample mean, and effects from
  correlated samples.
- Use interpretation tables when there are multiple combinations, thresholds, or
  failure modes. Make every row state the direct observation and the likely mechanism.
- Keep uncertainty honest. A likely cause is not a confirmed cause.

## Formatting

- Use LaTeX for display and inline mathematics.
- Use short headings to expose the reasoning stages.
- Use formulas around the explanation, not as a substitute for it.
- Avoid decorative summaries, repetitive restatement, and unexplained jargon.
- Prefer concrete language such as "the measurement subtracts the part already
  explained by the posterior state" over abstract labels.

## Scope

- Default to answering in the conversation.
- Read a referenced document when it is needed for context, but do not edit it unless
  the user separately asks for a report or documentation change.
- Do not create a new document merely because the explanation is long.
