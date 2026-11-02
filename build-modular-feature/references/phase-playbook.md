# Phase Playbook

Use this reference when the task needs a fuller walkthrough than the main `SKILL.md`.

## 1. Discovery

Capture the minimum decision surface before touching code:

- feature goal
- intended audience or caller
- explicit success criteria
- constraints: deadlines, compatibility, rollout, performance, security, data shape
- whether the user wants implementation, design only, or review only

Output:

- one-paragraph summary of the goal
- explicit in-scope / out-of-scope notes when scope is easy to drift

## 2. Codebase Exploration

Inspect local reality before asking product questions.

Trace:

- the entrypoints for the current workflow
- similar or neighboring features
- config, schema, flags, and data flow
- test coverage and validation commands
- existing abstractions that should be reused

Answer these questions from the repo before asking the user:

- Where does the current flow start?
- Which file owns orchestration?
- Which modules own parsing, business logic, adapters, storage, output, or UI state?
- Which tests or fixtures already cover nearby behavior?

Output:

- architecture summary
- list of files that matter most
- candidate extension points
- likely risk areas

## 3. Clarifying Questions

Ask only after the exploration pass. Focus on decisions that materially change the implementation:

- edge-case semantics
- backward compatibility
- failure and retry behavior
- integration ownership
- performance limits
- rollout or migration expectations

If a preference is not specified, recommend the smallest change that matches local patterns.

Output:

- numbered unresolved questions
- recommended default beside each question when helpful

## 4. Architecture and Module Boundaries

When the task is non-trivial, compare two or three approaches:

1. Minimal changes
2. Clean architecture
3. Pragmatic balance

For each approach, define:

- affected modules
- new files or folders
- responsibilities per module
- integration points
- test impact
- main trade-offs

Recommend one approach. Favor pragmatic balance unless a stronger reason points elsewhere.

Output:

- short comparison
- recommended approach with rationale
- explicit module split plan

## 5. Implementation

Implement with narrow edits and clear ownership.

During implementation:

- keep central files mostly as wiring
- move branching logic and transformations into leaf modules
- add or update tests near the changed behavior
- preserve local naming and public interfaces unless the task requires change

If a file starts accumulating multiple new responsibilities, stop and split it.

Output:

- progress notes tied to modules, not just files
- implementation checklist

## 6. Quality Review

Run the relevant checks first. Then review:

- current diff
- impacted callers
- shared helpers
- config surface
- tests that cover or should cover the change

Review for:

- correctness bugs
- regression risk
- edge cases
- missing validation
- module boundary erosion
- oversized or mixed-responsibility files

Use `references/review-flow.md` for the standard review path.

## 7. Summary

Close with:

- what changed
- why the chosen structure fits the codebase
- checks run
- review findings or residual risk
- suggested follow-up work

Keep the summary concrete enough that another engineer can pick up where the work stopped.
