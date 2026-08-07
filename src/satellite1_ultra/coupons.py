"""Parametric fit-test coupons for calibration before full-size printing."""

from __future__ import annotations

from math import cos, pi, sin
from typing import cast

import cadquery as cq

from satellite1_ultra.geometry import (
    DEFAULT_PARAMETERS,
    DesignParameters,
    _depth_traced_profile,
    rounded_prism,
)


def _engrave(
    shape: cq.Shape,
    text: str,
    *,
    x: float,
    y: float,
    top_z: float,
    size: float = 4.0,
    depth: float = 0.35,
) -> cq.Shape:
    """Cut a shallow, support-free identifier into a known horizontal face."""
    letters = cq.Workplane("XY", origin=(x, y, top_z - depth)).text(text, size, depth, combine=True)
    return shape.cut(cast(cq.Shape, letters.val()))


def _engrave_arrow(
    shape: cq.Shape,
    *,
    x: float,
    y: float,
    top_z: float,
    length: float = 10.0,
    depth: float = 0.35,
) -> cq.Shape:
    """Cut a +Y orientation arrow into a known horizontal face."""
    shaft = cq.Workplane("XY", origin=(x, y, top_z - depth)).box(
        1.4, length, depth, centered=(True, False, False)
    )
    head = (
        cq.Workplane("XY", origin=(x, y + length, top_z - depth))
        .polyline([(-3.2, -3.0), (0.0, 2.0), (3.2, -3.0)])
        .close()
        .extrude(depth)
    )
    return shape.cut(cast(cq.Shape, shaft.union(head).val()))


