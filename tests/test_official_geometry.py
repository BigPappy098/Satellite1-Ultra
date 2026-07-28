"""Official reference geometry, datum and provenance validation."""

from __future__ import annotations

import math

import gmsh
import pytest

from satellite1_ultra.official import (
    BATCH1_CORE,
    BATCH1_HAT,
    MASTER_INTERFACE_Z,
    MID_PLATE,
    OFFICIAL_INTERFACE_Z,
    OFFICIAL_MOUNT_X,
    OFFICIAL_MOUNT_Y,
    PCB_SPACER,
    UPPER_STACK,
    board_keepout,
    core_clearance_extent,
    load_official_mesh,
    load_part,
    upper_reference_assembly,
)


@pytest.mark.geometry
@pytest.mark.requires_official_assets
@pytest.mark.parametrize("part", UPPER_STACK, ids=lambda part: part.name)
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
def test_official_interface_plane_is_the_measured_midplate_underside() -> None:
    """The value the divider bosses are built to must come from the official CAD."""
    mid_plate = load_part(MID_PLATE)
    downward = [
        face
        for face in mid_plate.Faces()
        if face.geomType() == "PLANE" and face.normalAt().z < -0.99 and face.Area() > 5000.0
    ]
    assert downward, "no large downward-facing seating plane found on the mid-plate"
    seating = min(downward, key=lambda face: abs(face.Center().z - OFFICIAL_INTERFACE_Z))
    assert seating.Center().z == pytest.approx(OFFICIAL_INTERFACE_Z, abs=1e-6)


@pytest.mark.geometry
@pytest.mark.requires_official_assets
def test_official_four_point_mount_pattern_is_measured_not_assumed() -> None:
    mid_plate = load_part(MID_PLATE)
    centres = {
        (round(abs(face.Center().x), 4), round(abs(face.Center().y), 4))
        for face in mid_plate.Faces()
        if face.geomType() == "CYLINDER"
    }
    assert (round(OFFICIAL_MOUNT_X, 4), round(OFFICIAL_MOUNT_Y, 4)) in centres


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
def test_board_keepout_contains_every_point_of_the_official_mesh() -> None:
    """A conservative envelope is only valid if it really does contain the board."""
    import numpy as np

    envelope = board_keepout(BATCH1_HAT)
    box = envelope.BoundingBox()
    vertices = np.asarray(load_official_mesh(BATCH1_HAT).vertices)
    assert vertices[:, 0].min() >= box.xmin - 1e-6
    assert vertices[:, 0].max() <= box.xmax + 1e-6
    assert vertices[:, 1].min() >= box.ymin - 1e-6
    assert vertices[:, 1].max() <= box.ymax + 1e-6
    assert vertices[:, 2].min() >= box.zmin - 1e-6
    assert vertices[:, 2].max() <= box.zmax + 1e-6


@pytest.mark.requires_official_assets
def test_core_placement_is_not_asserted() -> None:
    """The Core position is undetermined; the project must not pretend otherwise."""
    assert BATCH1_CORE.placement_evidence == "REQUIRES_PHYSICAL_VALIDATION"
    extent = core_clearance_extent()
    assert all(value > 0.0 for value in extent)


@pytest.mark.geometry
@pytest.mark.requires_official_assets
def test_reference_assembly_contains_official_stack_and_placed_board() -> None:
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
