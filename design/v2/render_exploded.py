"""Render the split shell: assembled, exploded, and from above."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import cadquery as cq

from satellite1_ultra import renders

renders.TESSELLATION_TOLERANCE = 0.05
renders.ANGULAR_TOLERANCE = 0.10

from parts import shell_segments, visible_assembly  # noqa: E402

from satellite1_ultra.official import official_upper_solids  # noqa: E402

OUT = Path(__file__).parent
HIDE = ("official_hat_batch1_rev4_1", "official_pcb_spacer")

SEGMENT_COLOR = {
    "shell_crown": (0.30, 0.33, 0.37),
    "shell_grille": (0.38, 0.41, 0.45),
    "shell_base": (0.30, 0.33, 0.37),
}


def exploded() -> dict[str, cq.Shape]:
    lift = {"shell_base": -70.0, "shell_grille": 0.0, "shell_crown": 70.0}
    parts: dict[str, cq.Shape] = {}
    for name, shape in shell_segments().items():
        parts[name] = shape.translate(cq.Vector(0.0, 0.0, lift[name]))
    for name, shape in official_upper_solids().items():
        if name not in HIDE:
            parts[name] = shape.translate(cq.Vector(0.0, 0.0, 130.0))
    return parts


def shade(parts: dict[str, cq.Shape]) -> dict[str, tuple[float, float, float]]:
    return {n: SEGMENT_COLOR.get(n, (0.62, 0.64, 0.67)) for n in parts}


def main() -> None:
    ex = exploded()
    renders._scene(
        OUT / "v2_exploded.png",
        ex,
        "v2 shell — three lapped segments",
        "longest print 146 mm; seams clear the grille by 5 mm; no hardware at the joints",
        view=renders.VIEWS[0],
        colors=shade(ex),
    )
    visible = visible_assembly()
    renders._scene(
        OUT / "v2_final_top.png",
        visible,
        "v2 — top",
        "Sat1 flush in the flat top to 0.005 mm, 0.4 mm hairline so it still lifts out",
        view=renders.VIEWS[3],
        colors=shade(visible),
    )
    renders._scene(
        OUT / "v2_final_side.png",
        visible,
        "v2 — side",
        "radiator window; smooth everywhere else",
        view=renders.VIEWS[2],
        colors=shade(visible),
    )
    print("rendered")


if __name__ == "__main__":
    main()
