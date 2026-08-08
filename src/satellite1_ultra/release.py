"""Create the clean, checksum-stamped builder release package."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from satellite1_ultra.builder_files import (
    CALIBRATION_STAGE_ONE,
    CALIBRATION_STAGE_TWO,
    FABRIC_WRAP_PRINT_ORDER,
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

#: Folder names inside the release package.  The website builds download links
#: from these, so they are named here rather than written out at both ends: the
#: published site once pointed at PRINT_THESE_FILES/1_CALIBRATION_FIRST and
#: friends, none of which have ever existed, and every download 404'd.
CALIBRATION_DIR = "1_PRINT_THIS_FIRST"
CALIBRATION_STAGE_TWO_DIR = "2_PRINT_THESE_NEXT"
ENCLOSURE_DIR = "3_ENCLOSURE_PARTS"
OFFICIAL_DIR = "4_SATELLITE_TOP_PARTS"
FABRIC_DIR = f"{ENCLOSURE_DIR}/OPTIONAL_FABRIC_WRAP"
GASKET_DIR = "GASKET_TEMPLATES"
STL_DIR = "ADVANCED/STL"
STEP_DIR = "ADVANCED/STEP"


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

    # One loose file at the top, then numbered folders in the order they are
    # used.  Everything a builder does not need on day one lives under ADVANCED.
    for name in PDF_GUIDES:
        _copy(root / "docs" / name, output / "GUIDES" / name)
    for name in ("BOM.csv", "FASTENERS.csv", "GASKETS.csv"):
        _copy(root / "docs" / name, output / "SHOPPING_LIST" / name)
    _copy(
        root / "config" / "physical_calibration.yaml",
        output / "ADVANCED" / "CALIBRATION_INPUT_TEMPLATE.yaml",
    )

    for part_name in PARTS:
        if part_name not in CALIBRATION_NAMES:
            _copy(
                root / "exports" / "step" / f"{part_name}.step",
                output / STEP_DIR / f"{part_name}.step",
            )
        # Everything printable ships in both formats, test pieces included.
        # The coupons used to be 3MF-only, which left the first page a builder
        # downloads from with no STL option at all, for no reason: the exports
        # have always existed. Only the gasket solids are excluded, and those
        # are cut from foam sheet rather than printed.
        if part_name not in GASKET_SOLIDS:
            for folder, suffix in (("STL", ".stl"), ("3MF", ".3mf")):
                _copy(
                    root / "exports" / folder.lower() / f"{part_name}{suffix}",
                    output / "ADVANCED" / folder / f"{part_name}{suffix}",
                )
    for name in sorted(CALIBRATION_NAMES):
        _copy(
            root / "exports" / "3mf" / f"{name}.3mf",
            output / "ADVANCED" / "CALIBRATION_PARTS" / f"{name}.3mf",
        )
    for path in sorted((root / "exports" / "assembly").glob("*.step")):
        _copy(path, output / STEP_DIR / "ASSEMBLIES" / path.name)
    for path in sorted((root / "exports" / "gasket_templates").glob("*.dxf")):
        _copy(path, output / GASKET_DIR / path.name)
    for path in sorted((root / "reports" / "renders").glob("*.png")):
        _copy(path, output / "ADVANCED" / "IMAGES" / path.name)
    # Both formats, side by side, under the same builder-facing name.  STLs
    # used to exist only in ADVANCED/STL under their source names, so the
    # folder a builder is told to print from was 3MF-only and the STL of the
    # same part was neither obviously present nor obviously current.
    for order, folder in (
        (CALIBRATION_STAGE_ONE, CALIBRATION_DIR),
        (CALIBRATION_STAGE_TWO, CALIBRATION_STAGE_TWO_DIR),
        (ULTRA_PRINT_ORDER, ENCLOSURE_DIR),
        # Swap-in skin segments for builders wrapping the body in cloth.
        (FABRIC_WRAP_PRINT_ORDER, FABRIC_DIR),
    ):
        for source_name, friendly_name, _quantity in order:
            _copy(root / "exports" / "3mf" / f"{source_name}.3mf", output / folder / friendly_name)
            _copy(
                root / "exports" / "stl" / f"{source_name}.stl",
                output / folder / f"{Path(friendly_name).stem}.stl",
            )
    official_by_name = {part.name: part for part in OFFICIAL_PRINT_PARTS_REQUIRED}
    for part in OFFICIAL_PRINT_PARTS_REQUIRED:
        _copy(
            part.stl_path,
            output / "ADVANCED" / "OFFICIAL_PARTS" / "REQUIRED_SINGLE_MATERIAL" / part.filename,
        )
    for source_name, friendly_name, _quantity in OFFICIAL_TOP_PRINT_ORDER:
        _copy(
            official_by_name[source_name].stl_path,
            output / OFFICIAL_DIR / friendly_name,
        )
    for part in OFFICIAL_PRINT_PARTS_OPTIONAL_MM:
        _copy(
            part.stl_path,
            output / "ADVANCED" / "OFFICIAL_PARTS" / "OPTIONAL_MULTI_MATERIAL" / part.filename,
        )

    read_first = """SATELLITE1 ULTRA

