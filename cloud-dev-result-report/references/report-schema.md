# Cloud Development Result Report Schema

状态：active | 更新日期：2026-11-11

## 目录

- [1. Purpose](#1-purpose)
- [2. Required Fields](#2-required-fields)
- [3. Optional Fields](#3-optional-fields)
- [4. Example](#4-example)
- [5. Evidence Rules](#5-evidence-rules)

## 1. Purpose

`development-result.json` is the structured, evidence-backed input used by
`scripts/render_result_report.py`. It summarizes the cloud task without replacing
`result.md`, `verification.log`, `cloud-code.patch` when present, or `review.md`.

## 2. Required Fields

| Field | Type | Meaning |
| --- | --- | --- |
| `task.id` | string | Exact task ID |
| `task.status` | string | `DONE`, `PARTIAL`, or `BLOCKED` |
| `task.repository` | string | Verified cloud repository path |
| `task.branch` | string | Checked-out branch |
| `task.base_commit` | string | Baseline commit |
| `task.result_commit` | string | Result commit, or `none` for no-change/blocked |
| `summary.requested` | string | User-requested outcome |
| `summary.implemented` | string or list | What was actually implemented |
| `acceptance` | array | Acceptance criteria with status and evidence |
| `verification` | array | Real commands and observed outcomes |

Each acceptance item requires:

| Field | Meaning |
| --- | --- |
| `criterion` | One user-observable acceptance criterion |
| `status` | `PASS`, `FAIL`, `PARTIAL`, or `NOT VERIFIED` |
| `evidence` | Direct evidence that supports the status |

Each verification item supports:

| Field | Meaning |
| --- | --- |
| `name` | Build, unit test, runtime test, or check name |
| `command` | Exact command |
| `exit_code` | Integer or `not-run` |
| `result` | `PASS`, `FAIL`, `PARTIAL`, or `NOT VERIFIED` |
| `evidence` | Concise observed output |
| `log_path` | Related log file, when available |

## 3. Optional Fields

Supported optional sections:

- `task.title`, `task.change_set`, `task.finished_at`
- `summary.data_flow`, `summary.module_boundaries`
- `changes.files`, `changes.diff_stat`, `changes.key_diffs`
- `changes.removed_obsolete_paths`
- `review.status`, `review.findings`, `review.unresolved`
- `risks.items`, `risks.not_verified`, `risks.next_action`
- `doc_discrepancy.status`, `doc_discrepancy.items`
- `sources`

Change item fields: `path`, `kind`, `purpose`.

Key diff fields: `path`, `language`, `code`, `explanation`.

Review finding fields: `severity`, `title`, `resolution`, `evidence`.

## 4. Example

```json
{
  "task": {
    "id": "ctclib-imu-delay-resample",
    "title": "IMU timestamp delay and resampling",
    "status": "DONE",
    "repository": "D:\\Code\\ctclib-nav",
    "branch": "main",
    "base_commit": "0123456",
    "result_commit": "abcdef0",
    "change_set": "code",
    "finished_at": "2026-11-11 18:00 +08:00"
  },
  "summary": {
    "requested": "Add config-driven IMU timestamp correction and resampling.",
    "implemented": [
      "Added optional imu_timestamp_delay_ms config.",
      "Added a focused time-alignment and resampling module.",
      "Connected the module at the single post-processing IMU ingestion point."
    ],
    "data_flow": [
      "Decoded IMU sample -> timestamp delay -> fixed-rate resampler -> INS consumer"
    ],
    "module_boundaries": [
      "Config reader parses and validates the optional value.",
      "ImuTimeAlignment owns delay, windowing, reset behavior, and callback propagation.",
      "Existing processor files only initialize and wire the module."
    ]
  },
  "acceptance": [
    {
      "criterion": "Explicit zero enables resampling while an omitted key preserves behavior.",
      "status": "PASS",
      "evidence": "Config presence and zero-value regression tests passed."
    }
  ],
  "changes": {
    "diff_stat": "6 files changed, 420 insertions, 18 deletions",
    "files": [
      {
        "path": "proj/ctclib_app/src/ImuTimeAlignment.c",
        "kind": "added",
        "purpose": "Implement fixed-grid resampling"
      }
    ],
    "key_diffs": [
      {
        "path": "proj/ctclib_app/src/ImuTimeAlignment.c",
        "language": "c",
        "code": "period_us = llround(1000000.0 / config->imu_freq);",
        "explanation": "Defines the fixed output interval from the configured IMU rate."
      }
    ],
    "removed_obsolete_paths": []
  },
  "verification": [
    {
      "name": "VS2019 build",
      "command": "windows-cpp-build start_build_project project_path=D:\\Code\\ctclib-nav\\proj\\ctclib_app\\ctclib_app.vcxproj configuration=Release; wait_for_build until terminal",
      "exit_code": 0,
      "result": "PASS",
      "evidence": "job status=succeeded, result.success=true, result.exit_code=0",
      "log_path": "D:\\Output\\build\\ctclib_app.log"
    }
  ],
  "review": {
    "status": "PASS_WITH_FIXES",
    "findings": [
      {
        "severity": "P1",
        "title": "Reset retained partial accumulator",
        "resolution": "Fixed",
        "evidence": "Accumulator is cleared on every reset and covered by regression test."
      }
    ],
    "unresolved": []
  },
  "risks": {
    "items": [],
    "not_verified": [],
    "next_action": "none"
  },
  "doc_discrepancy": {
    "status": "none",
    "items": []
  },
  "sources": [
    "result.md",
    "changed-files.txt",
    "verification.log",
    "cloud-code.patch",
    "review.md"
  ]
}
```

## 5. Evidence Rules

- Use exact paths, commands, commits, exit codes, and observed results.
- Keep long logs out of the report; retain the command and decisive lines.
- A clean build does not prove runtime behavior, and a smoke test does not prove unit-test
  coverage. Keep evidence scopes separate.
- A verification item marked `PASS` must have exit code `0`.
- `DONE` requires at least one acceptance item and one verification item, every acceptance
  status and verification result must be `PASS`, every verification exit code must be `0`,
  a concrete result commit for code changes, and empty `not_verified` and unresolved review
  lists.
- When the task defines `server_build_targets`, include one verification item for every
  server target and every other affected production target; do not collapse them into one
  generic build row.
- Do not include secrets, tokens, credentials, private keys, or unrelated user data.
- The HTML status and values must match `result.md` and the underlying artifacts.
