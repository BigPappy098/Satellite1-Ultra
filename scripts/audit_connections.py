"""Independent audit of every bolted joint and internal fit.

The validation suite passes, but it has already missed three real defects in
this design: an open trench where the flat top should be, crown bosses driven
into the official plate, and divider counterbores refilled by their own rib
frame. Each was found by looking at geometry rather than by a gate.

So this checks the thing the gates do not: for every fastener, that the
receiving part actually has material around its insert bore, that the passing
part actually has a clear hole aligned with it, and that the two are on the
same axis at the same height. Then it measures every skin segment against every
internal part.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

import cadquery as cq

from satellite1_ultra.configuration import load_design_parameters
from satellite1_ultra.geometry import (
    DesignParameters,
    _bolt_points,
    acoustic_mounts,
    ballast_cartridge,
    ballast_cartridge_lid,
    ballast_lid_fastener_positions,
    base_fastener_positions,
    base_skirt,
    bottom_plate_fastener_positions,
    bottom_service_plate,
    cage_fastener_positions,
    main_cabinet,
    official_mount_positions,
    placed_functional_parts,
    pressure_divider,
    shroud_fastener_positions,
    skin_segments,
    top_fastener_positions,
)

FAILURES: list[str] = []


def report(label: str, ok: bool, detail: str) -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {detail}")
    if not ok:
        FAILURES.append(f"{label}: {detail}")


@dataclass(frozen=True)
class Joint:
    """One bolted interface, described the way a screw actually experiences it."""

    name: str
    receiver: str  # part carrying the heat-set insert
    passer: str  # part the screw passes through
    positions: tuple[tuple[float, float], ...]
    insert_z: float  # plane the insert bore starts from
    insert_dir: float  # +1 bore runs up from that plane, -1 runs down
    pass_z0: float  # passing part's near face
    pass_z1: float  # passing part's far face


def _ring_material(
    shape: cq.Shape, x: float, y: float, z0: float, z1: float, r_inner: float, r_outer: float
) -> float:
    """Fraction of the annulus around an insert bore that is solid material."""
    outer = cq.Solid.makeCylinder(r_outer, z1 - z0, cq.Vector(x, y, z0), cq.Vector(0, 0, 1))
    inner = cq.Solid.makeCylinder(r_inner, z1 - z0, cq.Vector(x, y, z0), cq.Vector(0, 0, 1))
    probe = outer.cut(inner)
    reference = probe.Volume()
    return shape.intersect(probe).Volume() / reference if reference > 0 else 0.0


def _bore_is_clear(
    shape: cq.Shape, x: float, y: float, z0: float, z1: float, radius: float
) -> float:
    """Fraction of a screw's path through a part that is obstructed."""
    probe = cq.Solid.makeCylinder(radius, z1 - z0, cq.Vector(x, y, z0), cq.Vector(0, 0, 1))
    reference = probe.Volume()
    return shape.intersect(probe).Volume() / reference if reference > 0 else 1.0


def check_joint(joint: Joint, parts: dict[str, cq.Shape], p: DesignParameters) -> None:
    receiver, passer = parts[joint.receiver], parts[joint.passer]
    bore_r = p.insert_bore_diameter / 2.0
    boss_r = p.boss_outer_diameter / 2.0
    clear_r = p.fastener_clearance_diameter / 2.0
    depth = p.insert_bore_depth

    worst_material, worst_block, worst_at = 1.0, 0.0, ""
    for x, y in joint.positions:
        if joint.insert_dir > 0:
            z0, z1 = joint.insert_z, joint.insert_z + depth
        else:
            z0, z1 = joint.insert_z - depth, joint.insert_z
        # The insert needs a wall of material all the way round its bore.
        material = _ring_material(receiver, x, y, z0 + 0.5, z1 - 0.5, bore_r + 0.15, boss_r)
        # And the screw needs an unobstructed path through the other part.
        blocked = _bore_is_clear(
            passer,
            x,
            y,
            min(joint.pass_z0, joint.pass_z1),
            max(joint.pass_z0, joint.pass_z1),
            clear_r * 0.9,
        )
        if material < worst_material:
            worst_material, worst_at = material, f"({x:.0f},{y:.0f})"
        worst_block = max(worst_block, blocked)

    report(
        f"{joint.name}: insert seats in {joint.receiver}",
        worst_material > 0.90,
        f"worst boss wall {worst_material:.0%} solid at {worst_at}",
    )
    report(
        f"{joint.name}: screw clears {joint.passer}",
        worst_block < 0.02,
        f"worst obstruction {worst_block:.1%} of the bore",
    )


