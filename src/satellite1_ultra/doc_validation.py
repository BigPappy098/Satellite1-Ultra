"""Fail-closed validation for builder documentation and release references."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from satellite1_ultra.configuration import ROOT
from satellite1_ultra.exporting import PARTS, source_commit
from satellite1_ultra.official import OFFICIAL_PRINT_PARTS, OFFICIAL_PRINT_PARTS_REQUIRED

EVIDENCE_LABELS = {
    "VERIFIED_DIGITALLY",
    "DERIVED_FROM_OFFICIAL_CAD",
    "DERIVED_FROM_MANUFACTURER_DRAWING",
    "ENGINEERING_ESTIMATE",
    "REQUIRES_PHYSICAL_VALIDATION",
}
USER_GUIDES = (
    "START_HERE.md",
    "CALIBRATION_GUIDE.md",
    "PRINTING_GUIDE.md",
    "HARDWARE_AND_MATERIALS_GUIDE.md",
    "ASSEMBLY_GUIDE.md",
    "TESTING_AND_COMMISSIONING_GUIDE.md",
    "MAINTENANCE_GUIDE.md",
    "ENGINEERING_APPENDIX.md",
)
PDF_GUIDES = (
    "START_HERE.pdf",
    "START_HERE_CALIBRATION_GUIDE.pdf",
    "PRINTING_GUIDE.pdf",
    "ASSEMBLY_GUIDE.pdf",
    "TESTING_AND_COMMISSIONING_GUIDE.pdf",
    "MAINTENANCE_GUIDE.pdf",
)


def _csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def validate_documentation(root: Path = ROOT) -> dict[str, Any]:
    """Validate generated documentation against current exports and schedules."""
    docs = root / "docs"
    errors: list[str] = []
    checked_files: list[str] = []
    combined = ""
    image_captions: list[str] = []
    for guide_name in USER_GUIDES:
        guide = docs / guide_name
        if not guide.is_file():
            errors.append(f"missing guide: docs/{guide_name}")
            continue
        text = guide.read_text(encoding="utf-8")
        checked_files.append(str(guide.relative_to(root)))
        combined += "\n" + text
        if re.search(r"\b(?:TODO|TBD|FIXME|PLACEHOLDER)\b", text, flags=re.IGNORECASE):
            errors.append(f"placeholder marker in docs/{guide_name}")
        if re.search(r"\b(?:Claude|Gemini|Codex agent)\b", text, flags=re.IGNORECASE):
            errors.append(f"previous-agent reference in user guide docs/{guide_name}")
        for caption, ref in re.findall(r"!\[(.*?)\]\((.*?)\)", text):
            image_captions.append(caption)
            target = (
                root / "reports" / "renders" / Path(ref).name
                if ref.startswith("IMAGES/")
                else guide.parent / ref
            )
            if not target.is_file():
                errors.append(f"missing image referenced by {guide_name}: {ref}")
    duplicates = sorted(
        {caption for caption in image_captions if image_captions.count(caption) > 1}
    )
    if duplicates:
        errors.append("duplicate image captions: " + ", ".join(duplicates))

    try:
        bom = _csv_rows(docs / "BOM.csv")
        fasteners = _csv_rows(docs / "FASTENERS.csv")
        gaskets = _csv_rows(docs / "GASKETS.csv")
    except FileNotFoundError as exc:
        errors.append(f"missing schedule: {exc}")
        bom, fasteners, gaskets = [], [], []
    bom_ids = {row["id"] for row in bom}
    fastener_ids = {row["id"] for row in fasteners}
    gasket_ids = {row["id"] for row in gaskets}
    for identifier in sorted(set(re.findall(r"\bF\d{2}\b", combined)) - fastener_ids):
        errors.append(f"unknown fastener ID in guides: {identifier}")
    for identifier in sorted(set(re.findall(r"\bG\d{2}\b", combined)) - gasket_ids - {"G00"}):
        errors.append(f"unknown gasket ID in guides: {identifier}")
    for identifier in sorted(set(re.findall(r"\b[ABDEHOP]\d{2}\b", combined)) - bom_ids):
        errors.append(f"unknown BOM ID in guides: {identifier}")

    for part in OFFICIAL_PRINT_PARTS:
        if not part.stl_path.is_file():
            errors.append(f"missing preserved official printable: {part.stl_path}")
        if not part.step_path.is_file():
            errors.append(f"missing preserved official B-rep: {part.step_path}")
    for part in OFFICIAL_PRINT_PARTS_REQUIRED:
        if part.filename not in combined:
            errors.append(f"required official printable is absent from guides: {part.filename}")

    export_report = root / "reports" / "validation" / "export_validation.json"
    if not export_report.is_file():
        errors.append("missing export validation report")
        export_names: set[str] = set()
    else:
        records = json.loads(export_report.read_text(encoding="utf-8"))
        export_names = {str(record["part"]) for record in records}
        expected_names = set(PARTS)
        if export_names != expected_names:
            errors.append(
                "export-validation part set mismatch: "
                f"missing={sorted(expected_names - export_names)}, "
                f"extra={sorted(export_names - expected_names)}"
            )
        for record in records:
            name = str(record["part"])
            if record.get("source_commit") != source_commit():
                errors.append(
                    f"stale export {name}: {record.get('source_commit')} != {source_commit()}"
                )
            for directory, suffix in (("step", ".step"), ("stl", ".stl"), ("3mf", ".3mf")):
                if not (root / "exports" / directory / f"{name}{suffix}").is_file():
                    errors.append(f"missing export: exports/{directory}/{name}{suffix}")
    for filename in re.findall(r"`([a-z0-9_]+)\.3mf`", combined):
        if filename not in export_names:
            errors.append(f"guide references unknown 3MF part: {filename}")

    invalid_labels = sorted(
        {
            token
            for token in re.findall(r"\b[A-Z][A-Z_]{5,}\b", combined)
            if ("VERIFIED" in token or "DERIVED" in token or "VALIDATION" in token)
            and token not in EVIDENCE_LABELS
        }
    )
    if invalid_labels:
        errors.append("invalid evidence labels: " + ", ".join(invalid_labels))

    pdf_results: list[dict[str, Any]] = []
    for pdf_name in PDF_GUIDES:
        path = docs / pdf_name
        if not path.is_file():
            errors.append(f"missing PDF: docs/{pdf_name}")
            continue
        try:
            reader = PdfReader(path)
            if not reader.pages:
                raise ValueError("no pages")
            extracted = "".join(page.extract_text() or "" for page in reader.pages)
            if len(extracted) < 200:
                raise ValueError("insufficient extractable text")
            for page_number, page in enumerate(reader.pages, start=1):
                width = float(page.mediabox.width)
                height = float(page.mediabox.height)
                if not (590 <= width <= 600 and 835 <= height <= 845):
                    errors.append(
                        f"{pdf_name} page {page_number} is not A4 ({width:.1f} x {height:.1f} pt)"
                    )
            pdf_results.append(
                {"file": pdf_name, "pages": len(reader.pages), "bytes": path.stat().st_size}
            )
        except Exception as exc:
            errors.append(f"invalid PDF {pdf_name}: {exc}")

    if "DO NOT PRINT THE FULL ENCLOSURE YET." not in (docs / "START_HERE.md").read_text(
        encoding="utf-8"
    ):
        errors.append("mandatory calibration warning absent from START_HERE")

    result: dict[str, Any] = {
        "status": "PASS" if not errors else "FAIL",
        "evidence": "VERIFIED_DIGITALLY",
        "checked_files": checked_files,
        "pdfs": pdf_results,
        "errors": errors,
    }
    report_dir = root / "reports" / "validation"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "documentation.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    if errors:
        raise ValueError("documentation validation failed:\n- " + "\n- ".join(errors))
    return result
