#!/usr/bin/env python3
"""Build a deterministic data-time and parameter-variant output path."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


DATETIME_FORMATS = (
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y%m%d_%H%M%S",
    "%Y%m%dT%H%M%S",
    "%Y%m%d%H%M%S",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve a stable dataset-time and parameter-variant output path."
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--data-time", required=True)
    parser.add_argument(
        "--mode",
        required=True,
        choices=("calibration", "navigation", "analysis"),
    )
    parser.add_argument(
        "--variant",
        action="append",
        default=[],
        help="Changed parameter token or key=value; decimal points become p",
    )
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def parse_data_time(value: str) -> datetime:
    for fmt in DATETIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(
        "Unsupported --data-time format. Use one of: "
        + ", ".join(DATETIME_FORMATS)
    )


def normalize_variant(value: str) -> str:
    clean = value.strip().lower()
    if not clean:
        return ""
    if "=" in clean:
        key, raw_value = clean.split("=", 1)
        key = re.sub(r"[^a-z0-9]+", "_", key).strip("_")
        raw_value = raw_value.replace(".", "p").replace("-", "m").replace("+", "p")
        raw_value = re.sub(r"[^a-z0-9p_]+", "_", raw_value).strip("_")
        if not key or not raw_value:
            raise ValueError(f"Variant key and value must both be non-empty: {value!r}")
        clean = f"{key}_x{raw_value}"
    else:
        clean = clean.replace(".", "p").replace("-", "m").replace("+", "p")
        clean = re.sub(r"[^a-z0-9_]+", "_", clean).strip("_")
    if not clean:
        raise ValueError(f"Variant token is empty after normalization: {value!r}")
    return clean


def main() -> int:
    args = parse_args()
    try:
        data_time = parse_data_time(args.data_time)
        variants = [normalize_variant(value) for value in args.variant]
        variants = sorted({value for value in variants if value})
        name_parts = [data_time.strftime("%Y%m%dT%H%M%S"), args.mode, *variants]
        output_dir = args.root.resolve() / "_".join(name_parts)
        result = {
            "status": "success",
            "data_time": data_time.isoformat(),
            "mode": args.mode,
            "variant_tokens": variants,
            "output_dir": str(output_dir),
            "exists": output_dir.exists(),
            "rule": "reuse for identical data time, mode, and parameter variant",
        }
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result["output_dir"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
