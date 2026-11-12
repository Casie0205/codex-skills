from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import replace_literal as replacement


SCRIPT = Path(__file__).with_name("replace_literal.py")


class ReplaceLiteralTests(unittest.TestCase):
    def run_replace(
        self,
        root: Path,
        target: Path,
        old: bytes,
        new: bytes,
        expected_count: int = 1,
        apply: bool = True,
        encoding: str | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        old_file = root / "old.txt"
        new_file = root / "new.txt"
        old_file.write_bytes(old)
        new_file.write_bytes(new)
        command = [
            sys.executable,
            "-B",
            str(SCRIPT),
            "--path",
            str(target),
            "--old-file",
            str(old_file),
            "--new-file",
            str(new_file),
            "--expected-count",
            str(expected_count),
        ]
        if apply:
            command.append("--apply")
        if encoding:
            command.extend(["--encoding", encoding])
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        payload = json.loads(result.stdout)
        return result, payload

    def test_applies_one_exact_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "source.c"
            target.write_text("before\nneedle\nafter\n", encoding="utf-8")
            result, payload = self.run_replace(root, target, b"needle\n", b"changed\n")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(payload["applied"])
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "before\nchanged\nafter\n",
            )

    def test_normalizes_lf_snippet_to_crlf_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "source.h"
            target.write_bytes(b"first\r\nsecond\r\nthird\r\n")
            result, payload = self.run_replace(
                root,
                target,
                b"second\n",
                b"replacement\n",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(payload["newline"], "crlf")
            self.assertEqual(target.read_bytes(), b"first\r\nreplacement\r\nthird\r\n")

    def test_rejects_count_mismatch_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "source.c"
            original = b"needle\nneedle\n"
            target.write_bytes(original)
            result, payload = self.run_replace(root, target, b"needle\n", b"changed\n")
            self.assertEqual(result.returncode, 2)
            self.assertEqual(payload["status"], "count_mismatch")
            self.assertEqual(target.read_bytes(), original)

    def test_dry_run_does_not_write_and_bom_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "source.h"
            original = b"\xef\xbb\xbfneedle\n"
            target.write_bytes(original)
            result, payload = self.run_replace(
                root,
                target,
                b"needle\n",
                b"changed\n",
                apply=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(payload["applied"])
            self.assertTrue(payload["bom"])
            self.assertEqual(target.read_bytes(), original)

    def test_apply_preserves_utf8_bom(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "source.h"
            target.write_bytes(b"\xef\xbb\xbfneedle\n")
            result, payload = self.run_replace(
                root,
                target,
                b"needle\n",
                b"changed\n",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(payload["applied"])
            self.assertEqual(target.read_bytes(), b"\xef\xbb\xbfchanged\n")

    def test_apply_preserves_utf16_bom(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "source.h"
            target.write_bytes(b"\xff\xfe" + "needle\r\n".encode("utf-16-le"))
            result, payload = self.run_replace(
                root,
                target,
                b"needle\n",
                b"changed\n",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(payload["encoding"], "utf-16-le")
            self.assertEqual(
                target.read_bytes(),
                b"\xff\xfe" + "changed\r\n".encode("utf-16-le"),
            )

    def test_refuses_mixed_newlines(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "source.c"
            original = b"first\r\nneedle\nlast\r\n"
            target.write_bytes(original)
            result, payload = self.run_replace(root, target, b"needle\n", b"changed\n")
            self.assertEqual(result.returncode, 2)
            self.assertEqual(payload["status"], "mixed_newlines")
            self.assertEqual(target.read_bytes(), original)

    def test_ambiguous_utf8_requires_explicit_encoding(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "source.c"
            original = "needle 中文\n".encode("utf-8")
            target.write_bytes(original)
            result, payload = self.run_replace(
                root,
                target,
                "needle 中文\n".encode("utf-8"),
                "changed 中文\n".encode("utf-8"),
            )
            self.assertEqual(result.returncode, 3)
            self.assertEqual(payload["status"], "ambiguous_encoding")
            self.assertEqual(target.read_bytes(), original)

            result, payload = self.run_replace(
                root,
                target,
                "needle 中文\n".encode("utf-8"),
                "changed 中文\n".encode("utf-8"),
                encoding="utf-8",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(payload["encoding_confidence"], "explicit")
            self.assertEqual(target.read_bytes(), "changed 中文\n".encode("utf-8"))

    def test_atomic_write_failure_preserves_original(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "source.c"
            old_file = root / "old.txt"
            new_file = root / "new.txt"
            original = b"needle\n"
            target.write_bytes(original)
            old_file.write_bytes(b"needle\n")
            new_file.write_bytes(b"changed\n")
            with patch.object(replacement.os, "replace", side_effect=OSError("boom")):
                with self.assertRaises(OSError):
                    replacement.replace_literal(
                        path=target,
                        old_file=old_file,
                        new_file=new_file,
                        expected_count=1,
                        apply=True,
                    )
            self.assertEqual(target.read_bytes(), original)

    def test_rejects_empty_old_snippet(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "source.c"
            original = b"unchanged\n"
            target.write_bytes(original)
            result, payload = self.run_replace(root, target, b"", b"changed\n")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(payload["status"], "error")
            self.assertEqual(target.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
