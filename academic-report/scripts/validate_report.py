#!/usr/bin/env python3
"""Validate structure, references, and print sizing for an academic HTML report."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

try:
    from PIL import Image
except ImportError:
    Image = None


LOCAL_SCHEMES = ("",)


@dataclass
class ReportAudit:
    ids: list[str] = field(default_factory=list)
    refs: list[str] = field(default_factory=list)
    stylesheets: list[str] = field(default_factory=list)
    images: list[dict[str, str]] = field(default_factory=list)
    figure_count: int = 0
    table_count: int = 0
    titled_table_count: int = 0
    has_report_main: bool = False


class ReportParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.audit = ReportAudit()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        classes = set(values.get("class", "").split())

        if values.get("id"):
            self.audit.ids.append(values["id"])
        if tag == "section" and "report-section" in classes:
            self.audit.has_report_main = True
        if "report-main" in classes:
            self.audit.has_report_main = True
        if tag == "figure":
            self.audit.figure_count += 1
        if tag == "table":
            self.audit.table_count += 1
        if tag == "div" and "table-wrap" in classes and values.get("data-title"):
            self.audit.titled_table_count += 1

        for key in ("src", "href"):
            value = values.get(key)
            if value:
                self.audit.refs.append(value)
        if tag == "link" and "stylesheet" in values.get("rel", "").split():
            self.audit.stylesheets.append(values.get("href", ""))
        if tag == "img":
            self.audit.images.append(values)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("html", type=Path, help="Report HTML file")
    parser.add_argument(
        "--content-width-mm",
        type=float,
        default=170.0,
        help="Known A4 content width used for image-height checks",
    )
    parser.add_argument(
        "--max-image-height-mm",
        type=float,
        default=245.0,
        help="Maximum accepted printed height for one image",
    )
    return parser.parse_args()


def resolve_local_ref(report_dir: Path, value: str) -> Path | None:
    parts = urlsplit(value)
    if parts.scheme not in LOCAL_SCHEMES:
        return None
    if not parts.path:
        return None
    return (report_dir / unquote(parts.path)).resolve()


def main() -> None:
    args = parse_args()
    html_path = args.html.resolve()
    if not html_path.is_file():
        raise SystemExit(f"Report not found: {html_path}")

    source = html_path.read_text(encoding="utf-8")
    parser = ReportParser()
    parser.feed(source)
    audit = parser.audit
    report_dir = html_path.parent
    errors: list[str] = []
    warnings: list[str] = []

    duplicate_ids = sorted({item for item in audit.ids if audit.ids.count(item) > 1})
    if duplicate_ids:
        errors.append(f"Duplicate IDs: {', '.join(duplicate_ids)}")

    missing_refs = []
    for value in audit.refs:
        resolved = resolve_local_ref(report_dir, value)
        if resolved is not None and not resolved.exists():
            missing_refs.append(value)
    if missing_refs:
        errors.append(f"Missing local resources: {', '.join(sorted(set(missing_refs)))}")

    placeholders = sorted(
        set(re.findall(r"\{\{[^{}]+\}\}|\[TODO:[^\]]*\]|TODO:|FIXME:", source))
    )
    if placeholders:
        errors.append(f"Unresolved placeholders: {', '.join(placeholders)}")

    missing_alt = [image.get("src", "(missing src)") for image in audit.images if not image.get("alt", "").strip()]
    if missing_alt:
        errors.append(f"Images without alt text: {', '.join(missing_alt)}")

    if not audit.has_report_main:
        errors.append("Missing .report-main report container")
    if not audit.stylesheets:
        errors.append("No stylesheet is linked")

    print_styles = []
    for stylesheet in audit.stylesheets:
        resolved = resolve_local_ref(report_dir, stylesheet)
        if resolved is None or not resolved.is_file():
            continue
        css = resolved.read_text(encoding="utf-8")
        if "@media print" in css:
            print_styles.append(resolved)
    if not print_styles:
        errors.append("No linked stylesheet contains @media print")
    elif not any(re.search(r"size:\s*A4(?:\s+portrait)?", path.read_text(encoding="utf-8"), re.IGNORECASE) for path in print_styles):
        warnings.append("Print stylesheet does not declare size: A4 portrait")

    if audit.table_count and audit.titled_table_count < audit.table_count:
        warnings.append(
            f"{audit.table_count - audit.titled_table_count} table(s) do not use a data-title caption"
        )
    if not audit.images:
        warnings.append("Report contains no figures")
    if not audit.table_count:
        warnings.append("Report contains no tables")

    if Image is None:
        warnings.append("Pillow is unavailable; print image-height checks were skipped")
    else:
        for image in audit.images:
            source_value = image.get("src", "")
            resolved = resolve_local_ref(report_dir, source_value)
            if resolved is None or not resolved.is_file():
                continue
            try:
                with Image.open(resolved) as bitmap:
                    width, height = bitmap.size
            except OSError:
                warnings.append(f"Could not read image dimensions: {source_value}")
                continue
            printed_height = args.content_width_mm * height / width
            print(f"Image {source_value}: {width}x{height}, {printed_height:.1f} mm at {args.content_width_mm:g} mm width")
            if printed_height > args.max_image_height_mm:
                errors.append(
                    f"{source_value} would print at {printed_height:.1f} mm high; "
                    f"limit is {args.max_image_height_mm:.1f} mm"
                )

    print(
        f"Report {html_path}: {audit.figure_count} figures, "
        f"{audit.table_count} tables, {len(audit.images)} images"
    )
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        print(f"Validation failed with {len(errors)} error(s).")
        sys.exit(1)
    print(f"Validation passed with {len(warnings)} warning(s).")


if __name__ == "__main__":
    main()
