#!/usr/bin/env python3
"""Shared validation and text helpers for study-codebase outputs."""

from __future__ import annotations

import html
import re
from typing import Any, List


CONFIDENCE_VALUES = {"confirmed", "inferred", "open"}
LOCATION_RE = re.compile(r".+:\d+(?:-\d+)?$")


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def text(value: Any, fallback: str = "未記錄") -> str:
    if value is None or value == "" or value == []:
        return fallback
    return str(value)


def as_items(value: Any) -> List[Any]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [value]


def as_sentence(value: Any, fallback: str = "無") -> str:
    if isinstance(value, list):
        return "；".join(str(item) for item in value) or fallback
    return text(value, fallback)


def confidence(value: Any) -> str:
    normalized = str(value or "open").strip().lower()
    if normalized not in CONFIDENCE_VALUES:
        raise ValueError(f"invalid confidence value: {value}")
    return normalized


def confidence_badge(value: Any) -> str:
    label = confidence(value)
    css = {"confirmed": "success", "inferred": "warning", "open": "danger"}[label]
    return f'<span class="badge {css}">{esc(label)}</span>'


def location(value: Any, field: str) -> str:
    rendered = text(value, "")
    if not rendered:
        raise ValueError(f"{field} is required")
    if not LOCATION_RE.match(rendered):
        raise ValueError(f"{field} must end with path:line, got {rendered!r}")
    return rendered


def require_dict(value: Any, field: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    return value


def require_text(value: Any, field: str) -> str:
    rendered = text(value, "").strip()
    if not rendered:
        raise ValueError(f"{field} is required")
    return rendered


def validate(data: dict) -> None:
    meta = require_dict(data.get("meta"), "meta")
    summary = require_dict(data.get("summary"), "summary")
    require_text(meta.get("project"), "meta.project")
    require_text(meta.get("topic_id"), "meta.topic_id")
    require_text(meta.get("title"), "meta.title")
    require_text(summary.get("one_sentence"), "summary.one_sentence")
    if not as_items(summary.get("what_it_does")):
        raise ValueError("summary.what_it_does must contain at least one item")

    reading_path = require_list(data.get("reading_path"), "reading_path")
    if not reading_path:
        raise ValueError("reading_path must contain at least one item")
    for index, item in enumerate(reading_path):
        item = require_dict(item, f"reading_path[{index}]")
        if not isinstance(item.get("order"), int) or item["order"] < 1:
            raise ValueError(f"reading_path[{index}].order must be a positive integer")
        require_text(item.get("name"), f"reading_path[{index}].name")
        location(item.get("source"), f"reading_path[{index}].source")
        require_text(item.get("why"), f"reading_path[{index}].why")

    flow = require_list(data.get("flow"), "flow")
    if not flow:
        raise ValueError("flow must contain at least one item")
    for index, item in enumerate(flow):
        item = require_dict(item, f"flow[{index}]")
        if not isinstance(item.get("step"), int) or item["step"] < 1:
            raise ValueError(f"flow[{index}].step must be a positive integer")
        require_text(item.get("name"), f"flow[{index}].name")
        location(item.get("source"), f"flow[{index}].source")
        require_text(item.get("purpose"), f"flow[{index}].purpose")
        confidence(item.get("confidence"))

    for section in ("symbols", "data_structures", "evidence"):
        for index, item in enumerate(as_items(data.get(section))):
            if not isinstance(item, dict):
                raise ValueError(f"{section}[{index}] must be an object")
            confidence(item.get("confidence"))
            if section == "symbols":
                location(item.get("defined_at"), f"symbols[{index}].defined_at")
            if section == "evidence":
                location(item.get("source"), f"evidence[{index}].source")

    questions = data.get("questions", {})
    if questions is not None and not isinstance(questions, dict):
        raise ValueError("questions must be an object")
