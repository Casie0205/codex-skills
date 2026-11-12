#!/usr/bin/env python3
"""Focused tests for apply_calibration.py."""

from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

SCRIPT = Path(__file__).with_name("apply_calibration.py")
SPEC = importlib.util.spec_from_file_location("apply_calibration", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
APPLY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = APPLY
SPEC.loader.exec_module(APPLY)

GROUP_COLUMNS = {
    "lever_imu2gnss": (
        "LeverImu2Gnss X(m)",
        "LeverImu2Gnss Y(m)",
        "LeverImu2Gnss Z(m)",
    ),
    "lever_imu2car": (
        "leverImu2Car X(m)",
        "LeverImu2Car Y(m)",
        "LeverImu2Car Z(m)",
    ),
    "install_imu2car": (
        "AngleImu2Car X(deg)",
        "AngleImu2Car Y(deg)",
        "AngleImu2Car Z(deg)",
    ),
    "install_gnss2car": (
        "AngleGnss2Car X(deg)",
        "AngleGnss2Car Y(deg)",
        "AngleGnss2Car Z(deg)",
    ),
    "lever_imu2vio": (
        "LeverImu2Vio X(m)",
        "LeverImu2Vio Y(m)",
        "LeverImu2Vio Z(m)",
    ),
    "install_car2vio": (
        "AngleCar2Vio X(deg)",
        "AngleCar2Vio Y(deg)",
        "AngleCar2Vio Z(deg)",
    ),
    "gyo_sf": (
        "GyoSf X(persent)",
        "GyoSf Y(persent)",
        "GyoSf Z(persent)",
    ),
    "acc_sf": (
        "AccSf X(persent)",
        "AccSf Y(persent)",
        "AccSf Z(persent)",
    ),
    "gyo_cross": (
        "GyoCross XY(deg)",
        "GyoCross XZ(deg)",
        "GyoCross YZ(deg)",
        "GyoCross YX(deg)",
        "GyoCross ZX(deg)",
        "GyoCross ZY(deg)",
    ),
    "acc_cross": (
        "AccCross XY(deg)",
        "AccCross XZ(deg)",
        "AccCross YZ(deg)",
        "AccCross YX(deg)",
        "AccCross ZX(deg)",
        "AccCross ZY(deg)",
    ),
}


def config_value(path: Path, key: str) -> str:
    prefix = f"{key} = "
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line.split("=", 1)[1].split("#", 1)[0].strip()
    raise AssertionError(f"Missing {key} in {path}")


class ApplyCalibrationTests(unittest.TestCase):
    def test_relationship_specific_config_transforms(self) -> None:
        groups = {group.config_key: group for group in APPLY.GROUPS}
        vio_group = groups["lever_imu2vio"]
        config = APPLY.state_to_config(
            APPLY.config_to_state(
                np.array([-0.244, 0.125, 0.228]),
                vio_group,
            ),
            vio_group,
        )
        np.testing.assert_allclose(config, [-0.244, 0.125, 0.228])
        np.testing.assert_allclose(
            APPLY.config_to_state(
                np.array([-0.244, 0.125, 0.228]),
                vio_group,
            ),
            [0.125, -0.244, -0.228],
        )
        np.testing.assert_allclose(
            APPLY.state_to_config(
                np.array([-0.167, 0.192, 0.208]),
                vio_group,
            ),
            [0.192, -0.167, -0.208],
        )

        install_group = groups["install_car2vio"]
        np.testing.assert_allclose(
            APPLY.state_to_config(
                np.array([-21.3, 0.667, -5.0]),
                install_group,
            ),
            [-21.3, 0.667, 5.0],
        )
        raw = np.array(
            [
                [-21.3, 0.0, 353.62],
                [-21.3, 0.0, 354.62],
                [-21.3, 0.0, 353.62],
            ]
        )
        diagnostics = APPLY.diagnostic_values(
            raw,
            install_group,
            np.array([-21.3, 0.0, -6.38]),
        )
        self.assertAlmostEqual(1.0, float(np.ptp(diagnostics[:, 2])))
        no_motion = APPLY.diagnostic_values(
            np.tile(np.array([-21.3, 0.0, 353.62]), (3, 1)),
            install_group,
            np.array([-21.3, 0.0, -6.38]),
        )
        self.assertAlmostEqual(0.0, float(np.ptp(no_motion[:, 2])))
        across_zero = APPLY.diagnostic_values(
            np.array([[-21.3, 0.0, 359.0], [-21.3, 0.0, 1.0]]),
            install_group,
            np.array([-21.3, 0.0, 359.0]),
        )
        self.assertAlmostEqual(2.0, float(np.ptp(across_zero[:, 2])))
        np.testing.assert_allclose(across_zero[:, 2], [359.0, 361.0])
        self.assertAlmostEqual(
            0.0,
            float(np.max(np.abs(no_motion[:, 2] - (-6.38)))),
        )

    def test_gyro_scale_factor_is_written_to_final_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            columns = ["Week", "SOW"]
            for group_columns in GROUP_COLUMNS.values():
                for column in group_columns:
                    columns.extend((column, f"{column}[STD]"))
            rows = []
            for index, value in enumerate((0.0, -0.1, -0.2)):
                values = {column: 0.0 for column in columns}
                values["Week"] = 2444
                values["SOW"] = 100.0 + index
                values["GyoSf Z(persent)"] = value
                values["GyoSf Z(persent)[STD]"] = 0.01
                values["GyoCross XY(deg)"] = value + 1.0
                values["GyoCross XY(deg)[STD]"] = 0.1
                values["GyoCross XZ(deg)"] = 5.0
                values["GyoCross XZ(deg)[STD]"] = 0.2
                values["AngleCar2Vio Y(deg)"] = 1.0
                values["leverImu2Car X(m)"] = 5.0
                rows.append(
                    "INS_EST_STATE,"
                    + ",".join(f"{values[column]:.9g}" for column in columns)
                )
            dr_est = root / "dr_est.prodef"
            dr_est.write_text(
                "#PROTOCOL_DEFINE0,V1,{INS_EST_STATE},"
                + ",".join(columns)
                + "*ff\n"
                + "\n".join(rows)
                + "\n",
                encoding="utf-8",
            )

            config_lines = ["> START_CTCCFG", "[ctclib_ins]", "ins_mode = 1"]
            for group, group_columns in GROUP_COLUMNS.items():
                count = len(group_columns)
                config_lines.append(
                    f"{group} = " + ",".join("0" for _ in range(count))
                )
                config_lines.append(f"{group}_std = " + ",".join("1" for _ in range(count)))
                if group == "gyo_sf":
                    mask = ",".join("1" if axis == 2 else "0" for axis in range(count))
                elif group == "gyo_cross":
                    mask = "1,0,0,0,1,0"
                elif group == "install_car2vio":
                    mask = "1,1,1"
                else:
                    mask = ",".join("0" for _ in range(count))
                config_lines.append(
                    f"est_{group} = {mask}"
                )
            config_lines.append("> END_CTCCFG")
            source = root / "source.ctccfg"
            source.write_text("\n".join(config_lines) + "\n", encoding="utf-8")
            output = root / "final.ctccfg"

            process = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--dr-est",
                    str(dr_est),
                    "--config",
                    str(source),
                    "--output-config",
                    str(output),
                    "--window-seconds",
                    "1",
                    "--min-window-samples",
                    "2",
                ],
                capture_output=True,
                check=False,
                encoding="utf-8",
                text=True,
            )
            self.assertEqual(0, process.returncode, process.stderr)
            self.assertEqual("0", config_value(output, "ins_mode"))
            self.assertEqual("0,0,-0.15", config_value(output, "gyo_sf"))
            self.assertEqual("1,1,0.01", config_value(output, "gyo_sf_std"))
            self.assertEqual("0,0,1", config_value(output, "est_gyo_sf"))
            self.assertEqual(
                "0.85,0,0,0,0,0", config_value(output, "gyo_cross")
            )
            self.assertEqual(
                "0.1,1,1,1,1,1", config_value(output, "gyo_cross_std")
            )
            self.assertEqual("0,0,0", config_value(output, "lever_imu2car"))
            self.assertEqual("1,1,1", config_value(output, "lever_imu2car_std"))
            self.assertEqual("0,0,0", config_value(output, "install_car2vio"))
            self.assertEqual("1,1,1", config_value(output, "install_car2vio_std"))
            report_path = output.with_name(
                output.stem + "_calibration_report.csv"
            )
            with report_path.open(encoding="utf-8", newline="") as handle:
                report = {row["group"]: row for row in csv.DictReader(handle)}
            self.assertEqual("1,1,1", report["lever_imu2car"]["config_std"])
            self.assertEqual(
                "missing_vio_input", report["install_car2vio"]["status"]
            )
            self.assertEqual(
                "0,0,0", report["install_car2vio"]["config_value"]
            )
            self.assertEqual(
                "1,1,1", report["install_car2vio"]["config_std"]
            )


if __name__ == "__main__":
    unittest.main()
