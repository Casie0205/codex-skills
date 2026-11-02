#!/usr/bin/env python3
"""Build human-readable MathType V2 intermediates and AI review ledger."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


ISSUE_DESCRIPTIONS = {
    "RT_TOKEN": "源式与 MathType 回读的字符序列不一致",
    "RT_STRUCTURE": "源式与 MathType 回读的结构树不一致",
    "RT_MATHML_STYLE": "MathML 字形序列不一致",
    "RT_MTEF_STYLE": "最终 MTEF 粗体/斜体样式不一致",
    "RT_MTEF_FONT_PROFILE": (
        "最终 MTEF FONT_DEF 未同时满足 Times New Roman、Euclid Extra，"
        "或普通样式槽未映射到 Times New Roman，"
        "或 EQN_PREFS 的 Math Extra 样式未指向 Euclid Extra，"
        "或仍含精确旧字体 MT Extra"
    ),
    "READBACK_REPLACEMENT_CHAR": "MathType 回读含 U+FFFD 替换字符",
    "SPECIAL_ACCENT_SCRIPT_UNSUPPORTED": "重音后角标不属于通用安全修正规则",
    "SPECIAL_ACCENT_SCRIPT_MIXED": "同式存在混合重音角标字符",
    "SPECIAL_ACCENT_SCRIPT_UNCORRECTED": "重音角标未做自动几何修正",
    "SPECIAL_TEX_READBACK_SKIPPED_PERIOD_ACCENT": (
        "普通句点重音会触发 MathType TeX 导出器弹窗，已跳过非必要 TeX 诊断"
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--intermediate-output", type=Path, required=True)
    parser.add_argument("--review-output", type=Path, required=True)
    return parser.parse_args()


def load_jsonl(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    header: dict[str, Any] = {}
    formulas: list[dict[str, Any]] = []
    summary: dict[str, Any] = {}
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
            record_type = record.get("type")
            if record_type == "header":
                header = record
            elif record_type == "formula":
                formulas.append(record)
            elif record_type == "summary":
                summary = record
    formulas.sort(key=lambda item: int(item.get("sourceIndex", 0)))
    return header, formulas, summary


def issue_codes(formula: dict[str, Any]) -> list[str]:
    raw = formula.get("reviewIssueCodes", "")
    if isinstance(raw, list):
        return [str(item) for item in raw if str(item)]
    return [item for item in str(raw).split(",") if item]


def code_block(value: Any, language: str = "") -> str:
    text = "" if value is None else str(value)
    return f"````{language}\n{text}\n````"


def safe_cell(value: Any) -> str:
    return str(value).replace("|", r"\|").replace("\r", " ").replace("\n", " ")


def format_header(header: dict[str, Any], summary: dict[str, Any]) -> list[str]:
    return [
        f"- 源文档：`{header.get('sourcePath', '')}`",
        f"- 源 SHA-256：`{header.get('sourceSha256', '')}`",
        f"- 源 OMML 数量：{header.get('sourceOmmlCount', 0)}",
        f"- 批处理策略：`{header.get('conversionPolicy', summary.get('conversionPolicy', ''))}`",
        f"- 已生成 MathType：{summary.get('convertedCount', 0)}",
        f"- 自动通过：{summary.get('cleanConversionCount', 0)}",
        f"- 待 AI 复核：{summary.get('reviewRequiredCount', 0)}",
        f"- 致命错误：{summary.get('fatalErrorCount', 0)}",
        (
            "- MTEF 字体配置通过："
            f"{summary.get('mtefFontProfileMatchCount', 0)}/"
            f"{header.get('sourceOmmlCount', 0)}"
        ),
    ]


def build_intermediate(
    header: dict[str, Any],
    formulas: Iterable[dict[str, Any]],
    summary: dict[str, Any],
) -> str:
    lines = [
        "# MathType V2 全量公式中间量",
        "",
        "本文件保存每个 Word 原生公式转换后的源 MathML、MathType 诊断 TeX 和自动检查状态。"
        "TeX 只用于核对，不是 MathType 对象的生成输入。",
        "",
        *format_header(header, summary),
        "",
    ]
    for formula in formulas:
        index = int(formula.get("sourceIndex", 0))
        codes = issue_codes(formula)
        status = "待 AI 复核" if formula.get("reviewRequired", False) else "自动通过"
        lines.extend(
            [
                f"## 公式 {index:04d}",
                "",
                f"- 状态：{status}",
                f"- 风险代码：`{','.join(codes) if codes else '无'}`",
                f"- Word 位置：{formula.get('wordStart', '')}–{formula.get('wordEnd', '')}",
                "",
                "源公式规范化 MathML：",
                "",
                code_block(formula.get("normalizedMathMl", ""), "xml"),
                "",
                "MathType 回读诊断 TeX：",
                "",
                code_block(formula.get("readbackTex", ""), "tex"),
                "",
            ]
        )
    return "\n".join(lines)


def build_review(
    header: dict[str, Any],
    formulas: Iterable[dict[str, Any]],
    summary: dict[str, Any],
) -> str:
    flagged = [item for item in formulas if item.get("reviewRequired", False)]
    lines = [
        "# MathType V2 AI 复核台账",
        "",
        "本台账只收录通用批处理已生成对象、但自动闭环存在差异的公式。"
        "这些差异不触发全量重跑；AI 确认后登记结论，必要时只重做对应公式索引。",
        "",
        *format_header(header, summary),
        "",
        "## 待复核总表",
        "",
        "| 源公式索引 | 风险代码 | 当前状态 | 特殊规则编号 | 复核结论 |",
        "|---:|---|---|---|---|",
    ]
    if not flagged:
        lines.append("| — | — | 无待复核项 | — | — |")
    for formula in flagged:
        index = int(formula.get("sourceIndex", 0))
        codes = ",".join(issue_codes(formula))
        lines.append(
            f"| {index} | {safe_cell(codes)} | 待 AI 复核 |  |  |"
        )

    lines.extend(["", "## 风险代码说明", ""])
    observed_codes = sorted(
        {code for formula in flagged for code in issue_codes(formula)}
    )
    if not observed_codes:
        lines.append("- 本次没有风险代码。")
    for code in observed_codes:
        lines.append(f"- `{code}`：{ISSUE_DESCRIPTIONS.get(code, '未登记的新风险类型')}")

    for formula in flagged:
        index = int(formula.get("sourceIndex", 0))
        codes = issue_codes(formula)
        lines.extend(
            [
                "",
                f"## 公式 {index:04d}",
                "",
                f"- 风险代码：`{','.join(codes)}`",
                "- 当前状态：待 AI 复核",
                "- 特殊规则编号：",
                "- 复核结论：",
                "- 局部重做结果：",
                "",
                "源公式规范化 MathML：",
                "",
                code_block(formula.get("normalizedMathMl", ""), "xml"),
                "",
                "MathType 回读 MathML：",
                "",
                code_block(formula.get("readbackMathMl", ""), "xml"),
                "",
                "MathType 回读诊断 TeX：",
                "",
                code_block(formula.get("readbackTex", ""), "tex"),
            ]
        )
    return "\n".join(lines) + "\n"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    args = parse_args()
    header, formulas, summary = load_jsonl(args.manifest)
    write_text(
        args.intermediate_output,
        build_intermediate(header, formulas, summary),
    )
    write_text(
        args.review_output,
        build_review(header, formulas, summary),
    )
    print(
        json.dumps(
            {
                "formula_count": len(formulas),
                "review_required_count": sum(
                    1 for item in formulas if item.get("reviewRequired", False)
                ),
                "intermediate_output": str(args.intermediate_output.resolve()),
                "review_output": str(args.review_output.resolve()),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
