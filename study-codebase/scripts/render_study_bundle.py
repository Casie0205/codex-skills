#!/usr/bin/env python3
"""Render a read-only code study bundle from study-result.json."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

from study_common import validate
from study_html import build_html
from study_markdown import build_csv, build_markdown, build_questions


def write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding=encoding,
            newline="\n",
            dir=str(path.parent),
            prefix=f".{path.name}-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        temp_path = None
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink()
            except OSError:
                pass


def render(input_path: Path, output_root: Path) -> list[Path]:
    data = json.loads(input_path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("top-level JSON value must be an object")
    validate(data)

    outputs = [
        (output_root / "study-report.html", build_html(data), "utf-8"),
        (output_root / "study-note.md", build_markdown(data), "utf-8"),
        (output_root / "questions.md", build_questions(data), "utf-8"),
        (output_root / "symbol-index.csv", build_csv(data), "utf-8-sig"),
    ]
    for path, content, encoding in outputs:
        write_text(path, content, encoding)
    return [path for path, _, _ in outputs]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()

    try:
        output_root = args.output_root.resolve(strict=True)
        input_path = args.input.resolve(strict=True)
        if not output_root.is_dir():
            raise ValueError(f"output root is not a directory: {output_root}")
        try:
            input_path.relative_to(output_root)
        except ValueError as exc:
            raise ValueError("input must stay within output-root") from exc
        outputs = render(input_path, output_root)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    for path in outputs:
        print(f"Wrote {path} ({path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
