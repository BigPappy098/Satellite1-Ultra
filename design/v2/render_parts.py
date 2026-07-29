"""Render the v2 production-candidate parts."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import cadquery as cq

from satellite1_ultra import renders

renders.TESSELLATION_TOLERANCE = 0.05
renders.ANGULAR_TOLERANCE = 0.10

from parts import internal_assembly, visible_assembly  # noqa: E402

OUT = Path(__file__).parent


def shade(parts: dict[str, cq.Shape]) -> dict[str, tuple[float, float, float]]:
    palette = {
        "outer_shell": (0.33, 0.35, 0.38),
        "main_cabinet": (0.55, 0.42, 0.30),
        "pressure_divider": (0.30, 0.45, 0.55),
    }
    return {n: palette.get(n, (0.60, 0.62, 0.65)) for n in parts}


def main() -> None:
    visible = visible_assembly()
    for view in (renders.VIEWS[0], renders.VIEWS[1]):
        renders._scene(
            OUT / f"v2_parts_{view.name}.png",
            visible,
            f"v2 shell with acoustic windows — {view.name}",
            "smooth superellipse skin; grille only over the driver and the two radiators",
            view=view,
            colors=shade(visible),
        )
    internal = internal_assembly()
    renders._scene(
        OUT / "v2_internal_iso.png",
        internal,
        "v2 internals — iso",
        "shell, sealed cabinet and pressure divider on the square 160 mm section",
        view=renders.VIEWS[0],
        colors=shade(internal),
    )
    print("rendered")


if __name__ == "__main__":
    main()
