"""Parametric fit-test coupons for calibration before full-size printing."""

from __future__ import annotations

from math import cos, pi, sin
from typing import cast

import cadquery as cq

from satellite1_ultra.geometry import DEFAULT_PARAMETERS, DesignParameters, rounded_prism
from satellite1_ultra.official import SPEAKER_CHAMBER_25W, load_part


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


def threaded_interface_coupon(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> cq.Shape:
    """Exact official chamber-top engagement band, derived without redrawing."""
    _ = parameters
    chamber = load_part(SPEAKER_CHAMBER_25W)
    clip = cq.Workplane("XY", origin=(0.0, 0.0, -20.0)).box(
        120.0,
        120.0,
        20.0,
        centered=(True, True, False),
    )
    return chamber.intersect(cast(cq.Shape, clip.val()))


def active_driver_coupon(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """ND91-4 cutout, frame, and bolt-circle fit coupon."""
    p = parameters
    plate = cq.Workplane("XY").circle(p.driver_carrier_diameter / 2.0).extrude(3.0)
    plate = plate.cut(cq.Workplane("XY").circle(p.driver_print_cutout_diameter / 2.0).extrude(3.0))
    radius = p.driver_bolt_circle / 2.0
    points = [
        (radius * cos(pi / 4.0 + i * pi / 2.0), radius * sin(pi / 4.0 + i * pi / 2.0))
        for i in range(4)
    ]
    return cast(
        cq.Shape,
        plate.faces(">Z").workplane().pushPoints(points).hole(p.driver_mount_hole_diameter).val(),
    )


def passive_radiator_coupon(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> cq.Shape:
    """SB12PACR-00 cutout, frame, and bolt-circle fit coupon."""
    p = parameters
    plate = cq.Workplane("XY").circle(p.pr_carrier_diameter / 2.0).extrude(3.0)
    plate = plate.cut(cq.Workplane("XY").circle(p.pr_print_cutout_diameter / 2.0).extrude(3.0))
    radius = p.pr_bolt_circle / 2.0
    points = [
        (radius * cos(pi / 4.0 + i * pi / 2.0), radius * sin(pi / 4.0 + i * pi / 2.0))
        for i in range(4)
    ]
    return cast(
        cq.Shape,
        plate.faces(">Z").workplane().pushPoints(points).hole(p.pr_mount_hole_diameter).val(),
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
    for x, diameter in zip((-22.5, -7.5, 7.5, 22.5), (4.4, 4.5, 4.6, 4.7), strict=True):
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
                    p.insert_outer_diameter / 2.0,
                    p.insert_depth,
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
        .hole(p.driver_mount_hole_diameter)
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


COUPONS = {
    "coupon_official_interface": official_interface_coupon,
    "coupon_threaded_interface": threaded_interface_coupon,
    "coupon_active_driver": active_driver_coupon,
    "coupon_passive_radiator": passive_radiator_coupon,
    "coupon_heat_set_insert": heat_set_insert_coupon,
    "coupon_gasket_base": gasket_compression_coupon_base,
    "coupon_gasket_cap": gasket_compression_coupon_cap,
    "coupon_cable_passage": cable_passage_coupon,
}
