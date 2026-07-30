"""High-quality review renders of the finished v2 form."""

from __future__ import annotations

from pathlib import Path

import cadquery as cq

from satellite1_ultra import renders
from satellite1_ultra.configuration import load_design_parameters
from satellite1_ultra.geometry import mic_isolation_bushing, official_mount_positions, skin_segments
from satellite1_ultra.official import official_upper_solids

OUT = Path(__file__).resolve().parents[1] / "reports" / "renders"
HIDE = ("official_hat_batch1_rev4_1", "official_pcb_spacer")

SHADE = {
    "shell_base": (0.29, 0.31, 0.34),
    "shell_grille": (0.33, 0.35, 0.38),
    "shell_crown": (0.29, 0.31, 0.34),
    "mic_isolation_bushing": (0.80, 0.58, 0.24),
}


def visible(parameters: cq.Shape) -> dict[str, cq.Shape]:
    parts: dict[str, cq.Shape] = dict(skin_segments(parameters))
    parts.update({n: s for n, s in official_upper_solids().items() if n not in HIDE})
    return parts


def exploded(parameters: cq.Shape) -> dict[str, cq.Shape]:
    lift = {"shell_base": -75.0, "shell_grille": 0.0, "shell_crown": 75.0}
    parts: dict[str, cq.Shape] = {}
    for name, shape in skin_segments(parameters).items():
        parts[name] = shape.translate(cq.Vector(0.0, 0.0, lift[name]))
    for index, (x, y) in enumerate(official_mount_positions(parameters)):
        parts[f"mic_isolation_bushing_{index}"] = mic_isolation_bushing(parameters).translate(
            cq.Vector(x, y, parameters.official_interface_z + 120.0)
        )
    for name, shape in official_upper_solids().items():
        if name not in HIDE:
            parts[name] = shape.translate(cq.Vector(0.0, 0.0, 145.0))
    return parts


def shade(parts: dict[str, cq.Shape]) -> dict[str, tuple[float, float, float]]:
    out = {}
    for name in parts:
        key = "mic_isolation_bushing" if name.startswith("mic_isolation") else name
        out[name] = SHADE.get(key, (0.60, 0.62, 0.65))
    return out


def main() -> None:
    renders.TESSELLATION_TOLERANCE = 0.025
    renders.ANGULAR_TOLERANCE = 0.06
    p = load_design_parameters()
    body = 2.0 * p.body_half
    height = p.shell_flat_top_z - p.shell_bottom_z
    note = (
        f"{body:.0f} x {body:.0f} x {height:.1f} mm  |  superellipse n = 4.13  |  "
        f"sealed 3.966 L  |  official top flush"
    )

    scene = visible(p)
    for view in (renders.VIEWS[0], renders.VIEWS[1], renders.VIEWS[2], renders.VIEWS[3]):
        renders._scene(
            OUT / f"v2_review_{view.name}.png",
            scene,
            f"Satellite1 Ultra v2 — {view.name}",
            note,
            view=view,
            colors=shade(scene),
        )
    ex = exploded(p)
    renders._scene(
        OUT / "v2_review_exploded.png",
        ex,
        "Satellite1 Ultra v2 — skin, isolators, official top",
        "three lapped skin segments; nothing here is glued",
        view=renders.VIEWS[0],
        colors=shade(ex),
    )
    print("rendered v2 review sheets")


if __name__ == "__main__":
    main()
