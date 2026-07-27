"""Manufactured-geometry B-rep validation."""

from __future__ import annotations

from itertools import combinations

import cadquery as cq
import pytest

from satellite1_ultra.exporting import PARTS, print_oriented
from satellite1_ultra.geometry import (
    DEFAULT_PARAMETERS,
    DesignParameters,
    acoustic_mounts,
    driver_keepout,
    main_cabinet,
    passive_radiator_keepout,
    placed_functional_parts,
    pressure_divider,
    rounded_prism,
    rounded_rect_stations,
)
from satellite1_ultra.official import MID_PLATE, load_part


@pytest.mark.geometry
@pytest.mark.parametrize("name", sorted(PARTS))
def test_manufactured_parts_are_valid_single_solids(name: str) -> None:
    shape = PARTS[name].builder(DEFAULT_PARAMETERS)
    box = shape.BoundingBox()
    assert shape.isValid()
    assert len(shape.Solids()) == 1
    assert shape.Volume() > 100.0
    assert all(value > 0.0 for value in (box.xlen, box.ylen, box.zlen))


@pytest.mark.geometry
@pytest.mark.parametrize("name", sorted(PARTS))
def test_every_part_fits_the_build_volume(name: str) -> None:
    box = print_oriented(PARTS[name].builder(DEFAULT_PARAMETERS)).BoundingBox()
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
def test_cabinet_is_one_closed_shell() -> None:
    shape = main_cabinet()
    assert len(shape.Solids()) == 1
    assert all(shell.Closed() for shell in shape.Shells())


@pytest.mark.geometry
def test_every_clamp_insert_bore_clears_the_component_bore() -> None:
    """The defect that motivated the clamp-ring mount must stay impossible."""
    from satellite1_ultra.geometry import _bolt_points, _depth_cylinder

    p = DEFAULT_PARAMETERS
    for mount in acoustic_mounts(p).values():
        bore = _depth_cylinder(
            mount.bore_diameter / 2.0, -1.0, mount.pad_depth + 3.0, mount.face_point, mount.inward
        )
        for point in _bolt_points(mount.face_point, mount.inward, mount.bolt_circle):
            insert = _depth_cylinder(
                p.insert_bore_diameter / 2.0,
                mount.ledge_depth,
                p.insert_bore_depth,
                point,
                mount.inward,
            )
            assert insert.intersect(bore).Volume() == pytest.approx(0.0, abs=1e-6)


@pytest.mark.geometry
@pytest.mark.requires_official_assets
def test_divider_seats_on_the_official_mid_plate_without_interference() -> None:
    from satellite1_ultra.validation import _min_distance

    divider = pressure_divider()
    mid_plate = load_part(MID_PLATE)
    assert divider.intersect(mid_plate).Volume() < 0.01
    assert _min_distance(divider, mid_plate) == pytest.approx(0.0, abs=1e-6)


@pytest.mark.geometry
def test_functional_assembly_has_only_classified_interference() -> None:
    from satellite1_ultra.validation import INTENDED_CONTACTS

    parts = placed_functional_parts()
    detected: set[frozenset[str]] = set()
    for (first_name, first), (second_name, second) in combinations(parts.items(), 2):
        volume = first.intersect(second).Volume()
        pair = frozenset((first_name, second_name))
        if volume > 0.01:
            detected.add(pair)
            assert pair in INTENDED_CONTACTS, (
                f"invalid collision: {first_name}/{second_name} = {volume:.3f} mm^3"
            )
    assert detected == set(INTENDED_CONTACTS)


def test_rounded_rect_stations_walk_the_whole_perimeter() -> None:
    stations = rounded_rect_stations(192.0, 212.0, 34.0, 9.5)
    assert len(stations) > 60
    for x, y, _ in stations:
        assert abs(x) <= 96.001 and abs(y) <= 106.001


def test_cadquery_shape_type_contract() -> None:
    assert isinstance(main_cabinet(), cq.Shape)
