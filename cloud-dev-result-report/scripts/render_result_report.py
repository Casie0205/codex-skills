#!/usr/bin/env python3
"""Render a self-contained HTML report for a cloud development result."""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def as_items(value: Any) -> List[Any]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [value]


def text(value: Any, fallback: str = "unknown") -> str:
    if value is None or value == "":
        return fallback
    return str(value)


def bullets(value: Any, empty: str = "None recorded.") -> str:
    items = as_items(value)
    if not items:
        return f'<p class="empty">{esc(empty)}</p>'
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def badge(value: Any) -> str:
    label = text(value, "UNKNOWN").upper().replace("_", " ")
    css = "neutral"
    if label in {"DONE", "PASS", "PASSED", "FIXED"}:
        css = "success"
    elif label in {"PARTIAL", "WARN", "WARNING", "PASS WITH FIXES"}:
        css = "warning"
    elif label in {"BLOCKED", "FAIL", "FAILED", "NOT VERIFIED"}:
        css = "danger"
    return f'<span class="badge {css}">{esc(label)}</span>'


def table(headers: List[str], rows: Iterable[List[str]], empty: str) -> str:
    rendered_rows = list(rows)
    if not rendered_rows:
        return f'<p class="empty">{esc(empty)}</p>'
    head = "".join(f"<th>{esc(item)}</th>" for item in headers)
    body = "".join(
        "<tr>"
        + "".join(
            f'<td data-label="{esc(headers[index])}">{cell}</td>'
            for index, cell in enumerate(row)
        )
        + "</tr>"
        for row in rendered_rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def render_files(files: Any) -> str:
    rows = []
    for item in as_items(files):
        if isinstance(item, dict):
            rows.append(
                [
                    f"<code>{esc(text(item.get('path')))}</code>",
                    esc(text(item.get("kind"))),
                    esc(text(item.get("purpose"), "")),
                ]
            )
        else:
            rows.append([f"<code>{esc(item)}</code>", "", ""])
    return table(["Path", "Kind", "Purpose"], rows, "No changed files recorded.")


def render_key_diffs(diffs: Any) -> str:
    blocks = []
    for item in as_items(diffs):
        if not isinstance(item, dict):
            blocks.append(f'<pre><code>{esc(item)}</code></pre>')
            continue
        language = esc(text(item.get("language"), "text"))
        blocks.append(
            '<article class="diff-card">'
            f'<div class="diff-head"><code>{esc(text(item.get("path")))}</code>'
            f'<span>{language}</span></div>'
            f'<p>{esc(text(item.get("explanation"), ""))}</p>'
            f'<pre><code class="language-{language}">{esc(text(item.get("code"), ""))}</code></pre>'
            "</article>"
        )
    if not blocks:
        return '<p class="empty">No key diff was selected.</p>'
    return "".join(blocks)


def render_verification(items: Any) -> str:
    rows = []
    for item in as_items(items):
        if not isinstance(item, dict):
            rows.append([esc(item), "", "", "", ""])
            continue
        rows.append(
            [
                f"<strong>{esc(text(item.get('name')))}</strong>",
                f"<code>{esc(text(item.get('command'), 'not recorded'))}</code>",
                esc(text(item.get("exit_code"), "not-run")),
                badge(item.get("result", "NOT VERIFIED")),
                esc(text(item.get("evidence"), "")),
            ]
        )
    return table(
        ["Check", "Command", "Exit", "Result", "Observed evidence"],
        rows,
        "No verification evidence recorded.",
    )


def render_acceptance(items: Any) -> str:
    rows = []
    for item in as_items(items):
        if not isinstance(item, dict):
            rows.append([esc(item), badge("NOT VERIFIED"), ""])
            continue
        rows.append(
            [
                esc(text(item.get("criterion"))),
                badge(item.get("status", "NOT VERIFIED")),
                esc(text(item.get("evidence"), "")),
            ]
        )
    return table(
        ["Acceptance criterion", "Status", "Evidence"],
        rows,
        "No acceptance criteria recorded.",
    )


def render_review(review: Any) -> str:
    if not isinstance(review, dict):
        return '<p class="empty">No review result recorded.</p>'
    rows = []
    for item in as_items(review.get("findings")):
        if not isinstance(item, dict):
            rows.append([esc(item), "", "", ""])
            continue
        rows.append(
            [
                badge(item.get("severity", "unknown")),
                esc(text(item.get("title"))),
                esc(text(item.get("resolution"))),
                esc(text(item.get("evidence"), "")),
            ]
        )
    findings = table(
        ["Severity", "Finding", "Resolution", "Evidence"],
        rows,
        "No review findings recorded.",
    )
    unresolved = bullets(review.get("unresolved"), "No unresolved review item.")
    return (
        f'<p><span class="label">Review status</span> {badge(review.get("status", "unknown"))}</p>'
        f"{findings}"
        '<h3>Unresolved review items</h3>'
        f"{unresolved}"
    )


def render_doc_discrepancy(value: Any) -> str:
    if isinstance(value, dict):
        status = value.get("status", "none")
        items = value.get("items")
    else:
        status = value or "none"
        items = []
    return f"<p>{badge(status)}</p>{bullets(items, 'No document discrepancy recorded.')}"


def validate(data: Dict[str, Any]) -> None:
    task = data.get("task")
    if not isinstance(task, dict):
        raise ValueError("task must be an object")
    missing = [
        field
        for field in ("id", "status", "repository", "branch", "base_commit", "result_commit")
        if not task.get(field)
    ]
    if missing:
        raise ValueError(f"missing task fields: {', '.join(missing)}")
    if str(task["status"]).upper() not in {"DONE", "PARTIAL", "BLOCKED"}:
        raise ValueError("task.status must be DONE, PARTIAL, or BLOCKED")
    summary = data.get("summary")
    if not isinstance(summary, dict) or not summary.get("requested"):
        raise ValueError("summary.requested is required")
    acceptance = data.get("acceptance")
    if not isinstance(acceptance, list):
        raise ValueError("acceptance must be an array")
    for index, item in enumerate(acceptance):
        if not isinstance(item, dict) or not str(item.get("criterion", "")).strip():
            raise ValueError(f"acceptance[{index}].criterion is required")
        result = str(item.get("status", "")).upper()
        if result not in {"PASS", "FAIL", "PARTIAL", "NOT VERIFIED"}:
            raise ValueError(f"acceptance[{index}].status is invalid")
        if not str(item.get("evidence", "")).strip():
            raise ValueError(f"acceptance[{index}].evidence is required")

    verification = data.get("verification")
    if not isinstance(verification, list):
        raise ValueError("verification must be an array")
    for index, item in enumerate(verification):
        if not isinstance(item, dict):
            raise ValueError(f"verification[{index}] must be an object")
        result = str(item.get("result", "")).upper()
        exit_code = str(item.get("exit_code", "")).strip()
        if result not in {"PASS", "FAIL", "PARTIAL", "NOT VERIFIED"}:
            raise ValueError(f"verification[{index}].result is invalid")
        if not str(item.get("evidence", "")).strip():
            raise ValueError(f"verification[{index}].evidence is required")
        if result == "PASS" and exit_code != "0":
            raise ValueError(
                f"verification[{index}] is PASS but exit_code is {exit_code or 'missing'}"
            )

    status = str(task["status"]).upper()
    if status == "DONE":
        if not acceptance:
            raise ValueError("DONE requires acceptance criteria")
        if not verification:
            raise ValueError("DONE requires at least one verification record")
        if any(str(item.get("status", "")).upper() != "PASS" for item in acceptance):
            raise ValueError("DONE requires every acceptance criterion to PASS")
        if any(str(item.get("result", "")).upper() != "PASS" for item in verification):
            raise ValueError("DONE requires every verification result to PASS")
        if any(str(item.get("exit_code", "")).strip() != "0" for item in verification):
            raise ValueError("DONE requires every verification exit_code to be 0")
        if str(task.get("change_set", "")).lower() != "none" and str(
            task["result_commit"]
        ).lower() == "none":
            raise ValueError("DONE code changes require a concrete result_commit")
        risks = data.get("risks", {})
        if isinstance(risks, dict) and as_items(risks.get("not_verified")):
            raise ValueError("DONE cannot contain not_verified items")
        review = data.get("review", {})
        if isinstance(review, dict) and as_items(review.get("unresolved")):
            raise ValueError("DONE cannot contain unresolved review items")


def build_html(data: Dict[str, Any]) -> str:
    task = data["task"]
    summary = data["summary"]
    changes = data.get("changes", {}) if isinstance(data.get("changes", {}), dict) else {}
    risks = data.get("risks", {}) if isinstance(data.get("risks", {}), dict) else {}
    generated_at = data.get("generated_at") or datetime.now().astimezone().isoformat(
        timespec="seconds"
    )
    task_title = text(task.get("title"), text(task.get("id")))
    commit_range = f"{text(task.get('base_commit'))}..{text(task.get('result_commit'))}"
    source_items = as_items(data.get("sources"))
    review = data.get("review", {})
    review_status = review.get("status", "UNKNOWN") if isinstance(review, dict) else "UNKNOWN"

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(task_title)} - Cloud Development Result</title>
<style>
:root {{
  --page: #edf0f3;
  --paper: #ffffff;
  --ink: #17212b;
  --muted: #5c6673;
  --line: #d7dde4;
  --accent: #1f5c8b;
  --success: #1f6f4a;
  --warning: #9a6700;
  --danger: #b42318;
  --soft: #f6f8fa;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--page);
  color: var(--ink);
  font: 15px/1.55 "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
}}
.page {{
  width: min(1440px, calc(100% - 48px));
  margin: 24px auto;
  background: var(--paper);
  border: 1px solid var(--line);
  box-shadow: 0 10px 30px rgba(23, 33, 43, 0.08);
}}
header {{
  padding: 34px 42px 30px;
  border-bottom: 5px solid var(--accent);
}}
.eyebrow {{
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}}
h1 {{ margin: 8px 0 16px; font-size: 34px; line-height: 1.2; letter-spacing: 0; }}
h2 {{ margin: 0 0 18px; font-size: 23px; letter-spacing: 0; }}
h3 {{ margin: 24px 0 10px; font-size: 17px; letter-spacing: 0; }}
p {{ margin: 9px 0; }}
code, pre {{ font-family: "Cascadia Mono", "Consolas", monospace; }}
code {{ font-size: 13px; overflow-wrap: anywhere; }}
pre {{
  margin: 12px 0 0;
  padding: 16px;
  overflow: auto;
  background: #111820;
  color: #e9eef4;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}}
section {{ padding: 28px 42px; border-bottom: 1px solid var(--line); }}
.meta, .summary-grid {{
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}}
.meta-item, .summary-card {{
  padding: 12px 14px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--soft);
  min-width: 0;
}}
.meta-item span, .label {{
  display: block;
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}}
.meta-item strong, .summary-card strong {{ display: block; margin-top: 4px; overflow-wrap: anywhere; }}
.task-line {{ overflow-wrap: anywhere; }}
.summary-grid {{ grid-template-columns: 1.25fr 1.25fr 1fr 1fr; }}
.badge {{
  display: inline-block;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}}
.success {{ background: #e7f4ed; color: var(--success); }}
.warning {{ background: #fff3d6; color: var(--warning); }}
.danger {{ background: #fde8e7; color: var(--danger); }}
.neutral {{ background: #e9edf2; color: #46515e; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 14px; table-layout: fixed; }}
th, td {{
  padding: 11px 12px;
  border: 1px solid var(--line);
  vertical-align: top;
  text-align: left;
  overflow-wrap: anywhere;
}}
th {{ background: #edf2f6; font-size: 13px; }}
td {{ font-size: 14px; }}
th:nth-child(1), td:nth-child(1) {{ width: 24%; }}
ul {{ margin: 8px 0 0; padding-left: 22px; }}
li + li {{ margin-top: 5px; }}
.empty {{ color: var(--muted); font-style: italic; }}
.diff-card {{ margin-top: 16px; border: 1px solid var(--line); border-radius: 6px; }}
.diff-head {{
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  background: var(--soft);
}}
.diff-card p {{ padding: 0 12px; }}
.diff-card pre {{ margin: 0; border-radius: 0 0 6px 6px; }}
.notice {{
  border-left: 4px solid var(--accent);
  padding: 11px 14px;
  background: #f1f6fa;
}}
footer {{ padding: 22px 42px 30px; color: var(--muted); font-size: 12px; }}
@media (max-width: 900px) {{
  .page {{ width: calc(100% - 20px); margin: 10px auto; }}
  header, section, footer {{ padding-left: 20px; padding-right: 20px; }}
  .meta, .summary-grid {{ grid-template-columns: 1fr 1fr; }}
}}
@media (max-width: 640px) {{
  .meta, .summary-grid {{ grid-template-columns: 1fr; }}
  table, thead, tbody, tr, th, td {{ display: block; width: 100%; }}
  thead {{ display: none; }}
  tr {{ margin-top: 12px; border: 1px solid var(--line); }}
  td {{ border: 0; border-bottom: 1px solid var(--line); }}
  td:last-child {{ border-bottom: 0; }}
  td::before {{
    content: attr(data-label);
    display: block;
    margin-bottom: 3px;
    color: var(--muted);
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
  }}
}}
</style>
</head>
<body>
<main class="page" data-task-id="{esc(task['id'])}" data-status="{esc(task['status'])}">
  <header>
    <div class="eyebrow">Cloud Development Result</div>
    <h1>{esc(task_title)}</h1>
    <p class="task-line">{badge(task.get("status"))} <strong>{esc(task["id"])}</strong></p>
    <div class="meta">
      <div class="meta-item"><span>Repository</span><strong>{esc(task["repository"])}</strong></div>
      <div class="meta-item"><span>Branch</span><strong>{esc(task["branch"])}</strong></div>
      <div class="meta-item"><span>Commit range</span><strong>{esc(commit_range)}</strong></div>
      <div class="meta-item"><span>Finished</span><strong>{esc(task.get("finished_at", "unknown"))}</strong></div>
    </div>
  </header>

  <section>
    <h2>Executive Summary</h2>
    <div class="summary-grid">
      <div class="summary-card"><strong>Requested</strong><p>{esc(summary["requested"])}</p></div>
      <div class="summary-card"><strong>Implemented</strong>{bullets(summary.get("implemented"))}</div>
      <div class="summary-card"><strong>Change set</strong><p>{esc(task.get("change_set", "unknown"))}</p></div>
      <div class="summary-card"><strong>Review</strong><p>{badge(review_status)}</p></div>
    </div>
  </section>

  <section>
    <h2>Data Flow and Module Boundaries</h2>
    <h3>Data flow</h3>
    {bullets(summary.get("data_flow"), "No data-flow change recorded.")}
    <h3>Module boundaries</h3>
    {bullets(summary.get("module_boundaries"), "No module-boundary decision recorded.")}
  </section>

  <section>
    <h2>Changes</h2>
    <p><span class="label">Diff summary</span>{esc(changes.get("diff_stat", "unknown"))}</p>
    {render_files(changes.get("files"))}
    <h3>Removed obsolete paths</h3>
    {bullets(changes.get("removed_obsolete_paths"), "No obsolete path removed.")}
    <h3>Selected key diffs</h3>
    {render_key_diffs(changes.get("key_diffs"))}
  </section>

  <section>
    <h2>Verification Evidence</h2>
    <h3>Acceptance criteria</h3>
    {render_acceptance(data.get("acceptance"))}
    <h3>Commands and observed evidence</h3>
    {render_verification(data.get("verification"))}
  </section>

  <section>
    <h2>Code Review</h2>
    {render_review(data.get("review"))}
  </section>

  <section>
    <h2>Risks and Open Items</h2>
    <h3>Risks</h3>
    {bullets(risks.get("items"), "No remaining risk recorded.")}
    <h3>Not verified</h3>
    {bullets(risks.get("not_verified"), "No unverified item recorded.")}
    <p class="notice"><strong>Next action:</strong> {esc(risks.get("next_action", "none"))}</p>
  </section>

  <section>
    <h2>Document Discrepancy</h2>
    {render_doc_discrepancy(data.get("doc_discrepancy"))}
  </section>

  <footer>
    <p><strong>Generated from:</strong> {esc(", ".join(str(item) for item in source_items) or "unspecified artifacts")}</p>
    <p><strong>Generated at:</strong> {esc(generated_at)}</p>
    <p>This report summarizes the result bundle. Raw logs, patch files, and review records remain authoritative.</p>
  </footer>
</main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()

    temp_path = None
    try:
        output_root = args.output_root.resolve(strict=True)
        input_path = args.input.resolve(strict=True)
        output_path = args.output.resolve(strict=False)
        if not output_root.is_dir():
            raise ValueError(f"output root is not a directory: {output_root}")
        try:
            input_path.relative_to(output_root)
            output_path.relative_to(output_root)
        except ValueError as exc:
            raise ValueError("input and output must stay within output_root") from exc
        if input_path == output_path:
            raise ValueError("input and output must be different files")

        data = json.loads(input_path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise ValueError("top-level JSON value must be an object")
        validate(data)
        document = build_html(data)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=str(output_path.parent),
            prefix=".development-result-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(document)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, output_path)
        temp_path = None
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink()
            except OSError:
                pass

    print(f"Wrote {output_path} ({output_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
