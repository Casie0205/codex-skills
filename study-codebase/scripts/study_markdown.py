#!/usr/bin/env python3
"""Render copy-friendly Markdown, questions, and CSV from study data."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any

from study_common import (
    as_items,
    as_sentence,
    confidence,
    require_dict,
    text,
)


def md_cell(value: Any) -> str:
    rendered = as_sentence(value, "")
    return rendered.replace("|", "\\|").replace("\n", "<br>")


def md_bullets(value: Any, empty: str = "無") -> str:
    items = as_items(value)
    if not items:
        return f"- {empty}\n"
    return "".join(f"- {item}\n" for item in items)


def build_markdown(data: dict) -> str:
    meta = require_dict(data.get("meta"), "meta")
    summary = require_dict(data.get("summary"), "summary")
    questions = data.get("questions", {}) if isinstance(data.get("questions", {}), dict) else {}
    generated_at = text(
        meta.get("generated_at"),
        datetime.now().astimezone().isoformat(timespec="seconds"),
    )
    lines = [
        f"# {text(meta.get('title'))}",
        "",
        f"> Project: `{text(meta.get('project'))}` | Topic: `{text(meta.get('topic_id'))}`",
        f"> Repository: `{text(meta.get('repository'), 'unavailable')}` | "
        f"Source revision: `{text(meta.get('source_commit'), 'unavailable')}`",
        f"> Generated: {generated_at}",
        "",
        "## 目錄",
        "",
        "- [1. 快速理解](#1-快速理解)",
        "- [2. 閱讀路徑](#2-閱讀路徑)",
        "- [3. 執行流程](#3-執行流程)",
        "- [4. 關鍵符號](#4-關鍵符號)",
        "- [5. 關鍵資料結構](#5-關鍵資料結構)",
        "- [6. 配置映射](#6-配置映射)",
        "- [7. 證據與置信度](#7-證據與置信度)",
        "- [8. 待確認問題](#8-待確認問題)",
        "- [9. 下一步閱讀](#9-下一步閱讀)",
        "- [10. 來源](#10-來源)",
        "",
        "## 1. 快速理解",
        "",
        f"**一句話：** {text(summary.get('one_sentence'))}",
        "",
        "### 這個流程在做什麼",
        "",
        md_bullets(summary.get("what_it_does"), "未記錄"),
        "",
        "### 關鍵發現",
        "",
        md_bullets(summary.get("key_findings"), "未記錄"),
        "",
        "### 閱讀策略",
        "",
        md_bullets(summary.get("reading_strategy"), "未記錄"),
        "",
        "## 2. 閱讀路徑",
        "",
    ]
    for item in data["reading_path"]:
        lines.append(
            f"{item['order']}. **{text(item['name'])}** "
            f"(`{text(item['source'])}`)：{text(item['why'])}"
        )

    lines.extend(["", "## 3. 執行流程", ""])
    for item in data["flow"]:
        lines.extend(
            [
                f"### {item['step']}. {text(item['name'])}",
                "",
                f"- 位置：`{text(item['source'])}`",
                f"- 置信度：`{confidence(item.get('confidence'))}`",
                f"- 目的：{text(item['purpose'])}",
            ]
        )
        for key, label in [
            ("caller", "呼叫者"),
            ("callee", "被呼叫者"),
            ("input", "輸入"),
            ("output", "輸出"),
            ("state", "狀態"),
            ("normal", "正常分支"),
            ("error", "錯誤分支"),
            ("next", "下一步閱讀"),
        ]:
            if item.get(key) not in (None, "", []):
                lines.append(f"- {label}：{text(item[key])}")
        if item.get("code"):
            language = text(item.get("code_language"), "text")
            lines.extend(["", f"```{language}", str(item["code"]), "```"])
        lines.append("")

    lines.extend(["## 4. 關鍵符號", ""])
    symbols = as_items(data.get("symbols"))
    if symbols:
        lines.extend(
            [
                "| 符號 | 類型 | 定義位置 | 責任 | 置信度 |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for item in symbols:
            lines.append(
                f"| {md_cell(item.get('name'))} | {md_cell(item.get('kind'))} | "
                f"`{md_cell(item.get('defined_at'))}` | {md_cell(item.get('role'))} | "
                f"`{confidence(item.get('confidence'))}` |"
            )
    else:
        lines.append("- 未記錄。")

    lines.extend(["", "## 5. 關鍵資料結構", ""])
    structures = as_items(data.get("data_structures"))
    if structures:
        for item in structures:
            lines.extend(
                [
                    f"### {text(item.get('name'))}",
                    "",
                    f"- 定義位置：`{text(item.get('defined_at'))}`",
                    f"- 置信度：`{confidence(item.get('confidence'))}`",
                    f"- 用途：{text(item.get('purpose'))}",
                    f"- 欄位：{as_sentence(item.get('fields'))}",
                    f"- 所有權：{text(item.get('ownership'))}",
                    "",
                ]
            )
    else:
        lines.append("- 未記錄。")

    lines.extend(["", "## 6. 配置映射", ""])
    config_map = as_items(data.get("config_map"))
    if config_map:
        lines.extend(
            [
                "| 參數 | 配置來源 | 消費位置 | 意義 | 預設值 |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for item in config_map:
            lines.append(
                f"| {md_cell(item.get('key'))} | `{md_cell(item.get('source'))}` | "
                f"`{md_cell(item.get('consumed_at'))}` | {md_cell(item.get('meaning'))} | "
                f"{md_cell(item.get('default'))} |"
            )
    else:
        lines.append("- 未記錄。")

    lines.extend(["", "## 7. 證據與置信度", ""])
    evidence = as_items(data.get("evidence"))
    if evidence:
        for item in evidence:
            lines.append(
                f"- `{confidence(item.get('confidence'))}` "
                f"{text(item.get('claim'))} (`{text(item.get('source'))}`)"
            )
    else:
        lines.append("- 未記錄。")

    lines.extend(
        [
            "",
            "## 8. 待確認問題",
            "",
            "### 已確認",
            "",
            md_bullets(questions.get("confirmed"), "無"),
            "### 推測",
            "",
            md_bullets(questions.get("inferred"), "無"),
            "### 待確認",
            "",
            md_bullets(questions.get("open"), "無"),
            "## 9. 下一步閱讀",
            "",
            md_bullets(data.get("next_reading"), "未指定"),
            "## 10. 來源",
            "",
            md_bullets(data.get("sources"), "未記錄"),
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_questions(data: dict) -> str:
    meta = require_dict(data.get("meta"), "meta")
    questions = data.get("questions", {}) if isinstance(data.get("questions", {}), dict) else {}
    lines = [
        f"# {text(meta.get('title'))} - 待確認問題",
        "",
        f"> Topic: `{text(meta.get('topic_id'))}` | "
        f"Source revision: `{text(meta.get('source_commit'), 'unavailable')}`",
        "",
        "## 目錄",
        "",
        "- [1. 已確認](#1-已確認)",
        "- [2. 推測](#2-推測)",
        "- [3. 待確認](#3-待確認)",
        "",
        "## 1. 已確認",
        "",
        md_bullets(questions.get("confirmed"), "無"),
        "## 2. 推測",
        "",
        md_bullets(questions.get("inferred"), "無"),
        "## 3. 待確認",
        "",
        md_bullets(questions.get("open"), "無"),
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_csv(data: dict) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["name", "kind", "defined_at", "role", "confidence"])
    for item in as_items(data.get("symbols")):
        writer.writerow(
            [
                text(item.get("name"), ""),
                text(item.get("kind"), ""),
                text(item.get("defined_at"), ""),
                text(item.get("role"), ""),
                confidence(item.get("confidence")),
            ]
        )
    return output.getvalue()
