#!/usr/bin/env python3
"""Build Markdown intermediates and round-trip audit files for formula conversion."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Iterable

def read_jsonl(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    header: dict[str, Any] = {}
    formulas: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            record_type = record.get("type")
            if record_type == "header":
                header = record
            elif record_type == "formula":
                formulas.append(record)
            elif record_type not in {"summary"}:
                raise ValueError(
                    f"Unsupported record type at {path}:{line_number}: "
                    f"{record_type!r}"
                )
    formulas.sort(key=lambda item: int(item["sourceIndex"]))
    return header, formulas


def clean_context(value: str) -> str:
    return " ".join(clean_xml_text(value).replace("\x07", " ").split())


def clean_xml_text(value: str) -> str:
    return "".join(
        character
        for character in (value or "")
        if ord(character) >= 32 or character in "\t\n\r"
    )


def strip_inline_delimiters(value: str) -> str:
    result = (value or "").strip()
    if len(result) >= 2 and result.startswith("$") and result.endswith("$"):
        return result[1:-1]
    return result


def validate_source_rows(formulas: Iterable[dict[str, Any]]) -> None:
    rows = list(formulas)
    expected = list(range(1, len(rows) + 1))
    actual = [int(row["sourceIndex"]) for row in rows]
    if actual != expected:
        raise ValueError(
            "Formula sourceIndex values are not a complete ascending sequence."
        )
    for row in rows:
        normalized = row.get("normalizedTex", "")
        if not normalized:
            raise ValueError(
                f"Formula {row['sourceIndex']} has empty normalized TeX."
            )
        if "?" in normalized:
            raise ValueError(
                f"Formula {row['sourceIndex']} has a question mark in normalized TeX."
            )
        if any(ord(character) > 127 for character in normalized):
            raise ValueError(
                f"Formula {row['sourceIndex']} has non-ASCII normalized TeX."
            )


def write_markdown_documents(
    raw_path: Path,
    normalized_path: Path,
    source_note: str,
    formulas: list[dict[str, Any]],
) -> None:
    with raw_path.open("w", encoding="utf-8", newline="\n") as raw_stream:
        raw_stream.write("# Word 原始公式与原始导出 TeX 中间量\n\n")
        raw_stream.write(source_note + "\n\n")
        for row in formulas:
            raw_stream.write(
                f"## 公式 {int(row['sourceIndex']):04d} "
                f"(Word range {row.get('start')}-{row.get('end')})\n\n"
            )
            raw_stream.write("Word 原始线性文本：\n\n````text\n")
            raw_stream.write(
                clean_xml_text(row.get("sourceWordText", ""))
                + "\n````\n\n"
            )
            raw_stream.write("Word 原始导出 TeX：\n\n````tex\n")
            raw_stream.write(
                clean_xml_text(row.get("rawWordTex", ""))
                + "\n````\n\n"
            )
            raw_stream.write(
                "上下文：" + clean_context(row.get("context", "")) + "\n\n"
            )

    with normalized_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as normalized_stream:
        normalized_stream.write("# 处理后 TeX 中间量\n\n")
        normalized_stream.write(source_note + "\n\n")
        for row in formulas:
            normalized_stream.write(
                f"## 公式 {int(row['sourceIndex']):04d} "
                f"(Word range {row.get('start')}-{row.get('end')})\n\n"
            )
            normalized_stream.write("NFKC 中间文本：\n\n````tex\n")
            normalized_stream.write(
                row.get("nfkcWordTex", "") + "\n````\n\n"
            )
            normalized_stream.write("MathType 输入 TeX：\n\n````tex\n")
            normalized_stream.write(
                row.get("normalizedTex", "") + "\n````\n\n"
            )
            normalized_stream.write(
                "规范化记录："
                + (row.get("replacementSummary", "") or "无")
                + "\n\n"
            )


def write_roundtrip_audit(
    output_dir: Path,
    formulas: list[dict[str, Any]],
    readback_path: Path | None,
) -> dict[str, int]:
    readback_by_index: dict[int, dict[str, Any]] = {}
    if readback_path is not None:
        _, readback_rows = read_jsonl(readback_path)
        readback_by_index = {
            int(row["sourceIndex"]): row for row in readback_rows
        }

    audit_rows: list[dict[str, Any]] = []
    for row in formulas:
        source_index = int(row["sourceIndex"])
        expected = row.get("normalizedTex", "")
        readback_record = readback_by_index.get(source_index)
        readback = (
            strip_inline_delimiters(readback_record.get("readbackTex", ""))
            if readback_record is not None
            else ""
        )
        audit_rows.append(
            {
                "sourceIndex": source_index,
                "wordStart": row.get("start"),
                "wordEnd": row.get("end"),
                "rawWordTex": row.get("rawWordTex", ""),
                "normalizedTex": expected,
                "readbackTex": readback,
                "exactEqual": (
                    readback_record is not None and expected == readback
                ),
                "containsQuestionMark": "?" in readback,
                "replacementSummary": row.get("replacementSummary", ""),
                "context": clean_context(row.get("context", "")),
            }
        )

    csv_path = output_dir / "04_逐式闭环核对.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(audit_rows[0]))
        writer.writeheader()
        writer.writerows(audit_rows)

    exact_count = sum(bool(row["exactEqual"]) for row in audit_rows)
    question_count = sum(
        bool(row["containsQuestionMark"]) for row in audit_rows
    )
    pending_count = 0 if readback_by_index else len(audit_rows)
    markdown_path = output_dir / "04_逐式闭环核对摘要.md"
    with markdown_path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write("# 逐式闭环核对摘要\n\n")
        stream.write(f"- 公式总数：{len(audit_rows)}\n")
        stream.write(f"- TeX 完全一致：{exact_count}\n")
        stream.write(f"- 含问号回读：{question_count}\n")
        stream.write(f"- 尚未回读：{pending_count}\n")
        stream.write(
            "- 完整逐式内容见 `04_逐式闭环核对.csv`；"
            "该表可按公式编号筛选、增删和复核。\n"
        )

    return {
        "formulaCount": len(audit_rows),
        "exactEqualCount": exact_count,
        "questionMarkCount": question_count,
        "pendingCount": pending_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--conversion-manifest", type=Path, required=True)
    parser.add_argument("--readback-manifest", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    header, formulas = read_jsonl(args.conversion_manifest)
    validate_source_rows(formulas)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    source_note = (
        f"来源：{header.get('sourcePath', '')}；"
        f"SHA-256：{header.get('sourceSha256', '')}；"
        f"公式数：{len(formulas)}。"
    )
    write_markdown_documents(
        args.output_dir / "02_Word公式导出中间量.md",
        args.output_dir / "03_处理后TeX中间量.md",
        source_note,
        formulas,
    )
    summary = write_roundtrip_audit(
        args.output_dir,
        formulas,
        args.readback_manifest,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
