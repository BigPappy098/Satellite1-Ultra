"""The builder package must contain the complete required print set."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from satellite1_ultra.builder_files import (
    CALIBRATION_STAGE_ONE,
    CALIBRATION_STAGE_TWO,
    FABRIC_WRAP_PRINT_ORDER,
    OFFICIAL_TOP_PRINT_ORDER,
    ULTRA_PRINT_ORDER,
)
from satellite1_ultra.configuration import ROOT
from satellite1_ultra.exporting import PARTS
from satellite1_ultra.official import (
    OFFICIAL_PRINT_PARTS_OPTIONAL_MM,
    OFFICIAL_PRINT_PARTS_REQUIRED,
)
from satellite1_ultra.release import (
    CALIBRATION_DIR,
    CALIBRATION_STAGE_TWO_DIR,
    ENCLOSURE_DIR,
    GASKET_DIR,
    OFFICIAL_DIR,
    RELEASE_NAME,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@pytest.mark.deep
def test_release_copies_official_printables_byte_for_byte() -> None:
    release = ROOT / "release" / RELEASE_NAME
    assert release.is_dir()
    for part in OFFICIAL_PRINT_PARTS_REQUIRED:
        copied = (
            release / "ADVANCED" / "OFFICIAL_PARTS" / "REQUIRED_SINGLE_MATERIAL" / part.filename
        )
        assert copied.is_file()
        assert _sha256(copied) == _sha256(part.stl_path)
    for part in OFFICIAL_PRINT_PARTS_OPTIONAL_MM:
        copied = release / "ADVANCED" / "OFFICIAL_PARTS" / "OPTIONAL_MULTI_MATERIAL" / part.filename
        assert copied.is_file()
        assert _sha256(copied) == _sha256(part.stl_path)


def test_beginner_print_folders_cover_every_required_print() -> None:
    release = ROOT / "release" / RELEASE_NAME
    covered = {source for source, _friendly, _quantity in CALIBRATION_STAGE_TWO}
    covered.update(source for source, _friendly, _quantity in ULTRA_PRINT_ORDER)
    covered.update(source for source, _friendly, _quantity in FABRIC_WRAP_PRINT_ORDER)
    nonprinted_gasket_solids = {
        "divider_gasket",
        "driver_gasket",
        "passive_radiator_gasket",
    }
    assert covered == set(PARTS) - nonprinted_gasket_solids
    # Folders come from release.py rather than being written out again here,
    # so renaming one cannot leave this test checking a path that no longer
    # exists while still reporting green.
    for order, folder in (
        (CALIBRATION_STAGE_ONE, CALIBRATION_DIR),
        (CALIBRATION_STAGE_TWO, CALIBRATION_STAGE_TWO_DIR),
        (ULTRA_PRINT_ORDER, ENCLOSURE_DIR),
    ):
        for source, friendly, _quantity in order:
            copied = release / folder / friendly
            assert _sha256(copied) == _sha256(ROOT / "exports" / "3mf" / f"{source}.3mf")

    official_by_name = {part.name: part for part in OFFICIAL_PRINT_PARTS_REQUIRED}
    for source, friendly, _quantity in OFFICIAL_TOP_PRINT_ORDER:
        copied = release / OFFICIAL_DIR / friendly
        assert _sha256(copied) == _sha256(official_by_name[source].stl_path)


def test_release_top_level_stays_simple() -> None:
    """One entry file and a short, ordered folder list — nothing else."""
    release = ROOT / "release" / RELEASE_NAME
    top = sorted(item.name for item in release.iterdir())
    assert top == sorted(
        [
            CALIBRATION_DIR,
            CALIBRATION_STAGE_TWO_DIR,
            ENCLOSURE_DIR,
            OFFICIAL_DIR,
            "ADVANCED",
            GASKET_DIR,
            "GUIDES",
            "SHOPPING_LIST",
            "SOURCE_CHECKSUMS.txt",
            "START_HERE.txt",
        ]
    ), top
    entry_points = [name for name in top if name.lower().endswith((".txt", ".md", ".pdf"))]
    assert entry_points == ["SOURCE_CHECKSUMS.txt", "START_HERE.txt"], entry_points
