#!/usr/bin/env python
"""Detect MathType's red error text in WMF equation previews."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from zipfile import ZipFile


PLACEABLE_WMF_KEY = 0x9AC6CDD7
META_SETTEXTCOLOR = 0x0209
RGB_MASK = 0x00FFFFFF
ERROR_RED_COLORREF = 0x000000FF


def wmf_text_colors(data: bytes) -> list[int]:
    """Return COLORREF values from valid META_SETTEXTCOLOR records."""
    if len(data) < 18:
        return []

    offset = 0
    if len(data) >= 22 and int.from_bytes(data[0:4], "little") == PLACEABLE_WMF_KEY:
        offset = 22

    if offset + 4 > len(data):
        return []
    header_words = int.from_bytes(data[offset + 2 : offset + 4], "little")
    if header_words < 9:
        return []
    offset += header_words * 2

    colors: list[int] = []
    while offset + 6 <= len(data):
        size_words = int.from_bytes(data[offset : offset + 4], "little")
        function = int.from_bytes(data[offset + 4 : offset + 6], "little")
        if size_words < 3:
            break
        record_bytes = size_words * 2
        record_end = offset + record_bytes
        if record_end > len(data):
            break
        if function == META_SETTEXTCOLOR and record_bytes >= 10:
            color = int.from_bytes(data[offset + 6 : offset + 10], "little")
            colors.append(color & RGB_MASK)
        offset = record_end
        if function == 0:
            break

    return colors


def wmf_has_math_type_error_red(data: bytes) -> bool:
    return ERROR_RED_COLORREF in wmf_text_colors(data)


def audit_docx_previews(docx_path: Path, entry_prefix: str) -> dict[str, object]:
    red_entries: list[str] = []
    scanned_entries = 0
    with ZipFile(docx_path, "r") as package:
        for info in package.infolist():
            if not info.filename.lower().endswith(".wmf"):
                continue
            if entry_prefix and not info.filename.startswith(entry_prefix):
                continue
            scanned_entries += 1
            if wmf_has_math_type_error_red(package.read(info.filename)):
                red_entries.append(info.filename)

    return {
        "document": str(docx_path.resolve()),
        "entryPrefix": entry_prefix,
        "scannedWmfCount": scanned_entries,
        "redErrorWmfCount": len(red_entries),
        "redErrorEntries": red_entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docx", type=Path, required=True)
    parser.add_argument(
        "--entry-prefix",
        default="",
        help="Only scan WMF package parts whose names start with this prefix.",
    )
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    result = audit_docx_previews(args.docx, args.entry_prefix)
    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(output)
    if args.report:
        if args.report.exists():
            raise FileExistsError(args.report)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output + "\n", encoding="utf-8")
    if result["redErrorWmfCount"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
