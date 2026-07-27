"""Authoritative parametric B-rep geometry for Satellite1 Ultra."""

from __future__ import annotations

from dataclasses import dataclass
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
    acoustic_top_z: float = -31.0
    acoustic_bottom_z: float = -194.0
    acoustic_floor_thickness: float = 6.0
    divider_thickness: float = 4.0
    base_bottom_z: float = -212.0
    bottom_plate_thickness: float = 4.0
    driver_axis_z: float = -87.0
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
    carrier_recess: float = 2.0
    insert_outer_diameter: float = 4.6
    insert_depth: float = 5.7
    boss_outer_diameter: float = 9.4
    gasket_thickness: float = 2.0
    gasket_land_width: float = 5.0
    cable_passage_diameter: float = 8.0
    official_mount_x: float = 45.0534
    official_mount_y: float = 31.5467

    @property
    def inner_width(self) -> float:
        return self.outer_width - 2.0 * self.wall_thickness

    @property
    def inner_depth(self) -> float:
        return self.outer_depth - 2.0 * self.wall_thickness

    @property
    def inner_corner_radius(self) -> float:
        return self.corner_radius - self.wall_thickness


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
            p.driver_carrier_diameter / 2.0,
            p.carrier_recess,
            (0.0, -half_depth, p.driver_axis_z),
            (0.0, 1.0, 0.0),
        )
    )
    cabinet = cabinet.cut(
        _radial_cylinder(
            p.driver_cutout_diameter / 2.0,
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
                p.pr_carrier_diameter / 2.0,
                p.carrier_recess,
                (start_x, 0.0, p.pr_axis_z),
                direction,
            )
        )
        cabinet = cabinet.cut(
            _radial_cylinder(
                p.pr_cutout_diameter / 2.0,
                cutter_length,
                (start_x + side, 0.0, p.pr_axis_z),
                direction,
            )
        )

    active_face_y = -half_depth + p.carrier_recess
    for x, z in _bolt_positions(p.driver_bolt_circle, p.driver_axis_z):
        cabinet = cabinet.fuse(
            _radial_cylinder(
                p.boss_outer_diameter / 2.0,
                p.insert_depth + 3.0,
                (x, active_face_y, z),
                (0.0, 1.0, 0.0),
            )
        )
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
        for y, z in _bolt_positions(p.pr_bolt_circle, p.pr_axis_z):
            cabinet = cabinet.fuse(
                _radial_cylinder(
                    p.boss_outer_diameter / 2.0,
                    p.insert_depth + 3.0,
                    (face_x, y, z),
                    direction,
                )
            )
            cabinet = cabinet.cut(
                _radial_cylinder(
                    p.insert_outer_diameter / 2.0,
                    p.insert_depth,
                    (face_x, y, z),
                    direction,
                )
            )
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
    return circular_carrier(
        p.driver_carrier_diameter,
        p.driver_cutout_diameter,
        p.driver_bolt_circle,
        p.carrier_thickness,
        p.driver_mount_hole_diameter,
    )


def passive_radiator_carrier(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    p = parameters
    return circular_carrier(
        p.pr_carrier_diameter,
        p.pr_cutout_diameter,
        p.pr_bolt_circle,
        p.carrier_thickness,
        p.pr_mount_hole_diameter,
    )


def pressure_divider(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Airtight divider and exact official four-point mid-plate interface."""
    p = parameters
    z0 = p.acoustic_top_z
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
    return divider


def driver_keepout(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Dimensionally conservative ND91-4 envelope derived from its drawing."""
    p = parameters
    face_y = -p.outer_depth / 2.0 - (p.carrier_thickness - p.carrier_recess)
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
    face_x = side * (p.outer_width / 2.0 + p.carrier_thickness - p.carrier_recess)
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
    return flange.fuse(basket).fuse(excursion)


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
