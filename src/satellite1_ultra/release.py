"""Create the clean, checksum-stamped builder release package."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from satellite1_ultra.builder_files import (
    CALIBRATION_PRINT_ORDER,
    OFFICIAL_TOP_PRINT_ORDER,
    ULTRA_PRINT_ORDER,
)
from satellite1_ultra.configuration import ROOT
from satellite1_ultra.doc_validation import PDF_GUIDES
from satellite1_ultra.exporting import PARTS, source_commit
from satellite1_ultra.official import (
    OFFICIAL_PRINT_PARTS_OPTIONAL_MM,
    OFFICIAL_PRINT_PARTS_REQUIRED,
)

RELEASE_NAME = "Satellite1-Ultra-RC1"
CALIBRATION_NAMES = {name for name in PARTS if name.startswith("coupon_")} | {"cable_gland"}
GASKET_SOLIDS = {"divider_gasket", "driver_gasket", "passive_radiator_gasket"}


def _copy(source: Path, target: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"required release input is missing: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def package_release(
    output: Path = ROOT / "release" / RELEASE_NAME,
    root: Path = ROOT,
) -> Path:
    """Rebuild the release directory from current, validated outputs."""
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    for name in PDF_GUIDES:
        _copy(root / "docs" / name, output / name)
    for name in ("BOM.csv", "FASTENERS.csv", "GASKETS.csv"):
        _copy(root / "docs" / name, output / name)
    _copy(
        root / "config" / "physical_calibration.yaml",
        output / "CALIBRATION_INPUT_TEMPLATE.yaml",
    )

    for part_name in PARTS:
        if part_name not in CALIBRATION_NAMES:
            _copy(
                root / "exports" / "step" / f"{part_name}.step",
                output / "STEP" / f"{part_name}.step",
            )
        if part_name not in CALIBRATION_NAMES | GASKET_SOLIDS:
            for folder, suffix in (("STL", ".stl"), ("3MF", ".3mf")):
                _copy(
                    root / "exports" / folder.lower() / f"{part_name}{suffix}",
                    output / folder / f"{part_name}{suffix}",
                )
    for name in sorted(CALIBRATION_NAMES):
        _copy(
            root / "exports" / "3mf" / f"{name}.3mf",
            output / "CALIBRATION_PARTS" / f"{name}.3mf",
        )
    for path in sorted((root / "exports" / "assembly").glob("*.step")):
        _copy(path, output / "STEP" / "ASSEMBLIES" / path.name)
    for path in sorted((root / "exports" / "gasket_templates").glob("*.dxf")):
        _copy(path, output / "GASKET_TEMPLATES" / path.name)
    for path in sorted((root / "reports" / "renders").glob("*.png")):
        _copy(path, output / "IMAGES" / path.name)
    for source_name, friendly_name, _quantity in CALIBRATION_PRINT_ORDER:
        _copy(
            root / "exports" / "3mf" / f"{source_name}.3mf",
            output / "PRINT_THESE_FILES" / "1_CALIBRATION_FIRST" / friendly_name,
        )
    for source_name, friendly_name, _quantity in ULTRA_PRINT_ORDER:
        _copy(
            root / "exports" / "3mf" / f"{source_name}.3mf",
            output / "PRINT_THESE_FILES" / "2_ULTRA_ENCLOSURE_PARTS" / friendly_name,
        )
    official_by_name = {part.name: part for part in OFFICIAL_PRINT_PARTS_REQUIRED}
    for part in OFFICIAL_PRINT_PARTS_REQUIRED:
        _copy(
            part.stl_path,
            output / "OFFICIAL_PARTS" / "REQUIRED_SINGLE_MATERIAL" / part.filename,
        )
    for source_name, friendly_name, _quantity in OFFICIAL_TOP_PRINT_ORDER:
        _copy(
            official_by_name[source_name].stl_path,
            output / "PRINT_THESE_FILES" / "3_SQUIRCLE_TOP_PARTS" / friendly_name,
        )
    for part in OFFICIAL_PRINT_PARTS_OPTIONAL_MM:
        _copy(
            part.stl_path,
            output / "OFFICIAL_PARTS" / "OPTIONAL_MULTI_MATERIAL" / part.filename,
        )

    read_first = """SATELLITE1 ULTRA - READ THIS FIRST

1. Open BUILD_SATELLITE1_ULTRA_FOR_BEGINNERS.pdf.
2. Do not print the large enclosure parts yet.
3. Open PRINT_THESE_FILES/1_CALIBRATION_FIRST and print those files first.
4. Pass the checks in the guide.
5. Then print every file in PRINT_THESE_FILES/2_ULTRA_ENCLOSURE_PARTS and
   PRINT_THESE_FILES/3_SQUIRCLE_TOP_PARTS. Print the quantity shown in each
   filename/guide.

You can ignore STEP, STL, 3MF, IMAGES, reports, and source files unless the
beginner guide specifically sends you there.

Do not print the old official Squircle speaker chamber, speaker plate, or
anti-slip ring. The Ultra files replace them.
"""
    (output / "00_READ_ME_FIRST.txt").write_text(read_first, encoding="utf-8")

    notes = f"""# Satellite1 Ultra RC1

Status: `DIGITAL_PROTOTYPE_READY`.

This package is generated from source commit `{source_commit()}`.

**DO NOT PRINT THE FULL ENCLOSURE YET. PRINT AND COMPLETE THE CALIBRATION
PARTS FIRST.**

Supported hardware: FutureProofHomes Satellite1 Batch 1, Core rev4.1 plus
HAT rev4.1 / R2024.12.06. Satellite1.1 / Batch 2 is unsupported.

This package includes every required printable: the custom Ultra parts plus
the six unmodified official Squircle upper-stack STL files under
`OFFICIAL_PARTS/REQUIRED_SINGLE_MATERIAL/`. Do not print the official original
speaker chamber, speaker plate, or anti-slip ring; the Ultra parts replace them.

First-time builders should ignore the advanced CAD folders, open
`BUILD_SATELLITE1_ULTRA_FOR_BEGINNERS.pdf`, and print only from the numbered
folders under `PRINT_THESE_FILES/`.

No physical unit has been validated. Fit, sealing, acoustic performance,
thermal margin, Wi-Fi, microphones, LEDs, buttons, and wake-word performance
remain `REQUIRES_PHYSICAL_VALIDATION`.
"""
    (output / "RELEASE_NOTES.md").write_text(notes, encoding="utf-8")

    files = sorted(path for path in output.rglob("*") if path.is_file())
    checksum_path = output / "SOURCE_CHECKSUMS.txt"
    checksum_path.write_text(
        "".join(f"{_digest(path)}  {path.relative_to(output)}\n" for path in files),
        encoding="utf-8",
    )
    archive = output.parent / f"{RELEASE_NAME}.zip"
    if archive.exists():
        archive.unlink()
    shutil.make_archive(str(archive.with_suffix("")), "zip", output.parent, output.name)
    if not archive.is_file() or archive.stat().st_size < 100_000:
        raise ValueError("release archive generation failed")
    return output
