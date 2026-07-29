"""v2 production-candidate parts on the flat-top superellipse form.

Reuses the shape-agnostic mount, fastener and seal machinery from
`satellite1_ultra.geometry` unchanged; only the section family and the top
treatment differ.  Every solid here is a true B-rep built from primitives and
booleans, so the project's no-mesh rule still holds.

Section note
------------
A superellipse offset by a constant distance is not another superellipse, so
walls are built by *scaling* the half-size.  At the flat of a face that gives
exactly the nominal thickness; at the 45-degree corner it gives 1.20x nominal.
Walls therefore get thicker at the corners, never thinner, which is the safe
direction.
"""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from typing import cast

import cadquery as cq
from v2_silhouette import (
    BODY_HALF,
    BOTTOM_ROLL,
    CABINET_OFFSET,
    OFFICIAL_FULL_Z,
    OFFICIAL_HALF,
    POCKET_CLEARANCE,
    SHELL_WALL,
    TOP_ROLL,
    TOP_Z,
    _prism,
    outer_body,
)

from satellite1_ultra.geometry import (
    DEFAULT_PARAMETERS,
    _apply_mount,
    _blind_insert,
    _compression_stop,
    acoustic_mounts,
    base_fastener_positions,
    cage_fastener_positions,
    official_mount_positions,
    shroud_fastener_positions,
    top_fastener_positions,
)

# --------------------------------------------------------------------- #
# v2 parameter set
# --------------------------------------------------------------------- #
# Square 160 mm cabinet inside a 184 mm body: 92 - 12 = 80 half-size.
# Z layout solved so the gross sealed prism reproduces v1's 3.966 L.
V2 = replace(
    DEFAULT_PARAMETERS,
    outer_width=160.0,
    outer_depth=160.0,
    grille_width_margin=24.0,
    grille_depth_margin=24.0,
    acoustic_top_z=-33.0,
    acoustic_bottom_z=-225.5,
    base_bottom_z=-247.5,
    # Driver and radiators share one axis height so the three grille windows
    # read as a single band around the body, centred on the visible silhouette.
    driver_axis_z=-117.0,
    pr_axis_z=-117.0,
    # Divider boss tops drop by the isolation bushing's flange thickness so the
    # official stack still seats at -6.8 and the flat top stays flush.
    official_interface_z=-8.8,
)

BODY_BOTTOM_Z = V2.base_bottom_z - 4.0

WINDOW_DIAMETER = 124.0  # grille field over each acoustic component
SLOT_WIDTH = 3.4
SLOT_PITCH = 7.0
FABRIC_GROOVE_W = 2.2
FABRIC_GROOVE_D = 1.5

# --------------------------------------------------------------------- #
# Shell split
# --------------------------------------------------------------------- #
# Seams sit 5 mm clear of the grille windows (which span z -179 to -55), so
# no seam grazes a window edge and leaves a fragile sliver.  That puts the
# whole grille field in one segment, and every segment inside the bed.
SEAM_Z = (-184.0, -50.0)
LAP_DEPTH = 12.0  # rabbet engagement
LAP_CLEARANCE = 0.25  # per-side sliding fit on the lap
SEAM_WALL = 5.0  # wall thickened inward across the joint
SEAM_RUNOUT = 4.0  # reinforcement below the seam plane
SHADOW_DEPTH = 0.3  # deliberate relief at the visible butt line
SHADOW_HEIGHT = 0.6

# Crush ribs stand proud of the socket bore, so the lap is a light press fit
# rather than a 0.25 mm slip fit that could rattle.
CRUSH_PROUD = 0.40  # 0.15 mm interference against the socket
CRUSH_WIDTH = 3.0
CRUSH_LENGTH = 8.0

# Skin retention.  Without these the shell simply lifts off.
CROWN_TAB_RADIUS = 5.0
CROWN_TAB_THICKNESS = 3.0
SHROUD_BOSS_HEIGHT = 8.0


def cabinet_envelope() -> cq.Shape:
    """Outer envelope of the sealed cabinet: a plain superellipse prism."""
    return _prism(BODY_HALF - CABINET_OFFSET, V2.acoustic_bottom_z, V2.acoustic_top_z)


