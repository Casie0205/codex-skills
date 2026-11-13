# Windows Shell Policy

状态：active | 更新日期：2026-11-12

## 目录

- [1. Shell Selection](#1-shell-selection)
- [2. File Operations](#2-file-operations)
- [3. PowerShell Rules](#3-powershell-rules)
- [4. Python Discovery](#4-python-discovery)
- [5. Failure Escalation](#5-failure-escalation)
- [6. Verification](#6-verification)

## 1. Shell Selection

Use one native Windows shell for the whole task:

1. Prefer PowerShell 7, `pwsh`.
2. Fall back to Windows PowerShell, `powershell`.
3. Do not invoke PowerShell through Bash with nested `powershell -Command` strings.

If the command runner only exposes Bash, create a `.ps1` file with the file tools and
run it through `-File`. Do not put pipes, variables, quotes, or multiple statements into
an inline command passed through another shell.

## 2. File Operations

Use `Read`, `Edit`, and `Write` tools before shell commands:

- Use `Read` to establish exact file content.
- If the `text-edit` MCP is configured, prefer its `replace_text` tool for source
  edits. The tool owns encoding detection, BOM preservation, newline preservation,
  ambiguity checks, and atomic writes.
- Use one minimal `Edit` only when `replace_text` is unavailable or the target is a
  non-source file with no encoding risk.
- Do not use PowerShell `Get-Content` as a substitute for `Read`.
- Do not use `Write` to rewrite a large existing file merely because `Edit` failed.

If `replace_text` is available, pass the exact block and replacement directly. Do not
pre-convert the file to UTF-8 and do not add an encoding argument on the first attempt.
The tool normally detects UTF-8, UTF-8 BOM, UTF-16 LE/BE, and legacy Windows text.

Use the structured failure result:

1. `NO_MATCH`: retry once with one returned candidate context block.
2. `AMBIGUOUS_MATCH`: add surrounding context or pass the correct `occurrence`.
3. `STALE_FILE`: re-read the file and retry with its current SHA-256.
4. `ENCODING_CONFIRMATION_REQUIRED`: inspect the returned encoding, use `dry_run`
   once, and retry with an explicit `encoding` only if the decoded content is correct.
5. `MIXED_NEWLINES`, `ENCODING_UNREPRESENTABLE`, `DECODE_ERROR`, or `WRITE_ERROR`:
   stop and report the result. Do not fall back to a full-file `Write`.

If `replace_text` is unavailable and `Edit` fails:

1. Re-read the exact region.
2. Check BOM, tabs, CRLF/LF, trailing spaces, and encoding.
3. Stop changing the anchor after two failed `Edit` attempts.
4. Use `scripts/replace_literal.py` with old/new text stored in separate UTF-8 files.

Example:

```powershell
& $PYTHON @PYTHON_ARGS "<skill-root>\scripts\replace_literal.py" `
  --path "<target-file>" `
  --old-file "<old-snippet.txt>" `
  --new-file "<new-snippet.txt>" `
  --expected-count 1
```

The command is a dry run without `--apply`. Apply only after the match count and line
number are correct:

```powershell
& $PYTHON @PYTHON_ARGS "<skill-root>\scripts\replace_literal.py" `
  --path "<target-file>" `
  --old-file "<old-snippet.txt>" `
  --new-file "<new-snippet.txt>" `
  --expected-count 1 `
  --apply
```

The helper preserves the source encoding, BOM, and dominant newline style. It does not
require Python third-party packages.

Store the temporary old/new snippet files under the task `output_path`, never inside the
repository unless the task explicitly allows those paths.

For a BOM-less file with non-ASCII content, dry-run reports
`encoding_confidence: utf8-assumed` or `locale-assumed`. Re-run with an explicit
`--encoding` before applying. A file with mixed CRLF/LF/CR newlines returns
`mixed_newlines` and must not be modified by this helper.

## 3. PowerShell Rules

- Use `-LiteralPath` for file-system paths.
- Prefer single-quoted literal paths.
- Do not nest pipelines inside `powershell -Command`.
- Put multi-command scripts in a `.ps1` file and execute that file.
- Use `-NoProfile -NonInteractive` for automation.
- Do not use alias, profile, or current-location assumptions.

## 4. Python Discovery

Python command names differ on Windows. Check in this order:

```powershell
$PYTHON = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
$PYTHON_ARGS = @()
if (-not $PYTHON) {
    $PYTHON = (Get-Command py.exe -ErrorAction SilentlyContinue).Source
    $PYTHON_ARGS = @("-3")
}
if (-not $PYTHON) {
    $PYTHON = (Get-Command python3.exe -ErrorAction SilentlyContinue).Source
}
if (-not $PYTHON) {
    throw "No Python interpreter found"
}
& $PYTHON @PYTHON_ARGS --version
```

If the runner exposes only Bash, check the names separately with `command -v python`,
`command -v py`, and `command -v python3`.

`python3` not found does not prove Python is absent. Prefer `python` or `py -3`; use an
explicit executable path only after discovery confirms it. Verify the selected command
with `python --version` or `py -3 --version` before using it.

## 5. Failure Escalation

Use bounded failure escalation:

- First shell quoting or pipe failure: switch to a script file.
- Second failure of the same form: stop and report the exact command and error.
- First `Edit` mismatch: use the `text-edit` MCP `replace_text` tool when available.
- If `replace_text` is unavailable, inspect exact bytes and whitespace, then use
  `replace_literal.py` after the second `Edit` mismatch.
- A `replace_text` result with candidates is actionable evidence. Use it for one
  precise retry instead of rewriting the whole file.
- `replace_literal.py` returning `no_match`, `count_mismatch`, `mixed_newlines`,
  `ambiguous_encoding`, or `error` is terminal. Report the helper JSON and stop.
- Never rewrite an existing file with `Write` after an edit failure unless the user
  explicitly approves a full-file replacement.
- Never chain Bash -> inline PowerShell -> inline Python -> full-file `Write` as a
  workaround for the same edit.

## 6. Verification

After every edit:

```powershell
git diff --check
git diff --stat
git diff -- <changed-file>
```

Read the changed region back and confirm that encoding, newlines, indentation, and
unrelated lines were preserved. A successful script exit code is not enough without
inspecting the diff.
