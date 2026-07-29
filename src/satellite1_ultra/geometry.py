"""Authoritative parametric B-rep geometry for Satellite1 Ultra.

Every manufactured part in this module is a true OpenCascade B-rep solid built
from primitive solids and booleans.  No mesh, voxel, SDF or marching-cubes
geometry is used anywhere in the manufacturing path.

Master coordinate system (see README.md):

* origin  -- centre of the official Satellite1 mid-plate interface plane
* +Z      -- upward, toward the microphones
* -Y      -- active-driver front
* +/-X    -- opposed passive radiators

Acoustic-component mounting
---------------------------

Each acoustic component (one active driver on -Y, two opposed passive radiators
on +/-X) is retained by a printed *clamp ring* that bolts into blind heat-set
inserts placed well outboard of the component bolt circle.  The component is
sandwiched:

    cabinet seat -> component gasket -> component flange -> clamp ring -> M3

The clamp ring bottoms out on a continuous cabinet land, so gasket compression
is set by geometry rather than by torque, and the acoustic pressure boundary is
one uninterrupted gasket annulus.  The component's own bolt circle is left
unused, which is what makes the mount driver-agnostic and, critically, is what
keeps every fastener feature clear of the component through-bore.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from functools import lru_cache
from math import cos, pi, sin
from typing import cast

import cadquery as cq

Vector3 = tuple[float, float, float]
SegmentFn = Callable[[float, float, float, float], tuple[float, float, float, float]]


@dataclass(frozen=True)
class DesignParameters:
    """All principal dimensions in the documented master coordinate system."""

    # --- cabinet envelope -------------------------------------------------
    outer_width: float = 160.0
    outer_depth: float = 180.0
    corner_radius: float = 20.0
    wall_thickness: float = 4.0
    acoustic_top_z: float = -33.0
    acoustic_bottom_z: float = -194.0
    acoustic_floor_thickness: float = 8.0
    divider_thickness: float = 4.0
    base_bottom_z: float = -216.0
    bottom_plate_thickness: float = 4.0

    # --- active driver ----------------------------------------------------
    driver_axis_z: float = -96.0
    driver_cutout_diameter: float = 88.5
    driver_outer_diameter: float = 103.2
    driver_flange_thickness: float = 3.0
    driver_depth: float = 62.9
    driver_clamp_ring_diameter: float = 118.0
    driver_clamp_bolt_circle: float = 112.0
    driver_pad_diameter: float = 126.0

    # --- passive radiators ------------------------------------------------
    pr_axis_z: float = -116.0
    pr_cutout_diameter: float = 102.0
    pr_outer_diameter: float = 122.0
    pr_flange_thickness: float = 4.0
    pr_depth: float = 38.3
    pr_rear_excursion: float = 9.0
    pr_clamp_ring_diameter: float = 140.0
    pr_clamp_bolt_circle: float = 130.0
    pr_pad_diameter: float = 144.0
    pr_ledge_depth: float = 5.0

    # --- shared component-mount construction ------------------------------
    clamp_ring_thickness: float = 5.0
    clamp_lip: float = 1.0
    pad_backing: float = 3.0

    # --- fasteners --------------------------------------------------------
    insert_outer_diameter: float = 4.6
    insert_bore_diameter: float = 4.2
    insert_depth: float = 5.7
    insert_bore_extra: float = 1.5
    boss_outer_diameter: float = 9.4
    fastener_clearance_diameter: float = 3.4
    fastener_head_diameter: float = 6.5

    # --- sealing ----------------------------------------------------------
    gasket_thickness: float = 2.0
    gasket_land_width: float = 4.0
    gasket_compression_fraction: float = 0.25

    # --- manufacturing allowances ----------------------------------------
    component_bore_clearance: float = 0.20
    print_clearance: float = 0.30

    # --- official interface ----------------------------------------------
    official_mount_x: float = 45.0534
    official_mount_y: float = 31.5467
    official_interface_z: float = -6.8

    # --- miscellaneous ----------------------------------------------------
    cable_passage_x: float = 34.0
    cable_passage_y: float = 64.0
    cable_passage_diameter: float = 8.0
    grille_width_margin: float = 32.0
    grille_depth_margin: float = 32.0
    shell_wall_thickness: float = 3.0
    shell_slot_width: float = 4.2
    shell_slot_pitch: float = 9.5
    shell_base_band: float = 24.0
    shell_top_band: float = 22.0
    shell_tie_band: float = 9.0
    brace_rib_width: float = 5.0
    brace_rib_depth: float = 8.0
    board_revision: str = "public_batch_1"
    ballast_mass_g: float = 1054.0

    # ------------------------------------------------------------------ #
    # Derived quantities
    # ------------------------------------------------------------------ #
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
    def cavity_bottom_z(self) -> float:
        return self.acoustic_bottom_z + self.acoustic_floor_thickness

    @property
    def compressed_gasket_thickness(self) -> float:
        return self.gasket_thickness * (1.0 - self.gasket_compression_fraction)

    @property
    def divider_bottom_z(self) -> float:
        return self.acoustic_top_z + self.compressed_gasket_thickness

    @property
    def shell_top_z(self) -> float:
        """Top rim of the outer shell; the shroud skirt starts just above it."""
        return self.acoustic_top_z + 2.0

    @property
    def shell_bottom_z(self) -> float:
        return self.base_bottom_z - 4.0

    @property
    def shell_retention_z(self) -> float:
        """Plane the shell's retention bosses start from, just above the plate."""
        return self.base_bottom_z + self.bottom_plate_thickness

    @property
    def insert_bore_depth(self) -> float:
        """Printed bore is deeper than the insert so screws cannot bottom out."""
        return self.insert_depth + self.insert_bore_extra

    # -- active driver ----------------------------------------------------
    @property
    def driver_bore_diameter(self) -> float:
        return self.driver_cutout_diameter + self.component_bore_clearance

    @property
    def driver_seat_diameter(self) -> float:
        return self.driver_outer_diameter + 2.0 * self.print_clearance

    @property
    def driver_seat_depth(self) -> float:
        """Seat sits deep enough that the clamp lip reaches the recessed flange."""
        return self.compressed_gasket_thickness + self.driver_flange_thickness + self.clamp_lip

    @property
    def driver_pad_depth(self) -> float:
        return max(
            self.insert_bore_depth + self.pad_backing,
            self.driver_seat_depth + self.pad_backing,
        )

    # -- passive radiators -------------------------------------------------
    @property
    def pr_bore_diameter(self) -> float:
        return self.pr_cutout_diameter + self.component_bore_clearance

    @property
    def pr_seat_diameter(self) -> float:
        return self.pr_outer_diameter + 2.0 * self.print_clearance

    @property
    def pr_ledge_diameter(self) -> float:
        return self.pr_clamp_ring_diameter + 2.0 * self.print_clearance

    @property
    def pr_seat_depth(self) -> float:
        return (
            self.pr_ledge_depth
            + self.compressed_gasket_thickness
            + self.pr_flange_thickness
            + self.clamp_lip
        )

    @property
    def pr_pad_depth(self) -> float:
        return max(
            self.pr_ledge_depth + self.insert_bore_depth + self.pad_backing,
            self.pr_seat_depth + self.pad_backing,
        )


