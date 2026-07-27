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
    if not path.is_file():
        pytest.skip(f"{path} not generated; run `make validate` first")
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
    if not path.is_file():
        pytest.skip("exports not generated; run `make exports` first")
    with path.open(encoding="utf-8") as source:
        records = json.load(source)
    assert records
    for record in records:
        assert record["step_volume_error_mm3"] < 1e-2
        assert record["step_bounds_error_mm"] < 1e-6
        assert record["stl_validation"]["watertight"] is True
        assert record["stl_validation"]["connected_components"] == 1
        assert record["three_mf_validation"]["watertight"] is True
        assert Path(record["source_commit"]).name != ""
