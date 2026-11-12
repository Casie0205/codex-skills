#!/usr/bin/env python3
"""Generate CTCLib calibration configs for an ablation matrix."""

from __future__ import annotations

import argparse
import json
import math
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

STD_UNITS = {
    "lever_imu2gnss": "m",
    "lever_imu2car": "m",
    "install_imu2car": "deg",
    "install_gnss2car": "deg",
    "lever_imu2vio": "m",
    "install_car2vio": "deg",
    "gyo_sf": "percent",
    "acc_sf": "percent",
    "gyo_cross": "deg",
    "acc_cross": "deg",
}


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
    comment: str | None = None,
) -> None:
    indexes = entries.get(key, [])
    if len(indexes) > 1:
        raise ValueError(f"Duplicate key [{key}]")
    if indexes:
        index = indexes[0]
        if comment is None:
            comment_match = re.search(r"\s+#.*$", lines[index])
            suffix = comment_match.group(0) if comment_match else ""
        else:
            suffix = f" # {comment}"
        lines[index] = f"{key} = {value}{suffix}"
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


def split_values(value: str, key: str) -> list[str]:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if not parts:
        raise ValueError(f"{key} must contain at least one value")
    return parts


def validate_mask(value: str, expected_count: int, key: str) -> None:
    parts = split_values(value, key)
    if len(parts) != expected_count:
        raise ValueError(
            f"{key} has {len(parts)} values; expected {expected_count}"
        )
    if any(part not in {"0", "1"} for part in parts):
        raise ValueError(f"{key} must contain only 0 or 1")
    if not any(part == "1" for part in parts):
        raise ValueError(f"{key} must enable at least one axis")


def validate_std(
    value: str,
    expected_count: int,
    key: str,
    mask_value: str,
) -> None:
    parts = split_values(value, key)
    if len(parts) != expected_count:
        raise ValueError(
            f"{key} has {len(parts)} values; expected {expected_count}"
        )
    mask_parts = split_values(mask_value, f"{key} mask")
    try:
        numeric = [float(part) for part in parts]
    except ValueError as exc:
        raise ValueError(f"{key} must contain numeric values") from exc
    if any(item < 0 for item in numeric):
        raise ValueError(f"{key} must not contain negative values")
    for axis, (mask, std) in enumerate(zip(mask_parts, numeric)):
        if mask == "1" and (not math.isfinite(std) or std <= 0):
            raise ValueError(
                f"{key} axis {axis} must have positive finite STD when "
                "its estimate mask is 1"
            )


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
        estimate_masks = experiment.get("estimate_masks", {})
        std_overrides = experiment.get("std_overrides", {})
        unknown = selected.difference(ESTIMATE_GROUPS)
        if unknown:
            raise ValueError(f"Unknown groups in {name}: {sorted(unknown)}")
        misplaced_masks = set(estimate_masks).difference(selected)
        if misplaced_masks:
            raise ValueError(
                f"estimate_masks for unselected groups in {name}: "
                f"{sorted(misplaced_masks)}"
            )
        misplaced_stds = set(std_overrides).difference(selected)
        if misplaced_stds:
            raise ValueError(
                f"std_overrides for unselected groups in {name}: "
                f"{sorted(misplaced_stds)}"
            )
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
        base_start, base_end = section_bounds(base_lines, "ctclib_ins")
        base_entries = active_entries(base_lines, base_start, base_end)
        for group in ESTIMATE_GROUPS:
            key = f"est_{group}"
            std_key = f"{group}_std"
            base_value = get_value(base_lines, base_entries, key)
            if base_value is None:
                raise ValueError(f"Base config does not define {key}")
            base_std = get_value(base_lines, base_entries, std_key)
            if base_std is None:
                raise ValueError(f"Base config does not define {std_key}")
            expected_count = len(split_values(base_value, key))
            if group in selected:
                value = str(estimate_masks.get(group, base_value))
                std_value = str(std_overrides.get(group, base_std))
                validate_mask(value, expected_count, f"{name}.{key}")
                validate_std(
                    std_value,
                    expected_count,
                    f"{name}.{std_key}",
                    value,
                )
            else:
                value = zero_mask(base_value)
                std_value = zero_mask(base_std)
            set_value(
                lines,
                entries,
                end,
                key,
                value,
                comment="generated ablation estimate mask",
            )
            set_value(
                lines,
                entries,
                end,
                std_key,
                std_value,
                comment=f"generated ablation prior STD [{STD_UNITS[group]}]",
            )
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
