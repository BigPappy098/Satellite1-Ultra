"""Fit-coupon validity and official-derived interface checks."""

from __future__ import annotations

import math

import cadquery as cq
import pytest

from satellite1_ultra.configuration import load_design_parameters
from satellite1_ultra.coupons import COUPONS, active_driver_coupon, passive_radiator_coupon


@pytest.mark.geometry
@pytest.mark.parametrize("name", sorted(COUPONS))
def test_coupon_is_a_valid_single_solid(name: str) -> None:
    shape = COUPONS[name]()
    box = shape.BoundingBox()
    assert shape.isValid()
    assert len(shape.Solids()) == 1
    assert shape.Volume() > 100.0
    assert max(box.xlen, box.ylen, box.zlen) <= 256.0


def _seat_floor_depth(shape: cq.Shape, radius: float, degrees: float) -> float:
    """How far below the top face the seat floor sits, at one probe point."""
    box = shape.BoundingBox()
    x = radius * math.cos(math.radians(degrees))
    y = radius * math.sin(math.radians(degrees))
    z = box.zmax
    while z > box.zmin and not shape.isInside(cq.Vector(x, y, z)):
        z -= 0.01
    return box.zmax - z


@pytest.mark.geometry
def test_component_coupons_reproduce_the_seat_depth_they_are_meant_to_measure() -> None:
    """A coupon has to carry the cabinet's real seat depth, not merely be solid.

    The driver coupon once shipped with a 0.80 mm seat against a 5.50 mm
    design, because its recess was cut from an offset that started above the
    part. Every gate passed: they all model the cabinet, and the only coupon
    check asked whether the result was a valid single solid, which a 0.80 mm
    recess is. A builder measures flange thickness by seating the driver
    against this depth, so a coupon that lies about it is worse than none.
    """
    p = load_design_parameters()
    for coupon, seat_depth, probe_radius, name in (
        (active_driver_coupon(p), p.driver_seat_depth, 41.5, "active driver"),
        (passive_radiator_coupon(p), p.pr_seat_depth, 50.0, "passive radiator"),
    ):
        for degrees in (0.0, 45.0):
            measured = _seat_floor_depth(coupon, probe_radius, degrees)
            assert measured == pytest.approx(seat_depth, abs=0.05), (
                f"{name} coupon seat is {measured:.2f} mm deep at {degrees:.0f} deg, "
                f"but the cabinet seat is {seat_depth:.2f} mm"
            )


@pytest.mark.geometry
def test_driver_coupon_seat_follows_the_traced_frame_outline() -> None:
    """The seat must be the driver's outline, not a circle it floats in.

    Probed at a tab and mid-edge: a circular seat reads the same in both
    directions, and the ND91-4 frame differs by roughly 14 mm between them.
    """
    p = load_design_parameters()
    coupon = active_driver_coupon(p)
    box = coupon.BoundingBox()
    top = box.zmax - 0.5

    def seat_edge(degrees: float) -> float:
        dx = math.cos(math.radians(degrees))
        dy = math.sin(math.radians(degrees))
        radius = 30.0
        while radius < 60.0:
            if coupon.isInside(cq.Vector(radius * dx, radius * dy, top)):
                return radius
            radius += 0.02
        raise AssertionError(f"no seat wall found at {degrees} deg")

    tab = seat_edge(0.0)
    mid = seat_edge(45.0)
    assert tab - mid > 3.0, (
        f"seat spans {2 * tab:.2f} mm at a tab and {2 * mid:.2f} mm mid-edge; "
        "a difference this small means the seat is round, not the frame outline"
    )
    # Each direction sits one clearance outside the frame it has to accept.
    expected_tab = p.driver_outer_diameter / 2.0 + p.print_clearance
    assert tab == pytest.approx(expected_tab, abs=0.15)
