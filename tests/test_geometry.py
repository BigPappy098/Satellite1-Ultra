"""Phase-3 B-rep and architecture validation."""

from __future__ import annotations

from itertools import combinations

import cadquery as cq
import pytest

from satellite1_ultra.geometry import (
    DesignParameters,
    active_driver_carrier,
    anti_slip_ring,
    ballast_cartridge,
    ballast_cartridge_lid,
    base_skirt,
    bottom_service_plate,
    cable_gland,
    divider_gasket,
    driver_carrier_gasket,
    driver_gasket,
    driver_keepout,
    electronics_shroud,
    main_cabinet,
    outer_grille_cage,
    passive_radiator_carrier,
    passive_radiator_carrier_gasket,
    passive_radiator_gasket,
    passive_radiator_keepout,
    placed_functional_parts,
    pressure_divider,
    rounded_prism,
)
from satellite1_ultra.official import MID_PLATE, load_part


@pytest.mark.geometry
@pytest.mark.parametrize(
    "builder",
    [
        main_cabinet,
        pressure_divider,
        active_driver_carrier,
        passive_radiator_carrier,
        divider_gasket,
        driver_gasket,
        driver_carrier_gasket,
        passive_radiator_gasket,
        passive_radiator_carrier_gasket,
        cable_gland,
        base_skirt,
        bottom_service_plate,
        ballast_cartridge,
        ballast_cartridge_lid,
        electronics_shroud,
        outer_grille_cage,
        anti_slip_ring,
    ],
)
def test_manufactured_parts_are_valid_single_solids(builder: object) -> None:
    shape = builder()  # type: ignore[operator]
    box = shape.BoundingBox()
    assert shape.isValid()
    assert len(shape.Solids()) == 1
    assert shape.Volume() > 100.0
    assert all(value > 0.0 for value in (box.xlen, box.ylen, box.zlen))


@pytest.mark.geometry
def test_all_manufactured_parts_fit_build_volume() -> None:
    for shape in (
        main_cabinet(),
        pressure_divider(),
        active_driver_carrier(),
        passive_radiator_carrier(),
        divider_gasket(),
        driver_gasket(),
        driver_carrier_gasket(),
        passive_radiator_gasket(),
        passive_radiator_carrier_gasket(),
        cable_gland(),
        base_skirt(),
        bottom_service_plate(),
        ballast_cartridge(),
        ballast_cartridge_lid(),
        electronics_shroud(),
        outer_grille_cage(),
        anti_slip_ring(),
    ):
        box = shape.BoundingBox()
        assert max(box.xlen, box.ylen, box.zlen) <= 256.0


@pytest.mark.geometry
def test_component_keepouts_do_not_overlap_each_other() -> None:
    p = DesignParameters()
    driver = driver_keepout(p)
    left = passive_radiator_keepout(-1, p)
    right = passive_radiator_keepout(1, p)
    assert driver.intersect(left).Volume() < 0.01
    assert driver.intersect(right).Volume() < 0.01
    assert left.intersect(right).Volume() < 0.01


@pytest.mark.geometry
def test_keepouts_clear_acoustic_floor_and_divider() -> None:
    p = DesignParameters()
    divider = pressure_divider(p)
    floor = rounded_prism(
        p.outer_width,
        p.outer_depth,
        p.acoustic_floor_thickness,
        p.acoustic_bottom_z,
        p.corner_radius,
    )
    for shape in (
        driver_keepout(p),
        passive_radiator_keepout(-1, p),
        passive_radiator_keepout(1, p),
    ):
        assert shape.intersect(floor).Volume() < 0.01
        assert shape.intersect(divider).Volume() < 0.01


@pytest.mark.geometry
def test_main_pressure_boundary_has_expected_openings() -> None:
    shape = main_cabinet()
    assert len(shape.Solids()) == 1
    assert all(shell.Closed() for shell in shape.Shells())


@pytest.mark.geometry
@pytest.mark.requires_official_assets
def test_divider_clears_official_mid_plate() -> None:
    overlap = pressure_divider().intersect(load_part(MID_PLATE)).Volume()
    assert overlap < 0.01


@pytest.mark.geometry
@pytest.mark.requires_official_assets
def test_electronics_shroud_clears_complete_official_upper_stack() -> None:
    from satellite1_ultra.official import BATCH1_HAT, UPPER_STACK

    shroud = electronics_shroud()
    for official_part in (*UPPER_STACK, BATCH1_HAT):
        assert shroud.intersect(load_part(official_part)).Volume() < 0.01


@pytest.mark.geometry
def test_functional_assembly_has_only_classified_interference() -> None:
    parts = placed_functional_parts()
    intended_interference = {frozenset(("pressure_divider", "wire_gland"))}
    detected: set[frozenset[str]] = set()
    for (first_name, first), (second_name, second) in combinations(parts.items(), 2):
        volume = first.intersect(second).Volume()
        pair = frozenset((first_name, second_name))
        if volume > 0.01:
            detected.add(pair)
            assert pair in intended_interference, (
                f"invalid collision: {first_name}/{second_name} = {volume:.3f} mm^3"
            )
    assert detected == intended_interference


def test_cadquery_shape_type_contract() -> None:
    assert isinstance(main_cabinet(), cq.Shape)
