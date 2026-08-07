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
from math import copysign, cos, degrees, gamma, pi, sin, sqrt
from typing import cast

import cadquery as cq

Vector3 = tuple[float, float, float]
SegmentFn = Callable[[float, float, float, float], tuple[float, float, float, float]]

# Superellipse exponent of the official Satellite1 squircle, measured from the
# official lock ring: max fit error 0.38 mm across the quarter, against 1.00 mm
# for a best-fit rounded rectangle.  Every section of the v2 enclosure uses it,
# which is what makes the body and the official top read as a single part.
SECTION_EXPONENT = 4.13


@dataclass(frozen=True)
class DesignParameters:
    """All principal dimensions in the documented master coordinate system."""

    # --- cabinet envelope -------------------------------------------------
    # Square 160 mm cabinet inside a 184 mm body.  The Z layout is solved so
    # the gross sealed prism reproduces v1's 3.966 L on the narrower plan.
    outer_width: float = 160.0
    outer_depth: float = 160.0
    corner_radius: float = 20.0
    wall_thickness: float = 4.0
    acoustic_top_z: float = -33.0
    acoustic_bottom_z: float = -214.3
    acoustic_floor_thickness: float = 8.0
    divider_thickness: float = 4.0
    base_bottom_z: float = -236.3
    bottom_plate_thickness: float = 4.0

    # --- active driver ----------------------------------------------------
    # Driver and radiators are separated 36 mm in Z. Aligning them for a single
    # grille band made their component envelopes overlap by 338 mm^3 in the
    # cabinet corner -- the driver basket would foul a radiator basket. 36 mm is
    # the least separation that measures exactly zero overlap.
    driver_axis_z: float = -100.0
    driver_cutout_diameter: float = 76.45
    #: Across the four mounting ears.  Sets what the seat recess must clear.
    driver_outer_diameter: float = 103.2
    #: The frame between the corners.  This is the continuous surface the
    #: gasket seals against; the corners carry the mounting holes.
    driver_flange_body_diameter: float = 88.5
    #: One quadrant of the frame outline at 5 degree steps, normalised to the
    #: tab radius, traced from the product photograph. The frame is a circular
    #: body with four tabs, not a disc and not a straight-sided square.
    driver_frame_profile: tuple[float, ...] = (
        1.0000,
        0.9924,
        0.9729,
        0.9507,
        0.9315,
        0.9156,
        0.9014,
        0.8890,
        0.8791,
        0.8716,
        0.8655,
        0.8608,
        0.8583,
        0.8578,
        0.8579,
        0.8577,
        0.8573,
        0.8573,
        0.8573,
        0.8573,
        0.8573,
        0.8577,
        0.8579,
        0.8578,
        0.8583,
        0.8608,
        0.8655,
        0.8716,
        0.8791,
        0.8890,
        0.9014,
        0.9156,
        0.9315,
        0.9507,
        0.9729,
        0.9924,
        1.0000,
    )
    driver_flange_thickness: float = 3.0
    driver_depth: float = 62.9
    driver_clamp_ring_diameter: float = 118.0
    driver_clamp_bolt_circle: float = 112.0
    driver_pad_diameter: float = 126.0

    # --- passive radiators ------------------------------------------------
    # These mirror the selected radiator in config/components.yaml (currently
    # the Dayton DSA115-PR) and the mounts derived from it.  They are duplicated
    # deliberately, and test_checked_in_configuration_matches_authoritative_defaults
    # fails if a component swap leaves them behind.
    pr_axis_z: float = -136.0
    pr_cutout_diameter: float = 93.73
    pr_outer_diameter: float = 115.57
    pr_flange_thickness: float = 4.0
    pr_depth: float = 29.72
    pr_rear_excursion: float = 9.0
    pr_clamp_ring_diameter: float = 134.0
    pr_clamp_bolt_circle: float = 124.0
    pr_pad_diameter: float = 138.0
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
    # Divider boss tops drop by the isolation bushing's flange thickness so the
    # official stack still seats at -6.8 and the flat top stays flush.
    official_interface_z: float = -8.8

    # --- miscellaneous ----------------------------------------------------
    cable_passage_x: float = 34.0
    cable_passage_y: float = 64.0
    cable_passage_diameter: float = 8.0
    grille_width_margin: float = 28.0
    grille_depth_margin: float = 28.0
    shell_wall_thickness: float = 3.0
    # --- v2 monolith skin -------------------------------------------------
    # Flat top coplanar with the official top plate, so the Sat1 sits flush.
    shell_flat_top_z: float = 17.09
    shell_top_roll: float = 22.0
    shell_bottom_roll: float = 6.0
    # A true uniform gap, because the pocket is offset from the official part's
    # own outline rather than from our fitted superellipse. Dimensioning it
    # against the fit instead left 0.05 mm of radial gap at the 45 degree
    # corner, since n = 4.13 only matches the real curve to 0.38 mm.
    official_pocket_clearance: float = 0.4
    official_full_section_z: float = -7.0
    official_plate_top_z: float = 3.2
    # Grille windows over the driver and the two radiators only.
    window_diameter: float = 124.0
    shell_slot_width: float = 3.4
    shell_slot_pitch: float = 7.0
    # Fabric-wrap retention channels, cut only into the fabric part variant.
    fabric_groove_width: float = 2.2
    fabric_groove_depth: float = 1.5
    # --- skin split -------------------------------------------------------
    # Seams sit 5 mm clear of the windows so none grazes a window edge.
    seam_lower_z: float = -203.0
    seam_upper_z: float = -33.0
    lap_depth: float = 12.0
    lap_clearance: float = 0.25
    seam_wall_thickness: float = 5.0
    seam_runout: float = 4.0
    shadow_depth: float = 0.3
    shadow_height: float = 0.6
    crush_proud: float = 0.40
    crush_width: float = 3.0
    crush_length: float = 8.0
    crown_tab_radius: float = 5.0
    crown_tab_thickness: float = 3.0
    shroud_boss_height: float = 8.0
    # --- microphone isolation --------------------------------------------
    bushing_flange_thickness: float = 2.0
    bushing_flange_diameter: float = 13.0
    bushing_body_diameter: float = 8.6
    bushing_body_height: float = 3.7
    shoulder_screw_length: float = 16.0
    shoulder_screw_diameter: float = 4.0
    shoulder_head_clearance: float = 0.3
    brace_rib_width: float = 5.0
    brace_rib_depth: float = 8.0
    board_revision: str = "public_batch_1"
    ballast_mass_g: float = 867.0  # two 6 mm plates, 100 x 92 mm
    # Usable build volume, per axis, measured on the reference machine (a
    # modified Ender 5: X 220 mm, Y 200 mm, generous Z). The 188 mm body prints
    # with 6 mm of margin per side, comfortably clearing a 3 mm brim.
    build_volume_x: float = 220.0
    build_volume_y: float = 200.0
    build_volume_z: float = 250.0

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
        """The skin's flat top, coplanar with the official top plate."""
        return self.shell_flat_top_z

    @property
    def shell_bottom_z(self) -> float:
        return self.base_bottom_z - 4.0

    @property
    def body_half(self) -> float:
        """Half-size of the visible body: cabinet plus the grille margin."""
        return (self.outer_width + self.grille_width_margin) / 2.0

    @property
    def official_half(self) -> float:
        """Half-size of the official squircle the skin lands flush against."""
        return 55.0

    @property
    def flat_top_half(self) -> float:
        """Half-size where the top roll finishes and the flat top begins."""
        return self.body_half - self.shell_top_roll

    @property
    def cabinet_offset(self) -> float:
        """Radial inset from the visible body to the cabinet's outer face."""
        return self.shell_wall_thickness + self.shell_gap

    @property
    def shell_gap(self) -> float:
        """Air gap between the skin's inner face and the cabinet."""
        return self.grille_width_margin / 2.0 - self.shell_wall_thickness

    @property
    def seam_positions(self) -> tuple[float, ...]:
        return (self.seam_lower_z, self.seam_upper_z)

    @property
    def lap_mid_half(self) -> float:
        """Half-size of the lap's dividing surface, mid-way through the wall."""
        return self.body_half - self.seam_wall_thickness / 2.0

    @property
    def shoulder_stop_z(self) -> float:
        """Hard face the shoulder screw bottoms on, in the divider boss."""
        return self.official_interface_z - self.bushing_body_height

    @property
    def build_volume_mm(self) -> tuple[float, float, float]:
        """Usable build volume, per axis, for the printability gate."""
        return (self.build_volume_x, self.build_volume_y, self.build_volume_z)

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
        """Diameter that circumscribes the seat, which is a rounded square.

        The sealing gates use this as the seat's outer extent when probing for
        solid cabinet material.  The superellipse recess reaches further at the
        corners than a circle through its flats does, so returning the flats
        figure left the probes testing a ring the recess intrudes into and
        reporting a leak that is really four corner slivers.
        """
        # The tabs are the widest part, so the circumscribing diameter is the
        # component's outer diameter plus clearance on each side.
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
        p.driver_bore_diameter < p.driver_flange_body_diameter,
        "active-driver bore is wider than the flange body that has to seal against "
        "it; the driver would fall through the baffle",
    )
    require(
        p.driver_flange_body_diameter <= p.driver_outer_diameter,
        "active-driver sealing body cannot be wider than the across-ears envelope",
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


def superellipse_wire(
    half_x: float,
    half_y: float,
    z: float,
    exponent: float = SECTION_EXPONENT,
    count: int = 160,
) -> cq.Wire:
    """Closed spline approximating |x/a|^n + |y/b|^n = 1 at height *z*.

    This is the section family of the official Satellite1 squircle, measured
    from the official lock ring at n = 4.13 with a 0.38 mm maximum fit error.
    A best-fit rounded rectangle misses the same profile by 1.00 mm, so using
    the true superellipse is what lets the printed body and the official top
    read as one continuous form.
    """
    points = []
    for index in range(count):
        theta = 2.0 * pi * index / count
        c, s = cos(theta), sin(theta)
        points.append(
            cq.Vector(
                half_x * copysign(abs(c) ** (2.0 / exponent), c),
                half_y * copysign(abs(s) ** (2.0 / exponent), s),
                z,
            )
        )
    # periodic=True closes the curve itself; repeating the first point breaks it.
    return cq.Wire.assembleEdges([cq.Edge.makeSpline(points, periodic=True)])


def section_prism(
    width: float,
    depth: float,
    height: float,
    z0: float,
    exponent: float = SECTION_EXPONENT,
) -> cq.Shape:
    """Straight prism on the superellipse section.

    Replaces :func:`rounded_prism` everywhere the enclosure's visible or
    sealing geometry is concerned.  Walls are formed by scaling the half-size
    rather than true offsetting, which gives exactly the nominal thickness at
    the flat of a face and 1.20x nominal at the 45-degree corner -- thicker at
    the corners, never thinner, which is the safe direction.
    """
    if min(width, depth, height) <= 0.0:
        raise ValueError("Invalid section-prism dimensions")
    face = cq.Face.makeFromWires(superellipse_wire(width / 2.0, depth / 2.0, z0, exponent))
    return cast(cq.Shape, cq.Solid.extrudeLinear(face, cq.Vector(0.0, 0.0, height)))


def section_ring(
    outer_width: float,
    outer_depth: float,
    inner_width: float,
    inner_depth: float,
    thickness: float,
    exponent: float = SECTION_EXPONENT,
) -> cq.Shape:
    """Flat gasket or flange ring on the superellipse section."""
    outer = section_prism(outer_width, outer_depth, thickness, 0.0, exponent)
    inner = section_prism(inner_width, inner_depth, thickness + 2.0, -1.0, exponent)
    return outer.cut(inner)


def section_area(half_x: float, half_y: float, exponent: float = SECTION_EXPONENT) -> float:
    """Exact area enclosed by the superellipse, for volume solving."""
    return 4.0 * half_x * half_y * gamma(1.0 + 1.0 / exponent) ** 2 / gamma(1.0 + 2.0 / exponent)


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


def _profile_radius(profile: tuple[float, ...], theta: float) -> float:
    """Normalised frame radius at ``theta``, from the traced quadrant.

    The table covers 0 to 90 degrees; the frame is four-fold symmetric, so any
    angle folds into that range and is linearly interpolated between samples.
    """
    deg = degrees(theta) % 90.0
    step = 90.0 / (len(profile) - 1)
    index = int(deg / step)
    if index >= len(profile) - 1:
        return profile[-1]
    span = (deg - index * step) / step
    return profile[index] * (1.0 - span) + profile[index + 1] * span


def _depth_traced_profile(
    profile: tuple[float, ...],
    tab_radius: float,
    depth_from_face: float,
    length: float,
    face_point: Vector3,
    inward: Vector3,
    count: int = 288,
    clearance: float = 0.0,
) -> cq.Shape:
    """The component's real outline driven into a mount face.

    Built from the outline traced off the manufacturer's photograph rather than
    a curve fitted through two dimensions. Fitting is what went wrong twice
    here: a superellipse through 88.5 and 103.2 agrees at exactly those two
    angles and runs 0.66 mm narrow at 30 degrees, and a straight-sided rounded
    square has flats the frame does not have. The frame is a circular body
    carrying four tabs, and only the traced outline captures that.
    """
    # Own basis rather than _mount_basis, which rejects vertical directions by
    # design: the cabinet mounts are all on walls, but the coupon is built
    # looking down the Z axis.
    normal = cq.Vector(*inward).normalized()
    seed = cq.Vector(0.0, 0.0, 1.0)
    if abs(normal.z) > 0.9:
        seed = cq.Vector(1.0, 0.0, 0.0)
    u_vec = normal.cross(seed).normalized()
    v_vec = normal.cross(u_vec).normalized()
    u = (u_vec.x, u_vec.y, u_vec.z)
    v = (v_vec.x, v_vec.y, v_vec.z)
    start = _offset(face_point, inward, depth_from_face)
    points = []
    for index in range(count):
        theta = 2.0 * pi * index / count
        # Added, not scaled: scaling the profile would shrink the gap on the
        # body in proportion to its smaller radius, leaving 0.26 mm where the
        # tabs get 0.30.
        r = tab_radius * _profile_radius(profile, theta) + clearance
        du, dv = r * cos(theta), r * sin(theta)
        points.append(
            cq.Vector(
                start[0] + u[0] * du + v[0] * dv,
                start[1] + u[1] * du + v[1] * dv,
                start[2] + u[2] * du + v[2] * dv,
            )
        )
    # A polyline, not a periodic spline. A closed spline forced through this
    # many points across the concave tab transitions produces a solid whose
    # booleans fail silently: the seat looked right, but intersecting it with
    # the seal probe returned an empty shape, which the gate read as "no
    # cabinet material" and reported as a leak. At 288 segments the sagitta is
    # 0.003 mm, 130 times finer than a 0.4 mm extrusion bead, so nothing is
    # lost by describing the curve as straight runs.
    wire = cq.Wire.makePolygon([*points, points[0]])
    return cast(cq.Shape, cq.Solid.extrudeLinear(wire, [], cq.Vector(*inward) * length))


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
    #: Traced outline of the component frame, one quadrant normalised to the
    #: tab radius. Empty keeps the seat round, which is right for the
    #: DSA115-PR's circular flange.
    seat_profile: tuple[float, ...] = ()
    #: Radius the tabs reach, including clearance.
    seat_tab_radius: float = 0.0


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
        seat_profile=p.driver_frame_profile,
        seat_tab_radius=p.driver_outer_diameter / 2.0,
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
    if mount.seat_profile:
        cabinet = cabinet.cut(
            _depth_traced_profile(
                mount.seat_profile,
                mount.seat_tab_radius,
                -1.0,
                mount.seat_depth + 1.0,
                face,
                inward,
                clearance=p.print_clearance,
            )
        )
    else:
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
    """Four skin-crown fastener positions, clear of the official stack.

    They must sit outboard of the official mid-plate footprint, whose half-span
    is 55 mm, by at least a boss radius. v1 used a deeper cabinet and an
    asymmetric -26 mm inset on Y, which on the square v2 cabinet put a boss at
    y = 54 -- inside the plate, fouling a rear feature by 184 mm^3. The inset is
    symmetric now and the clearance is asserted rather than assumed.
    """
    p = parameters
    x = p.outer_width / 2.0 - 18.0
    y = p.outer_depth / 2.0 - 18.0
    clear = 55.0 + p.boss_outer_diameter / 2.0
    if min(x, y) < clear:
        raise ValueError(
            f"crown fastener inset leaves {min(x, y):.1f} mm; "
            f"needs {clear:.1f} mm to clear the official mid-plate"
        )
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
        p.outer_width, p.outer_depth, height, p.acoustic_bottom_z, p.corner_radius
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
    """Retains the active driver against its cabinet seat, glue-free.

    The lip loads the round flange body directly over the gasket rather than
    the four ears.  Clamping only the ears puts a bending moment across the
    flange and leaves compression on the seal depending on frame stiffness;
    loading it above the gasket reacts the force straight through the joint.
    The bore still clears the cutout, so nothing shadows the cone.
    """
    p = parameters
    return _clamp_ring(
        p.driver_clamp_ring_diameter,
        p.driver_cutout_diameter + 2.0,
        p.driver_flange_body_diameter - 1.0,
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
    divider = rounded_prism(p.outer_width, p.outer_depth, p.divider_thickness, z0, p.corner_radius)
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
            p.bushing_flange_diameter / 2.0 + 1.6,
            interface_z - z0,
            cq.Vector(x, y, z0),
            cq.Vector(0.0, 0.0, 1.0),
        )
        divider = divider.fuse(boss)
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

    # Every cut at this interface happens after the rib frame is fused. Cutting
    # the counterbores first let the ribs fill them straight back in, which
    # measured as an 88 mm^3 overlap with each isolation bushing.
    for x, y in mounts:
        # Counterbore seats the isolation bushing's body and its floor is the
        # hard face the shoulder screw bottoms on.  The insert bore starts
        # below it so the heat-set insert still gets its full depth.
        divider = divider.cut(
            cq.Solid.makeCylinder(
                (p.bushing_body_diameter + 2.0 * p.print_clearance) / 2.0,
                p.bushing_body_height,
                cq.Vector(x, y, p.shoulder_stop_z),
                cq.Vector(0.0, 0.0, 1.0),
            )
        )
        divider = divider.cut(_blind_insert(x, y, p.shoulder_stop_z, -1.0, p))

    # Bosses the shell crown bolts down onto.  Without these the skin is not
    # attached to anything and lifts straight off.
    for x, y in shroud_fastener_positions(p):
        boss_top_z = z0 + p.divider_thickness + p.shroud_boss_height
        boss = cq.Solid.makeCylinder(
            p.boss_outer_diameter / 2.0,
            p.shroud_boss_height,
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
        # Outer edge stops inside the round flange body, NOT at the across-ears
        # diameter.  Between the ears there is no flange to compress against, so
        # a gasket taken out to 103.2 mm is uncompressed over most of its
        # circumference: four leak paths straight out of the chamber.
        return (p.driver_bore_diameter, p.driver_flange_body_diameter - 1.5)
    if component.startswith("pr"):
        # Stop inside the radiator's rim, not at the seat.  The seat is the
        # flange plus print clearance, so a gasket taken out to it overhangs
        # the flange edge by that clearance and its outer band is compressed
        # by nothing.  Still spans the Ø106.93 bolt circle, whose holes pass
        # through this flange and would otherwise vent the chamber.
        return (p.pr_bore_diameter + 3.0, p.pr_outer_diameter - 1.0)
    raise ValueError(f"unknown sealed component: {component}")


def driver_gasket(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Seals against the round body of the ND91-4 flange.

    The frame is a Ø85.09 mm sealing body with four ears reaching Ø103.2 mm,
    and the four Ø4.0 mounting holes on the Ø93.3 mm circle are in those ears.
    With the correct Ø76.45 mm cutout those holes sit roughly 6 mm outboard of
    the sealed band, so they open ambient-to-ambient and vent nothing.

    An earlier revision spanned this gasket all the way to Ø103.2 mm to cover
    those holes, which only made sense while the cutout was wrongly recorded as
    Ø88.5 mm.  Out there the gasket bridges fresh air between the ears and is
    compressed nowhere but on them.
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
            size[0], size[1], 14.0, centered=(True, True, False)
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
    """Steel plate stack that the tray accepts: width, depth, total thickness.

    Inset 10 mm per side rather than 5, so the four lid bosses have room to sit
    in the tray walls without touching either the steel or the outer shell.
    """
    width, depth = ballast_tray_extent(parameters)
    return (width - 20.0, depth - 20.0, 12.0)


def ballast_lid_fastener_positions(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> tuple[tuple[float, float], ...]:
    """Four lid screws carried by the tray walls, clear of the steel stack.

    One boss sits at the middle of each wall face, just outboard of the steel
    and just inboard of the shell, so its full diameter is bonded to wall
    material.  Placing them diagonally at the corners instead, offset from the
    plate edge, left every boss attached to a rounded corner by a sliver.
    """
    p = parameters
    plate_width, plate_depth, _ = ballast_plate_extent(p)
    clear = p.boss_outer_diameter / 2.0 + 1.3
    return (
        (-(plate_width / 2.0 + clear), 0.0),
        (plate_width / 2.0 + clear, 0.0),
        (0.0, -(plate_depth / 2.0 + clear)),
        (0.0, plate_depth / 2.0 + clear),
    )


def ballast_cartridge(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Removable dry ballast tray with four blind insert-retained lid bosses."""
    p = parameters
    width, depth = ballast_tray_extent(p)
    tray = rounded_prism(width, depth, 16.0, 0.0, 10.0)
    cavity = rounded_prism(width - 8.0, depth - 8.0, 14.0, 2.0, 6.0)
    tray = tray.cut(cavity)
    for x, y in ballast_lid_fastener_positions(p):
        boss = cq.Solid.makeCylinder(
            p.boss_outer_diameter / 2.0,
            14.0,
            cq.Vector(x, y, 2.0),
            cq.Vector(0.0, 0.0, 1.0),
        )
        tray = tray.fuse(boss)
        tray = tray.cut(_blind_insert(x, y, 16.0, -1.0, p))
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


@lru_cache(maxsize=8)
def official_pocket_wire(clearance: float, count: int = 192) -> cq.Wire:
    """The official stack's real outline, offset outward by *clearance*.

    Deliberately not our own superellipse. SECTION_EXPONENT = 4.13 matches the
    official curve to 0.38 mm, and the real outline runs up to 0.350 mm outside
    the ideal at the 45 degree corner -- so a pocket built from the fit and
    given a 0.4 mm allowance actually delivered 0.05 mm there, and the official
    part fouled its own pocket. Offsetting the measured outline gives a genuinely
    uniform gap, which is both tighter to look at and correct to assemble.
    """
    from satellite1_ultra.official import official_upper_solids

    solids = official_upper_solids()
    union = (
        solids["official_top_plate"]
        .fuse(solids["official_lock_ring"])
        .fuse(solids["official_mid_plate"])
    )
    # z = 14 is inside the band where the stack is at its full 110 mm width.
    slab = union.intersect(cq.Solid.makeBox(400.0, 400.0, 0.4, cq.Vector(-200.0, -200.0, 14.0)))
    best: tuple[float, cq.Face] | None = None
    for face in slab.Faces():
        if face.geomType() != "PLANE":
            continue
        try:
            area = cq.Face.makeFromWires(face.outerWire()).Area()
        except Exception:
            continue
        if best is None or area > best[0]:
            best = (area, face)
    if best is None:
        raise ValueError("could not find the official stack's full-width outline")
    outline = best[1].outerWire()

    # Offset by sampling and re-splining rather than with Wire.offset2D. The
    # offset2D result is geometrically right -- it differs from this by about
    # 10 mm^3 -- but it does not survive a STEP round trip: the exported crown
    # reopened 194043 mm^3 light, while the same shell built from a spline
    # profile reopens with zero error. A clean periodic spline is the same class
    # of curve the body's own sections use, and those round-trip exactly.
    points = [outline.positionAt(index / count) for index in range(count)]
    offset: list[cq.Vector] = []
    for index, point in enumerate(points):
        previous = points[index - 1]
        following = points[(index + 1) % count]
        tx, ty = following.x - previous.x, following.y - previous.y
        length = sqrt(tx * tx + ty * ty)
        if length <= 0.0:
            raise ValueError("degenerate official outline sample")
        nx, ny = ty / length, -tx / length
        # The outline is convex about the origin, so orient the normal outward.
        if nx * point.x + ny * point.y < 0.0:
            nx, ny = -nx, -ny
        offset.append(cq.Vector(point.x + nx * clearance, point.y + ny * clearance, point.z))
    return cq.Wire.assembleEdges([cq.Edge.makeSpline(offset, periodic=True)])


def official_pocket(z0: float, z1: float, clearance: float) -> cq.Shape:
    """Straight-sided well the official assembly lifts out of."""
    wire = official_pocket_wire(clearance)
    face = cq.Face.makeFromWires(wire)
    base = face.Center().z
    return cast(
        cq.Shape,
        cq.Solid.extrudeLinear(face, cq.Vector(0.0, 0.0, z1 - z0)).translate(
            cq.Vector(0.0, 0.0, z0 - base)
        ),
    )


def body_half_at(z: float, parameters: DesignParameters = DEFAULT_PARAMETERS) -> float:
    """Half-size of the visible silhouette at height *z*.

    A vertical body, rolled over a generous radius into a single flat top, and
    softened at the ground edge.  The flat top is coplanar with the official
    top plate, so the Satellite1 module sits flush in it.
    """
    p = parameters
    top = p.shell_flat_top_z
    if z >= top:
        return p.flat_top_half
    shoulder = top - p.shell_top_roll
    if z > shoulder:
        d = (z - shoulder) / p.shell_top_roll
        return p.body_half - p.shell_top_roll * (1.0 - sqrt(max(1.0 - d * d, 0.0)))
    roll_top = p.shell_bottom_z + p.shell_bottom_roll
    if z < roll_top:
        d = (roll_top - z) / p.shell_bottom_roll
        return p.body_half - p.shell_bottom_roll * (1.0 - sqrt(max(1.0 - d * d, 0.0)))
    return p.body_half


def _skin_loft(
    offset: float,
    z0: float,
    z1: float,
    parameters: DesignParameters,
    steps: int = 14,
) -> cq.Shape:
    zs = [z0 + (z1 - z0) * i / steps for i in range(steps + 1)]
    wires = [
        superellipse_wire(
            max(body_half_at(z, parameters) - offset, 0.5),
            max(body_half_at(z, parameters) - offset, 0.5),
            z,
        )
        for z in zs
    ]
    return cast(cq.Shape, cq.Solid.makeLoft(wires, ruled=False))


def skin_body(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
    offset: float = 0.0,
) -> cq.Shape:
    """Solid bounded by the silhouette, inset by *offset*, base to flat top.

    Straight sections are true extrusions and only the two rolls are lofted, so
    a smooth loft cannot bulge the vertical body outward.
    """
    p = parameters
    roll_top = p.shell_bottom_z + p.shell_bottom_roll
    shoulder = p.shell_flat_top_z - p.shell_top_roll
    solid = _skin_loft(offset, p.shell_bottom_z, roll_top, p)
    span = 2.0 * (p.body_half - offset)
    solid = solid.fuse(section_prism(span, span, shoulder - roll_top, roll_top))
    return solid.fuse(_skin_loft(offset, shoulder, p.shell_flat_top_z, p))


def _window_slots(
    centre: Vector3,
    normal: str,
    parameters: DesignParameters,
) -> cq.Shape:
    """Vertical slot field clipped to one circular grille window."""
    p = parameters
    cx, cy, cz = centre
    radius = p.window_diameter / 2.0
    reach = 4.0 * p.shell_wall_thickness
    cutters: list[cq.Shape] = []
    count = int(p.window_diameter // p.shell_slot_pitch)
    for index in range(-count, count + 1):
        offset = index * p.shell_slot_pitch
        if abs(offset) > radius - p.shell_slot_width:
            continue
        half_len = sqrt(max(radius**2 - offset**2, 0.0))
        if normal == "y":
            box = cq.Workplane("XY", origin=(cx + offset, cy, cz)).box(
                p.shell_slot_width, reach, 2.0 * half_len, centered=(True, True, True)
            )
        else:
            box = cq.Workplane("XY", origin=(cx, cy + offset, cz)).box(
                reach, p.shell_slot_width, 2.0 * half_len, centered=(True, True, True)
            )
        cutters.append(cast(cq.Shape, box.val()))
    return cq.Compound.makeCompound(cutters)


def acoustic_windows(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """Grille fields over the driver (-Y) and both radiators (+/-X).

    The +Y rear face is left solid: the skin is cosmetic and the cabinet inside
    it is sealed, so open area only matters where a cone actually radiates.
    """
    p = parameters
    driver = _window_slots((0.0, -p.body_half, p.driver_axis_z), "y", p)
    result = driver
    for side in (-1.0, 1.0):
        result = result.fuse(_window_slots((side * p.body_half, 0.0, p.pr_axis_z), "x", p))
    return result


def _fabric_grooves(parameters: DesignParameters) -> cq.Shape:
    """Concealed wrap-retention channels just inside both rolls."""
    p = parameters
    span = 2.0 * p.body_half
    grooves: list[cq.Shape] = []
    for z0 in (
        p.shell_bottom_z + p.shell_bottom_roll,
        p.shell_flat_top_z - p.shell_top_roll - p.fabric_groove_width,
    ):
        ring = section_prism(span, span, p.fabric_groove_width, z0).cut(
            section_prism(
                span - 2.0 * p.fabric_groove_depth,
                span - 2.0 * p.fabric_groove_depth,
                p.fabric_groove_width + 2.0,
                z0 - 1.0,
            )
        )
        grooves.append(ring)
    return grooves[0].fuse(grooves[1])


@lru_cache(maxsize=8)
def skin_shell(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
    fabric: bool = False,
) -> cq.Shape:
    """The one-piece monolith skin before it is split for printing.

    *fabric* adds the wrap-retention channels.  They are off by default because
    on the bare printed finish they read as horizontal seam lines, which is
    exactly what this design exists to remove.
    """
    p = parameters
    outer = skin_body(p)
    inner = skin_body(p, offset=p.shell_wall_thickness)
    span = 2.0 * (p.body_half - p.shell_wall_thickness)
    # Open the base so the skin is a shell rather than a solid block.
    inner = inner.fuse(section_prism(span, span, 2.1, p.shell_bottom_z - 2.0))
    # Stop the hollow one wall short of the top plane, so the flat top is a
    # closed deck of full wall thickness.  Letting the hollow run to the top
    # left only a 3 mm rim at the outer edge and an open trench around the
    # official pocket -- the top looked flush in section but you could see
    # straight into the electronics bay from above.
    deck = 2.0 * (p.body_half + 5.0)
    inner = inner.cut(
        section_prism(
            deck,
            deck,
            p.shell_top_roll,
            p.shell_flat_top_z - p.shell_wall_thickness,
        )
    )
    shell = outer.cut(inner)
    # Flush pocket the official module drops into, with a hairline all round.
    shell = shell.cut(
        official_pocket(
            p.official_full_section_z - 14.0,
            p.shell_flat_top_z + 2.0,
            p.official_pocket_clearance,
        )
    )
    shell = shell.cut(acoustic_windows(p))
    if fabric:
        shell = shell.cut(_fabric_grooves(p))
    return shell


def _seam_reinforcement(parameters: DesignParameters) -> cq.Shape:
    """Local inward wall thickening across every seam, to carry the laps."""
    p = parameters
    span_in = 2.0 * (p.body_half - p.shell_wall_thickness)
    span_seam = 2.0 * (p.body_half - p.seam_wall_thickness)
    bands: list[cq.Shape] = []
    for zs in p.seam_positions:
        z0 = zs - p.seam_runout
        z1 = zs + p.lap_depth + 2.0
        bands.append(
            section_prism(span_in, span_in, z1 - z0, z0).cut(
                section_prism(span_seam, span_seam, z1 - z0 + 2.0, z0 - 1.0)
            )
        )
    return bands[0].fuse(bands[1])


def _crush_ribs(zs: float, parameters: DesignParameters) -> cq.Shape:
    """Interference ribs at the four face centres of a tongue.

    The socket bore sits at mid + lap_clearance; the ribs reach mid +
    crush_proud, so each joint closes on real interference instead of rattling
    in clearance.  Only the face centres are used, where the superellipse
    normal is axis aligned and a plain box is a true radial rib.
    """
    p = parameters
    mid = p.lap_mid_half
    ribs: list[cq.Shape] = []
    for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        box = cq.Workplane(
            "XY",
            origin=(
                sx * (mid + p.crush_proud / 2.0),
                sy * (mid + p.crush_proud / 2.0),
                zs + 2.0,
            ),
        ).box(
            p.crush_proud if sx else p.crush_width,
            p.crush_width if sx else p.crush_proud,
            p.crush_length,
            centered=(True, True, False),
        )
        ribs.append(cast(cq.Shape, box.val()))
    return cq.Compound.makeCompound(ribs)


def _straight_body(z0: float, z1: float, parameters: DesignParameters) -> cq.Shape:
    """The body over a span that lies entirely in its straight section.

    Geometrically identical to skin_body there, but a single extrusion rather
    than a fusion of two lofts and a prism. Trimming a bridge against the fused
    solid produced composite spline faces that cost the crown 0.0221 mm^3 on a
    STEP round trip, against a 0.0066 mm^3 budget -- while the same operation
    against this extrusion round-trips at 2e-6.
    """
    p = parameters
    shoulder = p.shell_flat_top_z - p.shell_top_roll
    roll_top = p.shell_bottom_z + p.shell_bottom_roll
    if not (roll_top <= z0 and z1 <= shoulder):
        raise ValueError("span is not inside the body's straight section")
    span = 2.0 * p.body_half
    return section_prism(span, span, z1 - z0, z0)


def _crown_retention(crown: cq.Shape, parameters: DesignParameters) -> cq.Shape:
    """Bolt the crown down onto the divider's bosses.

    Four tabs, each webbed back to the skin so the screw load is carried into
    the wall rather than by an unsupported stalk.
    """
    p = parameters
    tab_z = p.divider_bottom_z + p.divider_thickness + p.shroud_boss_height
    outer = _straight_body(tab_z - 1.0, tab_z + p.crown_tab_thickness + 1.0, p)
    for x, y in shroud_fastener_positions(p):
        tab = cq.Solid.makeCylinder(
            p.crown_tab_radius,
            p.crown_tab_thickness,
            cq.Vector(x, y, tab_z),
            cq.Vector(0.0, 0.0, 1.0),
        )
        reach = 2.0 * p.body_half
        if x:
            bridge = cq.Workplane(
                "XY", origin=(x + reach / 2.0 * (1.0 if x > 0 else -1.0), y, tab_z)
            ).box(reach, 9.0, p.crown_tab_thickness, centered=(True, True, False))
        else:
            bridge = cq.Workplane(
                "XY", origin=(x, y + reach / 2.0 * (1.0 if y > 0 else -1.0), tab_z)
            ).box(9.0, reach, p.crown_tab_thickness, centered=(True, True, False))
        crown = crown.fuse(tab).fuse(cast(cq.Shape, bridge.val()).intersect(outer))
        crown = crown.cut(
            cq.Solid.makeCylinder(
                p.fastener_clearance_diameter / 2.0,
                p.crown_tab_thickness,
                cq.Vector(x, y, tab_z),
                cq.Vector(0.0, 0.0, 1.0),
            )
        )
    return crown


def _base_retention(base: cq.Shape, parameters: DesignParameters) -> cq.Shape:
    """Bolt the base segment down into the bottom service plate."""
    p = parameters
    retention_z = p.shell_retention_z
    outer = _straight_body(retention_z - 1.0, retention_z + 11.0, p)
    for x, y in cage_fastener_positions(p):
        boss = cq.Solid.makeCylinder(
            p.boss_outer_diameter / 2.0,
            10.0,
            cq.Vector(x, y, retention_z),
            cq.Vector(0.0, 0.0, 1.0),
        )
        reach = 2.0 * p.body_half
        if x:
            bridge = cq.Workplane(
                "XY", origin=(x + reach / 2.0 * (1.0 if x > 0 else -1.0), y, retention_z)
            ).box(reach, 9.0, 6.0, centered=(True, True, False))
        else:
            bridge = cq.Workplane(
                "XY", origin=(x, y + reach / 2.0 * (1.0 if y > 0 else -1.0), retention_z)
            ).box(9.0, reach, 6.0, centered=(True, True, False))
        base = base.fuse(boss).fuse(cast(cq.Shape, bridge.val()).intersect(outer))
        base = base.cut(_blind_insert(x, y, retention_z, 1.0, p))
    return base


SKIN_SEGMENTS = ("shell_base", "shell_grille", "shell_crown")


@lru_cache(maxsize=8)
def skin_segments(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
    fabric: bool = False,
) -> dict[str, cq.Shape]:
    """Split the skin into three printable segments joined by lapped rabbets.

    The outer surface is continuous across every joint; the only visible mark
    is a deliberate relief.  A designed shadow line reads as intentional, where
    a bare butt joint would show FDM layer registration error between three
    separate prints as a ragged and obviously accidental step.

    There is no hardware at the seams: the radial gap to the cabinet is only
    9 mm at the faces and 10.8 mm at the corners, too little for an M3 boss.
    The laps carry shear and alignment, the crown bolts to the pressure divider
    and the base to the bottom service plate, and the grille segment -- which
    carries the entire visible grille -- is held captive between them.
    """
    p = parameters
    blank = skin_shell(p, fabric).fuse(_seam_reinforcement(p))
    mid = p.lap_mid_half
    span = 2.0 * (p.body_half + 5.0)
    bounds = [p.shell_bottom_z - 5.0, *p.seam_positions, p.shell_flat_top_z + 5.0]

    segments: dict[str, cq.Shape] = {}
    for index, name in enumerate(SKIN_SEGMENTS):
        z0, z1 = bounds[index], bounds[index + 1]
        piece = blank.intersect(section_prism(span, span, z1 - z0, z0))
        if z1 in p.seam_positions:
            tongue = blank.intersect(section_prism(2.0 * mid, 2.0 * mid, p.lap_depth, z1))
            piece = piece.fuse(tongue)
        if z0 in p.seam_positions:
            socket_span = 2.0 * (mid + p.lap_clearance)
            piece = piece.cut(
                section_prism(
                    socket_span,
                    socket_span,
                    p.lap_depth + p.lap_clearance + 1.0,
                    z0 - 1.0,
                )
            )
        segments[name] = piece

    for index, zs in enumerate(p.seam_positions):
        owner = SKIN_SEGMENTS[index]
        segments[owner] = segments[owner].fuse(_crush_ribs(zs, p))

    for zs in p.seam_positions:
        relief = section_prism(span, span, p.shadow_height, zs - p.shadow_height / 2.0).cut(
            section_prism(
                2.0 * (p.body_half - p.shadow_depth),
                2.0 * (p.body_half - p.shadow_depth),
                p.shadow_height * 3.0,
                zs - p.shadow_height,
            )
        )
        for name, piece in segments.items():
            segments[name] = piece.cut(relief)

    segments["shell_crown"] = _crown_retention(segments["shell_crown"], p)
    segments["shell_base"] = _base_retention(segments["shell_base"], p)
    return segments


def shell_base(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    return skin_segments(parameters)["shell_base"]


def shell_grille(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    return skin_segments(parameters)["shell_grille"]


def shell_crown(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    return skin_segments(parameters)["shell_crown"]


def shell_base_fabric(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    return skin_segments(parameters, fabric=True)["shell_base"]


def shell_grille_fabric(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    return skin_segments(parameters, fabric=True)["shell_grille"]


def shell_crown_fabric(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    return skin_segments(parameters, fabric=True)["shell_crown"]


def mic_isolation_bushing(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """TPU 95A top-hat isolating the official stack from the divider.

    Only works with the specified M3 x d4 shoulder screw.  The shoulder bottoms
    on the counterbore floor and its head stops clear of the mid-plate, so the
    official stack rests on the elastomer and no clamping load passes through
    it.  With an ordinary M3 screw the fastener clamps in parallel with the
    elastomer at roughly 1.0e8 N/m against 2.9e6 N/m -- 35x stiffer -- leaving
    the TPU carrying under 3% of the path and isolating nothing.
    """
    p = parameters
    flange = cq.Solid.makeCylinder(
        p.bushing_flange_diameter / 2.0,
        p.bushing_flange_thickness,
        cq.Vector(0.0, 0.0, 0.0),
        cq.Vector(0.0, 0.0, 1.0),
    )
    body = cq.Solid.makeCylinder(
        p.bushing_body_diameter / 2.0,
        p.bushing_body_height,
        cq.Vector(0.0, 0.0, -p.bushing_body_height),
        cq.Vector(0.0, 0.0, 1.0),
    )
    bore = cq.Solid.makeCylinder(
        (p.shoulder_screw_diameter + 0.2) / 2.0,
        p.bushing_flange_thickness + p.bushing_body_height + 2.0,
        cq.Vector(0.0, 0.0, -p.bushing_body_height - 1.0),
        cq.Vector(0.0, 0.0, 1.0),
    )
    return flange.fuse(body).cut(bore)


def outer_shell(parameters: DesignParameters = DEFAULT_PARAMETERS) -> cq.Shape:
    """The whole skin as one solid, for assembly views and collision checks."""
    return skin_shell(parameters)


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
    return section_ring(
        2.0 * half_x,
        2.0 * half_y,
        2.0 * half_x - 7.0,
        2.0 * half_y - 7.0,
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
    # The flange is a rounded square, 88.5 across the flats and 103.2 across
    # the corners.  Modelling it as a Ø103.2 disc overstates it by about
    # 3400 mm^3 once the seat is cut to the real profile, which reads as an
    # interference with the cabinet that no physical driver would have.
    flange = _depth_traced_profile(
        p.driver_frame_profile,
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
    """Radiator frame plus full rear/outward excursion and tuning-mass envelope."""
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
        **skin_segments(p),
        "main_cabinet": main_cabinet(p),
        "divider_gasket": divider_gasket(compressed).translate(
            cq.Vector(0.0, 0.0, p.acoustic_top_z)
        ),
        "pressure_divider": pressure_divider(p),
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
            cq.Vector(0.0, 0.0, p.base_bottom_z + p.bottom_plate_thickness + 14.5)
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
    for index, (x, y) in enumerate(official_mount_positions(p)):
        parts[f"mic_isolation_bushing_{index}"] = mic_isolation_bushing(p).translate(
            cq.Vector(x, y, p.official_interface_z)
        )
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
