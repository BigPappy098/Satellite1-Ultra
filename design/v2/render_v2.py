"""Render the v2 flat-top monolith next to v1 for a like-for-like judgement."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import cadquery as cq  # noqa: E402

from satellite1_ultra import renders  # noqa: E402

# The stock tessellation is tuned for speed; a form review needs it smooth.
renders.TESSELLATION_TOLERANCE = 0.04
renders.ANGULAR_TOLERANCE = 0.08

from satellite1_ultra.geometry import (  # noqa: E402
    DEFAULT_PARAMETERS,
    electronics_shroud,
    outer_shell,
)
from satellite1_ultra.official import official_upper_solids  # noqa: E402
from v2_silhouette import report, solid_form, solved_layout  # noqa: E402

OUT = Path(__file__).parent
HIDE = ("official_hat_batch1_rev4_1", "official_pcb_spacer")


def v1_form() -> dict[str, cq.Shape]:
    parts: dict[str, cq.Shape] = {
        "body": outer_shell(DEFAULT_PARAMETERS),
        "shroud": electronics_shroud(DEFAULT_PARAMETERS),
    }
    parts.update({n: s for n, s in official_upper_solids().items() if n not in HIDE})
    return parts


def grey(parts: dict[str, cq.Shape]) -> dict[str, tuple[float, float, float]]:
    return {
        name: (0.60, 0.62, 0.65) if name.startswith("official") else (0.33, 0.35, 0.38)
        for name in parts
    }


def main() -> None:
    layout = solved_layout()
    report(layout)
    v2 = solid_form(layout)
    v1 = v1_form()

    for view in (renders.VIEWS[0], renders.VIEWS[1], renders.VIEWS[3]):
        renders._scene(
            OUT / f"v2_{view.name}.png",
            v2,
            f"v2 flat-top monolith — {view.name}",
            "superellipse body, rolled top edge, Sat1 flush in the top plane; "
            "184 sq x 270 tall",
            view=view,
            colors=grey(v2),
        )
    renders._scene(
        OUT / "v1_iso.png",
        v1,
        "v1 current — iso",
        "rounded-rectangle body, stepped shroud, perched top; 192 x 212 x 237",
        view=renders.VIEWS[0],
        colors=grey(v1),
    )
    print("rendered")


if __name__ == "__main__":
    main()