START HERE:  https://bigpappy098.github.io/Satellite1-Ultra/

That website walks you through the whole build, one step at a time, with a
picture for each step. It is much easier to follow than these folders.

If you would rather work offline, open GUIDES/SATELLITE1_ULTRA_BUILD_BOOK.pdf
and follow it from front to back.

CALIBRATION RUNS IN TWO ROUNDS
-----------------------------
1_PRINT_THIS_FIRST    One part. Print it, measure the marked slot and the flat
                      edge, and type both into the website. That gives your
                      printer's XY and Z scale.
2_PRINT_THESE_NEXT    The remaining test pieces, REGENERATED with your scale
                      already applied. Do not print the copies in this folder
                      as shipped; download your own from the website after
                      round one. Every one of them measures a feature your
                      scale error already moved, so reading them off an
                      uncorrected print mixes the two together and tells you
                      nothing you can act on.
3_ENCLOSURE_PARTS     The enclosure. Print after both rounds pass.
                      OPTIONAL_FABRIC_WRAP holds three alternative skin
                      segments, for wrapping the body in speaker cloth.
4_SATELLITE_TOP_PARTS The original Satellite1 top. Print all six.
GASKET_TEMPLATES      Print at 100% scale and cut three foam seals from them.
GUIDES                The full manuals as PDFs.
SHOPPING_LIST         What to buy: parts, screws, and seals.
ADVANCED              Source CAD, images, checksums. Ignore unless you need them.

THE ONE RULE
------------
Round one, then round two, then the big parts. Skipping straight to the test
pieces in folder 2 is how a builder ends up measuring a seat that is 0.9
percent small and concluding the shape is wrong.

Do not print the old Satellite1 speaker chamber, speaker plate, or rubber ring.
The Ultra parts replace all three.

Nothing here has been physically built and measured yet, so keep checking as
you go.
"""
    (output / "START_HERE.txt").write_text(read_first, encoding="utf-8")

    # Provenance stays with the package, just out of the builder's way.
    (output / "ADVANCED" / "BUILD_INFO.txt").write_text(
        f"""Satellite1 Ultra RC1
Generated from source commit {source_commit()}

Status: DIGITAL_PROTOTYPE_READY. No physical unit has been built and measured.
Fit, sealing, acoustic performance, thermal margin, Wi-Fi, microphones, LEDs,
buttons and wake-word performance are all REQUIRES_PHYSICAL_VALIDATION.

Supported hardware: FutureProofHomes Satellite1 Batch 1, Core rev4.1 with
HAT rev4.1 / R2024.12.06. Satellite1.1 / Batch 2 is not supported.
""",
        encoding="utf-8",
    )

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