@lru_cache(maxsize=4)
def main_cabinet() -> cq.Shape:
    """Sealed acoustic cabinet on the square superellipse section."""
    p = V2
    envelope = cabinet_envelope()
    cavity = _prism(
        BODY_HALF - CABINET_OFFSET - p.wall_thickness, p.cavity_bottom_z, p.acoustic_top_z + 1.0
    )
    cabinet = envelope.cut(cavity)

    # Vertical wall ribs, clear of every component envelope.
    rib_h = p.acoustic_top_z - p.cavity_bottom_z
    half = BODY_HALF - CABINET_OFFSET - p.wall_thickness
    for offset in (-56.0, 56.0):
        inset = p.brace_rib_depth / 2.0
        across = (p.brace_rib_width, p.brace_rib_depth)
        along = (p.brace_rib_depth, p.brace_rib_width)
        for centre, size in (
            ((offset, -half + inset), across),
            ((offset, half - inset), across),
            ((-half + inset, offset), along),
            ((half - inset, offset), along),
        ):
            rib = cq.Workplane("XY", origin=(centre[0], centre[1], p.cavity_bottom_z)).box(
                size[0], size[1], rib_h, centered=(True, True, False)
            )
            cabinet = cabinet.fuse(cast(cq.Shape, rib.val()).intersect(envelope))

    for mount in acoustic_mounts(p).values():
        cabinet = _apply_mount(cabinet, envelope, mount, p)

    # Divider interface: bosses, webs, compression stops, blind inserts.
    boss_h = 10.0
    for x, y in top_fastener_positions(p):
        boss = cq.Solid.makeCylinder(
            p.boss_outer_diameter / 2.0,
            boss_h,
            cq.Vector(x, y, p.acoustic_top_z - boss_h),
            cq.Vector(0.0, 0.0, 1.0),
        )
        if abs(y) > abs(x):
            wall_y = (half + p.wall_thickness) * (1.0 if y > 0 else -1.0)
            web = cq.Workplane("XY", origin=(x, (y + wall_y) / 2.0, p.acoustic_top_z - boss_h)).box(
                8.0, abs(wall_y - y), boss_h, centered=(True, True, False)
            )
        else:
            wall_x = (half + p.wall_thickness) * (1.0 if x > 0 else -1.0)
            web = cq.Workplane("XY", origin=((x + wall_x) / 2.0, y, p.acoustic_top_z - boss_h)).box(
                abs(wall_x - x), 8.0, boss_h, centered=(True, True, False)
            )
        cabinet = cabinet.fuse(boss).fuse(cast(cq.Shape, web.val()).intersect(envelope))
        cabinet = cabinet.fuse(_compression_stop(x, y, p.acoustic_top_z, 1.0, 3.0, p))
        cabinet = cabinet.cut(_blind_insert(x, y, p.acoustic_top_z, -1.0, p))

    for x, y in base_fastener_positions(p):
        pad = cq.Solid.makeCylinder(
            8.0, 4.0, cq.Vector(x, y, p.cavity_bottom_z), cq.Vector(0.0, 0.0, 1.0)
        )
        cabinet = cabinet.fuse(pad)
        cabinet = cabinet.cut(_blind_insert(x, y, p.acoustic_bottom_z, 1.0, p))
    return cabinet


