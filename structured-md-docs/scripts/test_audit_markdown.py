#!/usr/bin/env python3
"""Focused tests for audit_markdown.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("audit_markdown.py")


def run_audit(path: Path, *extra: str) -> tuple[int, set[str], dict]:
    process = subprocess.run(
        [sys.executable, str(SCRIPT), str(path), "--json", *extra],
        capture_output=True,
        check=False,
        encoding="utf-8",
        text=True,
    )
    result = json.loads(process.stdout)
    codes = {finding["code"] for finding in result["findings"]}
    return process.returncode, codes, result


class AuditMarkdownTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write(self, name: str, content: str) -> Path:
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_valid_document_with_toc(self) -> None:
        path = self.write(
            "valid.md",
            "# Document\n\n"
            "## Contents\n\n"
            "- [1. Problem](#1-problem)\n"
            "- [2. Result](#2-result)\n\n"
            "## 1. Problem\n\nText.\n\n"
            "## 2. Result\n\nConclusion.\n",
        )
        code, codes, _ = run_audit(path, "--strict")
        self.assertEqual(0, code)
        self.assertEqual(set(), codes)

    def test_multisection_document_requires_toc(self) -> None:
        path = self.write(
            "missing-toc.md",
            "# Document\n\n## 1. Problem\n\nText.\n\n## 2. Result\n\nText.\n",
        )
        code, codes, _ = run_audit(path)
        self.assertEqual(1, code)
        self.assertIn("MD101", codes)

    def test_single_content_section_still_requires_toc(self) -> None:
        path = self.write(
            "single-section.md",
            "# Document\n\n## Only section\n\nText.\n",
        )
        _, codes, _ = run_audit(path)
        self.assertIn("MD101", codes)

        code, codes, _ = run_audit(path, "--strict", "--no-require-toc")
        self.assertEqual(0, code)
        self.assertEqual(set(), codes)

    def test_stale_toc_reports_missing_and_unknown_anchor(self) -> None:
        path = self.write(
            "stale.md",
            "# Document\n\n"
            "## Contents\n\n"
            "- [1. Old](#1-old)\n"
            "- [2. Result](#2-result)\n\n"
            "## 1. Problem\n\nText.\n\n"
            "## 2. Result\n\nText.\n",
        )
        _, codes, _ = run_audit(path)
        self.assertTrue({"MD103", "MD106", "MD120"}.issubset(codes))

    def test_cross_file_heading_anchor_is_validated(self) -> None:
        self.write(
            "target.md",
            "# Target\n\n## Target section\n\nText.\n",
        )
        path = self.write(
            "linked.md",
            "# Document\n\n"
            "## Contents\n\n"
            "- [Target](#target)\n\n"
            "## Target\n\n"
            "[Valid](target.md#target-section)\n",
        )
        code, codes, _ = run_audit(path, "--strict")
        self.assertEqual(0, code)
        self.assertEqual(set(), codes)

        path.write_text(
            "# Document\n\n"
            "## Contents\n\n"
            "- [Target](#target)\n\n"
            "## Target\n\n"
            "[Invalid](target.md#missing)\n",
            encoding="utf-8",
        )
        _, codes, _ = run_audit(path)
        self.assertIn("MD122", codes)

    def test_broken_file_link_is_reported(self) -> None:
        path = self.write(
            "broken.md",
            "# Document\n\n"
            "## Contents\n\n"
            "- [1. A](#1-a)\n"
            "- [2. B](#2-b)\n\n"
            "## 1. A\n\n[Missing](missing.md)\n\n"
            "## 2. B\n",
        )
        _, codes, _ = run_audit(path)
        self.assertIn("MD121", codes)

    def test_reference_style_links_are_audited(self) -> None:
        self.write(
            "target.md",
            "# Target\n\n## Target section\n\nText.\n",
        )
        path = self.write(
            "references.md",
            "# Document\n\n"
            "## Contents\n\n"
            "- [1. A](#1-a)\n"
            "- [2. B](#2-b)\n\n"
            "## 1. A\n\n"
            "[Valid][valid]\n"
            "[Missing][missing]\n\n"
            "## 2. B\n\n"
            "[valid]: target.md#target-section\n"
            "[missing]: missing.md\n",
        )
        _, codes, _ = run_audit(path)
        self.assertIn("MD121", codes)
        self.assertNotIn("MD123", codes)

    def test_unclosed_fence_is_reported(self) -> None:
        path = self.write(
            "fence.md",
            "# Document\n\n"
            "## Contents\n\n"
            "- [1. A](#1-a)\n"
            "- [2. B](#2-b)\n\n"
            "## 1. A\n\n"
            "```text\nUnclosed\n\n"
            "## 2. B\n",
        )
        _, codes, _ = run_audit(path)
        self.assertIn("MD105", codes)

    def test_explicit_anchor_can_target_a_heading(self) -> None:
        path = self.write(
            "explicit.md",
            "# Document\n\n"
            "## Contents\n\n"
            "- [1. Problem](#stable-problem)\n"
            "- [2. Result](#2-result)\n\n"
            '<a id="stable-problem"></a>\n'
            "## 1. Problem\n\nText.\n\n"
            "## 2. Result\n\nText.\n",
        )
        code, codes, _ = run_audit(path, "--strict")
        self.assertEqual(0, code)
        self.assertEqual(set(), codes)

    def test_indented_atx_headings_are_detected(self) -> None:
        path = self.write(
            "indented.md",
            "# Document\n\n"
            "   ## First\n\nText.\n\n"
            "   ## Second\n\nText.\n",
        )
        _, codes, _ = run_audit(path)
        self.assertIn("MD101", codes)

    def test_github_slug_rules_keep_underscores_and_repeated_hyphens(self) -> None:
        path = self.write(
            "slugs.md",
            "# Document\n\n"
            "## Contents\n\n"
            "- [A_B](#a_b)\n"
            "- [A_B_C](#a_b_c)\n"
            "- [foo--bar](#foo--bar)\n\n"
            "## A_B\n\nText.\n\n"
            "## A_B_C\n\nText.\n\n"
            "## foo--bar\n\nText.\n",
        )
        code, codes, _ = run_audit(path, "--strict")
        self.assertEqual(0, code)
        self.assertEqual(set(), codes)

    def test_toc_after_intro_content_is_rejected(self) -> None:
        path = self.write(
            "late-toc.md",
            "# Document\n\n"
            "Intro line one.\n\n"
            "Intro line two.\n\n"
            "Intro line three.\n\n"
            "Intro line four.\n\n"
            "## Contents\n\n"
            "- [1. A](#1-a)\n"
            "- [2. B](#2-b)\n\n"
            "## 1. A\n\nText.\n\n"
            "## 2. B\n\nText.\n",
        )
        _, codes, _ = run_audit(path)
        self.assertIn("MD107", codes)

    def test_toc_after_single_intro_paragraph_is_rejected(self) -> None:
        path = self.write(
            "intro-before-toc.md",
            "# Document\n\n"
            "This is introductory prose, not metadata.\n\n"
            "## Contents\n\n"
            "- [1. A](#1-a)\n"
            "- [2. B](#2-b)\n\n"
            "## 1. A\n\nText.\n\n"
            "## 2. B\n\nText.\n",
        )
        _, codes, _ = run_audit(path)
        self.assertIn("MD107", codes)

    def test_short_status_block_before_toc_is_valid(self) -> None:
        path = self.write(
            "status-before-toc.md",
            "# Document\n\n"
            "**状态：** 初稿。\n\n"
            "## Contents\n\n"
            "- [1. A](#1-a)\n"
            "- [2. B](#2-b)\n\n"
            "## 1. A\n\nText.\n\n"
            "## 2. B\n\nText.\n",
        )
        code, codes, _ = run_audit(path, "--strict")
        self.assertEqual(0, code)
        self.assertEqual(set(), codes)

    def test_blockquote_lazy_continuation_is_valid_before_toc(self) -> None:
        path = self.write(
            "blockquote-before-toc.md",
            "# Document\n\n"
            "> Status: Draft.\n"
            "> Waiting for receiver validation.\n\n"
            "## Contents\n\n"
            "- [1. A](#1-a)\n"
            "- [2. B](#2-b)\n\n"
            "## 1. A\n\nText.\n\n"
            "## 2. B\n\nText.\n",
        )
        code, codes, _ = run_audit(path, "--strict")
        self.assertEqual(0, code)
        self.assertEqual(set(), codes)

    def test_hard_break_and_inline_code_placeholder_are_valid(self) -> None:
        path = self.write(
            "valid-inline.md",
            "# Document\n\n"
            "## Contents\n\n"
            "- [1. A](#1-a)\n"
            "- [2. B](#2-b)\n\n"
            "## 1. A\n\n"
            "First line  \n"
            "Second line with `TODO` literal.\n\n"
            "## 2. B\n\n"
            "Text.\n",
        )
        code, codes, _ = run_audit(path, "--strict")
        self.assertEqual(0, code)
        self.assertEqual(set(), codes)


if __name__ == "__main__":
    unittest.main()
