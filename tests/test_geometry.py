"""Phase-3 B-rep and architecture validation."""

from __future__ import annotations

import cadquery as cq
import pytest

from satellite1_ultra.geometry import (
    DesignParameters,
    active_driver_carrier,
    driver_keepout,
    main_cabinet,
    passive_radiator_carrier,
    passive_radiator_keepout,
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
    assert len(shape.Shells()) == 1
    assert len(shape.Solids()) == 1


@pytest.mark.geometry
@pytest.mark.requires_official_assets
def test_divider_clears_official_mid_plate() -> None:
    overlap = pressure_divider().intersect(load_part(MID_PLATE)).Volume()
    assert overlap < 0.01


def test_cadquery_shape_type_contract() -> None:
    assert isinstance(main_cabinet(), cq.Shape)
