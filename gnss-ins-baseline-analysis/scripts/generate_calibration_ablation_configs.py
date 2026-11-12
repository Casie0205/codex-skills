#!/usr/bin/env python3
"""Generate CTCLib calibration configs for an ablation matrix."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ESTIMATE_GROUPS = (
    "lever_imu2gnss",
    "lever_imu2car",
    "install_imu2car",
    "install_gnss2car",
    "lever_imu2vio",
    "install_car2vio",
    "gyo_sf",
    "acc_sf",
    "gyo_cross",
    "acc_cross",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate one CTCLib CALIB config per ablation experiment."
    )
    parser.add_argument("--base-config", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--output-config-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--name-prefix", required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def section_bounds(lines: list[str], section: str) -> tuple[int, int]:
    matches = [
        index
        for index, line in enumerate(lines)
        if re.match(rf"^\s*\[{re.escape(section)}\]\s*$", line)
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one [{section}] section, found {len(matches)}")
    start = matches[0]
    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].strip()
        if re.match(r"^\[.+\]$", stripped) or stripped.startswith(">"):
            end = index
            break
    return start, end


def active_entries(lines: list[str], start: int, end: int) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {}
    for index in range(start + 1, end):
        match = re.match(r"^\s*([A-Za-z0-9_\[\]]+)\s*=\s*(.*)$", lines[index])
        if not match:
            continue
        result.setdefault(match.group(1), []).append(index)
    return result


def get_value(
    lines: list[str], entries: dict[str, list[int]], key: str
) -> str | None:
    indexes = entries.get(key, [])
    if not indexes:
        return None
    if len(indexes) > 1:
        raise ValueError(f"Duplicate key [{key}]")
    return lines[indexes[0]].split("=", 1)[1].split("#", 1)[0].strip()


def set_value(
    lines: list[str],
    entries: dict[str, list[int]],
    section_end: int,
    key: str,
    value: str,
) -> None:
    indexes = entries.get(key, [])
    if len(indexes) > 1:
        raise ValueError(f"Duplicate key [{key}]")
    if indexes:
        index = indexes[0]
        comment_match = re.search(r"\s+#.*$", lines[index])
        comment = comment_match.group(0) if comment_match else ""
        lines[index] = f"{key} = {value}{comment}"
        return
    lines.insert(section_end, f"{key} = {value}")
    for key_indexes in entries.values():
        for position, line_index in enumerate(key_indexes):
            if line_index >= section_end:
                key_indexes[position] = line_index + 1
    entries[key] = [section_end]


def zero_mask(value: str) -> str:
    count = len([part for part in value.split(",") if part.strip()])
    return ",".join("0" for _ in range(count))


def main() -> int:
    args = parse_args()
    base_path = args.base_config.resolve()
    matrix_path = args.matrix.resolve()
    config_dir = args.output_config_dir.resolve()
    output_root = args.output_root.resolve()
    manifest_path = args.manifest_output.resolve()
    matrix = json.loads(matrix_path.read_text(encoding="utf-8-sig"))
    experiments = matrix.get("experiments", [])
    if not experiments:
        raise ValueError("Matrix must define at least one experiment")
    base_lines = base_path.read_text(encoding="utf-8-sig").splitlines()
    config_dir.mkdir(parents=True, exist_ok=True)
    manifest_experiments = []
    for experiment in experiments:
        name = str(experiment["name"])
        selected = set(experiment.get("groups", []))
        unknown = selected.difference(ESTIMATE_GROUPS)
        if unknown:
            raise ValueError(f"Unknown groups in {name}: {sorted(unknown)}")
        lines = list(base_lines)
        start, end = section_bounds(lines, "ctclib")
        ctclib_entries = active_entries(lines, start, end)
        output_dir = output_root / name
        set_value(
            lines,
            ctclib_entries,
            end,
            "dir_output",
            str(output_dir).replace("\\", "/"),
        )

        start, end = section_bounds(lines, "ctclib_ins")
        entries = active_entries(lines, start, end)
        set_value(lines, entries, end, "ins_mode", "1")
        set_value(lines, entries, end, "method_adaptive_calib", "1")
        for group in ESTIMATE_GROUPS:
            key = f"est_{group}"
            base_value = get_value(base_lines, active_entries(
                base_lines,
                *section_bounds(base_lines, "ctclib_ins"),
            ), key)
            if base_value is None:
                raise ValueError(f"Base config does not define {key}")
            value = base_value if group in selected else zero_mask(base_value)
            set_value(lines, entries, end, key, value)
        if len(lines) > 1 and lines[1].startswith("#"):
            lines[1] = (
                f"# M720 + Mova VIO ablation: {name}; "
                f"groups={','.join(sorted(selected)) or 'none'}."
            )
        config_path = config_dir / f"{args.name_prefix}_m720-mova-vio-ablation-{name}.ctccfg"
        if config_path.exists() and not args.force:
            raise ValueError(f"Config exists: {config_path}")
        config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        manifest_experiments.append(
            {
                "group": name,
                "groups": sorted(selected),
                "config": str(config_path),
                "output_dir": str(output_dir),
            }
        )
    result = {
        "base_config": str(base_path),
        "matrix": str(matrix_path),
        "experiments": manifest_experiments,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "success",
                "experiments": len(manifest_experiments),
                "manifest": str(manifest_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
