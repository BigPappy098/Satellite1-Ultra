"""Manufactured-geometry B-rep validation."""

from __future__ import annotations

from itertools import combinations

import cadquery as cq
import pytest

from satellite1_ultra.exporting import PARTS, print_oriented
from satellite1_ultra.geometry import (
    DEFAULT_PARAMETERS,
    SECTION_EXPONENT,
    SKIN_SEGMENTS,
    DesignParameters,
    acoustic_mounts,
    driver_keepout,
    main_cabinet,
    passive_radiator_keepout,
    placed_functional_parts,
    pressure_divider,
    rounded_prism,
    section_area,
    section_prism,
    skin_segments,
    skin_shell,
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
    """Per-axis, testing both in-plane rotations -- see PRINT-001.

    The old form compared max(x, y, z) against a scalar 256, which cannot
    represent a rectangular bed and passed a 192 x 212 mm shell that did not
    fit the target machine.
    """
    p = DEFAULT_PARAMETERS
    bed_x, bed_y, bed_z = p.build_volume_mm
    box = print_oriented(PARTS[name].builder(p)).BoundingBox()
    fits = (box.xlen <= bed_x and box.ylen <= bed_y) or (box.ylen <= bed_x and box.xlen <= bed_y)
    assert fits and box.zlen <= bed_z, (
        f"{name} is {box.xlen:.1f} x {box.ylen:.1f} x {box.zlen:.1f} mm"
    )


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
def test_official_stack_lands_on_elastomer_not_on_the_divider() -> None:
    """v2 inverts v1's requirement here, so the test has to invert with it.

    In v1 the divider boss tops seated directly on the official mid-plate. In v2
    that contact is precisely what must not exist: a rigid path there bypasses
    the isolation bushings and lets the woofer shake the microphone array. The
    bushing flanges carry the stack instead, and the divider stands clear.
    """
    from satellite1_ultra.validation import _min_distance

    p = DEFAULT_PARAMETERS
    divider = pressure_divider()
    mid_plate = load_part(MID_PLATE)
    assert divider.intersect(mid_plate).Volume() < 0.01
    # Closest approach is the mid-plate spigot bottom (-26.5) to the divider
    # slab top (-27.5). What matters is that it is a gap, not contact.
    standoff = _min_distance(divider, mid_plate)
    assert standoff >= 0.9, f"divider is only {standoff:.3f} mm below the official seat"

    # The bushing flange top must land exactly on the official seating plane.
    seat = p.official_interface_z + p.bushing_flange_thickness
    assert seat == pytest.approx(-6.8, abs=1e-9)


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


def test_section_matches_the_official_squircle() -> None:
    """The whole point of v2: our section is the official part's own curve.

    Measured off the official lock ring, the squircle is a superellipse with
    n = 4.13 to within 0.38 mm across the quarter. If SECTION_EXPONENT ever
    drifts, the printed body stops matching the official top and the design
    loses the property it exists for.
    """
    from math import cos, radians, sin

    half = 55.0
    q = SECTION_EXPONENT / (SECTION_EXPONENT - 1.0)
    # Support extents measured off the official lock ring at full width. Our
    # curve must track these to within the documented 0.38 mm fit error; the
    # corner is where the fit is loosest, which is why the official pocket is
    # offset from the real outline rather than from this idealisation.
    for angle, official in ((0.0, 55.000), (22.5, 62.453), (45.0, 66.114)):
        t = radians(angle)
        support = half * (abs(cos(t)) ** q + abs(sin(t)) ** q) ** (1.0 / q)
        assert abs(support - official) < 0.38, (
            f"{angle} deg: ours {support:.3f} vs official {official:.3f}"
        )


def test_section_prism_area_is_not_a_rounded_rectangle() -> None:
    """A superellipse encloses measurably more than a rounded rectangle."""
    prism = section_prism(152.0, 152.0, 10.0, 0.0)
    area = prism.Volume() / 10.0
    # The section is a 160-point spline through the curve, which encloses
    # about 0.57% more than the analytic superellipse.
    assert abs(area - section_area(76.0, 76.0)) < 200.0
    # 0.931 of the bounding square for n = 4.13; a 20 mm-radius rounded
    # rectangle of the same span would enclose about 0.985.
    assert 0.930 < area / (152.0 * 152.0) < 0.942


def test_skin_segments_are_each_one_printable_solid() -> None:
    """Three segments, each a single solid that fits the configured bed."""
    p = DEFAULT_PARAMETERS
    bed_x, bed_y, bed_z = p.build_volume_mm
    segments = skin_segments(p)
    assert set(segments) == set(SKIN_SEGMENTS)
    for name, shape in segments.items():
        assert len(shape.Solids()) == 1, f"{name} fragmented"
        box = shape.BoundingBox()
        fits = (box.xlen <= bed_x and box.ylen <= bed_y) or (
            box.ylen <= bed_x and box.xlen <= bed_y
        )
        assert fits and box.zlen <= bed_z, f"{name} does not fit the bed"


def test_official_top_sits_flush_in_the_flat_top() -> None:
    """The lip v2 exists to remove must stay removed."""
    from satellite1_ultra.official import official_upper_solids

    skin_top = skin_shell(DEFAULT_PARAMETERS).BoundingBox().zmax
    plate_top = official_upper_solids()["official_top_plate"].BoundingBox().zmax
    assert abs(plate_top - skin_top) < 0.05, f"{plate_top - skin_top:.3f} mm step at the junction"


def test_shoulder_screw_captures_without_clamping() -> None:
    """An ordinary M3 screw would defeat the mic isolation entirely."""
    p = DEFAULT_PARAMETERS
    head = p.shoulder_stop_z + p.shoulder_screw_length
    assert abs(head - (p.official_plate_top_z + p.shoulder_head_clearance)) < 1e-9


def test_cadquery_shape_type_contract() -> None:
    assert isinstance(main_cabinet(), cq.Shape)


def test_flat_top_is_a_closed_deck() -> None:
    """The top must be material, not a rim around an open trench.

    The flush-top measurement only checks the outer surface height, which was
    true while the hollow ran to the top plane and left a 3 mm rim with a hole
    behind it. This probes for real material across the whole annulus between
    the official pocket and the outer edge.
    """
    p = DEFAULT_PARAMETERS
    shell = skin_shell(p)
    inner_edge = p.official_half + p.official_pocket_clearance
    for fraction in (0.15, 0.5, 0.85):
        radius = inner_edge + (p.flat_top_half - inner_edge) * fraction
        probe = cq.Solid.makeBox(
            4.0,
            4.0,
            p.shell_wall_thickness - 0.4,
            cq.Vector(radius - 2.0, -2.0, p.shell_flat_top_z - p.shell_wall_thickness + 0.2),
        )
        filled = shell.intersect(probe).Volume()
        assert filled > 20.0, f"top deck is open at radius {radius:.1f} mm ({filled:.1f} mm3)"
