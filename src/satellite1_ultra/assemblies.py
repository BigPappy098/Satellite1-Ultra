"""Release assemblies: functional, complete-with-official, and exploded."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

import cadquery as cq
from cadquery.occ_impl.exporters.assembly import exportAssembly

from satellite1_ultra.configuration import ROOT
from satellite1_ultra.geometry import (
    DEFAULT_PARAMETERS,
    DesignParameters,
    placed_functional_parts,
)
from satellite1_ultra.official import PLACED_BOARDS, UPPER_STACK, board_keepout, load_part

Vector3 = tuple[float, float, float]


@dataclass(frozen=True)
class Placement:
    """Explosion direction and colour for one part in the release assembly."""

    direction: Vector3
    distance: float
    color: tuple[float, float, float]


#: Explosion vectors follow each part's documented removal direction.
PLACEMENTS: dict[str, Placement] = {
    "anti_slip_ring": Placement((0.0, 0.0, -1.0), 110.0, (0.10, 0.10, 0.10)),
    "outer_shell": Placement((0.0, 0.0, -1.0), 70.0, (0.35, 0.36, 0.38)),
    "bottom_service_plate": Placement((0.0, 0.0, -1.0), 45.0, (0.20, 0.22, 0.25)),
    "ballast_cartridge_lid": Placement((0.0, 0.0, -1.0), 30.0, (0.35, 0.37, 0.40)),
    "ballast_cartridge": Placement((0.0, 0.0, -1.0), 18.0, (0.30, 0.32, 0.35)),
    "base_skirt": Placement((0.0, 0.0, -1.0), 8.0, (0.13, 0.15, 0.18)),
    "main_cabinet": Placement((0.0, 0.0, 0.0), 0.0, (0.16, 0.18, 0.21)),
    "active_driver_gasket": Placement((0.0, -1.0, 0.0), 55.0, (0.12, 0.12, 0.12)),
    "driver_envelope": Placement((0.0, -1.0, 0.0), 75.0, (0.70, 0.30, 0.08)),
    "active_driver_clamp_ring": Placement((0.0, -1.0, 0.0), 100.0, (0.45, 0.46, 0.48)),
    "divider_gasket": Placement((0.0, 0.0, 1.0), 22.0, (0.12, 0.12, 0.12)),
    "pressure_divider": Placement((0.0, 0.0, 1.0), 34.0, (0.25, 0.28, 0.32)),
    "wire_gland": Placement((0.0, 0.0, 1.0), 46.0, (0.12, 0.12, 0.12)),
    "electronics_shroud": Placement((0.0, 0.0, 1.0), 60.0, (0.22, 0.24, 0.27)),
}
for _side, _sign in ((-1, -1.0), (1, 1.0)):
    PLACEMENTS[f"pr_{_side:+d}_gasket"] = Placement((_sign, 0.0, 0.0), 55.0, (0.12, 0.12, 0.12))
    PLACEMENTS[f"pr_{_side:+d}_envelope"] = Placement((_sign, 0.0, 0.0), 75.0, (0.12, 0.40, 0.72))
    PLACEMENTS[f"pr_{_side:+d}_clamp_ring"] = Placement(
        (_sign, 0.0, 0.0), 100.0, (0.45, 0.46, 0.48)
    )

OFFICIAL_EXPLOSION = 95.0


def _placement(name: str) -> Placement:
    return PLACEMENTS.get(name, Placement((0.0, 0.0, 1.0), 40.0, (0.5, 0.5, 0.5)))


def release_parts(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
    include_official: bool = True,
) -> dict[str, cq.Shape]:
    """Every solid in the release assembly, in master coordinates.

    Official *mechanical* parts are included as their exact B-reps.  The
    official boards are included as their conservative envelopes: the full HAT
    B-rep is 780 solids and 39 MB, which makes a release package unusable, and
    it is preserved byte-for-byte at its provenance path in any case.
    """
    parts = dict(placed_functional_parts(parameters))
    if include_official:
        for official in UPPER_STACK:
            parts[official.name] = load_part(official)
        for board in PLACED_BOARDS[parameters.board_revision]:
            parts[f"{board.name}_envelope"] = board_keepout(board)
    return parts


def release_assembly(
    parameters: DesignParameters = DEFAULT_PARAMETERS,
    include_official: bool = True,
    exploded: bool = False,
) -> cq.Assembly:
    """Build the release assembly, optionally exploded along removal directions."""
    name = "satellite1_ultra_exploded" if exploded else "satellite1_ultra_assembly"
    assembly = cq.Assembly(name=name)
    for part_name, shape in release_parts(parameters, include_official).items():
        placement = _placement(part_name)
        if part_name.startswith("official"):
            placed = shape.translate(cq.Vector(0.0, 0.0, OFFICIAL_EXPLOSION)) if exploded else shape
            color = cq.Color(0.62, 0.64, 0.67)
        else:
            offset = cq.Vector(*placement.direction) * (placement.distance if exploded else 0.0)
            placed = shape.translate(offset)
            color = cq.Color(*placement.color)
        assembly.add(placed, name=part_name, color=color)
    return assembly


def export_assemblies(
    output: Path = ROOT / "exports" / "assembly",
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> dict[str, Path]:
    """Write the functional, complete and exploded STEP assemblies."""
    output.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for label, official, exploded in (
        ("satellite1_ultra_functional", False, False),
        ("satellite1_ultra_complete", True, False),
        ("satellite1_ultra_exploded", True, True),
    ):
        assembly = release_assembly(parameters, official, exploded)
        path = output / f"{label}.step"
        exportAssembly(assembly, str(path))
        written[label] = path
    return written


def reopen_assembly(path: Path) -> cq.Shape:
    """Reopen an exported STEP assembly through the OCCT reader."""
    from cadquery import importers

    return cast(cq.Shape, importers.importStep(str(path)).val())
