"""Authoritative parametric B-rep geometry for Satellite1 Ultra."""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import cos, pi, sin
from typing import cast

import cadquery as cq


@dataclass(frozen=True)
class DesignParameters:
    """All principal dimensions in the documented master coordinate system."""

    outer_width: float = 160.0
    outer_depth: float = 160.0
    corner_radius: float = 20.0
    wall_thickness: float = 4.0
    acoustic_top_z: float = -33.0
    acoustic_bottom_z: float = -194.0
    acoustic_floor_thickness: float = 8.0
    divider_thickness: float = 4.0
    base_bottom_z: float = -216.0
    bottom_plate_thickness: float = 4.0
    driver_axis_z: float = -88.0
    driver_cutout_diameter: float = 88.5
    driver_outer_diameter: float = 103.2
    driver_carrier_diameter: float = 108.0
    driver_bolt_circle: float = 93.3
    driver_mount_hole_diameter: float = 3.4
    driver_depth: float = 62.9
    pr_axis_z: float = -129.0
    pr_cutout_diameter: float = 102.0
    pr_outer_diameter: float = 122.0
    pr_carrier_diameter: float = 128.0
    pr_bolt_circle: float = 111.5
    pr_mount_hole_diameter: float = 3.4
    pr_depth: float = 38.3
    pr_rear_excursion: float = 9.0
    carrier_thickness: float = 6.0
    carrier_recess: float = 8.0
    insert_outer_diameter: float = 4.6
    insert_depth: float = 5.7
    boss_outer_diameter: float = 9.4
    gasket_thickness: float = 2.0
    gasket_land_width: float = 5.0
    cable_passage_diameter: float = 8.0
    official_mount_x: float = 45.0534
    official_mount_y: float = 31.5467
    gasket_compression_fraction: float = 0.25
    print_clearance: float = 0.30
    board_revision: str = "public_batch_1"
    ballast_mass_g: float = 1100.0

    @property
    def inner_width(self) -> float:
        return self.outer_width - 2.0 * self.wall_thickness

    @property
    def inner_depth(self) -> float:
        return self.outer_depth - 2.0 * self.wall_thickness

    @property
    def inner_corner_radius(self) -> float:
        return self.corner_radius - self.wall_thickness

    @property
    def compressed_gasket_thickness(self) -> float:
        return self.gasket_thickness * (1.0 - self.gasket_compression_fraction)

    @property
    def divider_bottom_z(self) -> float:
        return self.acoustic_top_z + self.compressed_gasket_thickness

    @property
    def driver_print_cutout_diameter(self) -> float:
        return self.driver_cutout_diameter + 2.0 * self.print_clearance

    @property
    def pr_print_cutout_diameter(self) -> float:
        return self.pr_cutout_diameter + 2.0 * self.print_clearance


DEFAULT_PARAMETERS = DesignParameters()


def rounded_prism(
    width: float,
    depth: float,
    height: float,
    z0: float,
    radius: float,
) -> cq.Shape:
    """Construct a selector-free rounded-rectangle prism from primitive solids."""
    if min(width, depth, height, radius) <= 0.0 or 2.0 * radius >= min(width, depth):
        raise ValueError("Invalid rounded-prism dimensions")
    result = cq.Workplane("XY", origin=(0.0, 0.0, z0)).box(
        width - 2.0 * radius,
        depth,
        height,
        centered=(True, True, False),
    )
    result = result.union(
        cq.Workplane("XY", origin=(0.0, 0.0, z0)).box(
            width,
            depth - 2.0 * radius,
            height,
            centered=(True, True, False),
        )
    )
    x = width / 2.0 - radius
    y = depth / 2.0 - radius
    for center_x in (-x, x):
        for center_y in (-y, y):
            result = result.union(
                cq.Workplane("XY", origin=(center_x, center_y, z0)).circle(radius).extrude(height)
            )
    return cast(cq.Shape, result.val())


def _radial_cylinder(
    radius: float,
    length: float,
    start: tuple[float, float, float],
    direction: tuple[float, float, float],
) -> cq.Shape:
    return cq.Solid.makeCylinder(
        radius,
        length,
        cq.Vector(*start),
        cq.Vector(*direction),
    )


def _bolt_positions(bolt_circle: float, axis_z: float) -> tuple[tuple[float, float], ...]:
    radius = bolt_circle / 2.0
    return tuple(
        (
            radius * cos(pi / 4.0 + index * pi / 2.0),
            axis_z + radius * sin(pi / 4.0 + index * pi / 2.0),
        )
        for index in range(4)
    )


def _top_fastener_positions() -> tuple[tuple[float, float], ...]:
    return (
        (-45.0, -75.3),
        (45.0, -75.3),
        (-45.0, 75.3),
        (45.0, 75.3),
        (-75.3, -45.0),
        (-75.3, 45.0),
        (75.3, -45.0),
        (75.3, 45.0),
    )


