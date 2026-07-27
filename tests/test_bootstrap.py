"""Bootstrap verification."""

from pathlib import Path

import cadquery as cq
import pytest
from cadquery import exporters, importers


def test_cadquery_step_round_trip(tmp_path: Path) -> None:
    model = cq.Workplane("XY").box(10.0, 20.0, 30.0)
    step_path = tmp_path / "roundtrip.step"
    exporters.export(model, str(step_path))
    reloaded = importers.importStep(str(step_path)).val()
    assert reloaded.isValid()
    assert reloaded.Volume() == pytest.approx(6000.0, rel=1e-9)
    bounds = reloaded.BoundingBox()
    assert (bounds.xlen, bounds.ylen, bounds.zlen) == pytest.approx((10.0, 20.0, 30.0))


def test_master_datum_documented() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "origin: center of the official mid-plate interface plane" in readme
    assert "-Y: active-driver front" in readme
