#!/usr/bin/env python3
"""Focused regression tests for the MathType V2 Markdown review ledger."""

from __future__ import annotations

from build_mathtype_v2_markdown import build_review


def main() -> int:
    header = {
        "sourcePath": "sample.docx",
        "sourceSha256": "ABC",
        "sourceOmmlCount": 1,
        "conversionPolicy": "ReviewQueue",
    }
    formulas = [
        {
            "sourceIndex": 1,
            "reviewRequired": True,
            "reviewIssueCodes": "RT_MTEF_FONT_PROFILE",
            "normalizedMathMl": "<math/>",
            "readbackMathMl": "<math/>",
            "readbackTex": "x",
        }
    ]
    summary = {
        "convertedCount": 1,
        "cleanConversionCount": 0,
        "reviewRequiredCount": 1,
        "fatalErrorCount": 0,
        "mtefFontProfileMatchCount": 0,
    }

    output = build_review(header, formulas, summary)
    required_fragments = (
        "MTEF 字体配置通过：0/1",
        "`RT_MTEF_FONT_PROFILE`",
        "最终 MTEF FONT_DEF 未同时满足",
        "普通样式槽未映射到 Times New Roman",
        "Math Extra 样式未指向 Euclid Extra",
    )
    for fragment in required_fragments:
        if fragment not in output:
            raise AssertionError(
                f"Review ledger is missing expected text: {fragment}"
            )

    print('{"TestCount": 5, "Passed": 5}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
