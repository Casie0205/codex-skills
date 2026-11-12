#!/usr/bin/env python3
"""Focused tests for analyze_calibration_observability.py."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("analyze_calibration_observability.py")


class AnalyzeCalibrationObservabilityTests(unittest.TestCase):
    def test_csv_observability_is_per_axis(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "run"
            analysis_dir = root / "analysis"
            run_dir.mkdir()
            dr_est = run_dir / "dr_est.prodef"
            dr_est.write_text(
                "#PROTOCOL_DEFINE0,V1,{INS_EST_STATE},"
                "Week,SOW,"
                "GyoSf X(persent),GyoSf X(persent)[STD],"
                "GyoSf Y(persent),GyoSf Y(persent)[STD],"
                "GyoSf Z(persent),GyoSf Z(persent)[STD]*ff\n"
                "INS_EST_STATE,2444,100.0,0,0.1,0,0.1,-1,0.01\n"
                "INS_EST_STATE,2444,101.0,0,0.1,0,0.1,-1.1,0.01\n"
                "INS_EST_STATE,2444,102.0,0,0.1,0,0.1,-1.1,0.01\n"
                "INS_EST_STATE,2444,103.0,0,0.1,0,0.1,-1.2,0.01\n",
                encoding="utf-8",
            )
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "experiments": [
                            {
                                "group": "gyo_sf",
                                "groups": ["gyo_sf"],
                                "output_dir": str(run_dir),
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
                    "--manifest",
                    str(manifest),
                    "--output-dir",
                    str(analysis_dir),
                ],
                capture_output=True,
                check=False,
                encoding="utf-8",
                text=True,
            )
            self.assertEqual(0, process.returncode, process.stderr)

            with (analysis_dir / "calibration_observability_summary.csv").open(
                encoding="utf-8", newline=""
            ) as handle:
                rows = {row["axis"]: row for row in csv.DictReader(handle)}

            self.assertEqual("false", rows["GyoSf X(persent)"]["observable"])
            self.assertEqual("0", rows["GyoSf X(persent)"]["changed_samples"])
            self.assertEqual("0", rows["GyoSf X(persent)"]["changed_transitions"])
            self.assertEqual("", rows["GyoSf X(persent)"]["first_change_elapsed_s"])

            self.assertEqual("false", rows["GyoSf Y(persent)"]["observable"])
            self.assertEqual("0", rows["GyoSf Y(persent)"]["changed_samples"])

            self.assertEqual("true", rows["GyoSf Z(persent)"]["observable"])
            self.assertEqual("3", rows["GyoSf Z(persent)"]["changed_samples"])
            self.assertEqual("2", rows["GyoSf Z(persent)"]["changed_transitions"])
            self.assertEqual("1", rows["GyoSf Z(persent)"]["first_change_elapsed_s"])


if __name__ == "__main__":
    unittest.main()
