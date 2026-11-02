# Output Contract

Use these output shapes to keep the workflow predictable and easy to scan.

## 1. Codebase Structure Summary

Include:

- entrypoint or top-level flow
- adjacent or similar features
- likely integration point
- config and test surface
- key structural risks

## 2. Unresolved Questions

For each question, include:

- the question
- why it matters
- recommended default when reasonable

Ask only for decisions that exploration could not settle.

## 3. Architecture Options

For each option, include:

- short name
- module layout
- pros
- cons

For the recommendation, include:

- why it fits the current codebase
- what stays in main files
- what moves into dedicated modules

## 4. File and Module Split Plan

List:

- files to create
- files to modify
- single responsibility of each new module
- which central files remain thin and what they should contain

Avoid vague plans such as "update utils" or "adjust helpers as needed."

## 5. Implementation Checklist

Use a short checklist with action-oriented items such as:

- add module
- wire module into flow
- update config
- add tests
- run checks

Prefer module-level steps over a long file-by-file dump.

## 6. Validation Plan

Include:

- commands or checks to run
- expected signals of success
- any gaps that cannot be verified locally

## 7. Review Results

Structure:

- findings first, ordered by severity
- file paths and line numbers when possible
- missing tests or weak validation
- if no issues, explicit "no issues found" statement plus residual risk

## 8. Final Summary

Include:

- what was built
- key module-boundary decisions
- checks run
- review outcome
- suggested next steps

Keep the summary concrete, short, and implementation-focused.
