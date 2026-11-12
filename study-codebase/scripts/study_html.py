#!/usr/bin/env python3
"""Render the self-contained screenshot-friendly HTML study report."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from study_common import (
    as_items,
    as_sentence,
    confidence_badge,
    esc,
    require_dict,
    text,
)


def render_bullets(value: Any, empty: str = "無") -> str:
    items = as_items(value)
    if not items:
        return f'<p class="empty">{esc(empty)}</p>'
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def render_reading_path(items: list) -> str:
    blocks = []
    for item in items:
        blocks.append(
            '<li class="screenshot-block">'
            f'<strong>{esc(item.get("order"))}. {esc(item.get("name"))}</strong>'
            f'<code>{esc(item.get("source"))}</code>'
            f'<span>{esc(item.get("why"))}</span>'
            "</li>"
        )
    return '<ol class="reading-path">' + "".join(blocks) + "</ol>"


def render_flow(items: list) -> str:
    blocks = []
    for item in items:
        code = text(item.get("code"), "")
        code_block = ""
        if code:
            language = esc(text(item.get("code_language"), "text"))
            code_block = f'<pre><code class="language-{language}">{esc(code)}</code></pre>'
        fields = [
            ("caller", "呼叫者"),
            ("callee", "被呼叫者"),
            ("input", "輸入"),
            ("output", "輸出"),
            ("state", "狀態與生命週期"),
            ("normal", "正常分支"),
            ("error", "錯誤分支"),
            ("next", "下一步閱讀"),
        ]
        definitions = "".join(
            f"<dt>{esc(label)}</dt><dd>{esc(text(item.get(key), '未記錄'))}</dd>"
            for key, label in fields
            if item.get(key) not in (None, "", [])
        )
        blocks.append(
            '<article class="flow-step screenshot-block">'
            '<div class="step-head">'
            f'<span class="step-number">{esc(item.get("step"))}</span>'
            f'<h3>{esc(item.get("name"))}</h3>'
            f'{confidence_badge(item.get("confidence"))}'
            "</div>"
            f'<p class="source"><code>{esc(item.get("source"))}</code></p>'
            f'<p class="purpose">{esc(item.get("purpose"))}</p>'
            f"{code_block}"
            f'<dl class="flow-meta">{definitions}</dl>'
            "</article>"
        )
    return "".join(blocks)


def render_symbols(items: list) -> str:
    if not items:
        return '<p class="empty">未記錄關鍵符號。</p>'
    rows = []
    for item in items:
        rows.append(
            "<tr>"
            f"<td><strong>{esc(text(item.get('name')))}</strong></td>"
            f"<td>{esc(text(item.get('kind')))}</td>"
            f"<td><code>{esc(text(item.get('defined_at')))}</code></td>"
            f"<td>{esc(text(item.get('role'), ''))}</td>"
            f"<td>{confidence_badge(item.get('confidence'))}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>符號</th><th>類型</th><th>定義位置</th>"
        "<th>責任</th><th>置信度</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def render_structures(items: list) -> str:
    if not items:
        return '<p class="empty">未記錄關鍵資料結構。</p>'
    blocks = []
    for item in items:
        blocks.append(
            '<article class="info-block screenshot-block">'
            f'<div class="block-head"><h3>{esc(text(item.get("name")))}</h3>'
            f'{confidence_badge(item.get("confidence"))}</div>'
            f'<p class="source"><code>{esc(text(item.get("defined_at")))}</code></p>'
            f'<p>{esc(text(item.get("purpose"), ""))}</p>'
            f'<dl class="flow-meta">'
            f'<dt>欄位</dt><dd>{esc(as_sentence(item.get("fields"), "未記錄"))}</dd>'
            f'<dt>所有權</dt><dd>{esc(text(item.get("ownership"), "未記錄"))}</dd>'
            "</dl></article>"
        )
    return "".join(blocks)


def render_config(items: list) -> str:
    if not items:
        return '<p class="empty">未記錄配置映射。</p>'
    rows = []
    for item in items:
        rows.append(
            "<tr>"
            f"<td><code>{esc(text(item.get('key')))}</code></td>"
            f"<td><code>{esc(text(item.get('source')))}</code></td>"
            f"<td><code>{esc(text(item.get('consumed_at')))}</code></td>"
            f"<td>{esc(text(item.get('meaning'), ''))}</td>"
            f"<td>{esc(text(item.get('default'), ''))}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>參數</th><th>配置來源</th><th>消費位置</th>"
        "<th>意義</th><th>預設值</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def render_evidence(items: list) -> str:
    if not items:
        return '<p class="empty">未記錄額外證據。</p>'
    blocks = []
    for item in items:
        blocks.append(
            '<li class="screenshot-block">'
            f'{confidence_badge(item.get("confidence"))}'
            f'<span>{esc(text(item.get("claim")))}</span>'
            f'<code>{esc(text(item.get("source")))}</code>'
            "</li>"
        )
    return '<ul class="evidence-list">' + "".join(blocks) + "</ul>"


def render_questions(questions: dict) -> str:
    groups = [
        ("confirmed", "已確認"),
        ("inferred", "推測"),
        ("open", "待確認"),
    ]
    blocks = []
    for key, label in groups:
        block = render_bullets(as_items(questions.get(key)), "無")
        blocks.append(
            f'<div class="question-group screenshot-block"><h3>{esc(label)}</h3>{block}</div>'
        )
    return "".join(blocks)


STYLE = """
:root {
  --page: #f2f4f6;
  --paper: #ffffff;
  --ink: #17212b;
  --muted: #5b6672;
  --line: #d8dee5;
  --accent: #1c5d86;
  --soft: #f7f9fb;
  --success: #1d6b48;
  --warning: #8b6200;
  --danger: #a62b24;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--page);
  color: var(--ink);
  font: 15px/1.6 "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
  overflow-wrap: anywhere;
}
.page {
  width: min(1120px, calc(100% - 32px));
  margin: 20px auto;
  background: var(--paper);
  border: 1px solid var(--line);
  box-shadow: 0 10px 28px rgba(23, 33, 43, 0.07);
}
header { padding: 30px 38px 26px; border-bottom: 5px solid var(--accent); }
.eyebrow {
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
h1 { margin: 8px 0 14px; font-size: 32px; line-height: 1.25; letter-spacing: 0; }
h2 { margin: 0 0 16px; font-size: 22px; letter-spacing: 0; }
h3 { margin: 0; font-size: 17px; letter-spacing: 0; }
p { margin: 9px 0; }
code, pre { font-family: "Cascadia Mono", Consolas, monospace; }
code { font-size: 13px; overflow-wrap: anywhere; }
pre {
  margin: 12px 0 0;
  padding: 14px;
  background: #111820;
  color: #edf2f7;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  border-radius: 5px;
  font-size: 13px;
  line-height: 1.5;
}
.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}
.success { background: #e4f3e9; color: var(--success); }
.warning { background: #fff1cf; color: var(--warning); }
.danger { background: #fbe6e5; color: var(--danger); }
.meta {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-top: 16px;
}
.meta-item {
  min-width: 0;
  padding: 10px 12px;
  border: 1px solid var(--line);
  background: var(--soft);
  border-radius: 5px;
}
.meta-item span {
  display: block;
  color: var(--muted);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}
.meta-item strong { display: block; margin-top: 3px; overflow-wrap: anywhere; }
nav.toc {
  padding: 18px 38px;
  border-bottom: 1px solid var(--line);
  background: var(--soft);
}
nav.toc strong { display: block; margin-bottom: 6px; }
nav.toc a {
  color: var(--accent);
  text-decoration: none;
  margin-right: 16px;
  white-space: nowrap;
}
section { padding: 26px 38px; border-bottom: 1px solid var(--line); }
.lead {
  padding: 12px 15px;
  border-left: 4px solid var(--accent);
  background: #f1f6fa;
  font-size: 16px;
}
.reading-path { list-style: none; padding: 0; margin: 12px 0 0; }
.reading-path li {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 4px 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--line);
}
.reading-path li span { grid-column: 1 / -1; color: var(--muted); }
.flow-step, .info-block {
  margin-top: 16px;
  padding: 18px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: #fff;
}
.step-head, .block-head {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: space-between;
}
.step-head h3, .block-head h3 { flex: 1; }
.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  font-weight: 700;
}
.source { margin: 8px 0 4px; }
.source code { color: var(--accent); }
.purpose { font-weight: 600; }
.flow-meta {
  display: grid;
  grid-template-columns: 125px 1fr;
  gap: 6px 14px;
  margin: 14px 0 0;
  padding-top: 12px;
  border-top: 1px solid var(--line);
}
.flow-meta dt { color: var(--muted); font-weight: 700; }
.flow-meta dd { margin: 0; overflow-wrap: anywhere; }
.info-block h3 { margin-bottom: 4px; }
table {
  width: 100%;
  margin-top: 12px;
  border-collapse: collapse;
  table-layout: fixed;
}
th, td {
  padding: 9px 10px;
  border: 1px solid var(--line);
  text-align: left;
  vertical-align: top;
  overflow-wrap: anywhere;
}
th { background: #edf3f7; font-size: 12px; }
td { font-size: 13px; }
.evidence-list { list-style: none; padding: 0; margin: 0; }
.evidence-list li {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 4px 10px;
  padding: 10px 0;
  border-bottom: 1px solid var(--line);
}
.evidence-list code { grid-column: 2; color: var(--accent); }
.question-group { margin-top: 16px; }
.empty { color: var(--muted); font-style: italic; }
footer { padding: 20px 38px 28px; color: var(--muted); font-size: 12px; }
@media (max-width: 760px) {
  .page { width: calc(100% - 16px); margin: 8px auto; }
  header, nav.toc, section, footer { padding-left: 18px; padding-right: 18px; }
  .meta { grid-template-columns: 1fr; }
  nav.toc a { display: block; margin: 4px 0; white-space: normal; }
  .reading-path li { grid-template-columns: 1fr; }
  .reading-path li span { grid-column: auto; }
  .reading-path code { display: block; }
  .step-head { flex-wrap: wrap; }
  .flow-meta { grid-template-columns: 1fr; }
  .flow-meta dt { margin-top: 8px; }
  table, thead, tbody, tr, th, td { display: block; width: 100%; }
  thead { display: none; }
  tr { margin-top: 10px; border: 1px solid var(--line); }
  td { border: 0; border-bottom: 1px solid var(--line); }
  td:last-child { border-bottom: 0; }
}
@media print {
  body { background: #fff; }
  .page { width: 100%; margin: 0; border: 0; box-shadow: none; }
  section { break-inside: auto; }
  .screenshot-block { break-inside: avoid; }
}
"""


def build_html(data: dict) -> str:
    meta = require_dict(data.get("meta"), "meta")
    summary = require_dict(data.get("summary"), "summary")
    questions = data.get("questions", {}) if isinstance(data.get("questions", {}), dict) else {}
    generated_at = text(
        meta.get("generated_at"),
        datetime.now().astimezone().isoformat(timespec="seconds"),
    )
    source_commit = text(meta.get("source_commit"), "unavailable")
    project = text(meta.get("project"))
    topic_id = text(meta.get("topic_id"))
    title = text(meta.get("title"))

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} - Codebase Study</title>
<style>{STYLE}</style>
</head>
<body>
<main class="page" data-topic-id="{esc(topic_id)}" data-source-commit="{esc(source_commit)}">
  <header>
    <div class="eyebrow">Codebase Study / Read Only</div>
    <h1>{esc(title)}</h1>
    <p><strong>{esc(project)} / {esc(topic_id)}</strong></p>
    <div class="meta">
      <div class="meta-item"><span>Repository</span><strong>{esc(text(meta.get("repository"), "unavailable"))}</strong></div>
      <div class="meta-item"><span>Source revision</span><strong>{esc(source_commit)}</strong></div>
      <div class="meta-item"><span>Generated</span><strong>{esc(generated_at)}</strong></div>
      <div class="meta-item"><span>Purpose</span><strong>{esc(text(meta.get("purpose"), "理解指定流程"))}</strong></div>
    </div>
  </header>

  <nav class="toc">
    <strong>目錄</strong>
    <a href="#1-快速理解">1. 快速理解</a>
    <a href="#2-閱讀路徑">2. 閱讀路徑</a>
    <a href="#3-執行流程">3. 執行流程</a>
    <a href="#4-關鍵符號">4. 關鍵符號</a>
    <a href="#5-關鍵資料結構">5. 關鍵資料結構</a>
    <a href="#6-配置映射">6. 配置映射</a>
    <a href="#7-證據與置信度">7. 證據與置信度</a>
    <a href="#8-待確認問題">8. 待確認問題</a>
    <a href="#9-下一步閱讀">9. 下一步閱讀</a>
    <a href="#10-來源">10. 來源</a>
  </nav>

  <section id="1-快速理解">
    <h2>1. 快速理解</h2>
    <p class="lead">{esc(summary.get("one_sentence"))}</p>
    <h3>這個流程在做什麼</h3>
    {render_bullets(summary.get("what_it_does"), "未記錄流程摘要。")}
    <h3>關鍵發現</h3>
    {render_bullets(summary.get("key_findings"), "未記錄額外發現。")}
    <h3>閱讀策略</h3>
    {render_bullets(summary.get("reading_strategy"), "未記錄閱讀策略。")}
  </section>

  <section id="2-閱讀路徑">
    <h2>2. 閱讀路徑</h2>
    {render_reading_path(data["reading_path"])}
  </section>

  <section id="3-執行流程">
    <h2>3. 執行流程</h2>
    {render_flow(data["flow"])}
  </section>

  <section id="4-關鍵符號">
    <h2>4. 關鍵符號</h2>
    {render_symbols(as_items(data.get("symbols")))}
  </section>

  <section id="5-關鍵資料結構">
    <h2>5. 關鍵資料結構</h2>
    {render_structures(as_items(data.get("data_structures")))}
  </section>

  <section id="6-配置映射">
    <h2>6. 配置映射</h2>
    {render_config(as_items(data.get("config_map")))}
  </section>

  <section id="7-證據與置信度">
    <h2>7. 證據與置信度</h2>
    {render_evidence(as_items(data.get("evidence")))}
  </section>

  <section id="8-待確認問題">
    <h2>8. 待確認問題</h2>
    {render_questions(questions)}
  </section>

  <section id="9-下一步閱讀">
    <h2>9. 下一步閱讀</h2>
    {render_bullets(data.get("next_reading"), "未指定下一步。")}
  </section>

  <section id="10-來源">
    <h2>10. 來源</h2>
    {render_bullets(data.get("sources"), "未記錄來源。")}
  </section>

  <footer>
    此頁由 study-result.json 生成。所有流程結論都應以報告列出的原始碼位置為準。
  </footer>
</main>
</body>
</html>
"""