def main() -> int:
    p = load_design_parameters()
    print("Building parts...")
    segments = skin_segments(p)
    parts: dict[str, cq.Shape] = {
        "main_cabinet": main_cabinet(p),
        "pressure_divider": pressure_divider(p),
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
        **segments,
    }

    divider_top = p.divider_bottom_z + p.divider_thickness
    joints = (
        Joint(
            "divider -> cabinet",
            "main_cabinet",
            "pressure_divider",
            top_fastener_positions(p),
            p.acoustic_top_z,
            -1.0,
            p.divider_bottom_z,
            divider_top,
        ),
        Joint(
            "base skirt -> cabinet",
            "main_cabinet",
            "base_skirt",
            base_fastener_positions(p),
            p.acoustic_bottom_z,
            1.0,
            p.acoustic_bottom_z - 8.0,
            p.acoustic_bottom_z,
        ),
        Joint(
            "bottom plate -> skirt",
            "base_skirt",
            "bottom_service_plate",
            bottom_plate_fastener_positions(p),
            p.base_bottom_z + p.bottom_plate_thickness,
            1.0,
            p.base_bottom_z,
            p.base_bottom_z + p.bottom_plate_thickness,
        ),
        Joint(
            "skin base -> bottom plate",
            "shell_base",
            "bottom_service_plate",
            cage_fastener_positions(p),
            p.shell_retention_z,
            1.0,
            p.base_bottom_z,
            p.base_bottom_z + p.bottom_plate_thickness,
        ),
        Joint(
            "skin crown -> divider",
            "pressure_divider",
            "shell_crown",
            shroud_fastener_positions(p),
            divider_top + p.shroud_boss_height,
            -1.0,
            divider_top + p.shroud_boss_height,
            divider_top + p.shroud_boss_height + p.crown_tab_thickness,
        ),
        Joint(
            "official stack -> divider",
            "pressure_divider",
            "pressure_divider",
            official_mount_positions(p),
            p.shoulder_stop_z,
            -1.0,
            p.shoulder_stop_z,
            p.shoulder_stop_z + 0.01,
        ),
        Joint(
            "ballast lid -> tray",
            "ballast_cartridge",
            "ballast_cartridge_lid",
            ballast_lid_fastener_positions(p),
            p.base_bottom_z + p.bottom_plate_thickness + 16.0,
            -1.0,
            p.base_bottom_z + p.bottom_plate_thickness + 14.5,
            p.base_bottom_z + p.bottom_plate_thickness + 18.0,
        ),
    )

    print("\nBolted joints")
    for joint in joints:
        check_joint(joint, parts, p)

    print("\nAcoustic component mounts (clamp ring bolt circles into the cabinet)")
    cabinet = parts["main_cabinet"]
    for name, mount in acoustic_mounts(p).items():
        worst = 1.0
        for point in _bolt_points(mount.face_point, mount.inward, mount.bolt_circle):
            axis = cq.Vector(*mount.inward)
            start = cq.Vector(*point) + axis * (mount.ledge_depth + 0.5)
            outer = cq.Solid.makeCylinder(
                p.boss_outer_diameter / 2.0, p.insert_bore_depth - 1.0, start, axis
            )
            inner = cq.Solid.makeCylinder(
                p.insert_bore_diameter / 2.0 + 0.15, p.insert_bore_depth - 1.0, start, axis
            )
            probe = outer.cut(inner)
            worst = min(worst, cabinet.intersect(probe).Volume() / probe.Volume())
        report(f"{name}: insert bosses solid", worst > 0.90, f"worst wall {worst:.0%} solid")

    print("\nSkin segment laps")
    names = ("shell_base", "shell_grille", "shell_crown")
    for lower, upper in pairwise(names):
        overlap = segments[lower].intersect(segments[upper]).Volume()
        report(
            f"{lower} <-> {upper} crush fit",
            0.5 < overlap < 400.0,
            f"{overlap:.1f} mm3 of designed interference",
        )

    print("\nSkin clearance to everything inside it")
    internal = {
        k: v
        for k, v in placed_functional_parts(p).items()
        if not k.startswith("shell_") and "envelope" not in k
    }
    for seg_name in names:
        seg = segments[seg_name]
        worst_gap, worst_name = 1e9, ""
        for other_name, other in internal.items():
            volume = seg.intersect(other).Volume()
            if volume > 0.01:
                worst_gap, worst_name = -volume, other_name
                break
        if worst_gap < 0:
            report(f"{seg_name} vs internals", False, f"collides with {worst_name}")
        else:
            report(f"{seg_name} vs internals", True, "no intersection with any internal part")

    print("\nElectronics bay")
    crown = segments["shell_crown"]
    board = cq.Solid.makeBox(
        88.0, 88.0, 26.0, cq.Vector(-44.0, -44.0, p.divider_bottom_z + p.divider_thickness)
    )
    intrusion = crown.intersect(board).Volume()
    report("crown clears the board envelope", intrusion < 0.01, f"{intrusion:.2f} mm3 intrusion")

    print(f"\n{'ALL CONNECTION CHECKS PASSED' if not FAILURES else f'{len(FAILURES)} FAILED'}")
    for item in FAILURES:
        print(f"  - {item}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
