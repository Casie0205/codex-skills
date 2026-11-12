#!/usr/bin/env python3
"""Tests for the read-only code study bundle renderer."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict


SCRIPT = Path(__file__).with_name("render_study_bundle.py")


def fixture() -> Dict[str, Any]:
    return {
        "meta": {
            "project": "ctclib",
            "topic_id": "post-entry-main-flow",
            "title": "CTCLib 後處理主流程",
            "repository": r"D:\Code\ctclib-nav",
            "source_commit": "abc1234",
            "generated_at": "2026-11-12 15:00 +08:00",
            "purpose": "理解後處理從入口到 GNSS 處理的閱讀路徑。",
        },
        "summary": {
            "one_sentence": "入口載入配置後，依序進入解碼與 GNSS 後處理。",
            "what_it_does": [
                "PostEntry 建立後處理執行環境。",
                "DataDecoder 將輸入資料送入回呼流程。",
            ],
            "key_findings": ["入口只負責裝配與調度。"],
            "reading_strategy": ["先讀入口，再沿回呼尋找下一個處理器。"],
        },
        "reading_path": [
            {
                "order": 1,
                "name": "PostEntry",
                "source": "proj/ctclib_app/src/PostEntry.c:120",
                "why": "確認配置與主流程如何開始。",
            },
            {
                "order": 2,
                "name": "DataDecoder",
                "source": "proj/ctclib_app/src/DataDecoder/DataDecoder.c:340",
                "why": "確認回呼與定位觸發。",
            },
        ],
        "flow": [
            {
                "step": 1,
                "name": "載入配置",
                "source": "proj/ctclib_app/src/PostEntry.c:120",
                "purpose": "建立後處理參數。",
                "caller": "PostEntry",
                "callee": "LoadConfig",
                "input": "配置檔路徑",
                "output": "配置結構",
                "state": "配置由入口持有",
                "normal": "配置有效時繼續",
                "error": "配置錯誤時停止",
                "next": "proj/ctclib_app/src/DataDecoder/DataDecoder.c:340",
                "confidence": "confirmed",
                "code_language": "c",
                "code": "status = LoadConfig(path, &config);",
            },
            {
                "step": 2,
                "name": "分派資料",
                "source": "proj/ctclib_app/src/DataDecoder/DataDecoder.c:340",
                "purpose": "依資料類型進入解碼流程。",
                "caller": "DataDecoder",
                "callee": "DispatchMessage",
                "input": "原始訊息",
                "output": "解碼後的觀測量",
                "normal": "資料類型已支援",
                "error": "未知資料類型被忽略",
                "confidence": "inferred",
            },
        ],
        "symbols": [
            {
                "name": "PostEntry",
                "kind": "function",
                "defined_at": "proj/ctclib_app/src/PostEntry.c:120",
                "role": "後處理入口",
                "confidence": "confirmed",
            },
            {
                "name": "DataDecoder",
                "kind": "function",
                "defined_at": "proj/ctclib_app/src/DataDecoder/DataDecoder.c:340",
                "role": "資料解碼與回呼",
                "confidence": "confirmed",
            },
        ],
        "data_structures": [
            {
                "name": "PostConfig",
                "defined_at": "proj/ctclib_app/include/PostConfig.h:24",
                "purpose": "後處理參數",
                "fields": "路徑、頻率、模式",
                "ownership": "由 PostEntry 建立",
                "confidence": "confirmed",
            }
        ],
        "config_map": [
            {
                "key": "imu_freq",
                "source": "config/default.ctccfg:12",
                "consumed_at": "proj/ctclib_app/src/PostEntry.c:150",
                "meaning": "IMU 輸出頻率",
                "default": "200",
            }
        ],
        "evidence": [
            {
                "claim": "PostEntry 載入配置後進入解碼流程。",
                "source": "proj/ctclib_app/src/PostEntry.c:120",
                "confidence": "confirmed",
            },
            {
                "claim": "錯誤資料類型可能被跳過。",
                "source": "proj/ctclib_app/src/DataDecoder/DataDecoder.c:340",
                "confidence": "inferred",
            },
        ],
        "questions": {
            "confirmed": ["PostEntry 是後處理入口。"],
            "inferred": ["未知訊息可能只記錄後跳過。"],
            "open": ["實際錯誤處理是否會切換後續流程仍未確認。"],
        },
        "next_reading": ["接著閱讀 DispatchMessage 的 switch 分支。"],
        "sources": ["D:\\DOC\\ctclib\\PostEntry_Flow.md", "proj/ctclib_app/src/PostEntry.c"],
    }


class RenderStudyBundleTests(unittest.TestCase):
    def run_renderer(
        self,
        data: Dict[str, Any],
        root: Path,
        encoding: str = "utf-8",
    ) -> subprocess.CompletedProcess[str]:
        input_path = root / "study-result.json"
        input_path.write_text(json.dumps(data, ensure_ascii=False), encoding=encoding)
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(SCRIPT),
                "--input",
                str(input_path),
                "--output-root",
                str(root),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_renders_complete_offline_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = self.run_renderer(fixture(), root, encoding="utf-8-sig")
            self.assertEqual(result.returncode, 0, result.stderr)
            for name in (
                "study-report.html",
                "study-note.md",
                "symbol-index.csv",
                "questions.md",
            ):
                self.assertTrue((root / name).is_file(), name)

            document = (root / "study-report.html").read_text(encoding="utf-8")
            self.assertIn("post-entry-main-flow", document)
            self.assertIn("abc1234", document)
            self.assertIn("CTCLib 後處理主流程", document)
            self.assertNotRegex(document, r'(src|href)="https?://')
            self.assertNotIn("{{", document)
            self.assertGreaterEqual(len(document.encode("utf-8")), 5000)

            markdown = (root / "study-note.md").read_text(encoding="utf-8")
            self.assertIn("[3. 執行流程](#3-執行流程)", markdown)
            self.assertIn("PostEntry", markdown)
            self.assertIn("```c", markdown)

            symbol_index = (root / "symbol-index.csv").read_text(encoding="utf-8-sig")
            self.assertIn("PostEntry", symbol_index)
            self.assertIn("confirmed", symbol_index)

            questions = (root / "questions.md").read_text(encoding="utf-8")
            self.assertIn("實際錯誤處理", questions)

    def test_rejects_empty_flow(self) -> None:
        data = fixture()
        data["flow"] = []
        with tempfile.TemporaryDirectory() as temp:
            result = self.run_renderer(data, Path(temp))
            self.assertNotEqual(result.returncode, 0)

    def test_rejects_source_without_line_number(self) -> None:
        data = fixture()
        data["flow"][0]["source"] = "proj/ctclib_app/src/PostEntry.c"
        with tempfile.TemporaryDirectory() as temp:
            result = self.run_renderer(data, Path(temp))
            self.assertNotEqual(result.returncode, 0)

    def test_rejects_invalid_confidence(self) -> None:
        data = fixture()
        data["flow"][0]["confidence"] = "maybe"
        with tempfile.TemporaryDirectory() as temp:
            result = self.run_renderer(data, Path(temp))
            self.assertNotEqual(result.returncode, 0)

    def test_rejects_input_outside_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            root = Path(temp)
            input_path = Path(outside) / "study-result.json"
            input_path.write_text(json.dumps(fixture()), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SCRIPT),
                    "--input",
                    str(input_path),
                    "--output-root",
                    str(root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)

    def test_rejects_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "study-result.json").write_text("{", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SCRIPT),
                    "--input",
                    str(root / "study-result.json"),
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
