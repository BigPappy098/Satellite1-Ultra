"""Official reference geometry and datum validation."""

from __future__ import annotations

import math

import gmsh
import pytest

from satellite1_ultra.official import (
    BATCH1_HAT,
    MASTER_INTERFACE_Z,
    MID_PLATE,
    PCB_SPACER,
    UPPER_STACK,
    load_part,
    upper_reference_assembly,
)


@pytest.mark.geometry
@pytest.mark.requires_official_assets
@pytest.mark.parametrize("part", UPPER_STACK)
def test_upper_stack_imports_with_positive_volume(part: object) -> None:
    shape = load_part(part)  # type: ignore[arg-type]
    bounds = shape.BoundingBox()
    assert all(math.isfinite(value) for value in (bounds.xlen, bounds.ylen, bounds.zlen))
    assert sum(solid.Volume() for solid in shape.Solids()) > 0


@pytest.mark.geometry
@pytest.mark.requires_official_assets
def test_master_datum_places_midplate_interface_at_zero() -> None:
    mid_plate = load_part(MID_PLATE)
    assert MASTER_INTERFACE_Z == pytest.approx(140.8)
    assert mid_plate.BoundingBox().zmax == pytest.approx(3.2, abs=1e-6)


@pytest.mark.geometry
@pytest.mark.requires_official_assets
def test_batch1_hat_mount_pattern_alignment() -> None:
    spacer = load_part(PCB_SPACER)
    hat = load_part(BATCH1_HAT)
    assert spacer.BoundingBox().xlen == pytest.approx(87.196698, abs=1e-5)
    assert hat.BoundingBox().xlen == pytest.approx(87.99709, abs=1e-5)
    assert hat.BoundingBox().ymax == pytest.approx(43.227892, abs=1e-5)


@pytest.mark.geometry
@pytest.mark.requires_official_assets
def test_reference_assembly_contains_official_stack_and_hat() -> None:
    assembly = upper_reference_assembly()
    assert len(assembly.objects) == 7


@pytest.mark.deep
@pytest.mark.requires_official_assets
def test_midplate_independent_gmsh_import() -> None:
    gmsh.initialize()
    try:
        imported = gmsh.model.occ.importShapes(str(MID_PLATE.path))
        gmsh.model.occ.synchronize()
        assert imported
        assert len(gmsh.model.getEntities(3)) == 1
    finally:
        gmsh.finalize()
