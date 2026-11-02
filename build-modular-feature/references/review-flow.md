# Review Flow

Use this reference for the standard review pass after implementation or investigation.

## Default Review Scope

Review:

- the current diff
- impacted callers and shared helpers
- touched config or pipeline stages
- tests that cover or should cover the change

Default focus:

- correctness
- regressions
- edge cases
- missing or weak tests
- module boundary drift
- file bloat and readability regressions

## Standard Order

1. Run the relevant checks first and note results.
2. Review the diff with the impacted context around it.
3. Check whether the structure stayed modular.
4. Report findings first, ordered by severity.
5. If no issues are found, say so clearly and note residual risk or test gaps.

## Using `$subagent-review`

If read-only subagents are available, use `$subagent-review` as the standard review path.

Requirements:

- keep the review single-level
- keep the review read-only
- do not ask the review subagent to modify files
- do not ask the review subagent to spawn another subagent
- give the subagent the diff scope, nearby callers/tests, and checks already run

Current local installation path:

- `C:\Users\liuzi\.codex\skills\subagent-review\SKILL.md`

## Reusable Review Prompt

```text
Review the changes I just made in this repository.

Goal:
- <one-sentence summary of the change>

Scope:
- Review the current diff and the impacted call sites/tests around it.
- Focus on correctness, regressions, edge cases, missing tests, module boundary drift, and file bloat.
- Treat this as read-only review. Do not modify files.
- Do not spawn additional subagents or delegate this review further.

Checks already run:
- <command and result, or "none">

Output:
- List findings first, ordered by severity.
- Include file paths and line numbers when possible.
- Call out missing tests or weak validation when relevant.
- If no issues are found, say that clearly and note any residual risk or test gaps.
```

## Main-Thread Fallback

If subagents are unavailable, run the same review in the main thread with the same scope and output contract. Do not skip review just because the delegated path is unavailable.