@lru_cache(maxsize=4)
def pressure_divider() -> cq.Shape:
    """Airtight divider carrying the official mid-plate interface."""
    p = V2
    z0 = p.divider_bottom_z
    divider = _prism(BODY_HALF - CABINET_OFFSET, z0, z0 + p.divider_thickness)
    divider = divider.cut(
        cq.Solid.makeCylinder(
            p.cable_passage_diameter / 2.0,
            p.divider_thickness,
            cq.Vector(p.cable_passage_x, p.cable_passage_y, z0),
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
    interface_z = p.official_interface_z
    for x, y in official_mount_positions(p):
        boss = cq.Solid.makeCylinder(
            BUSHING_FLANGE_D / 2.0 + 1.6,
            interface_z - z0,
            cq.Vector(x, y, z0),
            cq.Vector(0.0, 0.0, 1.0),
        )
        divider = divider.fuse(boss)
        # Counterbore seats the isolation bushing's body; the insert bore starts
        # below it so the heat-set insert still gets its full depth.
        divider = divider.cut(
            cq.Solid.makeCylinder(
                (BUSHING_BODY_D + 2.0 * p.print_clearance) / 2.0,
                BUSHING_BODY_H,
                cq.Vector(x, y, interface_z - BUSHING_BODY_H),
                cq.Vector(0.0, 0.0, 1.0),
            )
        )
        divider = divider.cut(_blind_insert(x, y, interface_z - BUSHING_BODY_H, -1.0, p))
    rib_bottom = z0 + p.divider_thickness
    for axis in ("x", "y"):
        for sign in (-1.0, 1.0):
            if axis == "x":
                origin, size = (
                    (0.0, sign * p.official_mount_y, rib_bottom),
                    (2.0 * p.official_mount_x, 5.0),
                )
            else:
                origin, size = (
                    (sign * p.official_mount_x, 0.0, rib_bottom),
                    (5.0, 2.0 * p.official_mount_y),
                )
            rib = cq.Workplane("XY", origin=origin).box(
                size[0], size[1], interface_z - rib_bottom, centered=(True, True, False)
            )
            divider = divider.fuse(cast(cq.Shape, rib.val()))

    # Bosses the shell crown bolts down onto.  Without these the skin is not
    # attached to anything and simply lifts off.
    for x, y in shroud_fastener_positions(p):
        boss = cq.Solid.makeCylinder(
            p.boss_outer_diameter / 2.0,
            SHROUD_BOSS_HEIGHT,
            cq.Vector(x, y, rib_bottom),
            cq.Vector(0.0, 0.0, 1.0),
        )
        divider = divider.fuse(boss)
        divider = divider.cut(_blind_insert(x, y, rib_bottom + SHROUD_BOSS_HEIGHT, -1.0, p))
    return divider


def _window_slots(centre: tuple[float, float, float], normal: str) -> cq.Shape:
    """Vertical slot field clipped to a circular window on one face."""
    cx, cy, cz = centre
    radius = WINDOW_DIAMETER / 2.0
    reach = 4.0 * SHELL_WALL
    cutters: list[cq.Shape] = []
    count = int(WINDOW_DIAMETER // SLOT_PITCH)
    for i in range(-count, count + 1):
        offset = i * SLOT_PITCH
        if abs(offset) > radius - SLOT_WIDTH:
            continue
        # Slot length is the chord of the window circle at this offset.
        half_len = (radius**2 - offset**2) ** 0.5
        if normal == "y":
            box = cq.Workplane("XY", origin=(cx + offset, cy, cz)).box(
                SLOT_WIDTH, reach, 2.0 * half_len, centered=(True, True, True)
            )
        else:
            box = cq.Workplane("XY", origin=(cx, cy + offset, cz)).box(
                reach, SLOT_WIDTH, 2.0 * half_len, centered=(True, True, True)
            )
        cutters.append(cast(cq.Shape, box.val()))
    return cq.Compound.makeCompound(cutters)


def acoustic_windows() -> cq.Shape:
    """The three grille fields: one over the driver, one over each radiator."""
    z = V2.driver_axis_z
    fields = [
        _window_slots((0.0, -BODY_HALF, z), "y"),
        _window_slots((0.0, BODY_HALF, z), "y"),
        _window_slots((-BODY_HALF, 0.0, z), "x"),
        _window_slots((BODY_HALF, 0.0, z), "x"),
    ]
    # -Y is the driver, +/-X are the radiators; +Y is the sealed rear, left solid.
    result = fields[0]
    for field in fields[2:]:
        result = result.fuse(field)
    return result


@lru_cache(maxsize=4)
def outer_shell(with_windows: bool = True, fabric_grooves: bool = False) -> cq.Shape:
    """The visible monolith: smooth skin, flat top, flush official pocket.

    *fabric_grooves* adds the wrap-retention channels.  They are off by default
    because on the bare printed finish they read as horizontal seam lines, which
    is exactly what this design exists to remove.
    """
    outer = outer_body(BODY_BOTTOM_Z)
    inner = outer_body(BODY_BOTTOM_Z, offset=SHELL_WALL)
    # Open the base so the skin is a shell, and sink the flush official pocket.
    inner = inner.fuse(_prism(BODY_HALF - SHELL_WALL, BODY_BOTTOM_Z - 2.0, BODY_BOTTOM_Z + 0.1))
    shell = outer.cut(inner)
    shell = shell.cut(_prism(OFFICIAL_HALF + POCKET_CLEARANCE, OFFICIAL_FULL_Z - 14.0, TOP_Z + 2.0))

    if with_windows:
        shell = shell.cut(acoustic_windows())

    if fabric_grooves:
        for z0 in (BODY_BOTTOM_Z + BOTTOM_ROLL, TOP_Z - TOP_ROLL - FABRIC_GROOVE_W):
            groove = _prism(BODY_HALF, z0, z0 + FABRIC_GROOVE_W).cut(
                _prism(BODY_HALF - FABRIC_GROOVE_D, z0 - 1.0, z0 + FABRIC_GROOVE_W + 1.0)
            )
            shell = shell.cut(groove)
    return shell


def _seam_reinforcement() -> cq.Shape:
    """Local inward wall thickening across every seam, for lap material."""
    bands: list[cq.Shape] = []
    for zs in SEAM_Z:
        z0, z1 = zs - SEAM_RUNOUT, zs + LAP_DEPTH + 2.0
        band = _prism(BODY_HALF - SHELL_WALL, z0, z1).cut(
            _prism(BODY_HALF - SEAM_WALL, z0 - 1.0, z1 + 1.0)
        )
        bands.append(band)
    result = bands[0]
    for band in bands[1:]:
        result = result.fuse(band)
    return result


@lru_cache(maxsize=4)
def _shell_blank() -> cq.Shape:
    """The one-piece shell plus the seam reinforcement, before splitting."""
    return outer_shell().fuse(_seam_reinforcement())


def shell_segments() -> dict[str, cq.Shape]:
    """Split the skin into three printable segments joined by lapped rabbets.

    The outer surface is continuous across every joint; the only visible mark
    is a deliberate 0.3 x 0.6 mm relief.  A designed shadow line reads as
    intentional, where a bare butt joint would show FDM layer mismatch as a
    ragged and obviously accidental step.

    There is no hardware at the seams: the radial gap to the cabinet is only
    9 mm at the faces and 10.8 mm at the corners, too little for an M3 boss.
    The laps carry shear and alignment, the top segment bolts to the pressure
    divider and the bottom segment to the base skirt, and the middle segment
    -- the one carrying the entire visible grille -- is clamped between them
    with no fasteners of its own.
    """
    blank = _shell_blank()
    mid_half = BODY_HALF - SEAM_WALL / 2.0
    top_z, bottom_z = TOP_Z + 5.0, BODY_BOTTOM_Z - 5.0

    def slab(z0: float, z1: float) -> cq.Shape:
        return _prism(BODY_HALF + 5.0, z0, z1)

    bounds = [bottom_z, *SEAM_Z, top_z]
    names = ("shell_base", "shell_grille", "shell_crown")
    segments: dict[str, cq.Shape] = {}
    for index, name in enumerate(names):
        piece = blank.intersect(slab(bounds[index], bounds[index + 1]))
        # Grow a tongue up into the segment above.
        if index + 1 < len(SEAM_Z) + 1 and bounds[index + 1] in SEAM_Z:
            zs = bounds[index + 1]
            tongue = blank.intersect(_prism(mid_half, zs, zs + LAP_DEPTH))
            piece = piece.fuse(tongue)
        # Hollow a matching socket for the tongue arriving from below.
        if bounds[index] in SEAM_Z:
            zs = bounds[index]
            socket = _prism(mid_half + LAP_CLEARANCE, zs - 1.0, zs + LAP_DEPTH + LAP_CLEARANCE)
            piece = piece.cut(socket)
        segments[name] = piece

    # Crush ribs on each tongue: the lower segment of every pair carries them.
    for index, zs in enumerate(SEAM_Z):
        owner = names[index]
        segments[owner] = segments[owner].fuse(_crush_ribs(zs))

    # Deliberate shadow line, cut equally from both sides of each seam.
    for zs in SEAM_Z:
        relief = _prism(BODY_HALF + 2.0, zs - SHADOW_HEIGHT / 2.0, zs + SHADOW_HEIGHT / 2.0).cut(
            _prism(BODY_HALF - SHADOW_DEPTH, zs - SHADOW_HEIGHT, zs + SHADOW_HEIGHT)
        )
        for name, piece in segments.items():
            segments[name] = piece.cut(relief)

    segments["shell_crown"] = _add_crown_retention(segments["shell_crown"])
    segments["shell_base"] = _add_base_retention(segments["shell_base"])
    return segments


def _crush_ribs(zs: float) -> cq.Shape:
    """Interference ribs at the four face centres of a tongue.

    The socket bore sits at mid + 0.25 mm; the ribs reach mid + 0.40 mm, so
    each joint closes on 0.15 mm of crush instead of rattling in clearance.
    Only the face centres are used, where the superellipse normal is axis
    aligned and a plain box is a true radial rib.
    """
    mid = BODY_HALF - SEAM_WALL / 2.0
    ribs: list[cq.Shape] = []
    for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        centre_x = sx * (mid + CRUSH_PROUD / 2.0)
        centre_y = sy * (mid + CRUSH_PROUD / 2.0)
        width = CRUSH_PROUD if sx else CRUSH_WIDTH
        depth = CRUSH_WIDTH if sx else CRUSH_PROUD
        box = cq.Workplane("XY", origin=(centre_x, centre_y, zs + 2.0)).box(
            width, depth, CRUSH_LENGTH, centered=(True, True, False)
        )
        ribs.append(cast(cq.Shape, box.val()))
    return cq.Compound.makeCompound(ribs)


def _add_crown_retention(crown: cq.Shape) -> cq.Shape:
    """Bolt the crown down onto the divider's shroud bosses.

    Four tabs, each webbed back to the skin so the screw load is carried into
    the wall rather than by an unsupported stalk.
    """
    p = V2
    tab_z = p.divider_bottom_z + p.divider_thickness + SHROUD_BOSS_HEIGHT
    outer = outer_body(BODY_BOTTOM_Z)
    for x, y in shroud_fastener_positions(p):
        tab = cq.Solid.makeCylinder(
            CROWN_TAB_RADIUS, CROWN_TAB_THICKNESS, cq.Vector(x, y, tab_z), cq.Vector(0, 0, 1)
        )
        reach = 2.0 * BODY_HALF
        if x:
            bridge = cq.Workplane(
                "XY", origin=(x + reach / 2.0 * (1 if x > 0 else -1), y, tab_z)
            ).box(reach, 9.0, CROWN_TAB_THICKNESS, centered=(True, True, False))
        else:
            bridge = cq.Workplane(
                "XY", origin=(x, y + reach / 2.0 * (1 if y > 0 else -1), tab_z)
            ).box(9.0, reach, CROWN_TAB_THICKNESS, centered=(True, True, False))
        crown = crown.fuse(tab).fuse(cast(cq.Shape, bridge.val()).intersect(outer))
        crown = crown.cut(
            cq.Solid.makeCylinder(
                p.fastener_clearance_diameter / 2.0,
                CROWN_TAB_THICKNESS,
                cq.Vector(x, y, tab_z),
                cq.Vector(0, 0, 1),
            )
        )
    return crown


def _add_base_retention(base: cq.Shape) -> cq.Shape:
    """Bolt the base segment down into the bottom service plate."""
    p = V2
    retention_z = p.shell_retention_z
    outer = outer_body(BODY_BOTTOM_Z)
    for x, y in cage_fastener_positions(p):
        boss = cq.Solid.makeCylinder(
            p.boss_outer_diameter / 2.0, 10.0, cq.Vector(x, y, retention_z), cq.Vector(0, 0, 1)
        )
        reach = 2.0 * BODY_HALF
        if x:
            bridge = cq.Workplane(
                "XY", origin=(x + reach / 2.0 * (1 if x > 0 else -1), y, retention_z)
            ).box(reach, 9.0, 6.0, centered=(True, True, False))
        else:
            bridge = cq.Workplane(
                "XY", origin=(x, y + reach / 2.0 * (1 if y > 0 else -1), retention_z)
            ).box(9.0, reach, 6.0, centered=(True, True, False))
        base = base.fuse(boss).fuse(cast(cq.Shape, bridge.val()).intersect(outer))
        base = base.cut(_blind_insert(x, y, retention_z, 1.0, p))
    return base


# --------------------------------------------------------------------- #
# Microphone isolation
# --------------------------------------------------------------------- #
# The mic array rides on the official stack.  Today that stack bolts to the
# divider, which bolts to the cabinet the driver is mounted in -- a direct
# mechanical path from the woofer to the microphones.
BUSHING_FLANGE_T = 2.0
BUSHING_FLANGE_D = 13.0
BUSHING_BODY_D = 8.6
# Counterbore depth is set by the shoulder screw, not chosen freely.  A stock
# 16 mm shoulder starting at the counterbore floor must end 0.3 mm above the
# mid-plate's top face at z = +3.2, so the floor sits at -12.5 and the body is
# -8.8 - (-12.5) = 3.7 mm deep.
SHOULDER_LENGTH = 16.0  # stock M3 x d4 shoulder screw
SHOULDER_DIAMETER = 4.0
HEAD_CLEARANCE = 0.3  # plate is captured, never clamped
MID_PLATE_TOP_Z = 3.2  # measured from the official CAD
BUSHING_BODY_H = 3.7
BUSHING_BORE_D = SHOULDER_DIAMETER + 0.2  # slip fit on the shoulder


def mic_isolation_bushing() -> cq.Shape:
    """TPU 95A top-hat isolating the official stack from the divider.

    Printed in the TPU already used for the anti-slip ring and gaskets.

    This part only works with an M3 x d4 shoulder screw, 16 mm shoulder.  The
    shoulder bottoms on the counterbore floor and its head stops 0.3 mm above
    the mid-plate, so the official stack rests on the elastomer and no clamping
    load passes through it.  With an ordinary M3 screw the fastener clamps in
    parallel with the elastomer at 1.005e8 N/m against 2.853e6 N/m -- 35x
    stiffer -- leaving the TPU carrying 2.8% of the path and isolating nothing.
    """
    flange = cq.Solid.makeCylinder(
        BUSHING_FLANGE_D / 2.0, BUSHING_FLANGE_T, cq.Vector(0, 0, 0), cq.Vector(0, 0, 1)
    )
    body = cq.Solid.makeCylinder(
        BUSHING_BODY_D / 2.0,
        BUSHING_BODY_H,
        cq.Vector(0, 0, -BUSHING_BODY_H),
        cq.Vector(0, 0, 1),
    )
    bore = cq.Solid.makeCylinder(
        BUSHING_BORE_D / 2.0,
        BUSHING_FLANGE_T + BUSHING_BODY_H + 2.0,
        cq.Vector(0, 0, -BUSHING_BODY_H - 1.0),
        cq.Vector(0, 0, 1),
    )
    return flange.fuse(body).cut(bore)


def visible_assembly() -> dict[str, cq.Shape]:
    from satellite1_ultra import official as o

    parts: dict[str, cq.Shape] = {"outer_shell": outer_shell()}
    for name, shape in o.official_upper_solids().items():
        if name in ("official_hat_batch1_rev4_1", "official_pcb_spacer"):
            continue
        parts[name] = shape
    return parts


def internal_assembly() -> dict[str, cq.Shape]:
    return {
        "outer_shell": outer_shell(),
        "main_cabinet": main_cabinet(),
        "pressure_divider": pressure_divider(),
    }


if __name__ == "__main__":
    from v2_silhouette import superellipse_area

    p = V2
    inner_half = BODY_HALF - CABINET_OFFSET - p.wall_thickness
    gross = superellipse_area(inner_half) * (p.acoustic_top_z - p.cavity_bottom_z) / 1.0e6
    print(f"cabinet inner        {2 * inner_half:8.1f} mm square")
    print(f"cavity height        {p.acoustic_top_z - p.cavity_bottom_z:8.1f} mm")
    print(f"gross sealed prism   {gross:8.3f} L   (v1: 3.966)")
    print(f"body                 {2 * BODY_HALF:.0f} sq x {TOP_Z - BODY_BOTTOM_Z:.1f} tall")
    cab = main_cabinet()
    print(f"cabinet volume       {cab.Volume() / 1.0e6:8.3f} L of material")
    print(
        f"cabinet bbox         {cab.BoundingBox().xlen:.1f} x {cab.BoundingBox().ylen:.1f}"
        f" x {cab.BoundingBox().zlen:.1f}"
    )
    sh = outer_shell()
    print(
        f"shell bbox           {sh.BoundingBox().xlen:.1f} x {sh.BoundingBox().ylen:.1f}"
        f" x {sh.BoundingBox().zlen:.1f}"
    )