DEFAULT_PARAMETERS = DesignParameters()


def validate_design_parameters(parameters: DesignParameters) -> None:
    """Reject impossible or unsupported parameter combinations before OCCT work."""
    p = parameters
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(120.0 <= p.outer_width <= 224.0, "outer_width must be 120-224 mm")
    require(140.0 <= p.outer_depth <= 224.0, "outer_depth must be 140-224 mm")
    require(2.4 <= p.wall_thickness <= 8.0, "wall_thickness must be 2.4-8.0 mm")
    require(
        p.wall_thickness + 4.0 < p.corner_radius < min(p.outer_width, p.outer_depth) / 2.0,
        "corner_radius must clear the wall and remain below half the enclosure span",
    )
    require(
        120.0 <= p.acoustic_top_z - p.acoustic_bottom_z <= 210.0,
        "acoustic chamber height must be 120-210 mm",
    )
    require(
        p.base_bottom_z < p.acoustic_bottom_z < p.acoustic_top_z < p.official_interface_z,
        "Z planes must order base < acoustic bottom < acoustic top < official interface",
    )
    require(p.acoustic_floor_thickness >= 4.0, "acoustic_floor_thickness must be >= 4 mm")
    require(3.0 <= p.divider_thickness <= 8.0, "divider_thickness must be 3-8 mm")
    require(3.0 <= p.bottom_plate_thickness <= 8.0, "bottom_plate_thickness must be 3-8 mm")
    require(
        0.15 <= p.gasket_compression_fraction <= 0.45,
        "gasket_compression_fraction must be 0.15-0.45",
    )
    require(1.0 <= p.gasket_thickness <= 4.0, "gasket_thickness must be 1-4 mm")
    require(0.10 <= p.print_clearance <= 1.0, "print_clearance must be 0.10-1.0 mm")
    require(
        p.insert_bore_diameter < p.insert_outer_diameter,
        "insert bore must be smaller than the insert outside diameter",
    )
    require(
        p.insert_bore_depth > p.insert_depth,
        "insert bore must be deeper than the insert",
    )
    require(
        p.driver_bore_diameter < p.driver_outer_diameter < p.driver_clamp_ring_diameter,
        "active-driver bore, flange, and clamp diameters must increase in that order",
    )
    require(
        p.pr_bore_diameter < p.pr_outer_diameter < p.pr_clamp_ring_diameter,
        "passive-radiator bore, flange, and clamp diameters must increase in that order",
    )
    require(
        p.driver_pad_diameter > p.driver_clamp_ring_diameter,
        "driver pad must extend beyond the clamp ring",
    )
    require(
        p.pr_pad_diameter > p.pr_clamp_ring_diameter,
        "radiator pad must extend beyond the clamp ring",
    )
    require(
        p.outer_width + p.grille_width_margin <= 256.0
        and p.outer_depth + p.grille_depth_margin <= 256.0,
        "outer shell must fit the 256 x 256 mm build envelope",
    )
    require(p.ballast_mass_g > 0.0, "ballast_mass_g must be positive")
    if errors:
        raise ValueError("Invalid design parameters: " + "; ".join(errors))


# ---------------------------------------------------------------------- #
# Primitive helpers
# ---------------------------------------------------------------------- #
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
    start: Vector3,
    direction: Vector3,
) -> cq.Shape:
    return cq.Solid.makeCylinder(radius, length, cq.Vector(*start), cq.Vector(*direction))


def _offset(point: Vector3, direction: Vector3, distance: float) -> Vector3:
    return (
        point[0] + direction[0] * distance,
        point[1] + direction[1] * distance,
        point[2] + direction[2] * distance,
    )


def _mount_basis(inward: Vector3) -> tuple[Vector3, Vector3]:
    """Return two unit vectors spanning the plane normal to ``inward``."""
    if abs(inward[2]) > 0.5:
        raise ValueError("acoustic mounts are horizontal by design")
    return (0.0, 0.0, 1.0), (
        inward[1] * 1.0 - inward[2] * 0.0,
        inward[2] * 0.0 - inward[0] * 1.0,
        0.0,
    )


def _bolt_points(
    face_point: Vector3,
    inward: Vector3,
    bolt_circle: float,
    phase: float = pi / 4.0,
) -> tuple[Vector3, ...]:
    """Four equally spaced points on ``bolt_circle`` in the mount face plane."""
    axis_u, axis_v = _mount_basis(inward)
    radius = bolt_circle / 2.0
    points: list[Vector3] = []
    for index in range(4):
        angle = phase + index * pi / 2.0
        offset_u = radius * cos(angle)
        offset_v = radius * sin(angle)
        points.append(
            (
                face_point[0] + axis_u[0] * offset_u + axis_v[0] * offset_v,
                face_point[1] + axis_u[1] * offset_u + axis_v[1] * offset_v,
                face_point[2] + axis_u[2] * offset_u + axis_v[2] * offset_v,
            )
        )
    return tuple(points)


def _depth_cylinder(
    radius: float,
    depth_from_face: float,
    length: float,
    face_point: Vector3,
    inward: Vector3,
) -> cq.Shape:
    return _radial_cylinder(radius, length, _offset(face_point, inward, depth_from_face), inward)


# ---------------------------------------------------------------------- #
# Acoustic component mount
# ---------------------------------------------------------------------- #
@dataclass(frozen=True)
class MountSpec:
    """Complete description of one clamp-ring acoustic component mount."""

    face_point: Vector3
    inward: Vector3
    pad_diameter: float
    pad_depth: float
    ledge_diameter: float
    ledge_depth: float
    seat_diameter: float
    seat_depth: float
    bore_diameter: float
    bolt_circle: float


def driver_mount(parameters: DesignParameters = DEFAULT_PARAMETERS) -> MountSpec:
    p = parameters
    return MountSpec(
        face_point=(0.0, -p.outer_depth / 2.0, p.driver_axis_z),
        inward=(0.0, 1.0, 0.0),
        pad_diameter=p.driver_pad_diameter,
        pad_depth=p.driver_pad_depth,
        ledge_diameter=0.0,
        ledge_depth=0.0,
        seat_diameter=p.driver_seat_diameter,
        seat_depth=p.driver_seat_depth,
        bore_diameter=p.driver_bore_diameter,
        bolt_circle=p.driver_clamp_bolt_circle,
    )


