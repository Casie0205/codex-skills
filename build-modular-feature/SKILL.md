---
name: build-modular-feature
description: This skill should be used when Codex needs to add or extend functionality in an existing codebase or framework, especially when the user asks to extend the current architecture, define module boundaries, keep the main flow clean, split behavior into separate modules instead of one file, or review current changes for regressions, edge cases, and structural issues.
---

# Build Modular Feature

Add or extend capabilities in an existing codebase without bloating the main flow or central files. Understand the codebase first, resolve ambiguity before implementation, and keep new behavior in focused modules with explicit responsibilities.

## Quick Start

1. Confirm the requested capability, scope, constraints, and success criteria.
2. Explore the codebase before asking design questions.
3. Identify extension points, adjacent features, key files, config, and current tests.
4. Ask clarifying questions only for decisions that exploration cannot settle.
5. Design two or three approaches and recommend one.
6. Implement with thin orchestration and separate modules.
7. Run checks, review the change, and summarize the outcome.

If the user explicitly asks for design only, stop after the architecture and validation plan. Otherwise, continue through implementation, review, and summary.

## Hard Rules

- Keep main files thin. Leave entrypoints, top-level workflows, routers, pipelines, or controllers responsible for orchestration, registration, and wiring only.
- Split responsibilities aggressively enough to keep code readable. Put business logic, parsing, transformation, validation, adapters, persistence, and output formatting into separate modules when they serve different jobs.
- Avoid god files. Do not keep appending unrelated logic to the current largest or most convenient file.
- Prefer local patterns. Reuse existing abstractions, naming, folder layout, and helper APIs before inventing new structure.
- Expand scope only when required by correctness. Do not mix opportunistic cleanup with the requested feature.
- Treat modularity as a quality requirement. Review for correctness and for structure.

## Workflow

### 1. Discovery

Clarify:

- requested capability
- user-visible outcome
- constraints, risks, and deadlines
- success criteria
- whether implementation is required now or design-first output is enough

Summarize the goal before moving on.

### 2. Codebase Exploration

Inspect before asking:

- entrypoints and control flow
- similar or adjacent features
- current abstractions and module boundaries
- configuration, schemas, and tests
- likely integration points and risks

Use `references/phase-playbook.md` to make the exploration pass systematic.

### 3. Clarifying Questions

Ask only after exploration. Focus on:

- edge cases and failure handling
- backward compatibility
- integration boundaries
- performance or rollout constraints
- design preferences that materially change the implementation

If the user leaves a preference open, recommend a default that fits the codebase.

### 4. Architecture and Module Boundaries

Produce two or three approaches when the architecture is non-trivial:

- minimal changes
- clean architecture
- pragmatic balance

For the recommended approach, define:

- which files stay thin
- which new modules or directories are needed
- each module's single responsibility
- data flow between orchestration and leaf modules
- config, tests, and review surface

Use `references/modularity-rules.md` as a hard gate.

### 5. Implementation

Implement only after the design is stable enough for the task. During implementation:

- modify central files mainly to wire in new modules
- place new behavior in focused files
- keep naming and public interfaces consistent with existing code
- add focused tests proportional to risk
- avoid piling helpers, parsing, output, and business rules into one file

### 6. Quality Review

Run relevant checks first and record what was verified.

For review:

- default scope: current diff, impacted callers, shared helpers, config, and tests
- default focus: correctness, regressions, edge cases, missing tests, module boundary drift, file bloat, and readability regressions

If read-only subagents are available, use `$subagent-review` for the review pass. Keep the review single-level and read-only. Do not delegate further. If subagents are unavailable, perform the same review in the main thread.

Use `references/review-flow.md` for the standard procedure and review prompt.

### 7. Summary

Report:

- what was built
- key structure decisions
- files created or changed
- checks run and outcomes
- review findings or residual risk
- suggested next steps

## Required Outputs

Produce these artifacts as the work progresses:

- codebase structure summary
- unresolved questions list
- architecture options with recommendation
- file and module split plan
- implementation checklist
- validation plan
- review results
- final summary

Use `references/output-contract.md` for the expected shape.

## Reference Map

Load only what is needed:

- `references/phase-playbook.md`: detailed phase actions, decision points, and default prompts
- `references/modularity-rules.md`: structural guardrails, file-splitting heuristics, and anti-patterns
- `references/review-flow.md`: review procedure, `$subagent-review` prompt, and fallback behavior
- `references/output-contract.md`: required artifacts and response shapes for planning, implementation, review, and closeout

## When To Stop And Ask

Pause and ask when:

- multiple architectures are plausible and the choice changes public behavior or large structural commitments
- rollout, compatibility, or data semantics are genuinely ambiguous
- the user must choose between conflicting trade-offs

Otherwise, make the smallest reasonable assumption that matches the existing codebase and continue.
