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

from satellite1_ultra.geometry import (
    DEFAULT_PARAMETERS,
    DesignParameters,
    _apply_mount,
    _blind_insert,
    _compression_stop,
    acoustic_mounts,
    base_fastener_positions,
    official_mount_positions,
    top_fastener_positions,
)
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
    body_half,
    outer_body,
    superellipse_wire,
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
)

BODY_BOTTOM_Z = V2.base_bottom_z - 4.0

WINDOW_DIAMETER = 124.0        # grille field over each acoustic component
SLOT_WIDTH = 3.4
SLOT_PITCH = 7.0
FABRIC_GROOVE_W = 2.2
FABRIC_GROOVE_D = 1.5


def cabinet_envelope() -> cq.Shape:
    """Outer envelope of the sealed cabinet: a plain superellipse prism."""
    return _prism(BODY_HALF - CABINET_OFFSET, V2.acoustic_bottom_z, V2.acoustic_top_z)


@lru_cache(maxsize=4)
def main_cabinet() -> cq.Shape:
    """Sealed acoustic cabinet on the square superellipse section."""
    p = V2
    envelope = cabinet_envelope()
    cavity = _prism(BODY_HALF - CABINET_OFFSET - p.wall_thickness, p.cavity_bottom_z,
                    p.acoustic_top_z + 1.0)
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
            p.boss_outer_diameter / 2.0, boss_h,
            cq.Vector(x, y, p.acoustic_top_z - boss_h), cq.Vector(0.0, 0.0, 1.0),
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
            p.cable_passage_diameter / 2.0, p.divider_thickness,
            cq.Vector(p.cable_passage_x, p.cable_passage_y, z0), cq.Vector(0.0, 0.0, 1.0),
        )
    )
    for x, y in top_fastener_positions(p):
        divider = divider.cut(
            cq.Solid.makeCylinder(
                p.fastener_clearance_diameter / 2.0, p.divider_thickness,
                cq.Vector(x, y, z0), cq.Vector(0.0, 0.0, 1.0),
            )
        )
    interface_z = p.official_interface_z
    for x, y in official_mount_positions(p):
        boss = cq.Solid.makeCylinder(
            p.boss_outer_diameter / 2.0, interface_z - z0,
            cq.Vector(x, y, z0), cq.Vector(0.0, 0.0, 1.0),
        )
        divider = divider.fuse(boss)
        divider = divider.cut(_blind_insert(x, y, interface_z, -1.0, p))
    rib_bottom = z0 + p.divider_thickness
    for axis in ("x", "y"):
        for sign in (-1.0, 1.0):
            if axis == "x":
                origin, size = (0.0, sign * p.official_mount_y, rib_bottom), (
                    2.0 * p.official_mount_x, 5.0)
            else:
                origin, size = (sign * p.official_mount_x, 0.0, rib_bottom), (
                    5.0, 2.0 * p.official_mount_y)
            rib = cq.Workplane("XY", origin=origin).box(
                size[0], size[1], interface_z - rib_bottom, centered=(True, True, False)
            )
            divider = divider.fuse(cast(cq.Shape, rib.val()))
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
    print(f"cabinet bbox         {cab.BoundingBox().xlen:.1f} x {cab.BoundingBox().ylen:.1f}"
          f" x {cab.BoundingBox().zlen:.1f}")
    sh = outer_shell()
    print(f"shell bbox           {sh.BoundingBox().xlen:.1f} x {sh.BoundingBox().ylen:.1f}"
          f" x {sh.BoundingBox().zlen:.1f}")
