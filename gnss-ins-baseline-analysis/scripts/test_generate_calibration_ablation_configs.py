#!/usr/bin/env python3
"""Focused tests for generate_calibration_ablation_configs.py."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("generate_calibration_ablation_configs.py")
SPEC = importlib.util.spec_from_file_location("ablation_generator", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)

GROUPS = (
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


def config_value(path: Path, key: str) -> str:
    prefix = f"{key} = "
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line.split("=", 1)[1].split("#", 1)[0].strip()
    raise AssertionError(f"Missing {key} in {path}")


class GenerateCalibrationAblationConfigsTests(unittest.TestCase):
    def test_selected_disabled_group_uses_explicit_mask_and_std(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            base = root / "base.ctccfg"
            base.write_text(
                "> START_CTCCFG\n"
                "[ctclib]\n"
                "dir_output = D:/old\n"
                "[ctclib_ins]\n"
                + "".join(
                    f"est_{group} = 0,0,0\n{group}_std = 1,1,1\n"
                    for group in GROUPS
                )
                + "> END_CTCCFG\n",
                encoding="utf-8",
            )
            matrix = root / "matrix.json"
            matrix.write_text(
                json.dumps(
                    {
                        "experiments": [
                            {
                                "name": "add_lever",
                                "groups": ["lever_imu2gnss"],
                                "estimate_masks": {
                                    "lever_imu2gnss": "1,1,1"
                                },
                                "std_overrides": {
                                    "lever_imu2gnss": "0.05,0.05,0.05"
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config_dir = root / "configs"
            output_root = root / "output"
            manifest = root / "manifest.json"

            process = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--base-config",
                    str(base),
                    "--matrix",
                    str(matrix),
                    "--output-config-dir",
                    str(config_dir),
                    "--output-root",
                    str(output_root),
                    "--name-prefix",
                    "26111217",
                    "--manifest-output",
                    str(manifest),
                ],
                capture_output=True,
                check=False,
                encoding="utf-8",
                text=True,
            )
            self.assertEqual(0, process.returncode, process.stderr)

            generated = config_dir / (
                "26111217_m720-mova-vio-ablation-add_lever.ctccfg"
            )
            self.assertEqual(
                "1,1,1", config_value(generated, "est_lever_imu2gnss")
            )
            self.assertEqual(
                "0.05,0.05,0.05",
                config_value(generated, "lever_imu2gnss_std"),
            )
            self.assertEqual(
                "0,0,0", config_value(generated, "est_install_car2vio")
            )
            self.assertEqual(
                "0,0,0", config_value(generated, "install_car2vio_std")
            )
            self.assertIn(
                "generated ablation estimate mask",
                generated.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "generated ablation prior STD [m]",
                generated.read_text(encoding="utf-8"),
            )

    def test_mask_validation_rejects_bad_length_and_non_binary(self) -> None:
        cases = (
            ("1,0", 3, "expected 3"),
            ("1,0,2", 3, "only 0 or 1"),
        )
        for value, expected_count, message in cases:
            with self.subTest(value=value), self.assertRaisesRegex(
                ValueError, message
            ):
                GENERATOR.validate_mask(value, expected_count, "test_mask")

    def test_std_validation_requires_finite_positive_enabled_axes(self) -> None:
        cases = (
            ("0,0,0", "positive finite STD"),
            ("0,0.05,0.05", "positive finite STD"),
            ("nan,0.05,0.05", "positive finite STD"),
            ("inf,0.05,0.05", "positive finite STD"),
            ("0.05,0.05", "expected 3"),
            ("abc,0.05,0.05", "numeric values"),
        )
        for value, message in cases:
            with self.subTest(value=value), self.assertRaisesRegex(
                ValueError, message
            ):
                GENERATOR.validate_std(
                    value,
                    3,
                    "test_std",
                    "1,0,0",
                )

    def test_misplaced_mask_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            base = root / "base.ctccfg"
            base.write_text(
                "> START_CTCCFG\n"
                "[ctclib]\n"
                "dir_output = D:/old\n"
                "[ctclib_ins]\n"
                + "".join(
                    f"est_{group} = 0,0,0\n{group}_std = 1,1,1\n"
                    for group in GROUPS
                )
                + "> END_CTCCFG\n",
                encoding="utf-8",
            )
            matrix = root / "matrix.json"
            matrix.write_text(
                json.dumps(
                    {
                        "experiments": [
                            {
                                "name": "bad_mask",
                                "groups": ["lever_imu2gnss"],
                                "estimate_masks": {
                                    "lever_imu2vio": "1,1,1"
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            process = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--base-config",
                    str(base),
                    "--matrix",
                    str(matrix),
                    "--output-config-dir",
                    str(root / "configs"),
                    "--output-root",
                    str(root / "output"),
                    "--name-prefix",
                    "26111217",
                    "--manifest-output",
                    str(root / "manifest.json"),
                ],
                capture_output=True,
                check=False,
                encoding="utf-8",
                text=True,
            )
            self.assertNotEqual(0, process.returncode)
            self.assertIn("estimate_masks for unselected groups", process.stderr)

    def test_selected_all_zero_mask_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            base = root / "base.ctccfg"
            base.write_text(
                "> START_CTCCFG\n"
                "[ctclib]\n"
                "dir_output = D:/old\n"
                "[ctclib_ins]\n"
                + "".join(
                    f"est_{group} = 0,0,0\n{group}_std = 1,1,1\n"
                    for group in GROUPS
                )
                + "> END_CTCCFG\n",
                encoding="utf-8",
            )
            matrix = root / "matrix.json"
            matrix.write_text(
                json.dumps(
                    {
                        "experiments": [
                            {
                                "name": "zero_mask",
                                "groups": ["lever_imu2gnss"],
                                "estimate_masks": {
                                    "lever_imu2gnss": "0,0,0"
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            process = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--base-config",
                    str(base),
                    "--matrix",
                    str(matrix),
                    "--output-config-dir",
                    str(root / "configs"),
                    "--output-root",
                    str(root / "output"),
                    "--name-prefix",
                    "26111217",
                    "--manifest-output",
                    str(root / "manifest.json"),
                ],
                capture_output=True,
                check=False,
                encoding="utf-8",
                text=True,
            )
            self.assertNotEqual(0, process.returncode)
            self.assertIn("must enable at least one axis", process.stderr)


if __name__ == "__main__":
    unittest.main()
