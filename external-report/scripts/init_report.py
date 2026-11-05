#!/usr/bin/env python3
"""Create a new client-facing report from the bundled report starter."""

from __future__ import annotations

import argparse
import html
import shutil
from datetime import date
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path, help="Destination report directory")
    parser.add_argument("--title", required=True, help="Report title")
    parser.add_argument(
        "--subtitle",
        default="围绕客户问题整理发现、处理结果、验证证据和剩余风险。",
    )
    parser.add_argument("--author", default="报告人")
    parser.add_argument("--period", default=date.today().strftime("%Y-%m"))
    parser.add_argument("--category", default="对外技术报告")
    parser.add_argument(
        "--report-date",
        default=date.today().isoformat(),
        help="Displayed report date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace starter files in a non-empty destination",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    skill_root = Path(__file__).resolve().parent.parent
    starter_root = skill_root / "assets" / "report-starter"
    output = args.output.resolve()

    if not starter_root.is_dir():
        raise SystemExit(f"Starter directory not found: {starter_root}")
    if output == starter_root:
        raise SystemExit("Output directory must not overwrite the skill starter")
    if output.exists() and any(output.iterdir()) and not args.force:
        raise SystemExit(
            f"Destination is not empty: {output}. Use --force only when replacement is intended."
        )

    output.mkdir(parents=True, exist_ok=True)
    shutil.copytree(starter_root, output, dirs_exist_ok=True)
    (output / "assets").mkdir(exist_ok=True)

    report_month = args.period[-2:] if len(args.period) >= 2 else args.period
    replacements = {
        "{{REPORT_TITLE}}": args.title,
        "{{REPORT_SUBTITLE}}": args.subtitle,
        "{{REPORT_AUTHOR}}": args.author,
        "{{REPORT_PERIOD}}": args.period,
        "{{REPORT_CATEGORY}}": args.category,
        "{{REPORT_DATE}}": args.report_date,
        "{{REPORT_MONTH}}": report_month,
    }
    index_path = output / "index.html"
    page = index_path.read_text(encoding="utf-8")
    for token, value in replacements.items():
        page = page.replace(token, html.escape(value))
    index_path.write_text(page, encoding="utf-8")

    print(f"Created {index_path}")
    print(f"Add report figures under {output / 'assets'}")
    print(f"Validate with: python {skill_root / 'scripts' / 'validate_report.py'} {index_path}")


if __name__ == "__main__":
    main()