def official_interface_coupon(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> cq.Shape:
    """Full four-point official mid-plate alignment and edge-clearance coupon."""
    p = parameters
    coupon = rounded_prism(120.0, 120.0, 3.0, 0.0, 15.0)
    recess = rounded_prism(110.6, 110.6, 1.0, 2.0, 11.0)
    coupon = coupon.cut(recess)
    for x in (-p.official_mount_x, p.official_mount_x):
        for y in (-p.official_mount_y, p.official_mount_y):
            hole = cq.Solid.makeCylinder(
                1.7,
                3.0,
                cq.Vector(x, y, 0.0),
                cq.Vector(0.0, 0.0, 1.0),
            )
            coupon = coupon.cut(hole)
    coupon = _engrave(coupon, "SAT1 INTERFACE R1", x=0.0, y=14.0, top_z=2.0, size=6.0)
    coupon = _engrave(coupon, "MEASURE XY 110.60", x=0.0, y=2.0, top_z=2.0, size=5.0)
    coupon = _engrave(coupon, "FRONT", x=0.0, y=-15.0, top_z=2.0, size=5.0)
    return _engrave_arrow(coupon, x=0.0, y=-35.0, top_z=2.0, length=10.0)


def _component_seat_coupon(
    pad_diameter: float,
    seat_diameter: float,
    seat_depth: float,
    bore_diameter: float,
    bolt_circle: float,
    ledge_diameter: float,
    ledge_depth: float,
    parameters: DesignParameters,
    seat_profile: tuple[float, ...] = (),
) -> cq.Shape:
    """A one-to-one slice of the real cabinet mount: ledge, seat, bore, inserts.

    ``seat_profile`` cuts the seat to the ND91-4's real outline, traced from
    the manufacturer's photograph: a circular body carrying four tabs. This coupon exists so a
    builder can drop the real driver in, feel whether it seats flush, and
    measure its flange thickness against a known recess depth. A round recess
    wide enough to clear the corners leaves the driver floating with roughly
    7.6 mm of slop at the flats, which measures nothing.
    """
    p = parameters
    thickness = max(ledge_depth + p.insert_bore_depth + p.pad_backing, seat_depth + p.pad_backing)
    coupon = cq.Workplane("XY").circle(pad_diameter / 2.0).extrude(thickness)
    if ledge_diameter:
        coupon = coupon.cut(
            cq.Workplane("XY", origin=(0.0, 0.0, thickness - ledge_depth))
            .circle(ledge_diameter / 2.0)
            .extrude(ledge_depth)
        )
    if seat_profile:
        coupon = coupon.cut(
            cq.Workplane("XY").add(
                _depth_traced_profile(
                    seat_profile,
                    (seat_diameter - 2.0 * parameters.print_clearance) / 2.0,
                    -(thickness - seat_depth),
                    seat_depth,
                    (0.0, 0.0, thickness),
                    (0.0, 0.0, -1.0),
                    clearance=parameters.print_clearance,
                )
            )
        )
    else:
        coupon = coupon.cut(
            cq.Workplane("XY", origin=(0.0, 0.0, thickness - seat_depth))
            .circle(seat_diameter / 2.0)
            .extrude(seat_depth)
        )
    coupon = coupon.cut(cq.Workplane("XY").circle(bore_diameter / 2.0).extrude(thickness))
    radius = bolt_circle / 2.0
    solid = cast(cq.Shape, coupon.val())
    for index in range(4):
        angle = pi / 4.0 + index * pi / 2.0
        x, y = radius * cos(angle), radius * sin(angle)
        solid = solid.cut(
            cq.Solid.makeCylinder(
                p.insert_bore_diameter / 2.0,
                p.insert_bore_depth,
                cq.Vector(x, y, thickness - ledge_depth),
                cq.Vector(0.0, 0.0, -1.0),
            )
        )
    return solid


def active_driver_coupon(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """ND91-4 seat, bore, clamp-ring bolt circle and insert fit coupon."""
    p = parameters
    coupon = _component_seat_coupon(
        p.driver_pad_diameter,
        p.driver_seat_diameter,
        p.driver_seat_depth,
        p.driver_bore_diameter,
        p.driver_clamp_bolt_circle,
        0.0,
        0.0,
        p,
        seat_profile=p.driver_frame_profile,
    )
    coupon = _engrave(
        coupon,
        "DRIVER R1",
        x=0.0,
        y=p.driver_pad_diameter / 2.0 - 5.5,
        top_z=p.driver_pad_depth,
        size=3.2,
    )
    coupon = _engrave(
        coupon,
        "FRONT",
        x=0.0,
        y=-p.driver_pad_diameter / 2.0 + 5.5,
        top_z=p.driver_pad_depth,
        size=3.2,
    )
    return coupon


def passive_radiator_coupon(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> cq.Shape:
    """Radiator ledge, seat, bore, clamp-ring bolt circle and insert coupon."""
    p = parameters
    coupon = _component_seat_coupon(
        p.pr_pad_diameter,
        p.pr_seat_diameter,
        p.pr_seat_depth,
        p.pr_bore_diameter,
        p.pr_clamp_bolt_circle,
        p.pr_ledge_diameter,
        p.pr_ledge_depth,
        p,
    )
    ledge_floor = p.pr_pad_depth - p.pr_ledge_depth
    coupon = _engrave(
        coupon,
        "PR R1",
        x=0.0,
        y=p.pr_seat_diameter / 2.0 + 4.2,
        top_z=ledge_floor,
        size=2.8,
    )
    coupon = _engrave(
        coupon,
        "FRONT",
        x=0.0,
        y=-p.pr_seat_diameter / 2.0 - 4.2,
        top_z=ledge_floor,
        size=2.8,
    )
    return coupon


def heat_set_insert_coupon(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> cq.Shape:
    """Four blind M3 insert bores spanning nominal diameter compensation."""
    _ = parameters
    coupon = cast(
        cq.Shape,
        cq.Workplane("XY").box(110.0, 32.0, 10.0, centered=(True, True, False)).val(),
    )
    for x, diameter in zip((-45.0, -30.0, -15.0, 0.0), (4.0, 4.1, 4.2, 4.3), strict=True):
        coupon = coupon.cut(
            cq.Solid.makeCylinder(
                diameter / 2.0,
                6.5,
                cq.Vector(x, 0.0, 10.0),
                cq.Vector(0.0, 0.0, -1.0),
            )
        )
        coupon = _engrave(coupon, f"{diameter:.1f}", x=x, y=-10.5, top_z=10.0, size=3.2)
    for x, diameter in zip((20.0, 35.0, 50.0), (3.4, 3.5, 3.6), strict=True):
        coupon = coupon.cut(
            cq.Solid.makeCylinder(
                diameter / 2.0,
                10.0,
                cq.Vector(x, 0.0, 0.0),
                cq.Vector(0.0, 0.0, 1.0),
            )
        )
        coupon = _engrave(coupon, f"{diameter:.1f}", x=x, y=-10.5, top_z=10.0, size=3.2)
    coupon = _engrave(coupon, "INSERT BORES", x=-22.5, y=10.5, top_z=10.0, size=3.2)
    return _engrave(coupon, "M3 CLEAR", x=35.0, y=10.5, top_z=10.0, size=3.2)


def gasket_compression_coupon_base(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> cq.Shape:
    """Base with blind inserts and 25% compression stops for a 2 mm sample."""
    p = parameters
    coupon = cast(
        cq.Shape,
        cq.Workplane("XY").box(60.0, 30.0, 8.0, centered=(True, True, False)).val(),
    )
    for y in (-10.0, 10.0):
        stop = cq.Workplane("XY", origin=(0.0, y, 8.0)).box(
            32.0,
            3.0,
            p.compressed_gasket_thickness,
            centered=(True, True, False),
        )
        coupon = coupon.fuse(cast(cq.Shape, stop.val()))
    for x in (-24.0, 24.0):
        for y in (-10.0, 10.0):
            coupon = coupon.cut(
                cq.Solid.makeCylinder(
                    p.insert_bore_diameter / 2.0,
                    p.insert_bore_depth,
                    cq.Vector(x, y, 8.0),
                    cq.Vector(0.0, 0.0, -1.0),
                )
            )
    return _engrave(coupon, "GASKET BASE R1", x=0.0, y=0.0, top_z=8.0, size=4.0)


def gasket_compression_coupon_cap(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> cq.Shape:
    """Flat cap for measuring compressed thickness and compression-set behavior."""
    p = parameters
    cap = cq.Workplane("XY").box(60.0, 30.0, 3.0, centered=(True, True, False))
    solid = cast(
        cq.Shape,
        cap.faces(">Z")
        .workplane()
        .pushPoints([(x, y) for x in (-24.0, 24.0) for y in (-10.0, 10.0)])
        .hole(p.fastener_clearance_diameter)
        .val(),
    )
    return _engrave(solid, "GASKET CAP R1", x=0.0, y=0.0, top_z=3.0, size=4.0)


def cable_passage_coupon(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> cq.Shape:
    """Divider-thickness gland interference and two-wire leak-test coupon."""
    p = parameters
    plate = cq.Workplane("XY").box(
        40.0,
        30.0,
        p.divider_thickness,
        centered=(True, True, False),
    )
    solid = cast(
        cq.Shape,
        plate.faces(">Z").workplane().hole(p.cable_passage_diameter).val(),
    )
    solid = _engrave(solid, "CABLE R1", x=0.0, y=10.0, top_z=p.divider_thickness, size=3.5)
    return _engrave(
        solid,
        f"BORE {p.cable_passage_diameter:.1f}",
        x=0.0,
        y=-10.0,
        top_z=p.divider_thickness,
        size=3.2,
    )


#: The official threaded mid-plate/lock-ring interface is deliberately absent
#: from this set. This design does not reproduce it: the official threaded
#: mid-plate, lock ring and top plate are printed from the unmodified official
#: files, so their thread fit is a property of the official geometry rather
#: than of anything derived here. The interface this design *does* derive is
#: the official four-point mount, covered by coupon_official_interface.
COUPONS = {
    "coupon_official_interface": official_interface_coupon,
    "coupon_active_driver": active_driver_coupon,
    "coupon_passive_radiator": passive_radiator_coupon,
    "coupon_heat_set_insert": heat_set_insert_coupon,
    "coupon_gasket_base": gasket_compression_coupon_base,
    "coupon_gasket_cap": gasket_compression_coupon_cap,
    "coupon_cable_passage": cable_passage_coupon,
}
