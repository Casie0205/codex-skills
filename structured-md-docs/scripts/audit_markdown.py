#!/usr/bin/env python3
"""Deterministic checks for structure-first Markdown documentation."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote


MARKDOWN_SUFFIXES = {".md", ".markdown"}
SKIP_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".next",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "target",
    "venv",
}
TOC_NAMES = {
    "目录",
    "内容目录",
    "contents",
    "table of contents",
    "toc",
}
ATX_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
SETEXT_UNDERLINE_RE = re.compile(r"^[ \t]*(=+|-+)[ \t]*$")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
INLINE_LINK_RE = re.compile(
    r"(?<!!)\[[^\]]*\]\(\s*(<[^>]+>|[^)\s]+)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)"
)
REFERENCE_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\[([^\]]*)\]")
REFERENCE_DEFINITION_RE = re.compile(
    r'^ {0,3}\[([^\]]+)\]:[ \t]*(<[^>]+>|\S+)'
    r'(?:[ \t]+(?:"[^"]*"|\'[^\']*\'|\([^)]*\)))?[ \t]*$'
)
TOC_LINK_RE = re.compile(
    r"\[[^\]]+\]\(\s*<?#([^)> \t]+)>?(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)"
)
EXPLICIT_ANCHOR_RE = re.compile(
    r"<a\s+[^>]*(?:id|name)\s*=\s*[\"']([^\"']+)[\"'][^>]*>",
    re.IGNORECASE,
)
PLACEHOLDER_RE = re.compile(r"(?:\bTODO\b|\bTBD\b|\bFIXME\b|\bXXX\b|<TODO>)", re.I)
METADATA_LINE_RE = re.compile(
    r"^(?:状态|status|日期|date|更新时间|updated|版本|version|范围|scope|作者|author)"
    r"\s*[:：]",
    re.I,
)
REMOTE_TARGET_RE = re.compile(r"^(?:https?|mailto|tel|ftp):", re.I)
WINDOWS_ABSOLUTE_RE = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\)")


@dataclass(frozen=True)
class Heading:
    level: int
    text: str
    line: int
    slug: str


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    line: int | None
    message: str


@dataclass
class FileAnalysis:
    path: Path
    text: str
    lines: list[str]
    frontmatter_end: int
    code_mask: list[bool]
    headings: list[Heading]
    anchors: set[str]
    heading_targets: dict[str, set[str]]
    reference_definitions: dict[str, list[tuple[str, int]]]
    toc: Heading | None
    toc_links: list[tuple[str, int]]


def normalized_heading_text(text: str) -> str:
    value = re.sub(r"<[^>]+>", "", text)
    value = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"`([^`]*)`", r"\1", value)
    value = re.sub(r"\*\*(.+?)\*\*", r"\1", value)
    value = re.sub(r"(?<!\w)__(.+?)__(?!\w)", r"\1", value)
    value = re.sub(r"\*(.+?)\*", r"\1", value)
    value = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"\1", value)
    value = value.replace("*", "").replace("~", "")
    value = re.sub(r"\\([\\`*{}\[\]()#+\-.!_>])", r"\1", value)
    return re.sub(r"\s+", " ", value).strip()


def slugify_heading(text: str) -> str:
    value = normalized_heading_text(text).lower()
    output: list[str] = []
    for char in value:
        category = unicodedata.category(char)
        if char.isspace():
            output.append("-")
        elif char in "-_":
            output.append(char)
        elif category[0] in {"L", "N"}:
            output.append(char)
    return "".join(output).strip("-")


def unique_slug(base: str, counts: dict[str, int]) -> str:
    count = counts.get(base, 0)
    counts[base] = count + 1
    return base if count == 0 else f"{base}-{count}"


def detect_frontmatter(lines: list[str]) -> int:
    if not lines or lines[0].strip() != "---":
        return 0
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return index + 1
    return 0


def build_code_mask(
    lines: list[str], frontmatter_end: int, findings: list[Finding], path: Path
) -> list[bool]:
    mask = [False] * len(lines)
    active: tuple[str, int, int, str] | None = None

    for index in range(frontmatter_end, len(lines)):
        raw = lines[index]
        if active is None:
            match = FENCE_RE.match(raw)
            if not match:
                continue
            marker = match.group(1)
            language = match.group(2).strip()
            active = (marker[0], len(marker), index, language)
            mask[index] = True
            continue

        mask[index] = True
        marker_char, marker_length, _, language = active
        closing = re.match(
            rf"^ {{0,3}}{re.escape(marker_char)}{{{marker_length},}}[ \t]*$", raw
        )
        if closing:
            if not language:
                findings.append(
                    Finding(
                        "warning",
                        "MD104",
                        str(path),
                        active[2] + 1,
                        "fenced code block has no language identifier",
                    )
                )
            active = None

    if active is not None:
        findings.append(
            Finding(
                "error",
                "MD105",
                str(path),
                active[2] + 1,
                "unclosed fenced code block",
            )
        )

    return mask


def extract_headings(
    lines: list[str], frontmatter_end: int, code_mask: list[bool]
) -> list[Heading]:
    raw_headings: list[tuple[int, str, int]] = []
    skip_next = False

    for index in range(frontmatter_end, len(lines)):
        if skip_next:
            skip_next = False
            continue
        if code_mask[index]:
            continue

        raw = lines[index]
        match = ATX_HEADING_RE.match(raw)
        if match:
            raw_headings.append(
                (len(match.group(1)), normalized_heading_text(match.group(2)), index + 1)
            )
            continue

        if index + 1 >= len(lines) or code_mask[index + 1]:
            continue
        underline = SETEXT_UNDERLINE_RE.match(lines[index + 1])
        if raw.strip() and underline and not raw.lstrip().startswith(("#", "-", "*", ">")):
            level = 1 if underline.group(1).startswith("=") else 2
            raw_headings.append((level, normalized_heading_text(raw), index + 1))
            skip_next = True

    slug_counts: dict[str, int] = {}
    headings: list[Heading] = []
    for level, text, line in raw_headings:
        base = slugify_heading(text)
        if not base:
            base = f"section-{line}"
        headings.append(Heading(level, text, line, unique_slug(base, slug_counts)))
    return headings


def find_toc(headings: Iterable[Heading]) -> Heading | None:
    for heading in headings:
        if normalized_heading_text(heading.text).casefold() in TOC_NAMES:
            return heading
    return None


def collect_toc_links(
    lines: list[str],
    code_mask: list[bool],
    headings: list[Heading],
    toc: Heading | None,
) -> list[tuple[str, int]]:
    if toc is None:
        return []
    end_line = len(lines) + 1
    for heading in headings:
        if heading.line > toc.line and heading.level <= toc.level:
            end_line = heading.line
            break

    links: list[tuple[str, int]] = []
    for line_number in range(toc.line + 1, end_line):
        index = line_number - 1
        if index >= len(lines) or code_mask[index]:
            continue
        for match in TOC_LINK_RE.finditer(lines[index]):
            links.append((unquote(match.group(1)), line_number))
    return links


def explicit_anchors(lines: list[str], code_mask: list[bool]) -> list[tuple[str, int]]:
    anchors: list[tuple[str, int]] = []
    for index, raw in enumerate(lines):
        if code_mask[index]:
            continue
        anchors.extend(
            (match.group(1), index + 1)
            for match in EXPLICIT_ANCHOR_RE.finditer(raw)
        )
    return anchors


def reference_definitions(
    lines: list[str], code_mask: list[bool]
) -> dict[str, list[tuple[str, int]]]:
    references: dict[str, list[tuple[str, int]]] = {}
    for index, raw in enumerate(lines):
        if code_mask[index]:
            continue
        match = REFERENCE_DEFINITION_RE.match(raw)
        if not match:
            continue
        label = re.sub(r"\s+", " ", match.group(1)).strip().casefold()
        target = match.group(2).strip("<>")
        references.setdefault(label, []).append((target, index + 1))
    return references


def strip_inline_code(text: str) -> str:
    return re.sub(r"(`+)(.+?)\1", "", text)


def analyze_file(path: Path) -> tuple[FileAnalysis | None, list[Finding]]:
    findings: list[Finding] = []
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as error:
        return None, [
            Finding("error", "MD001", str(path), None, f"cannot decode as UTF-8: {error}")
        ]
    except OSError as error:
        return None, [
            Finding("error", "MD002", str(path), None, f"cannot read file: {error}")
        ]

    lines = text.splitlines()
    frontmatter_end = detect_frontmatter(lines)
    code_mask = build_code_mask(lines, frontmatter_end, findings, path)
    headings = extract_headings(lines, frontmatter_end, code_mask)
    toc = find_toc(headings)
    toc_links = collect_toc_links(lines, code_mask, headings, toc)
    explicit = explicit_anchors(lines, code_mask)
    anchors = {heading.slug for heading in headings}
    anchors.update(anchor for anchor, _ in explicit)
    heading_targets: dict[str, set[str]] = {
        heading.slug: {heading.slug} for heading in headings
    }
    for anchor, anchor_line in explicit:
        for heading in headings:
            if anchor_line in {heading.line - 1, heading.line - 2}:
                heading_targets[heading.slug].add(anchor)
                break

    return (
        FileAnalysis(
            path=path,
            text=text,
            lines=lines,
            frontmatter_end=frontmatter_end,
            code_mask=code_mask,
            headings=headings,
            anchors=anchors,
            heading_targets=heading_targets,
            reference_definitions=reference_definitions(lines, code_mask),
            toc=toc,
            toc_links=toc_links,
        ),
        findings,
    )


def audit_structure(
    analysis: FileAnalysis, require_toc: bool, max_heading_depth: int
) -> list[Finding]:
    findings: list[Finding] = []
    path = str(analysis.path)
    h1 = [heading for heading in analysis.headings if heading.level == 1]
    content_headings = [
        heading
        for heading in analysis.headings
        if heading.level >= 2
        and normalized_heading_text(heading.text).casefold() not in TOC_NAMES
    ]

    if not h1:
        findings.append(
            Finding("error", "MD010", path, None, "document has no top-level title")
        )
    elif len(h1) > 1:
        findings.append(
            Finding(
                "warning",
                "MD011",
                path,
                h1[1].line,
                "document has multiple top-level titles",
            )
        )

    if require_toc and content_headings and analysis.toc is None:
        findings.append(
            Finding(
                "error",
                "MD101",
                path,
                None,
                "maintained document with content headings requires a table of contents",
            )
        )

    if analysis.toc is not None and content_headings:
        first_content = min(content_headings, key=lambda heading: heading.line)
        if analysis.toc.line > first_content.line:
            findings.append(
                Finding(
                    "error",
                    "MD102",
                    path,
                    analysis.toc.line,
                    "table of contents must appear before content sections",
                )
            )
        if h1:
            between = analysis.lines[h1[0].line : analysis.toc.line - 1]
            nonblank = [line for line in between if line.strip()]
            blocks = 0
            in_block = False
            for line in between:
                if line.strip() and not in_block:
                    blocks += 1
                    in_block = True
                elif not line.strip():
                    in_block = False
            invalid_block = False
            in_blockquote = False
            for line in between:
                if not line.strip():
                    in_blockquote = False
                    continue
                stripped = line.strip()
                if stripped.startswith(">"):
                    in_blockquote = True
                elif in_blockquote:
                    continue
                elif not METADATA_LINE_RE.match(normalized_heading_text(stripped)):
                    invalid_block = True
                    break
            if len(nonblank) > 6 or blocks > 2 or invalid_block:
                findings.append(
                    Finding(
                        "error",
                        "MD107",
                        path,
                        analysis.toc.line,
                        "table of contents is not immediately after the title or status block",
                    )
                )

        linked = {anchor for anchor, _ in analysis.toc_links}
        for anchor, line in analysis.toc_links:
            if anchor not in analysis.anchors:
                findings.append(
                    Finding(
                        "error",
                        "MD103",
                        path,
                        line,
                        f"table-of-contents anchor does not exist: #{anchor}",
                    )
                )

        for heading in content_headings:
            heading_links = analysis.heading_targets.get(heading.slug, {heading.slug})
            if heading.level == 2 and not heading_links.intersection(linked):
                findings.append(
                    Finding(
                        "error",
                        "MD106",
                        path,
                        heading.line,
                        f"top-level section is missing from the table of contents: {heading.text}",
                    )
                )

    previous: Heading | None = None
    for heading in analysis.headings:
        if heading.level > max_heading_depth:
            findings.append(
                Finding(
                    "warning",
                    "MD110",
                    path,
                    heading.line,
                    f"heading depth {heading.level} exceeds {max_heading_depth}",
                )
            )
        if previous is not None and heading.level > previous.level + 1:
            findings.append(
                Finding(
                    "warning",
                    "MD111",
                    path,
                    heading.line,
                    f"heading level jumps from H{previous.level} to H{heading.level}",
                )
            )
        previous = heading

    return findings


def resolve_local_target(source: Path, target: str) -> Path:
    decoded = unquote(target)
    if WINDOWS_ABSOLUTE_RE.match(decoded):
        return Path(decoded)
    candidate = Path(decoded)
    if candidate.is_absolute():
        return candidate
    return source.parent / candidate


def audit_links(analysis: FileAnalysis) -> list[Finding]:
    findings: list[Finding] = []
    path = str(analysis.path)

    def check_target(target: str, line: int) -> None:
        target = target.strip("<>")
        if not target or REMOTE_TARGET_RE.match(target):
            return
        if "{" in target or "}" in target or target.startswith("<"):
            return

        path_part, separator, fragment = target.partition("#")
        if not path_part:
            if separator and unquote(fragment) not in analysis.anchors:
                findings.append(
                    Finding(
                        "error",
                        "MD120",
                        path,
                        line,
                        f"local anchor does not exist: #{unquote(fragment)}",
                    )
                )
            return

        resolved = resolve_local_target(analysis.path, path_part)
        if not resolved.exists():
            findings.append(
                Finding(
                    "error",
                    "MD121",
                    path,
                    line,
                    f"linked path does not exist: {path_part}",
                )
            )
            return

        if separator and resolved.suffix.lower() in MARKDOWN_SUFFIXES:
            target_analysis, _ = analyze_file(resolved)
            if (
                target_analysis is not None
                and unquote(fragment) not in target_analysis.anchors
            ):
                findings.append(
                    Finding(
                        "error",
                        "MD122",
                        path,
                        line,
                        f"anchor does not exist in {path_part}: #{unquote(fragment)}",
                    )
                )

    defined_references = set(analysis.reference_definitions)
    for index, raw in enumerate(analysis.lines):
        if analysis.code_mask[index]:
            continue
        searchable = strip_inline_code(raw)
        for match in INLINE_LINK_RE.finditer(searchable):
            check_target(match.group(1), index + 1)
        for match in REFERENCE_LINK_RE.finditer(searchable):
            label = match.group(2) or match.group(1)
            normalized = re.sub(r"\s+", " ", label).strip().casefold()
            if normalized not in defined_references:
                findings.append(
                    Finding(
                        "error",
                        "MD123",
                        path,
                        index + 1,
                        f"reference link has no definition: {label}",
                    )
                )

    for entries in analysis.reference_definitions.values():
        for target, line in entries:
            check_target(target, line)

    return findings


def audit_lines(analysis: FileAnalysis) -> list[Finding]:
    findings: list[Finding] = []
    path = str(analysis.path)
    blank_run = 0

    for index, raw in enumerate(analysis.lines):
        if index < analysis.frontmatter_end or analysis.code_mask[index]:
            blank_run = 0
            continue
        trailing = raw[len(raw.rstrip(" \t")) :]
        if trailing and not (len(trailing) >= 2 and trailing == " " * len(trailing)):
            findings.append(
                Finding(
                    "warning",
                    "MD130",
                    path,
                    index + 1,
                    "trailing whitespace",
                )
            )
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            findings.append(
                Finding(
                    "warning",
                    "MD131",
                    path,
                    index + 1,
                    "tab-indented Markdown content",
                )
            )
        if not raw.strip():
            blank_run += 1
            if blank_run == 3:
                findings.append(
                    Finding(
                        "warning",
                        "MD132",
                        path,
                        index + 1,
                        "three or more consecutive blank lines",
                    )
                )
        else:
            blank_run = 0
        if PLACEHOLDER_RE.search(strip_inline_code(raw)):
            findings.append(
                Finding(
                    "warning",
                    "MD133",
                    path,
                    index + 1,
                    "unfinished placeholder marker",
                )
            )

    if analysis.text and not analysis.text.endswith(("\n", "\r")):
        findings.append(
            Finding(
                "warning",
                "MD134",
                path,
                len(analysis.lines),
                "file does not end with a newline",
            )
        )
    return findings


def audit_file(
    path: Path, require_toc: bool, max_heading_depth: int
) -> list[Finding]:
    analysis, findings = analyze_file(path)
    if analysis is None:
        return findings
    findings.extend(audit_structure(analysis, require_toc, max_heading_depth))
    findings.extend(audit_links(analysis))
    findings.extend(audit_lines(analysis))
    return findings


def iter_markdown_files(root: Path, ignores: list[str]) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in MARKDOWN_SUFFIXES:
            continue
        if any(part in SKIP_DIRECTORIES for part in path.parts):
            continue
        normalized = path.as_posix()
        if any(fnmatch.fnmatch(normalized, pattern) for pattern in ignores):
            continue
        yield path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Markdown structure, tables of contents, links, and formatting."
    )
    parser.add_argument("paths", nargs="+", help="Markdown file or directory to audit")
    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as failures"
    )
    parser.add_argument(
        "--json", action="store_true", help="Emit machine-readable JSON findings"
    )
    parser.add_argument(
        "--no-require-toc",
        action="store_true",
        help="Skip TOC checks for generated or disposable files",
    )
    parser.add_argument(
        "--max-heading-depth",
        type=int,
        default=4,
        help="Warn when heading depth exceeds this value (default: 4)",
    )
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        help="Glob pattern to skip; may be repeated",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    findings: list[Finding] = []
    files: list[Path] = []

    for raw_path in args.paths:
        path = Path(raw_path).expanduser().resolve()
        if not path.exists():
            findings.append(
                Finding("error", "MD000", str(path), None, "input path does not exist")
            )
            continue
        files.extend(iter_markdown_files(path, args.ignore))

    if not files and not findings:
        findings.append(
            Finding(
                "error",
                "MD003",
                ", ".join(str(Path(path).resolve()) for path in args.paths),
                None,
                "no Markdown files found",
            )
        )

    for path in files:
        findings.extend(
            audit_file(
                path,
                require_toc=not args.no_require_toc,
                max_heading_depth=args.max_heading_depth,
            )
        )

    findings.sort(key=lambda item: (item.path, item.line or 0, item.code))
    errors = sum(item.severity == "error" for item in findings)
    warnings = sum(item.severity == "warning" for item in findings)

    if args.json:
        print(
            json.dumps(
                {
                    "files_checked": len(files),
                    "errors": errors,
                    "warnings": warnings,
                    "findings": [asdict(item) for item in findings],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for finding in findings:
            location = finding.path
            if finding.line is not None:
                location += f":{finding.line}"
            print(
                f"{finding.severity.upper():7} {finding.code} {location} "
                f"{finding.message}"
            )
        print(
            f"Checked {len(files)} Markdown file(s): "
            f"{errors} error(s), {warnings} warning(s)"
        )

    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