def passive_radiator_mount(
    side: int,
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> MountSpec:
    if side not in (-1, 1):
        raise ValueError("side must be -1 or +1")
    p = parameters
    return MountSpec(
        face_point=(side * p.outer_width / 2.0, 0.0, p.pr_axis_z),
        inward=(-float(side), 0.0, 0.0),
        pad_diameter=p.pr_pad_diameter,
        pad_depth=p.pr_pad_depth,
        ledge_diameter=p.pr_ledge_diameter,
        ledge_depth=p.pr_ledge_depth,
        seat_diameter=p.pr_seat_diameter,
        seat_depth=p.pr_seat_depth,
        bore_diameter=p.pr_bore_diameter,
        bolt_circle=p.pr_clamp_bolt_circle,
    )


def acoustic_mounts(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> dict[str, MountSpec]:
    return {
        "active_driver": driver_mount(parameters),
        "pr_-1": passive_radiator_mount(-1, parameters),
        "pr_+1": passive_radiator_mount(1, parameters),
    }


def _apply_mount(
    cabinet: cq.Shape,
    envelope: cq.Shape,
    mount: MountSpec,
    parameters: DesignParameters,
) -> cq.Shape:
    """Fuse the internal mounting pad, then cut ledge, seat, bore and inserts."""
    p = parameters
    face, inward = mount.face_point, mount.inward

    pad = _depth_cylinder(mount.pad_diameter / 2.0, 0.0, mount.pad_depth, face, inward)
    cabinet = cabinet.fuse(pad.intersect(envelope))

    if mount.ledge_diameter > 0.0:
        cabinet = cabinet.cut(
            _depth_cylinder(
                mount.ledge_diameter / 2.0,
                -1.0,
                mount.ledge_depth + 1.0,
                face,
                inward,
            )
        )
    cabinet = cabinet.cut(
        _depth_cylinder(mount.seat_diameter / 2.0, -1.0, mount.seat_depth + 1.0, face, inward)
    )
    cabinet = cabinet.cut(
        _depth_cylinder(mount.bore_diameter / 2.0, -1.0, mount.pad_depth + 3.0, face, inward)
    )
    for point in _bolt_points(face, inward, mount.bolt_circle):
        cabinet = cabinet.cut(
            _depth_cylinder(
                p.insert_bore_diameter / 2.0,
                mount.ledge_depth,
                p.insert_bore_depth,
                point,
                inward,
            )
        )
    return cabinet


# ---------------------------------------------------------------------- #
# Fastener patterns
# ---------------------------------------------------------------------- #
def top_fastener_positions(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> tuple[tuple[float, float], ...]:
    """Eight divider-to-cabinet fastener positions, inboard of the gasket land."""
    p = parameters
    x_edge = p.outer_width / 2.0 - 18.0
    y_edge = p.outer_depth / 2.0 - 18.0
    return (
        (-45.0, -y_edge),
        (45.0, -y_edge),
        (-45.0, y_edge),
        (45.0, y_edge),
        (-x_edge, -45.0),
        (-x_edge, 45.0),
        (x_edge, -45.0),
        (x_edge, 45.0),
    )


def base_fastener_positions(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> tuple[tuple[float, float], ...]:
    """Four base-skirt-to-cabinet fastener positions, clear of the ballast tray."""
    p = parameters
    x = p.outer_width / 2.0 - 10.0
    y = p.outer_depth / 2.0 - 20.0
    return ((-x, -y), (x, -y), (-x, y), (x, y))


def bottom_plate_fastener_positions(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> tuple[tuple[float, float], ...]:
    """Four service-plate fastener positions in the base skirt."""
    p = parameters
    x = p.outer_width / 2.0 - p.corner_radius + p.corner_radius * 0.75 / 2**0.5
    y = p.outer_depth / 2.0 - p.corner_radius + p.corner_radius * 0.75 / 2**0.5
    return ((-x, -y), (x, -y), (-x, y), (x, y))


def shroud_fastener_positions(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> tuple[tuple[float, float], ...]:
    """Four electronics-shroud fastener positions, clear of the official stack.

    They sit outboard of the official mid-plate footprint (|x|, |y| <= 55 mm)
    and inboard of the shroud's tapered inner wall at the tab height.
    """
    p = parameters
    x = p.outer_width / 2.0 - 18.0
    y = p.outer_depth / 2.0 - 26.0
    return ((-x, 0.0), (x, 0.0), (0.0, -y), (0.0, y))


def cage_fastener_positions(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> tuple[tuple[float, float], ...]:
    """Four grille-cage retention positions on the bottom service plate."""
    p = parameters
    x = p.outer_width / 2.0 - 12.0
    y = p.outer_depth / 2.0 - 18.0
    return ((-x, 0.0), (x, 0.0), (0.0, -y), (0.0, y))


def official_mount_positions(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> tuple[tuple[float, float], ...]:
    """The four official mid-plate mount points, DERIVED_FROM_OFFICIAL_CAD."""
    p = parameters
    return tuple(
        (x, y)
        for x in (-p.official_mount_x, p.official_mount_x)
        for y in (-p.official_mount_y, p.official_mount_y)
    )


def _blind_insert(
    x: float,
    y: float,
    z: float,
    direction: float,
    parameters: DesignParameters,
) -> cq.Shape:
    return cq.Solid.makeCylinder(
        parameters.insert_bore_diameter / 2.0,
        parameters.insert_bore_depth,
        cq.Vector(x, y, z),
        cq.Vector(0.0, 0.0, direction),
    )


def _compression_stop(
    x: float,
    y: float,
    z: float,
    direction: float,
    radius: float,
    parameters: DesignParameters,
) -> cq.Shape:
    """Local raised land that hard-stops a bolted joint at target compression.

    It is an annulus, not a disc: a solid stop would cap the blind insert bore
    underneath it and the screw could never reach the insert.
    """
    p = parameters
    outer = cq.Solid.makeCylinder(
        radius,
        p.compressed_gasket_thickness,
        cq.Vector(x, y, z),
        cq.Vector(0.0, 0.0, direction),
    )
    bore = cq.Solid.makeCylinder(
        p.insert_bore_diameter / 2.0,
        p.compressed_gasket_thickness,
        cq.Vector(x, y, z),
        cq.Vector(0.0, 0.0, direction),
    )
    return outer.cut(bore)


# ---------------------------------------------------------------------- #
# Structural cabinet
# ---------------------------------------------------------------------- #
@lru_cache(maxsize=16)
def main_cabinet(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Structural acoustic cabinet: walls, floor, mounts, bracing, interfaces."""
    p = parameters
    height = p.acoustic_top_z - p.acoustic_bottom_z
    envelope = rounded_prism(
        p.outer_width,
        p.outer_depth,
        height,
        p.acoustic_bottom_z,
        p.corner_radius,
    )
    cavity = rounded_prism(
        p.inner_width,
        p.inner_depth,
        p.acoustic_top_z - p.cavity_bottom_z + 1.0,
        p.cavity_bottom_z,
        p.inner_corner_radius,
    )
    cabinet = envelope.cut(cavity)

    # Vertical wall ribs. Two per wall, clear of every component envelope.
    rib_height = p.acoustic_top_z - p.cavity_bottom_z
    half_width = p.inner_width / 2.0
    half_depth = p.inner_depth / 2.0
    for offset in (-56.0, 56.0):
        inset = p.brace_rib_depth / 2.0
        across = (p.brace_rib_width, p.brace_rib_depth)
        along = (p.brace_rib_depth, p.brace_rib_width)
        for centre, size in (
            ((offset, -half_depth + inset), across),
            ((offset, half_depth - inset), across),
            ((-half_width + inset, offset), along),
            ((half_width - inset, offset), along),
        ):
            rib = cq.Workplane("XY", origin=(centre[0], centre[1], p.cavity_bottom_z)).box(
                size[0],
                size[1],
                rib_height,
                centered=(True, True, False),
            )
            cabinet = cabinet.fuse(cast(cq.Shape, rib.val()))

    # Rear structural spine, tying the rear panel to floor and top rim.
    spine = cq.Workplane(
        "XY",
        origin=(0.0, half_depth - 5.0, p.cavity_bottom_z),
    ).box(20.0, 10.0, rib_height, centered=(True, True, False))
    cabinet = cabinet.fuse(cast(cq.Shape, spine.val()))

    # Acoustic component mounts.
    for mount in acoustic_mounts(p).values():
        cabinet = _apply_mount(cabinet, envelope, mount, p)

    # Divider interface: gasket land, compression stops, blind inserts. The
    # fastener bosses sit inboard of the gasket land so they cannot interrupt
    # it, so each one is tied back to its wall by a web under the rim.
    boss_height = 10.0
    for x, y in top_fastener_positions(p):
        boss = cq.Solid.makeCylinder(
            p.boss_outer_diameter / 2.0,
            boss_height,
            cq.Vector(x, y, p.acoustic_top_z - boss_height),
            cq.Vector(0.0, 0.0, 1.0),
        )
        if abs(y) > abs(x):
            wall_y = (half_depth + p.wall_thickness) * (1.0 if y > 0 else -1.0)
            web = cq.Workplane(
                "XY", origin=((x, (y + wall_y) / 2.0, p.acoustic_top_z - boss_height))
            ).box(8.0, abs(wall_y - y), boss_height, centered=(True, True, False))
        else:
            wall_x = (half_width + p.wall_thickness) * (1.0 if x > 0 else -1.0)
            web = cq.Workplane(
                "XY", origin=(((x + wall_x) / 2.0, y, p.acoustic_top_z - boss_height))
            ).box(abs(wall_x - x), 8.0, boss_height, centered=(True, True, False))
        cabinet = cabinet.fuse(boss).fuse(cast(cq.Shape, web.val()))
        cabinet = cabinet.fuse(_compression_stop(x, y, p.acoustic_top_z, 1.0, 3.0, p))
        cabinet = cabinet.cut(_blind_insert(x, y, p.acoustic_top_z, -1.0, p))

    # Base-skirt interface: local floor pads keep the blind bores well clear of
    # the acoustic floor's inner face.
    for x, y in base_fastener_positions(p):
        pad = cq.Solid.makeCylinder(
            8.0,
            4.0,
            cq.Vector(x, y, p.cavity_bottom_z),
            cq.Vector(0.0, 0.0, 1.0),
        )
        cabinet = cabinet.fuse(pad)
        cabinet = cabinet.cut(_blind_insert(x, y, p.acoustic_bottom_z, 1.0, p))

    return cabinet


# ---------------------------------------------------------------------- #
# Clamp rings
# ---------------------------------------------------------------------- #
def _clamp_ring(
    outer_diameter: float,
    bore_diameter: float,
    lip_diameter: float,
    bolt_circle: float,
    parameters: DesignParameters,
) -> cq.Shape:
    """Stepped clamp ring: outer face bottoms on the cabinet, lip loads the flange."""
    p = parameters
    body = (
        cq.Workplane("XY")
        .circle(outer_diameter / 2.0)
        .circle(bore_diameter / 2.0)
        .extrude(p.clamp_ring_thickness)
    )
    lip = (
        cq.Workplane("XY", origin=(0.0, 0.0, -p.clamp_lip))
        .circle(lip_diameter / 2.0)
        .circle(bore_diameter / 2.0)
        .extrude(p.clamp_lip)
    )
    ring = cast(cq.Shape, body.val()).fuse(cast(cq.Shape, lip.val()))
    radius = bolt_circle / 2.0
    for index in range(4):
        angle = pi / 4.0 + index * pi / 2.0
        x, y = radius * cos(angle), radius * sin(angle)
        ring = ring.cut(
            cq.Solid.makeCylinder(
                p.fastener_clearance_diameter / 2.0,
                p.clamp_ring_thickness,
                cq.Vector(x, y, 0.0),
                cq.Vector(0.0, 0.0, 1.0),
            )
        )
    return ring


def active_driver_clamp_ring(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Retains the active driver against its cabinet seat, glue-free."""
    p = parameters
    return _clamp_ring(
        p.driver_clamp_ring_diameter,
        p.driver_outer_diameter - 7.2,
        p.driver_outer_diameter - 0.8,
        p.driver_clamp_bolt_circle,
        p,
    )


def passive_radiator_clamp_ring(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Retains one passive radiator against its cabinet seat, glue-free."""
    p = parameters
    return _clamp_ring(
        p.pr_clamp_ring_diameter,
        p.pr_outer_diameter - 7.2,
        p.pr_outer_diameter - 0.8,
        p.pr_clamp_bolt_circle,
        p,
    )


# ---------------------------------------------------------------------- #
# Pressure divider and electronics interface
# ---------------------------------------------------------------------- #
def pressure_divider(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Airtight electronics/acoustic divider carrying the official interface."""
    p = parameters
    z0 = p.divider_bottom_z
    divider = rounded_prism(
        p.outer_width,
        p.outer_depth,
        p.divider_thickness,
        z0,
        p.corner_radius,
    )
    cable_x, cable_y = p.cable_passage_x, p.cable_passage_y
    divider = divider.cut(
        cq.Solid.makeCylinder(
            p.cable_passage_diameter / 2.0,
            p.divider_thickness,
            cq.Vector(cable_x, cable_y, z0),
            cq.Vector(0.0, 0.0, 1.0),
        )
    )
    for x, y in top_fastener_positions(p):
        divider = divider.cut(
            cq.Solid.makeCylinder(
                p.fastener_clearance_diameter / 2.0,
                p.divider_thickness,
                cq.Vector(x, y, z0),
                cq.Vector(0.0, 0.0, 1.0),
            )
        )

    # Official four-point mid-plate interface. The boss tops are coplanar with
    # the official mid-plate underside so the plate seats on material, and the
    # bosses are tied together by a rib frame so a 110 mm plate is not carried
    # on four unsupported stalks.
    interface_z = p.official_interface_z
    mounts = official_mount_positions(p)
    for x, y in mounts:
        boss = cq.Solid.makeCylinder(
            p.boss_outer_diameter / 2.0,
            interface_z - z0,
            cq.Vector(x, y, z0),
            cq.Vector(0.0, 0.0, 1.0),
        )
        divider = divider.fuse(boss)
        divider = divider.cut(_blind_insert(x, y, interface_z, -1.0, p))
    rib_top = interface_z
    rib_bottom = z0 + p.divider_thickness
    for axis in ("x", "y"):
        for sign in (-1.0, 1.0):
            if axis == "x":
                origin = (0.0, sign * p.official_mount_y, rib_bottom)
                size = (2.0 * p.official_mount_x, 5.0)
            else:
                origin = (sign * p.official_mount_x, 0.0, rib_bottom)
                size = (5.0, 2.0 * p.official_mount_y)
            rib = cq.Workplane("XY", origin=origin).box(
                size[0],
                size[1],
                rib_top - rib_bottom,
                centered=(True, True, False),
            )
            divider = divider.fuse(cast(cq.Shape, rib.val()))

    for x, y in shroud_fastener_positions(p):
        boss_top_z = z0 + p.divider_thickness + 8.0
        boss = cq.Solid.makeCylinder(
            p.boss_outer_diameter / 2.0,
            8.0,
            cq.Vector(x, y, z0 + p.divider_thickness),
            cq.Vector(0.0, 0.0, 1.0),
        )
        divider = divider.fuse(boss)
        divider = divider.cut(_blind_insert(x, y, boss_top_z, -1.0, p))
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
    """Cosmetic and structural transition from the outer shell to the official top.

    The shroud carries the visible shoulder of the product: it starts flush
    inside the outer shell's top rim, sweeps in to the official top-plate
    diameter, and leaves one controlled concentric reveal at each end. It is
    removed upward, so its widest section is its lowest.
    """
    p = parameters
    skirt_z = p.shell_top_z + 0.5
    shell_inner_width = p.outer_width + p.grille_width_margin - 2.0 * p.shell_wall_thickness
    shell_inner_depth = p.outer_depth + p.grille_depth_margin - 2.0 * p.shell_wall_thickness
    outer = rounded_loft(
        shell_inner_width - 1.0,
        shell_inner_depth - 1.0,
        p.corner_radius + 13.0,
        skirt_z,
        120.0,
        120.0,
        15.0,
        0.0,
    )
    inner = rounded_loft(
        shell_inner_width - 9.0,
        shell_inner_depth - 9.0,
        p.corner_radius + 9.0,
        skirt_z - 0.2,
        112.0,
        112.0,
        11.5,
        0.2,
    )
    shroud = outer.cut(inner)
    for x in (-30.0, 0.0, 30.0):
        vent = cq.Workplane(
            "XY",
            origin=(x, p.outer_depth / 2.0 - 4.0, -16.0),
        ).box(7.0, 24.0, 10.0, centered=(True, True, False))
        shroud = shroud.cut(cast(cq.Shape, vent.val()))
    service = cq.Workplane(
        "XY",
        origin=(0.0, p.outer_depth / 2.0 + 2.0, -24.0),
    ).box(40.0, 24.0, 12.0, centered=(True, True, False))
    shroud = shroud.cut(cast(cq.Shape, service.val()))

    tab_z = p.divider_bottom_z + p.divider_thickness + 8.0
    for x, y in shroud_fastener_positions(p):
        tab = cq.Solid.makeCylinder(5.0, 3.0, cq.Vector(x, y, tab_z), cq.Vector(0.0, 0.0, 1.0))
        hole = cq.Solid.makeCylinder(
            p.fastener_clearance_diameter / 2.0,
            3.0,
            cq.Vector(x, y, tab_z),
            cq.Vector(0.0, 0.0, 1.0),
        )
        reach = 120.0
        if x:
            bridge = cq.Workplane(
                "XY", origin=(x + reach / 2.0 * (1 if x > 0 else -1), y, tab_z)
            ).box(reach, 10.0, 3.0, centered=(True, True, False))
        else:
            bridge = cq.Workplane(
                "XY", origin=(x, y + reach / 2.0 * (1 if y > 0 else -1), tab_z)
            ).box(10.0, reach, 3.0, centered=(True, True, False))
        clipped = cast(cq.Shape, bridge.val()).intersect(outer)
        shroud = shroud.fuse(tab).fuse(clipped).cut(hole)
    return shroud


# ---------------------------------------------------------------------- #
# Replaceable seals
# ---------------------------------------------------------------------- #
def divider_gasket(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Uncompressed replaceable closed-cell divider gasket."""
    p = parameters
    margin = (p.wall_thickness - p.gasket_land_width / 2.0 - 1.0) / 2.0
    return rounded_ring(
        p.outer_width - 2.0 * margin,
        p.outer_depth - 2.0 * margin,
        p.corner_radius - margin,
        p.inner_width + 2.0 * margin,
        p.inner_depth + 2.0 * margin,
        p.inner_corner_radius + margin,
        p.gasket_thickness,
    )


def circular_gasket(
    outer_diameter: float,
    inner_diameter: float,
    thickness: float,
) -> cq.Shape:
    """Plain replaceable annular component gasket; no fastener penetrations."""
    return cast(
        cq.Shape,
        cq.Workplane("XY")
        .circle(outer_diameter / 2.0)
        .circle(inner_diameter / 2.0)
        .extrude(thickness)
        .val(),
    )


def component_gasket_annulus(
    component: str,
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> tuple[float, float]:
    """Inner and outer diameter of the gasket sealing one component flange.

    Single source of truth so the cut template, the solid, and the sealing
    gate can never describe different annuli.
    """
    p = parameters
    if component == "active_driver":
        return (p.driver_cutout_diameter, p.driver_outer_diameter)
    if component.startswith("pr"):
        return (p.pr_bore_diameter + 3.0, p.pr_seat_diameter)
    raise ValueError(f"unknown sealed component: {component}")


def driver_gasket(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Seals the full active-driver flange, including its unused bolt circle.

    The ND91-4 carries four Ø4.0 mounting holes on a Ø93.3 circle that this
    design does not use, and they sit only 0.4 mm outboard of the cutout edge.
    An inset gasket leaves those holes opening into the gap under the flange,
    which vents the chamber straight to atmosphere through the clamp-ring
    bore.  The gasket therefore spans the whole flange underside: inner edge
    at the cutout so no gap is left, outer edge at the flange rim so the
    entire band is compressed.
    """
    inner, outer = component_gasket_annulus("active_driver", parameters)
    return circular_gasket(outer, inner, parameters.gasket_thickness)


def passive_radiator_gasket(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    inner, outer = component_gasket_annulus("pr", parameters)
    return circular_gasket(outer, inner, parameters.gasket_thickness)


def cable_gland(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Slotted TPU wire gland; two bores seal individual insulated conductors."""
    p = parameters
    body = cq.Workplane("XY").circle(4.15).extrude(p.divider_thickness)
    flange = cq.Workplane("XY", origin=(0.0, 0.0, p.divider_thickness)).circle(7.0).extrude(1.5)
    gland = body.union(flange)
    for x in (-1.4, 1.4):
        gland = gland.cut(cq.Workplane("XY", origin=(x, 0.0, 0.0)).circle(0.9).extrude(5.5))
    slot = cq.Workplane("XY", origin=(0.0, 0.0, 0.0)).box(
        4.6, 7.0, 5.5, centered=(True, False, False)
    )
    return cast(cq.Shape, gland.cut(slot).val())


def leak_test_adapter(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Temporary TPU hose adapter for a low-pressure pre-wiring leak test.

    This service tool replaces the cable gland only while the electronics are
    absent. It is never part of the operating acoustic pressure boundary.
    """
    p = parameters
    flange = cq.Workplane("XY").circle(7.0).extrude(1.5)
    body = cq.Workplane("XY", origin=(0.0, 0.0, 1.5)).circle(4.15).extrude(p.divider_thickness)
    spigot = (
        cq.Workplane("XY", origin=(0.0, 0.0, 1.5 + p.divider_thickness)).circle(2.0).extrude(12.0)
    )
    adapter = flange.union(body).union(spigot)
    hose_bore = cq.Workplane("XY").circle(1.0).extrude(1.5 + p.divider_thickness + 12.0)
    adapter = adapter.cut(hose_bore)
    for x in (-2.0, 2.0):
        wire_bore = (
            cq.Workplane("XY", origin=(x, 0.0, 0.0)).circle(0.9).extrude(1.5 + p.divider_thickness)
        )
        adapter = adapter.cut(wire_bore)
    return cast(cq.Shape, adapter.val())


# ---------------------------------------------------------------------- #
# Base, ballast and service parts
# ---------------------------------------------------------------------- #
def base_skirt(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Non-acoustic ballast/service bay, open at top and bottom for service."""
    p = parameters
    height = p.acoustic_bottom_z - p.base_bottom_z
    outer = rounded_prism(p.outer_width, p.outer_depth, height, p.base_bottom_z, p.corner_radius)
    cavity = rounded_prism(
        p.inner_width,
        p.inner_depth,
        height + 2.0,
        p.base_bottom_z - 1.0,
        p.inner_corner_radius,
    )
    skirt = outer.cut(cavity)

    # Internal bosses that bolt the skirt up into the acoustic floor.
    for x, y in base_fastener_positions(p):
        boss_bottom = p.acoustic_bottom_z - 8.0
        boss = cq.Solid.makeCylinder(
            p.boss_outer_diameter / 2.0,
            8.0,
            cq.Vector(x, y, boss_bottom),
            cq.Vector(0.0, 0.0, 1.0),
        )
        gusset = cq.Workplane("XY", origin=(x * 1.06, y * 1.06, boss_bottom)).box(
            14.0, 14.0, 8.0, centered=(True, True, False)
        )
        skirt = skirt.fuse(boss).fuse(cast(cq.Shape, gusset.val()))
        skirt = skirt.cut(
            cq.Solid.makeCylinder(
                p.fastener_clearance_diameter / 2.0,
                8.0,
                cq.Vector(x, y, boss_bottom),
                cq.Vector(0.0, 0.0, 1.0),
            )
        )
        skirt = skirt.cut(
            cq.Solid.makeCylinder(
                p.fastener_head_diameter / 2.0,
                3.0,
                cq.Vector(x, y, boss_bottom),
                cq.Vector(0.0, 0.0, 1.0),
            )
        )

    # Service-plate bosses and blind inserts.
    for x, y in bottom_plate_fastener_positions(p):
        boss_bottom_z = p.base_bottom_z + p.bottom_plate_thickness
        boss = cq.Solid.makeCylinder(
            p.boss_outer_diameter / 2.0,
            8.0,
            cq.Vector(x, y, boss_bottom_z),
            cq.Vector(0.0, 0.0, 1.0),
        )
        skirt = skirt.fuse(boss)
        skirt = skirt.cut(_blind_insert(x, y, boss_bottom_z, 1.0, p))

    # Pass-throughs for the grille-cage retention bridges. The base bay is
    # outside the acoustic pressure boundary, so these also vent it.
    for x, y in cage_fastener_positions(p):
        bridge_z = p.shell_retention_z
        length = p.outer_width
        if x:
            origin = (x / abs(x) * p.outer_width / 2.0, y, bridge_z - 1.5)
            size = (length, 13.0)
        else:
            origin = (x, y / abs(y) * p.outer_depth / 2.0, bridge_z - 1.5)
            size = (13.0, length)
        slot = cq.Workplane("XY", origin=origin).box(
            size[0], size[1], 11.0, centered=(True, True, False)
        )
        skirt = skirt.cut(cast(cq.Shape, slot.val()))

    # Rear cable/service relief.
    relief = cq.Workplane(
        "XY",
        origin=(0.0, p.outer_depth / 2.0 - 2.0, p.base_bottom_z + p.bottom_plate_thickness + 2.0),
    ).box(26.0, 12.0, 10.0, centered=(True, True, False))
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
    for x, y in bottom_plate_fastener_positions(p):
        plate = plate.cut(
            cq.Solid.makeCylinder(
                p.fastener_clearance_diameter / 2.0,
                p.bottom_plate_thickness,
                cq.Vector(x, y, 0.0),
                cq.Vector(0.0, 0.0, 1.0),
            )
        )
    for x, y in cage_fastener_positions(p):
        plate = plate.cut(
            cq.Solid.makeCylinder(
                p.fastener_clearance_diameter / 2.0,
                p.bottom_plate_thickness,
                cq.Vector(x, y, 0.0),
                cq.Vector(0.0, 0.0, 1.0),
            )
        )
        plate = plate.cut(
            cq.Solid.makeCylinder(
                p.fastener_head_diameter / 2.0,
                2.0,
                cq.Vector(x, y, 0.0),
                cq.Vector(0.0, 0.0, 1.0),
            )
        )
    return plate


def ballast_tray_extent(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> tuple[float, float]:
    """Outer width and depth of the ballast tray, clear of every base fixing."""
    p = parameters
    return (p.outer_width - 40.0, p.outer_depth - 48.0)


def ballast_plate_extent(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> tuple[float, float, float]:
    """Steel plate stack that the tray accepts: width, depth, total thickness."""
    width, depth = ballast_tray_extent(parameters)
    return (width - 10.0, depth - 10.0, 10.0)


def ballast_lid_fastener_positions(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> tuple[tuple[float, float], ...]:
    """Four lid screws carried by the tray walls, clear of the steel stack.

    Each boss straddles the middle of a wall face, so its full diameter is
    bonded to wall material.  Measuring the offset from the steel plate edge
    instead placed the bosses diagonally outside the tray body, where a
    rounded corner left them attached by a sliver.
    """
    width, depth = ballast_tray_extent(parameters)
    return (
        (-width / 2.0, 0.0),
        (width / 2.0, 0.0),
        (0.0, -depth / 2.0),
        (0.0, depth / 2.0),
    )


def ballast_cartridge(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Removable dry ballast tray with four blind insert-retained lid bosses."""
    p = parameters
    width, depth = ballast_tray_extent(p)
    tray = rounded_prism(width, depth, 14.0, 0.0, 10.0)
    cavity = rounded_prism(width - 8.0, depth - 8.0, 12.0, 2.0, 6.0)
    tray = tray.cut(cavity)
    for x, y in ballast_lid_fastener_positions(p):
        boss = cq.Solid.makeCylinder(
            p.boss_outer_diameter / 2.0,
            12.0,
            cq.Vector(x, y, 2.0),
            cq.Vector(0.0, 0.0, 1.0),
        )
        tray = tray.fuse(boss)
        tray = tray.cut(_blind_insert(x, y, 14.0, -1.0, p))
    return tray


def ballast_cartridge_lid(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Mechanically retained lid with a locating tongue; no structural glue."""
    p = parameters
    width, depth = ballast_tray_extent(p)
    flange = rounded_prism(width, depth, 2.0, 1.5, 10.0)
    tongue = rounded_prism(width - 8.6, depth - 8.6, 1.5, 0.0, 5.7)
    lid = flange.fuse(tongue)
    for x, y in ballast_lid_fastener_positions(p):
        pad = cq.Solid.makeCylinder(
            p.boss_outer_diameter / 2.0,
            2.0,
            cq.Vector(x, y, 1.5),
            cq.Vector(0.0, 0.0, 1.0),
        )
        lid = lid.fuse(pad)
        lid = lid.cut(
            cq.Solid.makeCylinder(
                (p.boss_outer_diameter + p.print_clearance) / 2.0,
                1.5,
                cq.Vector(x, y, 0.0),
                cq.Vector(0.0, 0.0, 1.0),
            )
        )
        lid = lid.cut(
            cq.Solid.makeCylinder(
                p.fastener_clearance_diameter / 2.0,
                3.5,
                cq.Vector(x, y, 0.0),
                cq.Vector(0.0, 0.0, 1.0),
            )
        )
    return lid


# ---------------------------------------------------------------------- #
# Industrial-design shell
# ---------------------------------------------------------------------- #
def _place_active_disc(shape: cq.Shape, inner_face_y: float, axis_z: float) -> cq.Shape:
    return shape.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 90.0).translate(
        cq.Vector(0.0, inner_face_y, axis_z)
    )


def _place_pr_disc(shape: cq.Shape, side: int, inner_face_x: float, axis_z: float) -> cq.Shape:
    return shape.rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), side * 90.0).translate(
        cq.Vector(side * inner_face_x, 0.0, axis_z)
    )


def rounded_rect_stations(
    width: float,
    depth: float,
    radius: float,
    pitch: float,
) -> list[tuple[float, float, float]]:
    """Walk a rounded rectangle at constant arc length.

    Returns ``(x, y, normal_angle_deg)`` stations, so grille features can be
    placed truly normal to the surface instead of radially from the centre.
    """
    from math import atan2, degrees

    a = width / 2.0 - radius
    b = depth / 2.0 - radius
    arc = pi * radius / 2.0
    perimeter = 4.0 * (a + b) + 4.0 * arc
    count = max(8, round(perimeter / pitch))
    step = perimeter / count
    stations: list[tuple[float, float, float]] = []
    for index in range(count):
        s = index * step
        remaining = s
        for segment, length in _perimeter_segments(a, b, radius, arc):
            if remaining <= length:
                x, y, nx, ny = segment(remaining, a, b, radius)
                stations.append((x, y, degrees(atan2(ny, nx))))
                break
            remaining -= length
    return stations


def _seg_right(s: float, a: float, b: float, r: float) -> tuple[float, float, float, float]:
    return (a + r, -b + s, 1.0, 0.0)


def _arc_top_right(s: float, a: float, b: float, r: float) -> tuple[float, float, float, float]:
    angle = s / r
    return (a + r * cos(angle), b + r * sin(angle), cos(angle), sin(angle))


def _seg_top(s: float, a: float, b: float, r: float) -> tuple[float, float, float, float]:
    return (a - s, b + r, 0.0, 1.0)


def _arc_top_left(s: float, a: float, b: float, r: float) -> tuple[float, float, float, float]:
    angle = pi / 2.0 + s / r
    return (-a + r * cos(angle), b + r * sin(angle), cos(angle), sin(angle))


def _seg_left(s: float, a: float, b: float, r: float) -> tuple[float, float, float, float]:
    return (-a - r, b - s, -1.0, 0.0)


def _arc_bottom_left(s: float, a: float, b: float, r: float) -> tuple[float, float, float, float]:
    angle = pi + s / r
    return (-a + r * cos(angle), -b + r * sin(angle), cos(angle), sin(angle))


def _seg_bottom(s: float, a: float, b: float, r: float) -> tuple[float, float, float, float]:
    return (-a + s, -b - r, 0.0, -1.0)


def _arc_bottom_right(s: float, a: float, b: float, r: float) -> tuple[float, float, float, float]:
    angle = 3.0 * pi / 2.0 + s / r
    return (a + r * cos(angle), -b + r * sin(angle), cos(angle), sin(angle))


def _perimeter_segments(
    a: float, b: float, r: float, arc: float
) -> tuple[tuple[SegmentFn, float], ...]:
    return (
        (_seg_right, 2.0 * b),
        (_arc_top_right, arc),
        (_seg_top, 2.0 * a),
        (_arc_top_left, arc),
        (_seg_left, 2.0 * b),
        (_arc_bottom_left, arc),
        (_seg_bottom, 2.0 * a),
        (_arc_bottom_right, arc),
    )


def outer_shell(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Removable slotted industrial-design shell.

    A single continuous rounded-rectangle volume with one seam at the base:
    solid bands top and bottom, a fine vertical slot field over the whole
    acoustic section, and a mid-height tie band so no slot runs the full
    height. The slots are placed normal to the surface, so they keep constant
    width around the corners.
    """
    p = parameters
    width = p.outer_width + p.grille_width_margin
    depth = p.outer_depth + p.grille_depth_margin
    radius = p.corner_radius + 14.0
    wall = p.shell_wall_thickness
    bottom_z = p.shell_bottom_z
    top_z = p.shell_top_z

    shell = rounded_prism(width, depth, top_z - bottom_z, bottom_z, radius).cut(
        rounded_prism(
            width - 2.0 * wall,
            depth - 2.0 * wall,
            top_z - bottom_z + 2.0,
            bottom_z - 1.0,
            radius - wall,
        )
    )

    band_bottom = bottom_z + p.shell_base_band
    band_top = top_z - p.shell_top_band
    tie_centre = (band_bottom + band_top) / 2.0
    lower = (band_bottom, tie_centre - p.shell_tie_band / 2.0)
    upper = (tie_centre + p.shell_tie_band / 2.0, band_top)

    cutters: list[cq.Shape] = []
    for x, y, angle in rounded_rect_stations(width, depth, radius, p.shell_slot_pitch):
        for low, high in (lower, upper):
            box = (
                cq.Workplane("XY")
                .box(3.0 * wall, p.shell_slot_width, high - low, centered=(True, True, False))
                .translate((0.0, 0.0, low))
                .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle)
                .translate((x, y, 0.0))
            )
            cutters.append(cast(cq.Shape, box.val()))
    shell = shell.cut(cq.Compound.makeCompound(cutters))

    for x, y in cage_fastener_positions(p):
        retention_z = p.shell_retention_z
        boss = cq.Solid.makeCylinder(
            p.boss_outer_diameter / 2.0,
            10.0,
            cq.Vector(x, y, retention_z),
            cq.Vector(0.0, 0.0, 1.0),
        )
        if x:
            target_x = (width / 2.0 - wall) * (1.0 if x > 0 else -1.0)
            bridge = cq.Workplane("XY", origin=((x + target_x) / 2.0, y, retention_z)).box(
                abs(x - target_x), 9.0, 6.0, centered=(True, True, False)
            )
        else:
            target_y = (depth / 2.0 - wall) * (1.0 if y > 0 else -1.0)
            bridge = cq.Workplane("XY", origin=(x, (y + target_y) / 2.0, retention_z)).box(
                9.0, abs(y - target_y), 6.0, centered=(True, True, False)
            )
        shell = shell.fuse(boss).fuse(cast(cq.Shape, bridge.val()))
        shell = shell.cut(_blind_insert(x, y, retention_z, 1.0, p))
    return shell


def support_polygon(parameters: DesignParameters = DEFAULT_PARAMETERS) -> tuple[float, float]:
    """Half-width and half-depth of the ground contact patch."""
    p = parameters
    return (
        (p.outer_width + p.grille_width_margin) / 2.0 - 2.0,
        (p.outer_depth + p.grille_depth_margin) / 2.0 - 2.0,
    )


def anti_slip_ring(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Stretch-fit TPU perimeter foot defining the support polygon."""
    p = parameters
    half_x, half_y = support_polygon(p)
    return rounded_ring(
        2.0 * half_x,
        2.0 * half_y,
        p.corner_radius + 12.0,
        2.0 * half_x - 7.0,
        2.0 * half_y - 7.0,
        p.corner_radius + 9.0,
        2.0,
    )


# ---------------------------------------------------------------------- #
# Component envelopes
# ---------------------------------------------------------------------- #
def driver_keepout(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Conservative ND91-4 envelope: flange, full-diameter basket collar, motor.

    The basket collar is modelled at the manufacturer's recommended cutout
    diameter for the first 8 mm behind the mounting plane, so any printed
    feature that intrudes into the cutout is detected rather than passing
    through an optimistic cone.
    """
    p = parameters
    face_y = -p.outer_depth / 2.0 + p.driver_seat_depth - p.compressed_gasket_thickness
    inward = (0.0, 1.0, 0.0)
    face: Vector3 = (0.0, face_y, p.driver_axis_z)
    flange = _depth_cylinder(
        p.driver_outer_diameter / 2.0,
        -p.driver_flange_thickness,
        p.driver_flange_thickness,
        face,
        inward,
    )
    collar = _depth_cylinder(p.driver_cutout_diameter / 2.0, 0.0, 8.0, face, inward)
    remaining = p.driver_depth - p.driver_flange_thickness - 8.0
    basket = cq.Solid.makeCone(
        p.driver_cutout_diameter / 2.0,
        21.0,
        remaining - 3.0,
        cq.Vector(*_offset(face, inward, 8.0)),
        cq.Vector(*inward),
    )
    motor = _depth_cylinder(21.0, 8.0 + remaining - 3.0, 3.0, face, inward)
    return flange.fuse(collar).fuse(basket).fuse(motor)


def passive_radiator_keepout(
    side: int,
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> cq.Shape:
    """SB12PACR-00 frame plus full rear/outward excursion and tuning-mass envelope."""
    if side not in (-1, 1):
        raise ValueError("side must be -1 or +1")
    p = parameters
    face_x = side * (p.outer_width / 2.0 - p.pr_seat_depth + p.compressed_gasket_thickness)
    inward: Vector3 = (-float(side), 0.0, 0.0)
    face: Vector3 = (face_x, 0.0, p.pr_axis_z)
    flange = _depth_cylinder(
        p.pr_outer_diameter / 2.0, -p.pr_flange_thickness, p.pr_flange_thickness, face, inward
    )
    basket = _depth_cylinder(p.pr_cutout_diameter / 2.0, 0.0, p.pr_depth, face, inward)
    rear_excursion = _depth_cylinder(18.0, p.pr_depth, p.pr_rear_excursion, face, inward)
    outward_excursion = _depth_cylinder(
        40.0, -p.pr_flange_thickness - p.pr_rear_excursion, p.pr_rear_excursion, face, inward
    )
    return flange.fuse(basket).fuse(rear_excursion).fuse(outward_excursion)


# ---------------------------------------------------------------------- #
# Assemblies
# ---------------------------------------------------------------------- #
@lru_cache(maxsize=16)
def placed_functional_parts(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> dict[str, cq.Shape]:
    """Return functional parts and component envelopes in master coordinates."""
    p = parameters
    compressed = replace(p, gasket_thickness=p.compressed_gasket_thickness)
    driver_seat_y = -p.outer_depth / 2.0 + p.driver_seat_depth
    pr_seat_x = p.outer_width / 2.0 - p.pr_seat_depth
    parts: dict[str, cq.Shape] = {
        "anti_slip_ring": anti_slip_ring(p).translate(cq.Vector(0.0, 0.0, p.shell_bottom_z - 2.0)),
        "outer_shell": outer_shell(p),
        "main_cabinet": main_cabinet(p),
        "divider_gasket": divider_gasket(compressed).translate(
            cq.Vector(0.0, 0.0, p.acoustic_top_z)
        ),
        "pressure_divider": pressure_divider(p),
        "electronics_shroud": electronics_shroud(p),
        "wire_gland": cable_gland(p).translate(
            cq.Vector(p.cable_passage_x, p.cable_passage_y, p.divider_bottom_z)
        ),
        "active_driver_gasket": _place_active_disc(
            driver_gasket(compressed), driver_seat_y, p.driver_axis_z
        ),
        "active_driver_clamp_ring": _place_active_disc(
            active_driver_clamp_ring(p), -p.outer_depth / 2.0, p.driver_axis_z
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
            cq.Vector(0.0, 0.0, p.base_bottom_z + p.bottom_plate_thickness + 12.5)
        ),
    }
    for side in (-1, 1):
        parts[f"pr_{side:+d}_gasket"] = _place_pr_disc(
            passive_radiator_gasket(compressed), side, pr_seat_x, p.pr_axis_z
        )
        parts[f"pr_{side:+d}_clamp_ring"] = _place_pr_disc(
            passive_radiator_clamp_ring(p),
            side,
            p.outer_width / 2.0 - p.pr_ledge_depth,
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


def skeleton_assembly(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Assembly:
    """Structural skeleton, excluding official upper stack and cosmetic styling."""
    p = parameters
    assembly = cq.Assembly(name="satellite1_ultra_skeleton")
    assembly.add(main_cabinet(p), name="main_cabinet", color=cq.Color(0.15, 0.17, 0.20))
    assembly.add(pressure_divider(p), name="pressure_divider", color=cq.Color(0.25, 0.28, 0.32))
    assembly.add(driver_keepout(p), name="driver_keepout", color=cq.Color(0.75, 0.35, 0.10, 0.45))
    for side in (-1, 1):
        assembly.add(
            passive_radiator_keepout(side, p),
            name=f"passive_radiator_{side:+d}_keepout",
            color=cq.Color(0.15, 0.45, 0.75, 0.45),
        )
    return assembly
