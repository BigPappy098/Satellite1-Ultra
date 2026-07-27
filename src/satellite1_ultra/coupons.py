"""Parametric fit-test coupons for calibration before full-size printing."""

from __future__ import annotations

from math import cos, pi, sin
from typing import cast

import cadquery as cq

from satellite1_ultra.geometry import DEFAULT_PARAMETERS, DesignParameters, rounded_prism


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
    return coupon


def _component_seat_coupon(
    pad_diameter: float,
    seat_diameter: float,
    seat_depth: float,
    bore_diameter: float,
    bolt_circle: float,
    ledge_diameter: float,
    ledge_depth: float,
    parameters: DesignParameters,
) -> cq.Shape:
    """A one-to-one slice of the real cabinet mount: ledge, seat, bore, inserts."""
    p = parameters
    thickness = max(ledge_depth + p.insert_bore_depth + p.pad_backing, seat_depth + p.pad_backing)
    coupon = cq.Workplane("XY").circle(pad_diameter / 2.0).extrude(thickness)
    if ledge_diameter:
        coupon = coupon.cut(
            cq.Workplane("XY", origin=(0.0, 0.0, thickness - ledge_depth))
            .circle(ledge_diameter / 2.0)
            .extrude(ledge_depth)
        )
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
    return _component_seat_coupon(
        p.driver_pad_diameter,
        p.driver_seat_diameter,
        p.driver_seat_depth,
        p.driver_bore_diameter,
        p.driver_clamp_bolt_circle,
        0.0,
        0.0,
        p,
    )


def passive_radiator_coupon(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> cq.Shape:
    """SB12PACR-00 ledge, seat, bore, clamp-ring bolt circle and insert coupon."""
    p = parameters
    return _component_seat_coupon(
        p.pr_pad_diameter,
        p.pr_seat_diameter,
        p.pr_seat_depth,
        p.pr_bore_diameter,
        p.pr_clamp_bolt_circle,
        p.pr_ledge_diameter,
        p.pr_ledge_depth,
        p,
    )


def heat_set_insert_coupon(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> cq.Shape:
    """Four blind M3 insert bores spanning nominal diameter compensation."""
    _ = parameters
    coupon = cast(
        cq.Shape,
        cq.Workplane("XY").box(60.0, 20.0, 10.0, centered=(True, True, False)).val(),
    )
    for x, diameter in zip((-22.5, -7.5, 7.5, 22.5), (4.0, 4.1, 4.2, 4.3), strict=True):
        coupon = coupon.cut(
            cq.Solid.makeCylinder(
                diameter / 2.0,
                6.5,
                cq.Vector(x, 0.0, 10.0),
                cq.Vector(0.0, 0.0, -1.0),
            )
        )
    return coupon


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
    return coupon


def gasket_compression_coupon_cap(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> cq.Shape:
    """Flat cap for measuring compressed thickness and compression-set behavior."""
    p = parameters
    cap = cq.Workplane("XY").box(60.0, 30.0, 3.0, centered=(True, True, False))
    return cast(
        cq.Shape,
        cap.faces(">Z")
        .workplane()
        .pushPoints([(x, y) for x in (-24.0, 24.0) for y in (-10.0, 10.0)])
        .hole(p.fastener_clearance_diameter)
        .val(),
    )


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
    return cast(
        cq.Shape,
        plate.faces(">Z").workplane().hole(p.cable_passage_diameter).val(),
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
