#!/usr/bin/env python
"""Merge MathType OLE equations from a Word-saved donor into an original DOCX.

The donor supplies only the Equation.DSMT4 runs, OLE binary parts, and WMF
previews. All unrelated package parts and all original media are copied from
the original DOCX unchanged.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile, ZipInfo

from lxml import etree

from mathtype_wmf_audit import wmf_has_math_type_error_red


NS = {
    "ct": "http://schemas.openxmlformats.org/package/2006/content-types",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "o": "urn:schemas-microsoft-com:office:office",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "v": "urn:schemas-microsoft-com:vml",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
}

DOCUMENT_PART = "word/document.xml"
DOCUMENT_RELS_PART = "word/_rels/document.xml.rels"
CONTENT_TYPES_PART = "[Content_Types].xml"
MATH_TYPE_PROG_ID = "Equation.DSMT4"
IMAGE_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
)
OLE_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/oleObject"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Transplant inline MathType OLE equations into the untouched "
            "original DOCX package."
        )
    )
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--donor", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_xml(data: bytes, part_name: str) -> etree._Element:
    parser = etree.XMLParser(resolve_entities=False, remove_blank_text=False)
    try:
        return etree.fromstring(data, parser)
    except etree.XMLSyntaxError as exc:
        raise ValueError(f"Cannot parse {part_name}: {exc}") from exc


def serialize_xml(root: etree._Element) -> bytes:
    return etree.tostring(
        root,
        encoding="UTF-8",
        xml_declaration=True,
        standalone=True,
    )


def relationship_map(root: etree._Element) -> dict[str, etree._Element]:
    return {
        element.get("Id"): element
        for element in root.xpath("./pr:Relationship", namespaces=NS)
    }


def resolve_word_target(target: str) -> str:
    normalized = PurePosixPath("word") / PurePosixPath(target)
    parts: list[str] = []
    for part in normalized.parts:
        if part == "..":
            if not parts:
                raise ValueError(f"Relationship escapes package root: {target}")
            parts.pop()
        elif part != ".":
            parts.append(part)
    return "/".join(parts)


def find_math_type_run(ole: etree._Element) -> etree._Element:
    current = ole
    run_tag = f"{{{NS['w']}}}r"
    while current is not None and current.tag != run_tag:
        current = current.getparent()
    if current is None:
        raise ValueError("MathType OLE object does not have a w:r ancestor.")
    return current


def source_formula_targets(document: etree._Element) -> list[etree._Element]:
    formulas = document.xpath("//m:oMath", namespaces=NS)
    math_para_tag = f"{{{NS['m']}}}oMathPara"
    targets: list[etree._Element] = []
    seen: set[int] = set()
    for formula in formulas:
        parent = formula.getparent()
        target = parent if parent.tag == math_para_tag else formula
        identity = id(target)
        if identity in seen:
            raise ValueError("A source replacement target contains multiple formulas.")
        seen.add(identity)
        targets.append(target)
    return targets


def donor_math_type_runs(document: etree._Element) -> list[etree._Element]:
    objects = document.xpath(
        "//o:OLEObject[@ProgID=$prog_id]",
        namespaces=NS,
        prog_id=MATH_TYPE_PROG_ID,
    )
    runs = [find_math_type_run(ole) for ole in objects]
    if len({id(run) for run in runs}) != len(runs):
        raise ValueError("Multiple donor MathType objects share one Word run.")
    return runs


def allocate_numeric_relationship_id(
    used: set[str],
    next_number: int,
) -> tuple[str, int]:
    while True:
        relationship_id = f"rId{next_number}"
        next_number += 1
        if relationship_id not in used:
            used.add(relationship_id)
            return relationship_id, next_number


def prepare_run_identity(
    run: etree._Element,
    ordinal: int,
    used_anchor_ids: set[str],
    used_shape_ids: set[str],
    used_object_ids: set[str],
) -> None:
    anchor_attribute = f"{{{NS['w14']}}}anchorId"
    for object_element in run.xpath(".//w:object", namespaces=NS):
        anchor_id = object_element.get(anchor_attribute)
        if not anchor_id:
            raise ValueError(f"Equation {ordinal} has no Word anchor ID.")
        if anchor_id in used_anchor_ids:
            raise ValueError(
                f"Equation {ordinal} anchor ID collides with the original: "
                f"{anchor_id}"
            )
        used_anchor_ids.add(anchor_id)

    shapes = run.xpath(".//v:shape", namespaces=NS)
    ole_objects = run.xpath(
        ".//o:OLEObject[@ProgID=$prog_id]",
        namespaces=NS,
        prog_id=MATH_TYPE_PROG_ID,
    )
    if len(shapes) != 1 or len(ole_objects) != 1:
        raise ValueError(
            f"Equation {ordinal} does not contain exactly one VML shape and OLE object."
        )

    shape_id = shapes[0].get("id")
    object_shape_id = ole_objects[0].get("ShapeID")
    object_id = ole_objects[0].get("ObjectID")
    if not shape_id or shape_id != object_shape_id:
        raise ValueError(f"Equation {ordinal} has inconsistent VML shape IDs.")
    if not object_id:
        raise ValueError(f"Equation {ordinal} has no OLE object ID.")
    if shape_id in used_shape_ids:
        raise ValueError(
            f"Equation {ordinal} VML shape ID collides with the original: "
            f"{shape_id}"
        )
    if object_id in used_object_ids:
        raise ValueError(
            f"Equation {ordinal} OLE object ID collides with the original: "
            f"{object_id}"
        )
    used_shape_ids.add(shape_id)
    used_object_ids.add(object_id)


def donor_part_for_relationship(
    donor_relationships: dict[str, etree._Element],
    relationship_id: str,
    expected_type: str,
) -> str:
    relationship = donor_relationships.get(relationship_id)
    if relationship is None:
        raise ValueError(f"Donor relationship {relationship_id} was not found.")
    if relationship.get("Type") != expected_type:
        raise ValueError(
            f"Relationship {relationship_id} has unexpected type "
            f"{relationship.get('Type')}."
        )
    return resolve_word_target(relationship.get("Target"))


def append_relationship(
    relationships_root: etree._Element,
    relationship_id: str,
    relationship_type: str,
    target: str,
) -> None:
    relationship = etree.Element(f"{{{NS['pr']}}}Relationship")
    relationship.set("Id", relationship_id)
    relationship.set("Type", relationship_type)
    relationship.set("Target", target)
    relationships_root.append(relationship)


def ensure_default_content_type(
    content_types: etree._Element,
    extension: str,
    expected_content_type: str,
) -> None:
    existing = content_types.xpath(
        "./ct:Default[translate(@Extension,"
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')=$extension]",
        namespaces=NS,
        extension=extension.lower(),
    )
    if existing:
        if existing[0].get("ContentType") != expected_content_type:
            raise ValueError(
                f"The existing {extension} content type is "
                f"{existing[0].get('ContentType')}, not "
                f"{expected_content_type}."
            )
        return

    default = etree.Element(f"{{{NS['ct']}}}Default")
    default.set("Extension", extension)
    default.set("ContentType", expected_content_type)
    override_tag = f"{{{NS['ct']}}}Override"
    insert_at = len(content_types)
    for index, child in enumerate(content_types):
        if child.tag == override_tag:
            insert_at = index
            break
    content_types.insert(insert_at, default)


def clone_zip_info(source: ZipInfo, filename: str) -> ZipInfo:
    target = ZipInfo(filename=filename, date_time=source.date_time)
    target.compress_type = source.compress_type
    target.comment = source.comment
    target.extra = source.extra
    target.create_system = source.create_system
    target.create_version = source.create_version
    target.extract_version = source.extract_version
    target.external_attr = source.external_attr
    target.internal_attr = source.internal_attr
    target.flag_bits = source.flag_bits
    return target


def validate_package(path: Path, expected_equations: int) -> dict[str, int | bool]:
    xml_parts = 0
    parse_failures = 0
    total_entries = 0
    omml_count = 0
    math_type_count = 0
    generated_math_type_bins = 0
    times_new_roman_bins = 0
    euclid_extra_bins = 0
    mt_extra_bins = 0
    recognized_font_profile_bins = 0
    generated_preview_wmfs = 0
    red_error_preview_wmfs = 0
    with ZipFile(path, "r") as package:
        bad_entry = package.testzip()
        for info in package.infolist():
            total_entries += 1
            if (
                info.filename.startswith(
                    "word/embeddings/codexMathType"
                )
                and info.filename.endswith(".bin")
            ):
                generated_math_type_bins += 1
                binary = package.read(info.filename)
                times_new_roman_bins += int(
                    b"Times New Roman" in binary
                )
                euclid_extra_bins += int(b"Euclid Extra" in binary)
                mt_extra_bins += int(b"MT Extra" in binary)
                recognized_font_profile_bins += int(
                    b"Times New Roman" in binary
                    or b"Euclid Extra" in binary
                )
            if (
                info.filename.startswith("word/media/codexMathType")
                and info.filename.endswith(".wmf")
            ):
                generated_preview_wmfs += 1
                red_error_preview_wmfs += int(
                    wmf_has_math_type_error_red(package.read(info.filename))
                )
            if not (
                info.filename.lower().endswith(".xml")
                or info.filename.lower().endswith(".rels")
            ):
                continue
            xml_parts += 1
            try:
                root = parse_xml(package.read(info.filename), info.filename)
            except ValueError:
                parse_failures += 1
                continue
            omml_count += len(root.xpath("//m:oMath", namespaces=NS))
            math_type_count += len(
                root.xpath(
                    "//o:OLEObject[@ProgID=$prog_id]",
                    namespaces=NS,
                    prog_id=MATH_TYPE_PROG_ID,
                )
            )

    if bad_entry is not None:
        raise BadZipFile(f"CRC failure in {bad_entry}.")
    if parse_failures:
        raise ValueError(f"{parse_failures} XML parts failed to parse.")
    if omml_count:
        raise ValueError(f"{omml_count} OMML equations remain in the merged package.")
    if math_type_count != expected_equations:
        raise ValueError(
            f"Expected {expected_equations} MathType objects, found {math_type_count}."
        )
    if generated_math_type_bins != expected_equations:
        raise ValueError(
            "Generated MathType binary count mismatch: "
            f"expected {expected_equations}, found {generated_math_type_bins}."
        )
    if recognized_font_profile_bins != expected_equations:
        raise ValueError(
            "Not every generated MathType object contains the configured "
            "Times New Roman or Euclid Extra font profile: "
            f"{recognized_font_profile_bins}/{expected_equations}."
        )
    if mt_extra_bins != 0:
        raise ValueError(
            f"{mt_extra_bins} generated MathType objects still reference MT Extra."
        )
    if generated_preview_wmfs != expected_equations:
        raise ValueError(
            "Generated MathType preview count mismatch: "
            f"expected {expected_equations}, found {generated_preview_wmfs}."
        )
    if red_error_preview_wmfs != 0:
        raise ValueError(
            f"{red_error_preview_wmfs} generated MathType previews contain "
            "red translator-error text."
        )

    return {
        "zip_crc_ok": True,
        "entries": total_entries,
        "xml_parts": xml_parts,
        "xml_parse_failures": parse_failures,
        "omml_count": omml_count,
        "math_type_count": math_type_count,
        "generated_math_type_bins": generated_math_type_bins,
        "times_new_roman_bins": times_new_roman_bins,
        "euclid_extra_bins": euclid_extra_bins,
        "mt_extra_bins": mt_extra_bins,
        "recognized_font_profile_bins": recognized_font_profile_bins,
        "generated_preview_wmfs": generated_preview_wmfs,
        "red_error_preview_wmfs": red_error_preview_wmfs,
    }


def remove_formula_targets(
    root: etree._Element,
    targets: list[etree._Element],
) -> None:
    for target in targets:
        parent = target.getparent()
        if parent is None:
            raise ValueError("A formula target has no parent during comparison.")
        tail = target.tail
        previous = target.getprevious()
        if tail:
            if previous is not None:
                previous.tail = (previous.tail or "") + tail
            else:
                parent.text = (parent.text or "") + tail
        parent.remove(target)


def canonical_nonformula_document(
    document_xml: bytes,
    math_type: bool,
) -> bytes:
    root = parse_xml(document_xml, DOCUMENT_PART)
    targets = (
        donor_math_type_runs(root)
        if math_type
        else source_formula_targets(root)
    )
    remove_formula_targets(root, targets)
    return etree.tostring(
        root,
        method="c14n",
        exclusive=False,
        with_comments=False,
    )


def validate_original_preservation(
    original_path: Path,
    output_path: Path,
    expected_equations: int,
) -> dict[str, object]:
    allowed_modified = {
        CONTENT_TYPES_PART,
        DOCUMENT_PART,
        DOCUMENT_RELS_PART,
    }
    with ZipFile(original_path, "r") as original, ZipFile(
        output_path,
        "r",
    ) as output:
        original_names = set(original.namelist())
        output_names = set(output.namelist())
        added = sorted(output_names - original_names)
        removed = sorted(original_names - output_names)
        changed_original = sorted(
            name
            for name in original_names & output_names
            if original.read(name) != output.read(name)
        )
        unexpected_added = [
            name
            for name in added
            if not (
                re.fullmatch(
                    r"word/embeddings/codexMathType\d{4}\.bin",
                    name,
                )
                or re.fullmatch(
                    r"word/media/codexMathType\d{4}\.wmf",
                    name,
                )
            )
        ]
        original_media_changed = [
            name
            for name in changed_original
            if name.startswith("word/media/")
        ]
        original_nonformula = canonical_nonformula_document(
            original.read(DOCUMENT_PART),
            math_type=False,
        )
        output_nonformula = canonical_nonformula_document(
            output.read(DOCUMENT_PART),
            math_type=True,
        )

    if removed:
        raise ValueError(f"Original package parts were removed: {removed}")
    if set(changed_original) != allowed_modified:
        raise ValueError(
            "Unexpected original package changes: "
            f"{changed_original}; expected {sorted(allowed_modified)}"
        )
    if len(added) != expected_equations * 2 or unexpected_added:
        raise ValueError(
            "Unexpected added package parts: "
            f"count={len(added)}, unexpected={unexpected_added}"
        )
    if original_media_changed:
        raise ValueError(
            f"Original media changed: {original_media_changed}"
        )
    if original_nonformula != output_nonformula:
        raise ValueError(
            "Non-formula document XML differs after formula removal."
        )

    return {
        "original_entries": len(original_names),
        "output_entries": len(output_names),
        "added_parts": len(added),
        "removed_parts": len(removed),
        "changed_original_parts": changed_original,
        "unexpected_added_parts": len(unexpected_added),
        "original_media_changed": len(original_media_changed),
        "nonformula_xml_equal": True,
        "nonformula_xml_sha256": hashlib.sha256(
            original_nonformula
        ).hexdigest(),
    }


def merge(
    original_path: Path,
    donor_path: Path,
    output_path: Path,
) -> dict[str, object]:
    if not original_path.is_file():
        raise FileNotFoundError(original_path)
    if not donor_path.is_file():
        raise FileNotFoundError(donor_path)
    if output_path.exists():
        raise FileExistsError(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(original_path, "r") as original, ZipFile(donor_path, "r") as donor:
        original_names = set(original.namelist())
        donor_names = set(donor.namelist())
        required = {DOCUMENT_PART, DOCUMENT_RELS_PART, CONTENT_TYPES_PART}
        if not required.issubset(original_names):
            raise ValueError("Original DOCX is missing required package parts.")
        if not required.issubset(donor_names):
            raise ValueError("Donor DOCX is missing required package parts.")

        original_document = parse_xml(
            original.read(DOCUMENT_PART),
            DOCUMENT_PART,
        )
        donor_document = parse_xml(donor.read(DOCUMENT_PART), DOCUMENT_PART)
        original_relationships = parse_xml(
            original.read(DOCUMENT_RELS_PART),
            DOCUMENT_RELS_PART,
        )
        donor_relationships_root = parse_xml(
            donor.read(DOCUMENT_RELS_PART),
            DOCUMENT_RELS_PART,
        )
        content_types = parse_xml(
            original.read(CONTENT_TYPES_PART),
            CONTENT_TYPES_PART,
        )

        source_targets = source_formula_targets(original_document)
        donor_runs = donor_math_type_runs(donor_document)
        if len(source_targets) != len(donor_runs):
            raise ValueError(
                f"Formula count mismatch: original={len(source_targets)}, "
                f"donor={len(donor_runs)}."
            )

        donor_relationships = relationship_map(donor_relationships_root)
        existing_relationship_ids = set(relationship_map(original_relationships))
        numeric_relationship_numbers = [
            int(match.group(1))
            for relationship_id in existing_relationship_ids
            if (match := re.fullmatch(r"rId(\d+)", relationship_id))
        ]
        next_relationship_number = (
            max(numeric_relationship_numbers, default=0) + 1
        )
        used_anchor_ids = set(
            original_document.xpath("//w:object/@w14:anchorId", namespaces=NS)
        )
        used_shape_ids = set(
            original_document.xpath("//v:shape/@id", namespaces=NS)
        )
        used_object_ids = set(
            original_document.xpath("//o:OLEObject/@ObjectID", namespaces=NS)
        )
        new_parts: dict[str, tuple[bytes, ZipInfo]] = {}

        for ordinal, (source_target, donor_run) in enumerate(
            zip(source_targets, donor_runs),
            start=1,
        ):
            run = copy.deepcopy(donor_run)
            prepare_run_identity(
                run,
                ordinal,
                used_anchor_ids,
                used_shape_ids,
                used_object_ids,
            )

            ole_objects = run.xpath(
                ".//o:OLEObject[@ProgID=$prog_id]",
                namespaces=NS,
                prog_id=MATH_TYPE_PROG_ID,
            )
            previews = run.xpath(".//v:imagedata", namespaces=NS)
            if len(ole_objects) != 1 or len(previews) != 1:
                raise ValueError(
                    f"Equation {ordinal} has an unexpected OLE/preview structure."
                )

            donor_ole_rid = ole_objects[0].get(f"{{{NS['r']}}}id")
            donor_image_rid = previews[0].get(f"{{{NS['r']}}}id")
            donor_ole_part = donor_part_for_relationship(
                donor_relationships,
                donor_ole_rid,
                OLE_REL_TYPE,
            )
            donor_image_part = donor_part_for_relationship(
                donor_relationships,
                donor_image_rid,
                IMAGE_REL_TYPE,
            )

            new_image_rid, next_relationship_number = (
                allocate_numeric_relationship_id(
                    existing_relationship_ids,
                    next_relationship_number,
                )
            )
            new_ole_rid, next_relationship_number = (
                allocate_numeric_relationship_id(
                    existing_relationship_ids,
                    next_relationship_number,
                )
            )

            new_ole_name = f"codexMathType{ordinal:04d}.bin"
            new_image_name = f"codexMathType{ordinal:04d}.wmf"
            new_ole_part = f"word/embeddings/{new_ole_name}"
            new_image_part = f"word/media/{new_image_name}"
            if new_ole_part in original_names or new_image_part in original_names:
                raise ValueError("Generated package part collides with the original.")

            ole_objects[0].set(f"{{{NS['r']}}}id", new_ole_rid)
            previews[0].set(f"{{{NS['r']}}}id", new_image_rid)
            append_relationship(
                original_relationships,
                new_ole_rid,
                OLE_REL_TYPE,
                f"embeddings/{new_ole_name}",
            )
            append_relationship(
                original_relationships,
                new_image_rid,
                IMAGE_REL_TYPE,
                f"media/{new_image_name}",
            )

            if donor_ole_part not in donor_names:
                raise ValueError(f"Donor OLE part is missing: {donor_ole_part}")
            if donor_image_part not in donor_names:
                raise ValueError(f"Donor preview part is missing: {donor_image_part}")
            new_parts[new_ole_part] = (
                donor.read(donor_ole_part),
                donor.getinfo(donor_ole_part),
            )
            new_parts[new_image_part] = (
                donor.read(donor_image_part),
                donor.getinfo(donor_image_part),
            )

            parent = source_target.getparent()
            if parent is None:
                raise ValueError(f"Equation {ordinal} has no replaceable parent.")
            parent.replace(source_target, run)

        ensure_default_content_type(
            content_types,
            "bin",
            "application/vnd.openxmlformats-officedocument.oleObject",
        )
        ensure_default_content_type(
            content_types,
            "wmf",
            "image/x-wmf",
        )

        modified_parts = {
            DOCUMENT_PART: serialize_xml(original_document),
            DOCUMENT_RELS_PART: serialize_xml(original_relationships),
            CONTENT_TYPES_PART: serialize_xml(content_types),
        }

        original_parts_preserved = sum(
            name not in modified_parts for name in original_names
        )

        with tempfile.TemporaryDirectory(
            dir=output_path.parent,
            prefix=".mathtype-merge-",
        ) as temporary_directory:
            temporary_output = Path(temporary_directory) / output_path.name
            with ZipFile(temporary_output, "x") as output:
                for info in original.infolist():
                    data = modified_parts.get(
                        info.filename,
                        original.read(info.filename),
                    )
                    output.writestr(clone_zip_info(info, info.filename), data)
                for name in sorted(new_parts):
                    data, donor_info = new_parts[name]
                    output.writestr(clone_zip_info(donor_info, name), data)

            validation = validate_package(
                temporary_output,
                len(source_targets),
            )
            preservation = validate_original_preservation(
                original_path,
                temporary_output,
                len(source_targets),
            )
            if output_path.exists():
                raise FileExistsError(output_path)
            os.link(temporary_output, output_path)

    return {
        "original": str(original_path),
        "donor": str(donor_path),
        "output": str(output_path),
        "original_sha256": sha256_file(original_path),
        "donor_sha256": sha256_file(donor_path),
        "output_sha256": sha256_file(output_path),
        "formulas_replaced": len(source_targets),
        "ole_parts_added": len(source_targets),
        "preview_parts_added": len(source_targets),
        "original_parts_preserved": original_parts_preserved,
        "modified_original_parts": [
            CONTENT_TYPES_PART,
            DOCUMENT_PART,
            DOCUMENT_RELS_PART,
        ],
        "validation": validation,
        "preservation": preservation,
    }


def main() -> int:
    args = parse_args()
    resolved = {
        "original": args.original.resolve(),
        "donor": args.donor.resolve(),
        "output": args.output.resolve(),
        "report": args.report.resolve(),
    }
    reverse: dict[Path, str] = {}
    for label, path in resolved.items():
        if path in reverse:
            raise ValueError(
                f"{label} and {reverse[path]} resolve to the same path: {path}"
            )
        reverse[path] = label
    args.original = resolved["original"]
    args.donor = resolved["donor"]
    args.output = resolved["output"]
    args.report = resolved["report"]
    if args.report.exists():
        raise FileExistsError(args.report)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    result = merge(args.original, args.donor, args.output)
    report_text = json.dumps(result, ensure_ascii=False, indent=2)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        dir=args.report.parent,
        prefix=".mathtype-report-",
        suffix=".json",
        delete=False,
    ) as temporary_report:
        temporary_report.write(report_text)
        temporary_report_path = Path(temporary_report.name)
    try:
        if args.report.exists():
            raise FileExistsError(args.report)
        os.link(temporary_report_path, args.report)
    finally:
        temporary_report_path.unlink(missing_ok=True)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        raise
