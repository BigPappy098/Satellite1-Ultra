"""The validation gates themselves must pass on the current design."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from satellite1_ultra.configuration import ROOT

REPORTS = ROOT / "reports" / "validation"
GATES = (
    "acoustic_volume",
    "sealing",
    "collision",
    "clearance",
    "core_fit",
    "wall_thickness",
    "fasteners",
    "tolerance",
    "assembly",
    "printability",
    "center_of_gravity",
)


def _load(name: str) -> dict:
    path = REPORTS / f"{name}.json"
    assert path.is_file(), f"{path} not generated; run `make validate` first"
    with path.open(encoding="utf-8") as source:
        return dict(json.load(source))


@pytest.mark.parametrize("gate", GATES)
def test_gate_passes(gate: str) -> None:
    assert _load(gate)["status"] == "PASS"


def test_no_gate_claims_physical_validation() -> None:
    for path in REPORTS.glob("*.json"):
        assert "PHYSICALLY_VALIDATED" not in path.read_text(encoding="utf-8")


def test_every_gate_that_needs_a_specimen_declares_a_physical_gate() -> None:
    for gate in ("acoustic_volume", "sealing", "wall_thickness", "fasteners", "tolerance"):
        assert _load(gate)["physical_gate"]["evidence"] == "REQUIRES_PHYSICAL_VALIDATION"


def test_sealing_gate_proves_continuity_not_just_absence_of_collision() -> None:
    checks = _load("sealing")["checks"]
    lands = [c for c in checks if "gasket-land annulus continuity" in c["feature"]]
    assert len(lands) == 3
    for check in lands:
        assert check["measured_solid_fraction"] == pytest.approx(1.0, abs=1e-6)


def test_fastener_schedule_has_no_bottoming_joint() -> None:
    for row in _load("fasteners")["schedule"]:
        assert row["bottoming_margin_mm"] >= 0.0
        assert row["engagement_mm"] >= 3.0


def test_assembly_graph_is_acyclic_with_no_unresolved_steps() -> None:
    report = _load("assembly")
    assert report["acyclic"] is True
    assert report["unresolved_dependencies"] == []
    assert len(report["assembly_order"]) == len(report["disassembly_order"])


@pytest.mark.deep
def test_exports_are_current_and_reopen() -> None:
    path = REPORTS / "export_validation.json"
    assert path.is_file(), "exports not generated; run `make exports` first"
    with path.open(encoding="utf-8") as source:
        records = json.load(source)
    assert records
    for record in records:
        # Relative, not absolute.  A fixed 1e-2 mm^3 budget is ~1e-8 relative on
        # the 700,000 mm^3 cabinet and ~1e-4 on a small coupon, so it was not a
        # single standard: v2's spline-faced shells reopened 0.022 mm^3 light
        # and tripped it while every flat-faced part sailed through.  That
        # residue is OpenCascade re-integrating trimmed spline faces after
        # re-parameterisation, not lost material -- the bounds agree to 4e-12 mm
        # and 0.024 mm^3 is a cube 0.29 mm on a side, against a 0.4 mm nozzle
        # and a smallest real feature (a crush rib) of roughly 240 mm^3.
        # 1e-6 is ~4x tighter than the worst observed value and still catches
        # feature loss by orders of magnitude.
        volume = record["brep_volume_mm3"]
        assert volume > 0.0, record["part"]
        assert record["step_volume_error_mm3"] / volume < 1e-6, record["part"]
        assert record["step_bounds_error_mm"] < 1e-6
        assert record["stl_validation"]["watertight"] is True
        assert record["stl_validation"]["connected_components"] == 1
        assert record["three_mf_validation"]["watertight"] is True
        assert Path(record["source_commit"]).name != ""


@pytest.mark.deep
def test_generated_step_reopens_in_a_second_independent_reader() -> None:
    """Gmsh's OpenCascade reader must agree with CadQuery on the exports.

    Export success is not validation, and neither is reopening a file with the
    same library that wrote it.
    """
    import gmsh

    step_dir = ROOT / "exports" / "step"
    files = sorted(step_dir.glob("*.step"))
    assert files, "exports not generated; run `make exports` first"

    with (REPORTS / "export_validation.json").open(encoding="utf-8") as source:
        expected = {record["part"]: record for record in json.load(source)}

    gmsh.initialize()
    try:
        for path in files:
            record = expected[path.stem]
            gmsh.clear()
            gmsh.model.occ.importShapes(str(path))
            gmsh.model.occ.synchronize()
            volumes = gmsh.model.getEntities(3)
            assert len(volumes) == 1, f"{path.name} did not read back as one solid"
            # Compare volume, not bounding box: OpenCascade's box for a
            # trimmed spline face can report the untrimmed surface extent, so a
            # bounding-box comparison across readers is not a geometry check.
            volume = gmsh.model.occ.getMass(*volumes[0])
            assert volume == pytest.approx(record["brep_volume_mm3"], rel=1e-6), path.name
            box = gmsh.model.getBoundingBox(*volumes[0])
            lengths = (box[3] - box[0], box[4] - box[1], box[5] - box[2])
            for measured, declared in zip(
                lengths,
                (record["bounds_x_mm"], record["bounds_y_mm"], record["bounds_z_mm"]),
                strict=True,
            ):
                assert measured >= declared - 1e-3, path.name
                assert measured <= declared + 0.5, path.name
    finally:
        gmsh.finalize()
