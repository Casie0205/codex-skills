#!/usr/bin/env python3
"""Tests for the cloud development result report renderer."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict


SCRIPT = Path(__file__).with_name("render_result_report.py")


def fixture() -> Dict[str, Any]:
    return {
        "task": {
            "id": "task-example",
            "title": "Example task",
            "status": "DONE",
            "repository": r"D:\Code\example",
            "branch": "main",
            "base_commit": "0123456",
            "result_commit": "abcdef0",
            "change_set": "code",
            "finished_at": "2026-11-11 18:00 +08:00",
        },
        "summary": {
            "requested": "Implement the requested behavior.",
            "implemented": ["Implemented the behavior."],
            "data_flow": ["Input -> new module -> existing consumer"],
            "module_boundaries": ["The new module owns the added behavior."],
        },
        "acceptance": [
            {
                "criterion": "Behavior is implemented.",
                "status": "PASS",
                "evidence": "Regression test passed.",
            }
        ],
        "changes": {
            "diff_stat": "1 file changed",
            "files": [
                {
                    "path": "src/Feature.c",
                    "kind": "added",
                    "purpose": "Implement the feature.",
                }
            ],
            "key_diffs": [
                {
                    "path": "src/Feature.c",
                    "language": "c",
                    "code": "int feature(void) { return 1; }",
                    "explanation": "Adds the feature entrypoint.",
                }
            ],
            "removed_obsolete_paths": [],
        },
        "verification": [
            {
                "name": "Build",
                "command": "build",
                "exit_code": 0,
                "result": "PASS",
                "evidence": "success=true",
            }
        ],
        "review": {
            "status": "PASS",
            "findings": [],
            "unresolved": [],
        },
        "risks": {"items": [], "not_verified": [], "next_action": "none"},
        "doc_discrepancy": {"status": "none", "items": []},
        "sources": ["result.md", "verification.log"],
    }


class RenderResultReportTests(unittest.TestCase):
    def run_renderer(
        self,
        data: Dict[str, Any],
        root: Path,
        output_name: str = "report.html",
        encoding: str = "utf-8",
    ) -> subprocess.CompletedProcess[str]:
        input_path = root / "report.json"
        output_path = root / output_name
        input_path.write_text(json.dumps(data), encoding=encoding)
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(SCRIPT),
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--output-root",
                str(root),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_renders_bom_input_and_self_contained_html(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = self.run_renderer(fixture(), root, encoding="utf-8-sig")
            self.assertEqual(result.returncode, 0, result.stderr)
            document = (root / "report.html").read_text(encoding="utf-8")
            self.assertIn("task-example", document)
            self.assertIn("Acceptance criteria", document)
            self.assertNotIn("{{", document)
            self.assertNotRegex(document, r'(src|href)="https?://')

    def test_rejects_failed_verification_for_done(self) -> None:
        data = fixture()
        data["verification"][0]["result"] = "FAIL"
        with tempfile.TemporaryDirectory() as temp:
            result = self.run_renderer(data, Path(temp))
            self.assertNotEqual(result.returncode, 0)

    def test_rejects_unverified_acceptance_for_done(self) -> None:
        data = fixture()
        data["acceptance"][0]["status"] = "NOT VERIFIED"
        with tempfile.TemporaryDirectory() as temp:
            result = self.run_renderer(data, Path(temp))
            self.assertNotEqual(result.returncode, 0)

    def test_rejects_invalid_result_enum(self) -> None:
        data = fixture()
        data["verification"][0]["result"] = "BOGUS"
        with tempfile.TemporaryDirectory() as temp:
            result = self.run_renderer(data, Path(temp))
            self.assertNotEqual(result.returncode, 0)

    def test_rejects_output_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            root = Path(temp)
            input_path = root / "report.json"
            input_path.write_text(json.dumps(fixture()), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SCRIPT),
                    "--input",
                    str(input_path),
                    "--output",
                    str(Path(outside) / "report.html"),
                    "--output-root",
                    str(root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)

    def test_rejects_input_equals_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            input_path = root / "report.json"
            input_path.write_text(json.dumps(fixture()), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SCRIPT),
                    "--input",
                    str(input_path),
                    "--output",
                    str(input_path),
                    "--output-root",
                    str(root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
