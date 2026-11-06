from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from rtkplot_data import enu_from_llh, parse_rtkplot, summarize_dataset
from rtkplot_plots import output_paths

SAMPLE_ROWS = """\
# ignored header
0.0 0.0 0.0 10.0 0.01 0.02 0.03 1.0 2.0 18 1 1 1 1.2 0.8 0.9 1 1
0.2 0.0 0.000001 10.2 0.02 0.02 0.04 1.1 2.1 19 1 1 1 1.3 0.9 1.0 1 1
0.4 0.0 0.000002 10.4 0.03 0.02 0.05 NaN NaN 0 2 2 2 2.0 1.2 1.4 1 2
0.6 0.0 0.000003 10.6 0.04 0.02 0.06 1.3 2.3 17 4 4 4 2.5 1.5 1.6 1 4
0.8 0.0 0.000004
"""


class RtkPlotStudioTests(unittest.TestCase):
    def _write_sample(self, directory: Path) -> Path:
        path = directory / "gnss_rtkplot.txt"
        path.write_text(SAMPLE_ROWS, encoding="utf-8")
        return path

    def test_parse_and_summarize(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self._write_sample(Path(temp_dir))
            dataset = parse_rtkplot(path)
            summary = summarize_dataset(dataset)

        self.assertEqual(len(dataset.samples), 4)
        self.assertEqual(summary["samples"], 4)
        self.assertEqual(summary["fix_type_counts"], {"NO_SOLUTION": 1, "RTKFIX": 2, "RTKFLOAT": 1})
        self.assertEqual(summary["malformed_rows"], 1)
        self.assertEqual(summary["valid_position_samples"], 4)
        self.assertEqual(summary["plottable_position_samples"], 3)
        self.assertEqual(summary["finite_sigma_samples"], 4)

    def test_enu_conversion_preserves_origin(self) -> None:
        point = enu_from_llh(0.0, 0.0, 10.0, 0.0, 0.0, 10.0)
        self.assertAlmostEqual(point.east_m, 0.0, places=6)
        self.assertAlmostEqual(point.north_m, 0.0, places=6)
        self.assertAlmostEqual(point.up_m, 0.0, places=6)

        moved = enu_from_llh(0.0, 0.000001, 10.0, 0.0, 0.0, 10.0)
        self.assertAlmostEqual(moved.east_m, (6378137.0 + 10.0) * 0.000001, places=6)

    def test_output_base_with_dot_is_preserved(self) -> None:
        paths = output_paths(Path("run.2026.11.06"), ("svg", "png"))
        self.assertEqual(
            [path.name for path in paths],
            ["run.2026.11.06.svg", "run.2026.11.06.png"],
        )

    def test_cli_inspect_and_render(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            source = self._write_sample(directory)
            output = directory / "figures" / "sample_position"
            env = dict(os.environ)
            env["MPLBACKEND"] = "Agg"

            inspect_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "rtkplot_studio.py"),
                    "inspect",
                    "--input",
                    str(source),
                    "--json",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(inspect_result.returncode, 0, inspect_result.stderr)
            self.assertEqual(json.loads(inspect_result.stdout)["inputs"][0]["samples"], 4)

            render_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "rtkplot_studio.py"),
                    "render",
                    "--input",
                    str(source),
                    "--plot",
                    "position",
                    "--output",
                    str(output),
                    "--formats",
                    "svg,png",
                    "--json",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(render_result.returncode, 0, render_result.stderr)
            payload = json.loads(render_result.stdout)

            self.assertEqual(len(payload["outputs"]), 2)
            for output_path in payload["outputs"]:
                path = Path(output_path)
                self.assertTrue(path.exists())
                self.assertGreater(path.stat().st_size, 0)

            overwrite_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "rtkplot_studio.py"),
                    "render",
                    "--input",
                    str(source),
                    "--plot",
                    "position",
                    "--output",
                    str(output),
                    "--formats",
                    "svg,png",
                    "--json",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(overwrite_result.returncode, 2)
            self.assertFalse(json.loads(overwrite_result.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