def main_cabinet(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Structural acoustic cabinet with integral floor and blind insert bosses."""
    p = parameters
    height = p.acoustic_top_z - p.acoustic_bottom_z
    outer = rounded_prism(
        p.outer_width,
        p.outer_depth,
        height,
        p.acoustic_bottom_z,
        p.corner_radius,
    )
    cavity_bottom = p.acoustic_bottom_z + p.acoustic_floor_thickness
    inner = rounded_prism(
        p.inner_width,
        p.inner_depth,
        p.acoustic_top_z - cavity_bottom + 1.0,
        cavity_bottom,
        p.inner_corner_radius,
    )
    cabinet = outer.cut(inner)

    half_depth = p.outer_depth / 2.0
    half_width = p.outer_width / 2.0
    cutter_length = p.wall_thickness + p.carrier_recess + 2.0
    cabinet = cabinet.cut(
        _radial_cylinder(
            p.driver_carrier_diameter / 2.0 + p.print_clearance,
            p.carrier_recess,
            (0.0, -half_depth, p.driver_axis_z),
            (0.0, 1.0, 0.0),
        )
    )
    cabinet = cabinet.cut(
        _radial_cylinder(
            p.driver_print_cutout_diameter / 2.0,
            cutter_length,
            (0.0, -half_depth - 1.0, p.driver_axis_z),
            (0.0, 1.0, 0.0),
        )
    )
    for side in (-1.0, 1.0):
        start_x = side * half_width
        direction = (-side, 0.0, 0.0)
        cabinet = cabinet.cut(
            _radial_cylinder(
                p.pr_carrier_diameter / 2.0 + p.print_clearance,
                p.carrier_recess,
                (start_x, 0.0, p.pr_axis_z),
                direction,
            )
        )
        cabinet = cabinet.cut(
            _radial_cylinder(
                p.pr_print_cutout_diameter / 2.0,
                cutter_length,
                (start_x + side, 0.0, p.pr_axis_z),
                direction,
            )
        )

    active_face_y = -half_depth + p.carrier_recess
    active_seat = _radial_cylinder(
        p.driver_carrier_diameter / 2.0,
        2.0,
        (0.0, active_face_y, p.driver_axis_z),
        (0.0, 1.0, 0.0),
    ).cut(
        _radial_cylinder(
            p.driver_print_cutout_diameter / 2.0,
            2.0,
            (0.0, active_face_y, p.driver_axis_z),
            (0.0, 1.0, 0.0),
        )
    )
    cabinet = cabinet.fuse(active_seat)
    active_bolt_radius = p.driver_bolt_circle / 2.0
    for index, (x, z) in enumerate(_bolt_positions(p.driver_bolt_circle, p.driver_axis_z)):
        theta = pi / 4.0 + index * pi / 2.0
        bridge_start_radius = active_bolt_radius - 3.0
        carrier_radius = p.driver_carrier_diameter / 2.0
        bridge_end_radius = carrier_radius + 4.0
        bridge_outer_y = -half_depth + 2.0
        bridge_inner_y = active_face_y + p.insert_depth + 3.0
        inner_bridge = (
            cq.Workplane("XY")
            .box(
                carrier_radius - bridge_start_radius,
                bridge_inner_y - active_face_y,
                8.0,
            )
            .translate(
                (
                    (bridge_start_radius + carrier_radius) / 2.0,
                    (active_face_y + bridge_inner_y) / 2.0,
                    0.0,
                )
            )
            .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -theta * 180.0 / pi)
            .translate((0.0, 0.0, p.driver_axis_z))
        )
        outer_bridge = (
            cq.Workplane("XY")
            .box(
                bridge_end_radius - carrier_radius,
                bridge_inner_y - bridge_outer_y,
                8.0,
            )
            .translate(
                (
                    (carrier_radius + bridge_end_radius) / 2.0,
                    (bridge_outer_y + bridge_inner_y) / 2.0,
                    0.0,
                )
            )
            .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -theta * 180.0 / pi)
            .translate((0.0, 0.0, p.driver_axis_z))
        )
        cabinet = cabinet.fuse(cast(cq.Shape, inner_bridge.val()))
        cabinet = cabinet.fuse(cast(cq.Shape, outer_bridge.val()))
        stop = _radial_cylinder(
            2.4,
            p.compressed_gasket_thickness,
            (x, active_face_y, z),
            (0.0, -1.0, 0.0),
        ).cut(
            _radial_cylinder(
                p.driver_mount_hole_diameter / 2.0,
                p.compressed_gasket_thickness,
                (x, active_face_y, z),
                (0.0, -1.0, 0.0),
            )
        )
        cabinet = cabinet.fuse(
            _radial_cylinder(
                p.boss_outer_diameter / 2.0,
                p.insert_depth + 3.0,
                (x, active_face_y, z),
                (0.0, 1.0, 0.0),
            )
        )
        cabinet = cabinet.fuse(stop)
        cabinet = cabinet.cut(
            _radial_cylinder(
                p.insert_outer_diameter / 2.0,
                p.insert_depth,
                (x, active_face_y, z),
                (0.0, 1.0, 0.0),
            )
        )

    for side in (-1.0, 1.0):
        face_x = side * (half_width - p.carrier_recess)
        direction = (-side, 0.0, 0.0)
        pr_seat = _radial_cylinder(
            p.pr_carrier_diameter / 2.0,
            2.0,
            (face_x, 0.0, p.pr_axis_z),
            direction,
        ).cut(
            _radial_cylinder(
                p.pr_print_cutout_diameter / 2.0,
                2.0,
                (face_x, 0.0, p.pr_axis_z),
                direction,
            )
        )
        cabinet = cabinet.fuse(pr_seat)
        pr_bolt_radius = p.pr_bolt_circle / 2.0
        for index, (y, z) in enumerate(_bolt_positions(p.pr_bolt_circle, p.pr_axis_z)):
            theta = pi / 4.0 + index * pi / 2.0
            bridge_start_radius = pr_bolt_radius - 3.0
            carrier_radius = p.pr_carrier_diameter / 2.0
            bridge_end_radius = carrier_radius + 4.0
            bridge_outer_x = half_width - 2.0
            bridge_inner_x = half_width - p.carrier_recess - p.insert_depth - 3.0
            inner_bridge = (
                cq.Workplane("XY")
                .box(
                    half_width - p.carrier_recess - bridge_inner_x,
                    carrier_radius - bridge_start_radius,
                    8.0,
                )
                .translate(
                    (
                        side * (half_width - p.carrier_recess + bridge_inner_x) / 2.0,
                        (bridge_start_radius + carrier_radius) / 2.0,
                        0.0,
                    )
                )
                .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), theta * 180.0 / pi)
                .translate((0.0, 0.0, p.pr_axis_z))
            )
            outer_bridge = (
                cq.Workplane("XY")
                .box(
                    bridge_outer_x - bridge_inner_x,
                    bridge_end_radius - carrier_radius,
                    8.0,
                )
                .translate(
                    (
                        side * (bridge_outer_x + bridge_inner_x) / 2.0,
                        (carrier_radius + bridge_end_radius) / 2.0,
                        0.0,
                    )
                )
                .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), theta * 180.0 / pi)
                .translate((0.0, 0.0, p.pr_axis_z))
            )
            cabinet = cabinet.fuse(cast(cq.Shape, inner_bridge.val()))
            cabinet = cabinet.fuse(cast(cq.Shape, outer_bridge.val()))
            stop = _radial_cylinder(
                3.0,
                p.compressed_gasket_thickness,
                (face_x, y, z),
                (side, 0.0, 0.0),
            ).cut(
                _radial_cylinder(
                    p.pr_mount_hole_diameter / 2.0,
                    p.compressed_gasket_thickness,
                    (face_x, y, z),
                    (side, 0.0, 0.0),
                )
            )
            cabinet = cabinet.fuse(
                _radial_cylinder(
                    p.boss_outer_diameter / 2.0,
                    p.insert_depth + 3.0,
                    (face_x, y, z),
                    direction,
                )
            )
            cabinet = cabinet.fuse(stop)
            cabinet = cabinet.cut(
                _radial_cylinder(
                    p.insert_outer_diameter / 2.0,
                    p.insert_depth,
                    (face_x, y, z),
                    direction,
                )
            )

    top_boss_height = 10.0
    for x, y in _top_fastener_positions():
        stop = cq.Solid.makeCylinder(
            3.0,
            p.compressed_gasket_thickness,
            cq.Vector(x, y, p.acoustic_top_z),
            cq.Vector(0.0, 0.0, 1.0),
        ).cut(
            cq.Solid.makeCylinder(
                p.driver_mount_hole_diameter / 2.0,
                p.compressed_gasket_thickness,
                cq.Vector(x, y, p.acoustic_top_z),
                cq.Vector(0.0, 0.0, 1.0),
            )
        )
        boss = cq.Solid.makeCylinder(
            p.boss_outer_diameter / 2.0,
            top_boss_height,
            cq.Vector(x, y, p.acoustic_top_z - top_boss_height),
            cq.Vector(0.0, 0.0, 1.0),
        )
        insert = cq.Solid.makeCylinder(
            p.insert_outer_diameter / 2.0,
            p.insert_depth,
            cq.Vector(x, y, p.acoustic_top_z),
            cq.Vector(0.0, 0.0, -1.0),
        )
        cabinet = cabinet.fuse(boss).fuse(stop).cut(insert)

    for x in (-55.0, 55.0):
        for y in (-55.0, 55.0):
            floor_insert = cq.Solid.makeCylinder(
                p.insert_outer_diameter / 2.0,
                p.insert_depth,
                cq.Vector(x, y, p.acoustic_bottom_z),
                cq.Vector(0.0, 0.0, 1.0),
            )
            cabinet = cabinet.cut(floor_insert)

    rear_spine = cq.Workplane(
        "XY",
        origin=(0.0, p.inner_depth / 2.0 - 4.0, cavity_bottom + 6.0),
    ).box(
        16.0,
        10.0,
        p.acoustic_top_z - cavity_bottom - 12.0,
        centered=(True, True, False),
    )
    cabinet = cabinet.fuse(cast(cq.Shape, rear_spine.val()))
    return cabinet


def circular_carrier(
    outer_diameter: float,
    cutout_diameter: float,
    bolt_circle: float,
    thickness: float,
    hole_diameter: float,
) -> cq.Shape:
    """Create a local, flat-on-bed annular carrier with four clearance holes."""
    carrier = (
        cq.Workplane("XY")
        .circle(outer_diameter / 2.0)
        .circle(cutout_diameter / 2.0)
        .extrude(thickness)
    )
    radius = bolt_circle / 2.0
    holes = [
        (radius * cos(pi / 4.0 + index * pi / 2.0), radius * sin(pi / 4.0 + index * pi / 2.0))
        for index in range(4)
    ]
    return cast(
        cq.Shape, carrier.faces(">Z").workplane().pushPoints(holes).hole(hole_diameter).val()
    )


def active_driver_carrier(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    p = parameters
    carrier = circular_carrier(
        p.driver_carrier_diameter,
        p.driver_print_cutout_diameter,
        p.driver_bolt_circle,
        p.carrier_thickness,
        p.driver_mount_hole_diameter,
    )
    for x, y in _bolt_positions(p.driver_bolt_circle, 0.0):
        stop = cq.Solid.makeCylinder(
            2.4,
            p.compressed_gasket_thickness,
            cq.Vector(x, y, p.carrier_thickness),
            cq.Vector(0.0, 0.0, 1.0),
        ).cut(
            cq.Solid.makeCylinder(
                p.driver_mount_hole_diameter / 2.0,
                p.compressed_gasket_thickness,
                cq.Vector(x, y, p.carrier_thickness),
                cq.Vector(0.0, 0.0, 1.0),
            )
        )
        carrier = carrier.fuse(stop)
    return carrier


def passive_radiator_carrier(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    p = parameters
    carrier = circular_carrier(
        p.pr_carrier_diameter,
        p.pr_print_cutout_diameter,
        p.pr_bolt_circle,
        p.carrier_thickness,
        p.pr_mount_hole_diameter,
    )
    for x, y in _bolt_positions(p.pr_bolt_circle, 0.0):
        stop = cq.Solid.makeCylinder(
            3.0,
            p.compressed_gasket_thickness,
            cq.Vector(x, y, p.carrier_thickness),
            cq.Vector(0.0, 0.0, 1.0),
        ).cut(
            cq.Solid.makeCylinder(
                p.pr_mount_hole_diameter / 2.0,
                p.compressed_gasket_thickness,
                cq.Vector(x, y, p.carrier_thickness),
                cq.Vector(0.0, 0.0, 1.0),
            )
        )
        carrier = carrier.fuse(stop)
    return carrier


def pressure_divider(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Airtight divider and exact official four-point mid-plate interface."""
    p = parameters
    z0 = p.divider_bottom_z
    divider = rounded_prism(
        p.outer_width,
        p.outer_depth,
        p.divider_thickness,
        z0,
        p.corner_radius,
    )
    cable_x, cable_y = 0.0, 48.0
    divider = divider.cut(
        cq.Solid.makeCylinder(
            p.cable_passage_diameter / 2.0,
            p.divider_thickness,
            cq.Vector(cable_x, cable_y, z0),
            cq.Vector(0.0, 0.0, 1.0),
        )
    )
    for x, y in _top_fastener_positions():
        divider = divider.cut(
            cq.Solid.makeCylinder(
                p.driver_mount_hole_diameter / 2.0,
                p.divider_thickness,
                cq.Vector(x, y, z0),
                cq.Vector(0.0, 0.0, 1.0),
            )
        )
    for x in (-p.official_mount_x, p.official_mount_x):
        for y in (-p.official_mount_y, p.official_mount_y):
            boss_top_z = -7.0
            boss = cq.Solid.makeCylinder(
                p.boss_outer_diameter / 2.0,
                boss_top_z - z0,
                cq.Vector(x, y, z0),
                cq.Vector(0.0, 0.0, 1.0),
            )
            insert = cq.Solid.makeCylinder(
                p.insert_outer_diameter / 2.0,
                p.insert_depth,
                cq.Vector(x, y, boss_top_z),
                cq.Vector(0.0, 0.0, -1.0),
            )
            divider = divider.fuse(boss).cut(insert)
    for x, y in ((-60.0, 0.0), (60.0, 0.0), (0.0, -60.0), (0.0, 60.0)):
        boss_top_z = z0 + p.divider_thickness + 8.0
        boss = cq.Solid.makeCylinder(
            p.boss_outer_diameter / 2.0,
            8.0,
            cq.Vector(x, y, z0 + p.divider_thickness),
            cq.Vector(0.0, 0.0, 1.0),
        )
        insert = cq.Solid.makeCylinder(
            p.insert_outer_diameter / 2.0,
            p.insert_depth,
            cq.Vector(x, y, boss_top_z),
            cq.Vector(0.0, 0.0, -1.0),
        )
        divider = divider.fuse(boss).cut(insert)
    return divider


def rounded_ring(
    outer_width: float,
    outer_depth: float,
    outer_radius: float,
    inner_width: float,
    inner_depth: float,
    inner_radius: float,
    thickness: float,
) -> cq.Shape:
    """Create a flat rounded gasket or flange ring in local print coordinates."""
    outer = rounded_prism(outer_width, outer_depth, thickness, 0.0, outer_radius)
    inner = rounded_prism(inner_width, inner_depth, thickness, 0.0, inner_radius)
    return outer.cut(inner)


def _rounded_wire(width: float, depth: float, radius: float, z: float) -> cq.Wire:
    temporary = rounded_prism(width, depth, 0.1, z, radius)
    top_face = max(temporary.Faces(), key=lambda face: face.Center().z)
    return top_face.outerWire().translate(cq.Vector(0.0, 0.0, -0.1))


def rounded_loft(
    bottom_width: float,
    bottom_depth: float,
    bottom_radius: float,
    bottom_z: float,
    top_width: float,
    top_depth: float,
    top_radius: float,
    top_z: float,
) -> cq.Shape:
    """Selector-independent solid loft between two rounded rectangles."""
    return cq.Solid.makeLoft(
        [
            _rounded_wire(bottom_width, bottom_depth, bottom_radius, bottom_z),
            _rounded_wire(top_width, top_depth, top_radius, top_z),
        ]
    )


def electronics_shroud(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Vented, removable transition around the untouched official upper stack."""
    p = parameters
    bottom_z = p.divider_bottom_z + p.divider_thickness
    outer = rounded_loft(
        p.outer_width,
        p.outer_depth,
        p.corner_radius,
        bottom_z,
        120.0,
        120.0,
        15.0,
        0.0,
    )
    inner = rounded_loft(
        p.outer_width - 8.0,
        p.outer_depth - 8.0,
        p.corner_radius - 4.0,
        bottom_z - 0.2,
        110.6,
        110.6,
        11.0,
        0.2,
    )
    shroud = outer.cut(inner)
    for x in (-30.0, 0.0, 30.0):
        vent = cq.Workplane(
            "XY",
            origin=(x, p.outer_depth / 2.0 - 10.0, -16.0),
        ).box(
            7.0,
            24.0,
            10.0,
            centered=(True, True, False),
        )
        shroud = shroud.cut(cast(cq.Shape, vent.val()))
    tab_z = bottom_z + 8.0
    for x, y in ((-60.0, 0.0), (60.0, 0.0), (0.0, -60.0), (0.0, 60.0)):
        tab = cq.Solid.makeCylinder(
            5.0,
            3.0,
            cq.Vector(x, y, tab_z),
            cq.Vector(0.0, 0.0, 1.0),
        )
        hole = cq.Solid.makeCylinder(
            p.driver_mount_hole_diameter / 2.0,
            3.0,
            cq.Vector(x, y, tab_z),
            cq.Vector(0.0, 0.0, 1.0),
        )
        if x:
            outer_x = 75.0 if x > 0 else -75.0
            bridge = cq.Workplane(
                "XY",
                origin=((x + outer_x) / 2.0, 0.0, tab_z),
            ).box(
                abs(x - outer_x),
                10.0,
                3.0,
                centered=(True, True, False),
            )
        else:
            outer_y = 75.0 if y > 0 else -75.0
            bridge = cq.Workplane(
                "XY",
                origin=(0.0, (y + outer_y) / 2.0, tab_z),
            ).box(
                10.0,
                abs(y - outer_y),
                3.0,
                centered=(True, True, False),
            )
        shroud = shroud.fuse(tab).fuse(cast(cq.Shape, bridge.val())).cut(hole)
    return shroud


def divider_gasket(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Uncompressed replaceable closed-cell divider gasket."""
    p = parameters
    gasket = rounded_ring(
        p.outer_width - 2.0,
        p.outer_depth - 2.0,
        p.corner_radius - 1.0,
        p.inner_width + 2.0,
        p.inner_depth + 2.0,
        p.inner_corner_radius + 1.0,
        p.gasket_thickness,
    )
    for x, y in _top_fastener_positions():
        gasket = gasket.cut(
            cq.Solid.makeCylinder(
                3.2,
                p.gasket_thickness,
                cq.Vector(x, y, 0.0),
                cq.Vector(0.0, 0.0, 1.0),
            )
        )
    return gasket


def circular_gasket(
    outer_diameter: float,
    inner_diameter: float,
    bolt_circle: float,
    thickness: float,
    hole_diameter: float,
) -> cq.Shape:
    """Create a replaceable annular component gasket with fastener holes."""
    return circular_carrier(
        outer_diameter,
        inner_diameter,
        bolt_circle,
        thickness,
        hole_diameter,
    )


def driver_gasket(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    p = parameters
    return circular_gasket(
        p.driver_outer_diameter,
        p.driver_print_cutout_diameter,
        p.driver_bolt_circle,
        p.gasket_thickness,
        5.2,
    )


def driver_carrier_gasket(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    p = parameters
    return circular_gasket(
        p.driver_carrier_diameter,
        p.driver_print_cutout_diameter,
        p.driver_bolt_circle,
        p.gasket_thickness,
        5.2,
    )


def passive_radiator_gasket(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    p = parameters
    return circular_gasket(
        p.pr_outer_diameter,
        p.pr_print_cutout_diameter,
        p.pr_bolt_circle,
        p.gasket_thickness,
        6.4,
    )


def passive_radiator_carrier_gasket(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> cq.Shape:
    p = parameters
    return circular_gasket(
        p.pr_carrier_diameter,
        p.pr_print_cutout_diameter,
        p.pr_bolt_circle,
        p.gasket_thickness,
        6.4,
    )


def cable_gland(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Slotted TPU wire gland; two bores seal individual insulated conductors."""
    p = parameters
    body = cq.Workplane("XY").circle(4.15).extrude(p.divider_thickness)
    flange = cq.Workplane("XY", origin=(0.0, 0.0, p.divider_thickness)).circle(7.0).extrude(1.5)
    gland = body.union(flange)
    for x in (-1.4, 1.4):
        gland = gland.cut(cq.Workplane("XY", origin=(x, 0.0, 0.0)).circle(0.9).extrude(5.5))
    slot = cq.Workplane("XY", origin=(0.0, 0.0, 0.0)).box(
        4.6,
        7.0,
        5.5,
        centered=(True, False, False),
    )
    return cast(cq.Shape, gland.cut(slot).val())


def base_skirt(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Non-acoustic ballast/service bay with independent top and bottom fasteners."""
    p = parameters
    height = p.acoustic_bottom_z - p.base_bottom_z
    outer = rounded_prism(
        p.outer_width,
        p.outer_depth,
        height,
        p.base_bottom_z,
        p.corner_radius,
    )
    cavity = rounded_prism(
        p.inner_width,
        p.inner_depth,
        height - 3.0 + 1.0,
        p.base_bottom_z - 1.0,
        p.inner_corner_radius,
    )
    skirt = outer.cut(cavity)
    ceiling = rounded_prism(
        p.outer_width,
        p.outer_depth,
        3.0,
        p.acoustic_bottom_z - 3.0,
        p.corner_radius,
    )
    skirt = skirt.fuse(ceiling)
    for x in (-55.0, 55.0):
        for y in (-55.0, 55.0):
            skirt = skirt.cut(
                cq.Solid.makeCylinder(
                    p.driver_mount_hole_diameter / 2.0,
                    3.0,
                    cq.Vector(x, y, p.acoustic_bottom_z - 3.0),
                    cq.Vector(0.0, 0.0, 1.0),
                )
            )
    corner = 60.0 + 15.0 / 2**0.5
    for x in (-corner, corner):
        for y in (-corner, corner):
            boss_bottom_z = p.base_bottom_z + p.bottom_plate_thickness
            boss = cq.Solid.makeCylinder(
                p.boss_outer_diameter / 2.0,
                8.0,
                cq.Vector(x, y, boss_bottom_z),
                cq.Vector(0.0, 0.0, 1.0),
            )
            insert = cq.Solid.makeCylinder(
                p.insert_outer_diameter / 2.0,
                p.insert_depth,
                cq.Vector(x, y, boss_bottom_z),
                cq.Vector(0.0, 0.0, 1.0),
            )
            skirt = skirt.fuse(boss).cut(insert)
    for x, y, size_x, size_y in (
        (-83.0, 0.0, 28.0, 10.0),
        (83.0, 0.0, 28.0, 10.0),
        (0.0, -83.0, 10.0, 30.0),
        (0.0, 79.0, 10.0, 22.0),
    ):
        relief = cq.Workplane(
            "XY",
            origin=(x, y, p.base_bottom_z + p.bottom_plate_thickness),
        ).box(
            size_x,
            size_y,
            8.5,
            centered=(True, True, False),
        )
        skirt = skirt.cut(cast(cq.Shape, relief.val()))
    return skirt


def bottom_service_plate(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Flush underside plate, exported in its support-free print orientation."""
    p = parameters
    clearance = p.print_clearance
    plate = rounded_prism(
        p.inner_width - 2.0 * clearance,
        p.inner_depth - 2.0 * clearance,
        p.bottom_plate_thickness,
        0.0,
        p.inner_corner_radius - clearance / 2.0,
    )
    corner = 60.0 + 15.0 / 2**0.5
    for x in (-corner, corner):
        for y in (-corner, corner):
            plate = plate.cut(
                cq.Solid.makeCylinder(
                    p.driver_mount_hole_diameter / 2.0,
                    p.bottom_plate_thickness,
                    cq.Vector(x, y, 0.0),
                    cq.Vector(0.0, 0.0, 1.0),
                )
            )
    for x, y in ((-72.0, 0.0), (72.0, 0.0), (0.0, -72.0), (0.0, 72.0)):
        plate = plate.cut(
            cq.Solid.makeCylinder(
                p.driver_mount_hole_diameter / 2.0,
                p.bottom_plate_thickness,
                cq.Vector(x, y, 0.0),
                cq.Vector(0.0, 0.0, 1.0),
            )
        )
    return plate


def ballast_cartridge(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Removable dry ballast tray for a 120 x 120 x 9 mm steel plate stack."""
    _ = parameters
    tray = rounded_prism(132.0, 132.0, 12.5, 0.0, 10.0)
    cavity = rounded_prism(124.0, 124.0, 11.0, 2.0, 6.0)
    return tray.cut(cavity)


def ballast_cartridge_lid(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Compression-retained lid with a clearance tongue; no structural glue."""
    _ = parameters
    flange = rounded_prism(132.0, 132.0, 2.0, 1.5, 10.0)
    tongue = rounded_prism(123.4, 123.4, 1.5, 0.0, 5.7)
    return flange.fuse(tongue)


def outer_grille_cage(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Removable fabric cage with hard guards over every moving diaphragm."""
    p = parameters
    width, depth, center_y, radius = 192.0, 184.0, -4.0, 28.0
    bottom_z, top_z, ring_height = p.base_bottom_z, p.acoustic_top_z, 8.0
    bottom_ring = rounded_ring(
        width,
        depth,
        radius,
        width - 4.0,
        depth - 4.0,
        radius - 2.0,
        ring_height,
    ).translate(cq.Vector(0.0, center_y, bottom_z))
    top_ring = rounded_ring(
        width,
        depth,
        radius,
        width - 4.0,
        depth - 4.0,
        radius - 2.0,
        ring_height,
    ).translate(cq.Vector(0.0, center_y, top_z - ring_height))
    cage = bottom_ring.fuse(top_ring)

    arc_center_x = width / 2.0 - radius
    arc_center_y = depth / 2.0 - radius
    rail_radius = radius - 1.0
    for x_sign in (-1.0, 1.0):
        for y_sign in (-1.0, 1.0):
            x = x_sign * (arc_center_x + rail_radius / 2**0.5)
            y = center_y + y_sign * (arc_center_y + rail_radius / 2**0.5)
            cage = cage.fuse(
                cq.Solid.makeCylinder(
                    3.0,
                    top_z - bottom_z - 10.0,
                    cq.Vector(x, y, bottom_z + 5.0),
                    cq.Vector(0.0, 0.0, 1.0),
                )
            )

    active_guard_local = cast(
        cq.Shape,
        cq.Workplane("XY").circle(59.0).circle(53.0).extrude(3.0).val(),
    )
    active_guard = _place_active_disc(
        active_guard_local,
        -93.0,
        p.driver_axis_z,
    )
    cage = cage.fuse(active_guard)
    for side in (-1, 1):
        cage = cage.fuse(
            _place_pr_disc(
                cast(
                    cq.Shape,
                    cq.Workplane("XY").circle(65.0).circle(62.0).extrude(3.0).val(),
                ),
                side,
                93.0,
                p.pr_axis_z,
            )
        )
        side_rail = cq.Workplane(
            "XY",
            origin=(side * 94.5, 0.0, bottom_z + 5.0),
        ).box(
            3.0,
            8.0,
            -186.0 - (bottom_z + 5.0),
            centered=(True, True, False),
        )
        cage = cage.fuse(cast(cq.Shape, side_rail.val()))

    for x, y in ((-72.0, 0.0), (72.0, 0.0), (0.0, -72.0), (0.0, 72.0)):
        retention_z = bottom_z + p.bottom_plate_thickness
        boss = cq.Solid.makeCylinder(
            p.boss_outer_diameter / 2.0,
            ring_height,
            cq.Vector(x, y, retention_z),
            cq.Vector(0.0, 0.0, 1.0),
        )
        if x:
            target_x = 96.0 if x > 0 else -96.0
            bridge = cq.Workplane(
                "XY",
                origin=((x + target_x) / 2.0, y, retention_z),
            ).box(
                abs(x - target_x),
                8.0,
                ring_height - p.bottom_plate_thickness,
                centered=(True, True, False),
            )
        else:
            target_y = center_y + (92.0 if y > 0 else -92.0)
            bridge = cq.Workplane(
                "XY",
                origin=(x, (y + target_y) / 2.0, retention_z),
            ).box(
                8.0,
                abs(y - target_y),
                ring_height - p.bottom_plate_thickness,
                centered=(True, True, False),
            )
        insert = cq.Solid.makeCylinder(
            p.insert_outer_diameter / 2.0,
            p.insert_depth,
            cq.Vector(x, y, retention_z),
            cq.Vector(0.0, 0.0, 1.0),
        )
        cage = cage.fuse(boss).fuse(cast(cq.Shape, bridge.val())).cut(insert)
    return cage


def anti_slip_ring(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Stretch-fit TPU perimeter foot defining the support polygon."""
    _ = parameters
    return rounded_ring(190.0, 182.0, 27.0, 184.0, 176.0, 24.0, 2.0)


def _place_active_disc(shape: cq.Shape, inner_face_y: float, axis_z: float) -> cq.Shape:
    return shape.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 90.0).translate(
        cq.Vector(0.0, inner_face_y, axis_z)
    )


def _place_pr_disc(
    shape: cq.Shape,
    side: int,
    inner_face_x: float,
    axis_z: float,
) -> cq.Shape:
    return shape.rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), side * 90.0).translate(
        cq.Vector(side * inner_face_x, 0.0, axis_z)
    )


def placed_functional_parts(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> dict[str, cq.Shape]:
    """Return functional parts and component envelopes in master coordinates."""
    p = parameters
    compressed = replace(p, gasket_thickness=p.compressed_gasket_thickness)
    pocket_bottom = p.outer_width / 2.0 - p.carrier_recess
    active_pocket_y = -pocket_bottom
    active_carrier_inner_y = active_pocket_y - p.compressed_gasket_thickness
    pr_carrier_inner_x = pocket_bottom + p.compressed_gasket_thickness
    parts: dict[str, cq.Shape] = {
        "anti_slip_ring": anti_slip_ring(p).translate(cq.Vector(0.0, -4.0, p.base_bottom_z - 2.0)),
        "outer_grille_cage": outer_grille_cage(p),
        "main_cabinet": main_cabinet(p),
        "divider_gasket": divider_gasket(compressed).translate(
            cq.Vector(0.0, 0.0, p.acoustic_top_z)
        ),
        "pressure_divider": pressure_divider(p),
        "electronics_shroud": electronics_shroud(p),
        "wire_gland": cable_gland(p).translate(cq.Vector(0.0, 48.0, p.divider_bottom_z)),
        "active_carrier_gasket": _place_active_disc(
            driver_carrier_gasket(compressed),
            active_pocket_y,
            p.driver_axis_z,
        ),
        "active_driver_carrier": _place_active_disc(
            active_driver_carrier(p),
            active_carrier_inner_y,
            p.driver_axis_z,
        ),
        "active_driver_gasket": _place_active_disc(
            driver_gasket(compressed),
            active_carrier_inner_y - p.carrier_thickness,
            p.driver_axis_z,
        ),
        "driver_envelope": driver_keepout(p),
        "base_skirt": base_skirt(p),
        "bottom_service_plate": bottom_service_plate(p).translate(
            cq.Vector(0.0, 0.0, p.base_bottom_z)
        ),
        "ballast_cartridge": ballast_cartridge(p).translate(
            cq.Vector(0.0, 0.0, p.base_bottom_z + p.bottom_plate_thickness)
        ),
        "ballast_cartridge_lid": ballast_cartridge_lid(p).translate(
            cq.Vector(0.0, 0.0, p.base_bottom_z + p.bottom_plate_thickness + 11.0)
        ),
    }
    for side in (-1, 1):
        parts[f"pr_{side:+d}_carrier_gasket"] = _place_pr_disc(
            passive_radiator_carrier_gasket(compressed),
            side,
            pocket_bottom,
            p.pr_axis_z,
        )
        parts[f"pr_{side:+d}_carrier"] = _place_pr_disc(
            passive_radiator_carrier(p),
            side,
            pr_carrier_inner_x,
            p.pr_axis_z,
        )
        parts[f"pr_{side:+d}_component_gasket"] = _place_pr_disc(
            passive_radiator_gasket(compressed),
            side,
            pr_carrier_inner_x + p.carrier_thickness,
            p.pr_axis_z,
        )
        parts[f"pr_{side:+d}_envelope"] = passive_radiator_keepout(side, p)
    return parts


def functional_assembly(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Assembly:
    """Complete functional assembly before cosmetic grille/sleeve styling."""
    colors = {
        "main_cabinet": cq.Color(0.13, 0.15, 0.18),
        "pressure_divider": cq.Color(0.25, 0.28, 0.32),
        "base_skirt": cq.Color(0.13, 0.15, 0.18),
        "bottom_service_plate": cq.Color(0.20, 0.22, 0.25),
        "ballast_cartridge": cq.Color(0.30, 0.32, 0.35),
        "ballast_cartridge_lid": cq.Color(0.35, 0.37, 0.40),
    }
    assembly = cq.Assembly(name="satellite1_ultra_functional")
    for name, shape in placed_functional_parts(parameters).items():
        if "gasket" in name or name == "wire_gland":
            color = cq.Color(0.12, 0.12, 0.12)
        elif "driver" in name:
            color = cq.Color(0.70, 0.30, 0.08)
        elif name.startswith("pr_"):
            color = cq.Color(0.12, 0.40, 0.72)
        else:
            color = colors.get(name, cq.Color(0.22, 0.24, 0.27))
        assembly.add(shape, name=name, color=color)
    return assembly


def driver_keepout(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Dimensionally conservative ND91-4 envelope derived from its drawing."""
    p = parameters
    face_y = -p.outer_depth / 2.0 - (
        p.carrier_thickness - p.carrier_recess + 2.0 * p.compressed_gasket_thickness
    )
    flange = _radial_cylinder(
        p.driver_outer_diameter / 2.0,
        5.0,
        (0.0, face_y, p.driver_axis_z),
        (0.0, -1.0, 0.0),
    )
    basket = cq.Solid.makeCone(
        44.25,
        21.0,
        57.0,
        cq.Vector(0.0, face_y, p.driver_axis_z),
        cq.Vector(0.0, 1.0, 0.0),
    )
    motor = _radial_cylinder(
        21.0,
        p.driver_depth - 57.0,
        (0.0, face_y + 57.0, p.driver_axis_z),
        (0.0, 1.0, 0.0),
    )
    return flange.fuse(basket).fuse(motor)


def passive_radiator_keepout(
    side: int,
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> cq.Shape:
    """SB12PACR-00 basket plus full rear excursion/tuning-mass envelope."""
    if side not in (-1, 1):
        raise ValueError("side must be -1 or +1")
    p = parameters
    face_x = side * (
        p.outer_width / 2.0
        + p.carrier_thickness
        - p.carrier_recess
        + 2.0 * p.compressed_gasket_thickness
    )
    direction = (-float(side), 0.0, 0.0)
    flange = _radial_cylinder(
        p.pr_outer_diameter / 2.0,
        3.0,
        (face_x, 0.0, p.pr_axis_z),
        (float(side), 0.0, 0.0),
    )
    basket = _radial_cylinder(
        p.pr_cutout_diameter / 2.0,
        p.pr_depth,
        (face_x, 0.0, p.pr_axis_z),
        direction,
    )
    excursion = _radial_cylinder(
        18.0,
        p.pr_rear_excursion,
        (face_x - side * p.pr_depth, 0.0, p.pr_axis_z),
        direction,
    )
    outward_excursion = _radial_cylinder(
        40.0,
        p.pr_rear_excursion,
        (face_x, 0.0, p.pr_axis_z),
        (float(side), 0.0, 0.0),
    )
    return flange.fuse(basket).fuse(excursion).fuse(outward_excursion)


def skeleton_assembly(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Assembly:
    """Functional Phase-3 assembly, excluding official upper stack and styling."""
    p = parameters
    assembly = cq.Assembly(name="satellite1_ultra_skeleton")
    assembly.add(main_cabinet(p), name="main_cabinet", color=cq.Color(0.15, 0.17, 0.20))
    assembly.add(pressure_divider(p), name="pressure_divider", color=cq.Color(0.25, 0.28, 0.32))
    assembly.add(
        driver_keepout(p),
        name="driver_keepout",
        color=cq.Color(0.75, 0.35, 0.10, 0.45),
    )
    for side in (-1, 1):
        assembly.add(
            passive_radiator_keepout(side, p),
            name=f"passive_radiator_{side:+d}_keepout",
            color=cq.Color(0.15, 0.45, 0.75, 0.45),
        )
    return assembly
