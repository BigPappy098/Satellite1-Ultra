"""Geometric checks on the v2 split shell and the isolated official interface."""

from __future__ import annotations

import sys
from itertools import pairwise
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import cadquery as cq
from parts import (
    BODY_BOTTOM_Z,
    BUSHING_BODY_H,
    BUSHING_BORE_D,
    BUSHING_FLANGE_T,
    CROWN_TAB_THICKNESS,
    CRUSH_PROUD,
    HEAD_CLEARANCE,
    LAP_CLEARANCE,
    LAP_DEPTH,
    MID_PLATE_TOP_Z,
    SEAM_WALL,
    SEAM_Z,
    SHOULDER_DIAMETER,
    SHOULDER_LENGTH,
    SHROUD_BOSS_HEIGHT,
    V2,
    main_cabinet,
    mic_isolation_bushing,
    pressure_divider,
    shell_segments,
)
from v2_silhouette import BODY_HALF, TOP_Z

from satellite1_ultra.geometry import cage_fastener_positions, shroud_fastener_positions

BED_X, BED_Y = 220.0, 200.0


def check(label: str, ok: bool, detail: str) -> bool:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {detail}")
    return ok


def main() -> int:
    failures = 0
    print("Shell segments")
    segments = shell_segments()
    for name, shape in segments.items():
        box = shape.BoundingBox()
        fits = (box.xlen <= BED_X and box.ylen <= BED_Y) or (
            box.ylen <= BED_X and box.xlen <= BED_Y
        )
        failures += not check(
            f"{name} fits {BED_X:.0f}x{BED_Y:.0f} bed",
            fits,
            f"{box.xlen:.1f} x {box.ylen:.1f} x {box.zlen:.1f}",
        )
        failures += not check(
            f"{name} is one solid", len(shape.Solids()) == 1, f"{len(shape.Solids())} solid(s)"
        )

    print("\nLap fit (analytic)")
    corner = LAP_CLEARANCE * 1.202  # superellipse scaling at 45 degrees
    failures += not check(
        "radial clearance in range",
        0.15 <= LAP_CLEARANCE <= 0.35 and corner <= 0.4,
        f"{LAP_CLEARANCE:.2f} mm at the face, {corner:.2f} mm at the corner",
    )
    failures += not check(
        "engagement >= 3x wall",
        LAP_DEPTH >= 3.0 * SEAM_WALL / 2.0,
        f"{LAP_DEPTH:.0f} mm lap on a {SEAM_WALL / 2.0:.1f} mm tongue",
    )
    failures += not check(
        "seams clear the grille windows",
        all(abs(z - (-117.0)) > 62.0 for z in SEAM_Z),
        f"seams at {SEAM_Z}, windows span -179 to -55",
    )

    print("\nSolid interference between adjacent segments")
    names = list(segments)
    for lower, upper in pairwise(names):
        overlap = segments[lower].intersect(segments[upper]).Volume() / 1.0e3
        failures += not check(f"{lower} vs {upper}", overlap < 0.05, f"{overlap:.4f} cm3 overlap")

    print("\nSkin retention (the shell must not lift off or rattle)")
    p = V2
    tab_z = p.divider_bottom_z + p.divider_thickness + SHROUD_BOSS_HEIGHT
    for x, y in shroud_fastener_positions(p):
        probe = cq.Solid.makeCylinder(
            p.fastener_clearance_diameter / 2.0 + 1.2,
            CROWN_TAB_THICKNESS,
            cq.Vector(x, y, tab_z),
            cq.Vector(0, 0, 1),
        )
        got = segments["shell_crown"].intersect(probe).Volume()
        failures += not check(
            f"crown tab at ({x:.0f},{y:.0f})", got > 1.0, f"{got:.1f} mm3 of material"
        )
    for x, y in cage_fastener_positions(p):
        probe = cq.Solid.makeCylinder(
            p.boss_outer_diameter / 2.0,
            6.0,
            cq.Vector(x, y, p.shell_retention_z),
            cq.Vector(0, 0, 1),
        )
        got = segments["shell_base"].intersect(probe).Volume()
        failures += not check(
            f"base boss at ({x:.0f},{y:.0f})", got > 1.0, f"{got:.1f} mm3 of material"
        )
    interference = CRUSH_PROUD - LAP_CLEARANCE
    failures += not check(
        "crush ribs preload the lap",
        0.10 <= interference <= 0.25,
        f"{interference:.2f} mm interference against the socket bore",
    )

    print("\nOfficial interface isolation")
    divider = pressure_divider()
    seat = V2.official_interface_z + BUSHING_FLANGE_T
    failures += not check(
        "stack still seats at -6.8", abs(seat - (-6.8)) < 1e-9, f"seat lands at {seat:.2f} mm"
    )
    bushing = mic_isolation_bushing()
    failures += not check(
        "bushing height matches counterbore + flange",
        abs(bushing.BoundingBox().zlen - (BUSHING_BODY_H + BUSHING_FLANGE_T)) < 1e-6,
        f"{bushing.BoundingBox().zlen:.2f} mm",
    )
    failures += not check(
        "divider is one solid", len(divider.Solids()) == 1, f"{len(divider.Solids())} solid(s)"
    )
    # The shoulder must bottom on the counterbore floor and stop clear of the
    # plate, otherwise the screw clamps and the elastomer does nothing.
    floor = V2.official_interface_z - BUSHING_BODY_H
    head = floor + SHOULDER_LENGTH
    failures += not check(
        "shoulder screw captures without clamping",
        abs(head - (MID_PLATE_TOP_Z + HEAD_CLEARANCE)) < 1e-9,
        f"stock {SHOULDER_LENGTH:.0f} mm shoulder from {floor:.1f} ends at {head:.1f}, "
        f"plate top {MID_PLATE_TOP_Z:.1f}, clearance {head - MID_PLATE_TOP_Z:.2f} mm",
    )
    failures += not check(
        "bushing bore clears the shoulder",
        0.05 <= (BUSHING_BORE_D - SHOULDER_DIAMETER) / 2.0 <= 0.2,
        f"{(BUSHING_BORE_D - SHOULDER_DIAMETER) / 2.0:.2f} mm radial on a "
        f"d{SHOULDER_DIAMETER:.0f} shoulder",
    )

    print("\nOverall")
    cab = main_cabinet()
    box = cab.BoundingBox()
    failures += not check(
        "cabinet fits bed",
        box.xlen <= BED_X and box.ylen <= BED_Y,
        f"{box.xlen:.1f} x {box.ylen:.1f} x {box.zlen:.1f}",
    )
    print(
        f"  product envelope: {2 * BODY_HALF:.0f} x {2 * BODY_HALF:.0f} x "
        f"{TOP_Z - BODY_BOTTOM_Z:.1f} mm"
    )
    print(f"\n{'ALL CHECKS PASSED' if failures == 0 else f'{failures} CHECK(S) FAILED'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
