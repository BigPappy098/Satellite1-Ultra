"""Render what the skin hides: the cabinet's mounts, bosses and interfaces."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import cadquery as cq

from satellite1_ultra import renders

renders.TESSELLATION_TOLERANCE = 0.05
renders.ANGULAR_TOLERANCE = 0.10

from parts import (  # noqa: E402
    BODY_BOTTOM_Z,
    V2,
    main_cabinet,
    mic_isolation_bushing,
    pressure_divider,
    shell_segments,
)
from v2_silhouette import TOP_Z  # noqa: E402

from satellite1_ultra.geometry import (  # noqa: E402
    official_mount_positions,
)

OUT = Path(__file__).parent

COLORS = {
    "main_cabinet": (0.62, 0.47, 0.31),
    "pressure_divider": (0.26, 0.47, 0.55),
    "shell_base": (0.34, 0.37, 0.40),
    "shell_grille": (0.40, 0.43, 0.47),
    "shell_crown": (0.34, 0.37, 0.40),
}


def half(shape: cq.Shape) -> cq.Shape:
    """Remove the +Y half so the interior is visible."""
    cutter = cq.Solid.makeBox(400.0, 260.0, 500.0, cq.Vector(-200.0, 0.0, BODY_BOTTOM_Z - 20.0))
    return shape.cut(cutter)


def shade(parts: dict[str, cq.Shape]) -> dict[str, tuple[float, float, float]]:
    return {n: COLORS.get(n, (0.60, 0.62, 0.65)) for n in parts}


def main() -> None:
    # 1. The cabinet on its own: every acoustic mount and fastener boss.
    cabinet = {"main_cabinet": main_cabinet(), "pressure_divider": pressure_divider()}
    renders._scene(
        OUT / "v2_cabinet.png",
        cabinet,
        "v2 cabinet and divider — what the skin hides",
        "driver mount on -Y, radiator mounts on +/-X, 8 divider bosses, 4 base pads",
        view=renders.VIEWS[0],
        colors=shade(cabinet),
    )

    # 2. Cut away, so the seats, bores and gasket lands read from inside.
    cut = {name: half(shape) for name, shape in cabinet.items()}
    for name, shape in shell_segments().items():
        cut[name] = half(shape)
    renders._scene(
        OUT / "v2_cutaway.png",
        cut,
        "v2 cutaway — skin, cabinet, divider",
        "sealed cabinet inside the cosmetic skin; 9 mm radial gap all round",
        view=renders.VIEWS[0],
        colors=shade(cut),
    )

    bushings: dict[str, cq.Shape] = {}
    for index, (x, y) in enumerate(official_mount_positions(V2)):
        bushings[f"bushing_{index}"] = mic_isolation_bushing().translate(
            cq.Vector(x, y, V2.official_interface_z)
        )
    print("official interface z:", V2.official_interface_z)
    print("top z:", TOP_Z)
    print("rendered")


if __name__ == "__main__":
    main()
