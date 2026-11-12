#!/usr/bin/env python3
"""Check evaluated Visual Studio compile items for shared-source coverage."""

from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


PROPERTY_PATTERN = re.compile(r"\$\(([^)]+)\)")


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def normalized_path(path: Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def repository_path(repo: Path, value: str) -> Path:
    path = Path(value.replace("\\", "/"))
    if not path.is_absolute():
        path = repo / path
    return Path(os.path.abspath(str(path)))


def expand_properties(value: str, properties: Dict[str, str]) -> Tuple[str, Set[str]]:
    missing: Set[str] = set()

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name in properties:
            return properties[name]
        missing.add(name)
        return match.group(0)

    return PROPERTY_PATTERN.sub(replace, value), missing


def evaluate_condition(
    condition: Optional[str], properties: Dict[str, str]
) -> Optional[bool]:
    if not condition or not condition.strip():
        return True

    expanded, missing = expand_properties(condition.strip(), properties)
    if missing:
        return None

    lowered = expanded.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"

    for operator in (" and ", " or "):
        parts = re.split(operator, expanded, flags=re.IGNORECASE)
        if len(parts) > 1:
            values = [evaluate_condition(part, properties) for part in parts]
            if any(value is None for value in values):
                return None
            return all(values) if operator == " and " else any(values)

    exists_match = re.fullmatch(r"(!?)\s*Exists\(\s*'([^']+)'\s*\)", expanded, re.I)
    if exists_match:
        exists = Path(exists_match.group(2).replace("\\", "/")).exists()
        return not exists if exists_match.group(1) else exists

    compare_match = re.fullmatch(
        r"\s*(['\"]?)(.*?)\1\s*(==|!=)\s*(['\"]?)(.*?)\4\s*",
        expanded,
        re.IGNORECASE,
    )
    if compare_match:
        left = compare_match.group(2).strip()
        operator = compare_match.group(3)
        right = compare_match.group(5).strip()
        return left == right if operator == "==" else left != right

    return None


def walk_compile_items(
    element: ET.Element,
    properties: Dict[str, str],
    inherited_condition: Optional[str] = None,
) -> Iterable[Tuple[ET.Element, Optional[str]]]:
    own_condition = element.attrib.get("Condition")
    if inherited_condition and own_condition:
        condition = f"({inherited_condition}) And ({own_condition})"
    else:
        condition = own_condition or inherited_condition
    if local_name(element.tag) == "ClCompile":
        yield element, condition
        return
    for child in element:
        yield from walk_compile_items(child, properties, condition)


def is_excluded_from_build(
    item: ET.Element, properties: Dict[str, str]
) -> Tuple[bool, Set[str]]:
    for child in item:
        if local_name(child.tag) != "ExcludedFromBuild":
            continue
        condition = child.attrib.get("Condition")
        condition_value = evaluate_condition(condition, properties)
        if condition_value is False:
            return False, set()
        if condition_value is None:
            _, missing = expand_properties(condition or "", properties)
            return False, missing or {"unknown-condition"}
        expanded, missing = expand_properties((child.text or "").strip(), properties)
        if missing:
            return False, missing
        return expanded.lower() == "true", set()
    return False, set()


def project_compile_items(
    project_file: Path,
    properties: Dict[str, str],
) -> Tuple[Set[str], List[str], List[ET.Element], Dict[int, str]]:
    root = ET.parse(str(project_file)).getroot()
    compiled: Set[str] = set()
    indeterminate: List[str] = []
    raw_items: List[ET.Element] = []
    raw_conditions: Dict[int, str] = {}

    for item, condition in walk_compile_items(root, properties):
        condition_value = evaluate_condition(condition, properties)
        if condition_value is False:
            continue
        raw_items.append(item)
        raw_conditions[id(item)] = condition or ""
        if condition_value is None:
            indeterminate.append(f"condition is not evaluable: {condition}")
            continue
        excluded, missing = is_excluded_from_build(item, properties)
        if missing:
            indeterminate.append(
                f"ExcludedFromBuild is not evaluable: {sorted(missing)}"
            )
            continue
        if excluded:
            continue
        include = item.attrib.get("Include", "")
        expanded, missing = expand_properties(include, properties)
        if missing:
            indeterminate.append(f"include has unresolved properties: {sorted(missing)}")
            continue
        if "*" in expanded or "?" in expanded:
            indeterminate.append(f"compile item uses wildcard: {expanded}")
            continue
        path = Path(expanded.replace("\\", "/"))
        if not path.is_absolute():
            path = project_file.parent / path
        compiled.add(normalized_path(path))

    return compiled, indeterminate, raw_items, raw_conditions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--anchor-source", required=True)
    parser.add_argument("--required-source", required=True)
    parser.add_argument("--configuration", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--solution-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        repo = args.repo.resolve(strict=True)
        project_root = args.project_root
        if not project_root.is_absolute():
            project_root = repo / project_root
        project_root = project_root.resolve(strict=True)
        solution_dir = (
            args.solution_dir.resolve(strict=True) if args.solution_dir else None
        )
    except OSError as exc:
        print(f"ERROR: invalid repository or project root: {exc}", file=sys.stderr)
        return 2

    anchor = normalized_path(repository_path(repo, args.anchor_source))
    required = normalized_path(repository_path(repo, args.required_source))
    consumers: List[Path] = []
    failures: List[Path] = []
    indeterminate_projects: List[Path] = []

    for project_file in sorted(project_root.rglob("*.vcxproj")):
        properties = {
            "Configuration": args.configuration,
            "Platform": args.platform,
            "ProjectDir": str(project_file.parent) + os.sep,
            "MSBuildProjectDirectory": str(project_file.parent),
            "ProjectName": project_file.stem,
        }
        if solution_dir is not None:
            properties["SolutionDir"] = str(solution_dir) + os.sep
        try:
            compiled, indeterminate, _, _ = project_compile_items(
                project_file, properties
            )
        except ET.ParseError as exc:
            print(f"ERROR: invalid project XML: {project_file}: {exc}", file=sys.stderr)
            return 2
        if indeterminate:
            indeterminate_projects.append(project_file)
            for reason in indeterminate:
                print(f"INDETERMINATE: {project_file}: {reason}")
        if anchor not in compiled:
            continue
        consumers.append(project_file)
        if required not in compiled:
            failures.append(project_file)

    if not consumers:
        print(
            "ERROR: no evaluated .vcxproj consumes the anchor source: "
            f"{args.anchor_source}",
            file=sys.stderr,
        )
        return 2

    for project_file in consumers:
        status = "MISSING" if project_file in failures else "OK"
        print(f"{status}: {project_file}")

    if failures:
        print(
            f"ERROR: {len(failures)} anchor project(s) do not compile "
            f"{args.required_source} as an active ClCompile item",
            file=sys.stderr,
        )
        return 1
    if indeterminate_projects:
        print(
            "ERROR: one or more projects contain conditions or properties that "
            "cannot be evaluated; inspect them before declaring coverage",
            file=sys.stderr,
        )
        return 2

    print(
        f"OK: all {len(consumers)} anchor project(s) compile the required source "
        f"for {args.configuration}|{args.platform}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
