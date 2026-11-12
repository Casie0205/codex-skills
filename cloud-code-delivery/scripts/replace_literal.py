from __future__ import annotations

import argparse
import json
import locale
import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any


UTF8_BOM = b"\xef\xbb\xbf"
UTF16_LE_BOM = b"\xff\xfe"
UTF16_BE_BOM = b"\xfe\xff"


def decode_text_file(
    path: Path,
    encoding_override: str | None,
) -> tuple[str, str, bytes | None, str]:
    raw = path.read_bytes()
    if raw.startswith(UTF8_BOM):
        return raw[len(UTF8_BOM) :].decode("utf-8"), "utf-8", UTF8_BOM, "bom"
    if raw.startswith(UTF16_LE_BOM):
        return (
            raw[len(UTF16_LE_BOM) :].decode("utf-16-le"),
            "utf-16-le",
            UTF16_LE_BOM,
            "bom",
        )
    if raw.startswith(UTF16_BE_BOM):
        return (
            raw[len(UTF16_BE_BOM) :].decode("utf-16-be"),
            "utf-16-be",
            UTF16_BE_BOM,
            "bom",
        )
    if encoding_override:
        return raw.decode(encoding_override), encoding_override, None, "explicit"
    try:
        text = raw.decode("utf-8")
        confidence = "ascii" if all(byte < 128 for byte in raw) else "utf8-assumed"
        return text, "utf-8", None, confidence
    except UnicodeDecodeError:
        encoding = locale.getpreferredencoding(False) or "utf-8"
        return raw.decode(encoding), encoding, None, "locale-assumed"


def read_utf8_snippet(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def detect_newline(text: str) -> str:
    crlf_count = text.count("\r\n")
    lf_count = text.count("\n") - crlf_count
    cr_count = text.count("\r") - crlf_count
    if crlf_count == 0 and lf_count == 0 and cr_count == 0:
        return "none"
    if sum(count > 0 for count in (crlf_count, lf_count, cr_count)) > 1:
        return "mixed"
    if crlf_count > 0:
        return "crlf"
    if lf_count > 0:
        return "lf"
    return "cr"


def normalize_newlines(text: str, newline: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if newline == "crlf":
        return normalized.replace("\n", "\r\n")
    if newline == "cr":
        return normalized.replace("\n", "\r")
    return normalized


def line_number(text: str, offset: int) -> int:
    prefix = text[:offset]
    return (
        prefix.count("\n")
        + prefix.count("\r")
        - prefix.count("\r\n")
        + 1
    )


def encode_text(text: str, encoding: str, bom: bytes | None) -> bytes:
    data = text.encode(encoding)
    return (bom or b"") + data


def write_atomic(path: Path, data: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f"{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        temporary_path.write_bytes(data)
        if path.exists():
            os.chmod(temporary_path, stat.S_IMODE(path.stat().st_mode))
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def replace_literal(
    path: Path,
    old_file: Path,
    new_file: Path,
    expected_count: int,
    apply: bool,
    encoding_override: str | None = None,
) -> tuple[int, dict[str, Any]]:
    text, encoding, bom, encoding_confidence = decode_text_file(path, encoding_override)
    source_newline = detect_newline(text)
    result: dict[str, Any] = {
        "status": "ok",
        "path": str(path),
        "encoding": encoding,
        "encoding_confidence": encoding_confidence,
        "bom": bool(bom),
        "newline": source_newline,
        "expected_count": expected_count,
        "applied": False,
    }
    if source_newline == "mixed":
        result["status"] = "mixed_newlines"
        return 2, result
    if apply and encoding_confidence in {"utf8-assumed", "locale-assumed"}:
        result["status"] = "ambiguous_encoding"
        return 3, result

    old_text = normalize_newlines(read_utf8_snippet(old_file), source_newline)
    new_text = normalize_newlines(read_utf8_snippet(new_file), source_newline)
    if not old_text:
        raise ValueError("old snippet must not be empty")
    if expected_count < 1:
        raise ValueError("expected_count must be at least 1")

    count = text.count(old_text)
    result["match_count"] = count
    if count == 0:
        result["status"] = "no_match"
        return 2, result
    if count != expected_count:
        result["status"] = "count_mismatch"
        return 2, result

    offset = text.find(old_text)
    result["match_line"] = line_number(text, offset)
    updated = text.replace(old_text, new_text)
    result["changed"] = updated != text
    if apply and updated != text:
        write_atomic(path, encode_text(updated, encoding, bom))
        result["applied"] = True
    return 0, result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replace one exact literal block while preserving text encoding and newlines."
    )
    parser.add_argument("--path", required=True, type=Path)
    parser.add_argument("--old-file", required=True, type=Path)
    parser.add_argument("--new-file", required=True, type=Path)
    parser.add_argument("--expected-count", type=int, default=1)
    parser.add_argument(
        "--encoding",
        help="Explicit text encoding for a BOM-less file whose encoding is ambiguous.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the replacement. Without this flag the command is a dry run.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        path = args.path.resolve(strict=True)
        old_file = args.old_file.resolve(strict=True)
        new_file = args.new_file.resolve(strict=True)
        exit_code, result = replace_literal(
            path=path,
            old_file=old_file,
            new_file=new_file,
            expected_count=args.expected_count,
            apply=args.apply,
            encoding_override=args.encoding,
        )
    except Exception as exc:
        exit_code = 1
        result = {"status": "error", "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
