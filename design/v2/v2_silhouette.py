"""v2 seamless silhouette prototype — flat-top monolith.

One superellipse cross-section family for the whole product.  The body is
vertical, rolls over a generous top radius into a single flat plane, and the
official Satellite1 squircle drops into that plane dead flush: no lip, no
perched puck, no reveal.  Nothing here is production geometry; it exists to
judge the form.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

import cadquery as cq

# Superellipse exponent measured from the official lock ring (fit error 0.38 mm).
OFFICIAL_N = 4.13
OFFICIAL_HALF = 55.0          # official squircle is 110 mm across
OFFICIAL_TOP_Z = 17.09        # official top plate's top face — a true plane
OFFICIAL_FULL_Z = -7.0        # lowest z at which the official part is still 110 sq

BODY_HALF = 92.0              # 184 mm square body
TOP_Z = OFFICIAL_TOP_Z        # the product's flat top is the official top
TOP_ROLL = 22.0               # radius rolling the body into the flat top
BOTTOM_ROLL = 6.0             # quarter-round softening the ground edge
POCKET_CLEARANCE = 0.4        # hairline shadow gap around the official part

SHELL_WALL = 3.0
SHELL_GAP = 9.0               # shell inner face to cabinet outer face
CABINET_WALL = 4.0
CABINET_OFFSET = SHELL_WALL + SHELL_GAP
INNER_OFFSET = CABINET_OFFSET + CABINET_WALL


def body_half(z: float, z_bottom: float) -> float:
    """Outer half-size of the product silhouette at height *z*."""
    if z >= TOP_Z:
        return BODY_HALF - TOP_ROLL
    if z > TOP_Z - TOP_ROLL:
        # Quarter-round rolling the vertical body over into the flat top.
        d = (z - (TOP_Z - TOP_ROLL)) / TOP_ROLL
        return BODY_HALF - TOP_ROLL * (1.0 - math.sqrt(max(1.0 - d * d, 0.0)))
    if z < z_bottom + BOTTOM_ROLL:
        d = (z_bottom + BOTTOM_ROLL - z) / BOTTOM_ROLL
        return BODY_HALF - BOTTOM_ROLL * (1.0 - math.sqrt(max(1.0 - d * d, 0.0)))
    return BODY_HALF


def superellipse_wire(a: float, z: float, n: float = OFFICIAL_N, count: int = 160) -> cq.Wire:
    """Closed spline approximating |x/a|^n + |y/a|^n = 1 at height *z*."""
    points = []
    for i in range(count):
        t = 2.0 * math.pi * i / count
        c, s = math.cos(t), math.sin(t)
        x = a * math.copysign(abs(c) ** (2.0 / n), c)
        y = a * math.copysign(abs(s) ** (2.0 / n), s)
        points.append(cq.Vector(x, y, z))
    # periodic=True closes the curve itself; repeating the first point breaks it.
    return cq.Wire.assembleEdges([cq.Edge.makeSpline(points, periodic=True)])


def superellipse_area(a: float, n: float = OFFICIAL_N) -> float:
    """Exact area enclosed by the superellipse of half-size *a*."""
    return 4.0 * a * a * math.gamma(1.0 + 1.0 / n) ** 2 / math.gamma(1.0 + 2.0 / n)


def _prism(a: float, z0: float, z1: float) -> cq.Solid:
    face = cq.Face.makeFromWires(superellipse_wire(a, z0))
    return cq.Solid.extrudeLinear(face, cq.Vector(0.0, 0.0, z1 - z0))


def _roll(offset: float, z0: float, z1: float, z_bottom: float, steps: int = 14) -> cq.Solid:
    zs = [z0 + (z1 - z0) * i / steps for i in range(steps + 1)]
    wires = [superellipse_wire(max(body_half(z, z_bottom) - offset, 0.5), z) for z in zs]
    return cq.Solid.makeLoft(wires, ruled=False)


def outer_body(z_bottom: float, offset: float = 0.0) -> cq.Shape:
    """Solid bounded by the silhouette, inset by *offset*, base to flat top.

    Straight sections are true extrusions and only the two rolls are lofted, so
    a smooth loft cannot bulge the vertical body.
    """
    roll_top = z_bottom + BOTTOM_ROLL
    shoulder = TOP_Z - TOP_ROLL
    solid: cq.Shape = _roll(offset, z_bottom, roll_top, z_bottom)
    solid = solid.fuse(_prism(BODY_HALF - offset, roll_top, shoulder))
    return solid.fuse(_roll(offset, shoulder, TOP_Z, z_bottom))


@dataclass(frozen=True)
class Layout:
    z_bottom: float           # underside of the product
    cavity_floor: float       # inside face of the acoustic floor
    cavity_top: float         # underside of the pressure divider
    driver_axis: float
    pr_axis: float


def cavity_volume(layout: Layout) -> float:
    """Litres of sealed air in the straight-walled cabinet."""
    height = layout.cavity_top - layout.cavity_floor
    return superellipse_area(BODY_HALF - INNER_OFFSET) * height / 1.0e6


def solve_floor(layout: Layout, target_l: float) -> Layout:
    """Drop the cavity floor until the gross sealed prism hits *target_l*."""
    height = target_l * 1.0e6 / superellipse_area(BODY_HALF - INNER_OFFSET)
    return replace(layout, cavity_floor=layout.cavity_top - height)


def official_pocket(depth_to: float) -> cq.Shape:
    """Straight-sided well the official assembly lifts out of."""
    return _prism(OFFICIAL_HALF + POCKET_CLEARANCE, depth_to, TOP_Z + 1.0)


def solid_form(layout: Layout) -> dict[str, cq.Shape]:
    """The product as a viewer sees it: outer surface plus the official top."""
    from satellite1_ultra import official as o

    body = outer_body(layout.z_bottom).cut(official_pocket(OFFICIAL_FULL_Z - 12.0))
    parts: dict[str, cq.Shape] = {"body": body}
    for name, shape in o.official_upper_solids().items():
        if name in ("official_hat_batch1_rev4_1", "official_pcb_spacer"):
            continue
        parts[name] = shape
    return parts


def report(layout: Layout) -> None:
    inner = BODY_HALF - INNER_OFFSET
    print(f"footprint          {2 * BODY_HALF:8.1f} mm square")
    print(f"cabinet inner      {2 * inner:8.1f} mm square")
    print(f"section area       {superellipse_area(inner) / 100.0:8.1f} cm^2")
    print(f"cavity height      {layout.cavity_top - layout.cavity_floor:8.1f} mm")
    print(f"gross sealed prism {cavity_volume(layout):8.3f} L")
    print(f"cavity floor       {layout.cavity_floor:8.1f} mm")
    print(f"body bottom        {layout.z_bottom:8.1f} mm")
    total = TOP_Z - layout.z_bottom
    print(f"overall height     {total:8.1f} mm")
    print(f"aspect             {total / (2 * BODY_HALF):8.2f} : 1")
    print(f"flat top ring      {2 * (BODY_HALF - TOP_ROLL):8.1f} mm across "
          f"({BODY_HALF - TOP_ROLL - OFFICIAL_HALF:.1f} mm of flat around the Sat1)")


def solved_layout() -> Layout:
    base = Layout(
        z_bottom=-250.0, cavity_floor=-220.0, cavity_top=-34.0,
        driver_axis=-150.0, pr_axis=-165.0,
    )
    solved = solve_floor(base, 3.9664)
    # acoustic floor 8, ballast + base skirt 22, bottom plate 4
    return replace(solved, z_bottom=solved.cavity_floor - 8.0 - 22.0 - 4.0)


if __name__ == "__main__":
    report(solved_layout())
