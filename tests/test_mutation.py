"""Mutation testing: prove the validation gates detect representative defects.

A validation suite that only ever runs against a good design proves nothing.
Each test here injects one intentional defect, asserts that the gate which is
supposed to catch it reports FAIL, and restores the original state. Two of them
mutate the checked-in configuration file on disk so the configuration path
itself is exercised, not just the in-memory parameters; both restore the file
in a ``finally`` block.

The mutations are deliberately small and physically meaningful: each one is a
mistake a person could actually make while editing this design.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from satellite1_ultra.configuration import (
    ROOT,
    load_design_parameters,
    validate_physical_calibration,
)
from satellite1_ultra.doc_validation import validate_documentation
from satellite1_ultra.geometry import DesignParameters
from satellite1_ultra.validation import (
    clearance_report,
    collision_report,
    printability_report,
    sealing_report,
    stability_report,
    wall_thickness_report,
)

pytestmark = pytest.mark.mutation


def _baseline() -> DesignParameters:
    return load_design_parameters()


def _failed_features(report: dict[str, Any], *keys: str) -> list[str]:
    failures: list[str] = []
    for key in keys:
        for item in report.get(key, []):
            if isinstance(item, dict) and item.get("status") == "FAIL":
                failures.append(str(item.get("feature") or item.get("interface") or item))
    return failures


@contextmanager
def mutated_config(path: Path, old: str, new: str) -> Iterator[None]:
    """Temporarily rewrite a checked-in configuration file, then restore it.

    Restore through bytes.  read_text translates CRLF to LF, so reading a
    CRLF file and writing the result back rewrites every line ending, and the
    obvious `read_text() == original` check cannot see it because the second
    read normalises identically.  docs/BOM.csv is written by csv.writer and is
    CRLF, and it came back from a mutation run LF-only.
    """
    raw = path.read_bytes()
    original = raw.decode("utf-8")
    assert old in original, f"mutation anchor {old!r} not present in {path}"
    try:
        path.write_text(original.replace(old, new, 1), encoding="utf-8")
        yield
    finally:
        path.write_bytes(raw)
        assert path.read_bytes() == raw


# ---------------------------------------------------------------------- #
# Sealing
# ---------------------------------------------------------------------- #
def test_removing_the_pad_backing_is_caught_by_the_sealing_gate() -> None:
    """Blind inserts must stay blind; zero backing breaks the pressure boundary."""
    healthy = sealing_report(_baseline())
    assert healthy["status"] == "PASS"

    defective = sealing_report(replace(_baseline(), pad_backing=0.0))
    assert defective["status"] == "FAIL"
    assert any("blind" in feature for feature in _failed_features(defective, "checks"))


def test_a_pad_narrower_than_its_seat_is_caught_by_the_sealing_gate() -> None:
    """If the pad does not reach past the seat, the gasket land is discontinuous.

    Sized from the radiator rather than pinned to a literal.  This mutation was
    written as pr_pad_diameter=120.0 against the 122 mm SB12PACR-00, where 120
    left the land broken.  The Dayton DSA115-PR is 115.57 mm across, so a 120 mm
    pad still covers its seat: the gate kept failing, but on blind clamp
    inserts, while the continuity check this test names stayed green.  The
    status assertion passed and the test quietly stopped proving anything.

    Measured on the current parts: continuity survives at 120 mm and breaks at
    115 mm and below.  Taking 2 mm off the radiator's own outside diameter puts
    the pad inside the seat edge for any radiator, which is the geometric
    condition the check exists to catch.
    """
    base = _baseline()
    healthy = sealing_report(base)
    assert healthy["status"] == "PASS"

    mutant = replace(base, pr_pad_diameter=base.pr_outer_diameter - 2.0)
    defective = sealing_report(mutant)
    assert defective["status"] == "FAIL"
    assert any("continuity" in feature for feature in _failed_features(defective, "checks"))


# ---------------------------------------------------------------------- #
# Clearance
# ---------------------------------------------------------------------- #
def test_insert_bore_drawn_at_the_insert_outside_diameter_is_caught() -> None:
    """The exact defect found in the inherited design must now fail a gate."""
    mutant = replace(_baseline(), insert_bore_diameter=4.6, pr_clamp_bolt_circle=126.0)
    report = clearance_report(mutant)
    assert report["status"] == "FAIL"
    assert any("insert land" in feature for feature in _failed_features(report, "clearances"))


def test_over_compressed_gasket_is_caught_by_the_clearance_gate() -> None:
    mutant = replace(_baseline(), gasket_compression_fraction=0.60)
    report = clearance_report(mutant)
    assert report["status"] == "FAIL"
    assert any(
        "gasket compression" in feature for feature in _failed_features(report, "clearances")
    )


def test_a_shifted_official_interface_plane_is_caught() -> None:
    """Moving the official seating plane by 0.4 mm must not pass silently."""
    mutant = replace(_baseline(), official_interface_z=-7.2)
    report = clearance_report(mutant)
    assert report["status"] == "FAIL"
    assert any("official" in feature.lower() for feature in _failed_features(report, "clearances"))


def test_a_deeper_driver_that_hits_the_rear_wall_is_caught() -> None:
    mutant = replace(_baseline(), driver_depth=170.0)
    report = clearance_report(mutant)
    assert report["status"] == "FAIL"
    assert any("rear inner wall" in feature for feature in _failed_features(report, "clearances"))


# ---------------------------------------------------------------------- #
# Wall thickness
# ---------------------------------------------------------------------- #
def test_a_thin_cabinet_wall_is_caught_by_the_measured_section_probe() -> None:
    """Not just the parameter audit: the probe must measure the real section."""
    mutant = replace(_baseline(), wall_thickness=2.0)
    report = wall_thickness_report(mutant)
    assert report["status"] == "FAIL"
    measured = _failed_features(report, "measured_sections")
    assert measured, "the measured-section probes did not detect a 2.0 mm wall"


# ---------------------------------------------------------------------- #
# Collision
# ---------------------------------------------------------------------- #
@pytest.mark.deep
def test_a_radiator_that_intrudes_too_far_is_caught_by_the_collision_gate() -> None:
    """A radiator deep enough to reach the driver must be caught.

    This mutation used to drop a radiator to the driver's height
    (pr_axis_z=-100.0), which interfered when the radiator was the 38.3 mm-deep,
    122 mm SB12PACR-00.  The Dayton DSA115-PR is 29.72 mm deep and 115.57 mm
    across, so it reaches inward only to x = +-46.28 mm while the driver spans
    x = +-44 mm: the two never meet at any height, and the gate correctly
    reported PASS.  The mutation had stopped being a defect, so it tested
    nothing.

    Depth is the parameter that actually decides this, and it is the one that
    moves when a radiator is substituted.  Measured on the current layout, the
    gate is quiet through 38.3 mm and fires from 42.0 mm; 45.0 mm sits clear of
    that boundary without being so extreme that it would pass through an
    enclosure of any plausible size.
    """
    mutant = replace(_baseline(), pr_depth=45.0)
    report = collision_report(mutant)
    assert report["status"] == "FAIL"
    assert report["invalid_collision_count"] > 0


@pytest.mark.deep
def test_a_divider_pushed_into_the_official_mid_plate_is_caught() -> None:
    """Raising the interface plane above the official underside must collide.

    Note the sensitivity limit this mutation established: between -6.8 mm and
    about 0 mm the divider bosses stand inside the mid-plate's hollow centre and
    produce no interference at all. Seating-plane errors in that band are caught
    by the clearance gate's comparison against the measured official plane, not
    by the collision gate. See reports/CLAUDE_TAKEOVER_AUDIT.md.
    """
    mutant = replace(_baseline(), official_interface_z=2.0)
    report = collision_report(mutant)
    assert report["status"] == "FAIL"
    assert report["invalid_collision_count"] > 0


# ---------------------------------------------------------------------- #
# Printability and stability
# ---------------------------------------------------------------------- #
def test_a_part_larger_than_the_build_volume_is_caught() -> None:
    mutant = replace(_baseline(), outer_width=250.0, grille_width_margin=32.0)
    report = printability_report(mutant)
    assert report["status"] == "FAIL"
    assert any(item["status"] == "FAIL" for item in report["parts"])


def test_losing_the_ballast_is_caught_by_the_stability_gate() -> None:
    """A tall speaker without its low mass must not pass the tipping gate."""
    mutant = replace(_baseline(), base_bottom_z=-460.0)
    report = stability_report(mutant)
    assert report["status"] == "FAIL"
    assert report["minimum_tipping_angle_deg"] < 35.0


# ---------------------------------------------------------------------- #
# Configuration-file mutations
# ---------------------------------------------------------------------- #
def test_configuration_file_mutation_reaches_the_geometry() -> None:
    """Mutate default.yaml on disk and confirm the loader rejects it early."""
    path = ROOT / "config" / "default.yaml"
    with mutated_config(path, "  wall_thickness: 4.0", "  wall_thickness: 2.0"):
        with pytest.raises(ValueError, match="wall_thickness"):
            load_design_parameters()
    assert load_design_parameters().wall_thickness == pytest.approx(4.0)
    assert wall_thickness_report(load_design_parameters())["status"] == "PASS"


def test_component_data_mutation_reaches_the_mechanical_interface() -> None:
    """A wrong published cutout diameter must fail before geometry generation."""
    path = ROOT / "config" / "components.yaml"
    with mutated_config(path, "    cutout_diameter_mm: 88.5", "    cutout_diameter_mm: 108.0"):
        with pytest.raises(ValueError, match="active-driver bore"):
            load_design_parameters()
    assert load_design_parameters().driver_cutout_diameter == pytest.approx(88.5)


def test_impossible_physical_calibration_is_rejected_before_geometry_build() -> None:
    values = {
        "xy_scale_correction_fraction": 0.0,
        "z_scale_correction_fraction": 0.0,
        "fastener_clearance_diameter_offset_mm": 0.0,
        "insert_bore_diameter_offset_mm": 0.0,
        "driver_cutout_diameter_offset_mm": 0.0,
        "passive_radiator_cutout_diameter_offset_mm": 0.0,
        "cable_passage_diameter_offset_mm": 0.0,
        "gasket_sheet_thickness_mm": 2.0,
        "gasket_compressed_thickness_offset_mm": 0.0,
        "active_driver_flange_thickness_mm": 30.0,
        "passive_radiator_flange_thickness_mm": 4.0,
    }
    with pytest.raises(ValueError, match="outside the safe range"):
        validate_physical_calibration(values)


# ---------------------------------------------------------------------- #
# Documentation mutations
# ---------------------------------------------------------------------- #
def test_missing_documentation_image_is_caught() -> None:
    path = ROOT / "docs" / "ASSEMBLY_GUIDE.md"
    with mutated_config(
        path,
        "IMAGES/assembly_stage_03_driver.png",
        "IMAGES/intentionally_missing.png",
    ):
        with pytest.raises(ValueError, match="missing image"):
            validate_documentation()


def test_unknown_fastener_id_is_caught() -> None:
    path = ROOT / "docs" / "ASSEMBLY_GUIDE.md"
    with mutated_config(path, "F09, 4 screws", "F99, 4 screws"):
        with pytest.raises(ValueError, match="unknown fastener ID"):
            validate_documentation()


def test_missing_bom_entry_is_caught() -> None:
    path = ROOT / "docs" / "BOM.csv"
    # Bytes, not text: this file is CRLF, and restoring via read_text/write_text
    # silently converted it to LF on every mutation run.
    raw = path.read_bytes()
    original = raw.decode("utf-8")
    filtered = "\n".join(line for line in original.splitlines() if not line.startswith("H01,"))
    try:
        path.write_text(filtered + "\n", encoding="utf-8")
        with pytest.raises(ValueError, match="unknown BOM ID"):
            validate_documentation()
    finally:
        path.write_bytes(raw)
        assert path.read_bytes() == raw


def test_changed_export_source_is_caught() -> None:
    path = ROOT / "config" / "default.yaml"
    with mutated_config(path, "wall_thickness: 4.0", "wall_thickness: 4.01"):
        with pytest.raises(ValueError, match="stale export"):
            validate_documentation()
    assert validate_documentation()["status"] == "PASS"
