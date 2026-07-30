"""Official FutureProofHomes geometry import and master-datum placement.

The preserved files under ``reference-assets/official`` are never modified.
This module only *places* them into the documented master coordinate system and
derives conservative keep-out solids from them.

Two independent representations of the official electronics are used:

``load_part``
    Exact OCCT B-rep import of the official STEP file.  Authoritative for
    dimensions and datum verification.

``board_keepout``
    A conservative convex-band envelope built from the official STL twin of the
    same board.  Every point of the real board lies inside this envelope, so a
    clearance proved against it is proved against the board.  It exists because
    exact booleans against the 39 MB HAT B-rep do not complete in a usable time
    (measured: > 20 min for a single pairwise intersection).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import cast

import cadquery as cq
import numpy as np
import trimesh
from cadquery import importers
from numpy.typing import NDArray

ROOT = Path(__file__).resolve().parents[2]
OFFICIAL = ROOT / "reference-assets" / "official" / "Satellite1-Enclosures"

#: Master datum: the official 25 W speaker-chamber upper interface plane, taken
#: from the preserved STEP file's native Z.  DERIVED_FROM_OFFICIAL_CAD.
MASTER_INTERFACE_Z = 140.8

#: Official mid-plate underside, i.e. the plane a derived adapter must present.
#: Measured on the preserved mid-plate B-rep. DERIVED_FROM_OFFICIAL_CAD.
OFFICIAL_INTERFACE_Z = -6.8

#: Official four-point mid-plate mount pattern. DERIVED_FROM_OFFICIAL_CAD.
OFFICIAL_MOUNT_X = 45.0534
OFFICIAL_MOUNT_Y = 31.5467


@dataclass(frozen=True)
class OfficialPart:
    """An immutable official asset and its placement in the master system."""

    name: str
    relative_path: str
    color: tuple[float, float, float, float]
    translation: tuple[float, float, float] = (0.0, 0.0, -MASTER_INTERFACE_Z)
    mesh_path: str | None = None
    placement_evidence: str = "DERIVED_FROM_OFFICIAL_CAD"

    @property
    def path(self) -> Path:
        return OFFICIAL / self.relative_path

    @property
    def mesh(self) -> Path | None:
        return None if self.mesh_path is None else OFFICIAL / self.mesh_path


@dataclass(frozen=True)
class OfficialPrintPart:
    """One unmodified official printable included in the builder release."""

    identifier: str
    name: str
    filename: str
    stl_relative_path: str
    step_relative_path: str
    role: str
    required: bool = True
    quantity: int = 1
    material: str = "ASA (PETG alternative)"

    @property
    def stl_path(self) -> Path:
        return OFFICIAL / self.stl_relative_path

    @property
    def step_path(self) -> Path:
        return OFFICIAL / self.step_relative_path


_SQUIRCLE = "DIY Enclosures/Squircle Enclosures/Geometry Files"

MID_PLATE = OfficialPart(
    "official_mid_plate",
    f"{_SQUIRCLE}/STEP/Mid-Plate/Mid-Plate.step",
    (0.25, 0.28, 0.32, 1.0),
    mesh_path=f"{_SQUIRCLE}/STL/Mid-Plate/Mid-Plate.stl",
)
MID_PLATE_THREADS = OfficialPart(
    "official_mid_plate_threads",
    f"{_SQUIRCLE}/STEP/Mid-Plate/Mid-Plate Threads.step",
    (0.18, 0.20, 0.23, 1.0),
    mesh_path=f"{_SQUIRCLE}/STL/Mid-Plate/Mid-Plate Threads.stl",
)
TOP_PLATE = OfficialPart(
    "official_top_plate",
    f"{_SQUIRCLE}/STEP/Squircle Top/Top Plate Combined MM.step",
    (0.83, 0.84, 0.86, 1.0),
    mesh_path=f"{_SQUIRCLE}/STL/Squircle Top/Top Plate Combined MM.stl",
)
PCB_SPACER = OfficialPart(
    "official_pcb_spacer",
    f"{_SQUIRCLE}/STEP/Squircle Top/PCB Spacer.step",
    (0.70, 0.72, 0.75, 1.0),
    mesh_path=f"{_SQUIRCLE}/STL/Squircle Top/PCB Spacer.stl",
)
LOCK_RING = OfficialPart(
    "official_lock_ring",
    f"{_SQUIRCLE}/STEP/Squircle Top/Lock Ring.step",
    (0.15, 0.16, 0.18, 1.0),
    mesh_path=f"{_SQUIRCLE}/STL/Squircle Top/Lock Ring.stl",
)
SPEAKER_CHAMBER_25W = OfficialPart(
    "official_25w_speaker_chamber",
    f"{_SQUIRCLE}/STEP/Speaker Chamber/25-Watt Speaker Chamber.step",
    (0.25, 0.28, 0.32, 1.0),
    mesh_path=f"{_SQUIRCLE}/STL/Speaker Chamber/25-Watt Speaker Chamber.stl",
)

#: HAT placement: official PCB-spacer top plane (native Z = 150.0, master
#: Z = 9.2) with the HAT's six-hole outline aligned to the spacer's four-hole
#: pattern.  DERIVED_FROM_OFFICIAL_CAD.
BATCH1_HAT = OfficialPart(
    "official_hat_batch1_rev4_1",
    "assets/Hat R2024.12.06.step",
    (0.05, 0.34, 0.13, 1.0),
    (0.0, -0.999, 9.2),
    mesh_path="assets/Hat R2024.12.06.stl",
)
BATCH2_HAT = OfficialPart(
    "official_hat_batch2_rev6_1",
    "assets/Hat R2025.03.18.step",
    (0.05, 0.34, 0.13, 1.0),
    (0.0, -0.999, 9.2),
    mesh_path="assets/Hat R2025.03.18.stl",
)

#: Core placement requires physical validation. The published FutureProofHomes assets do
#: not contain an assembled Core+HAT model, and every stack-up this project
#: trialled put the Core inside the official mid-plate solid, so no placement is
#: asserted.  The Core is registered here for provenance and for its measured
#: overall size only; enclosure validation instead proves that a Core-sized
#: clearance volume fits in the electronics bay (see
#: :func:`core_clearance_extent` and the core-fit validation gate).
BATCH1_CORE = OfficialPart(
    "official_core_batch1_rev4_1",
    "assets/Core R2024.12.06.step",
    (0.05, 0.24, 0.34, 1.0),
    (0.0, 0.0, 0.0),
    mesh_path="assets/Core R2024.12.06.stl",
    placement_evidence="REQUIRES_PHYSICAL_VALIDATION",
)
BATCH2_CORE = OfficialPart(
    "official_core_batch2_rev5_1",
    "assets/Core R2025.03.18.step",
    (0.05, 0.24, 0.34, 1.0),
    (0.0, 0.0, 0.0),
    mesh_path="assets/Core R2025.03.stl",
    placement_evidence="REQUIRES_PHYSICAL_VALIDATION",
)

#: O06 snaps into the single-material top plate.  It is a required print, so it
#: belongs in the assembly and in every clearance and collision gate; leaving it
#: out meant builders fitted a part the CAD had never checked in place.
TOP_PLATE_SNAP_IN_DIFFUSER_RING = OfficialPart(
    "official_top_plate_snap_in_diffuser_ring",
    f"{_SQUIRCLE}/STEP/Squircle Top/Top Plate Snap-In Diffuser Ring.step",
    (0.88, 0.89, 0.91, 1.0),
    mesh_path=f"{_SQUIRCLE}/STL/Squircle Top/Top Plate Snap-In Diffuser Ring.stl",
)

UPPER_STACK = (
    MID_PLATE,
    MID_PLATE_THREADS,
    TOP_PLATE,
    PCB_SPACER,
    LOCK_RING,
    TOP_PLATE_SNAP_IN_DIFFUSER_RING,
)

_SQUIRCLE_STL = f"{_SQUIRCLE}/STL"
_SQUIRCLE_STEP = f"{_SQUIRCLE}/STEP"

# These are the complete official Squircle prints needed by the Ultra.  The
# original speaker chamber, speaker plate and anti-slip ring are deliberately
# excluded because the Ultra cabinet, base and TPU ring replace them.
OFFICIAL_PRINT_PARTS_REQUIRED = (
    OfficialPrintPart(
        "O01",
        "official_mid_plate",
        "official_mid_plate.stl",
        f"{_SQUIRCLE_STL}/Mid-Plate/Mid-Plate.stl",
        f"{_SQUIRCLE_STEP}/Mid-Plate/Mid-Plate.step",
        "Satellite1 electronics mid-plate",
    ),
    OfficialPrintPart(
        "O02",
        "official_mid_plate_threads",
        "official_mid_plate_threads.stl",
        f"{_SQUIRCLE_STL}/Mid-Plate/Mid-Plate Threads.stl",
        f"{_SQUIRCLE_STEP}/Mid-Plate/Mid-Plate Threads.step",
        "threaded interface between the mid-plate and top assembly",
    ),
    OfficialPrintPart(
        "O03",
        "official_pcb_spacer",
        "official_pcb_spacer.stl",
        f"{_SQUIRCLE_STL}/Squircle Top/PCB Spacer.stl",
        f"{_SQUIRCLE_STEP}/Squircle Top/PCB Spacer.step",
        "locates the HAT below the top plate",
    ),
    OfficialPrintPart(
        "O04",
        "official_lock_ring",
        "official_lock_ring.stl",
        f"{_SQUIRCLE_STL}/Squircle Top/Lock Ring.stl",
        f"{_SQUIRCLE_STEP}/Squircle Top/Lock Ring.step",
        "locks the top plate to the threaded interface",
    ),
    OfficialPrintPart(
        "O05",
        "official_top_plate",
        "official_top_plate.stl",
        f"{_SQUIRCLE_STL}/Squircle Top/Top Plate.stl",
        f"{_SQUIRCLE_STEP}/Squircle Top/Top Plate.step",
        "single-material top plate",
    ),
    OfficialPrintPart(
        "O06",
        "official_top_plate_snap_in_diffuser_ring",
        "official_top_plate_snap_in_diffuser_ring.stl",
        f"{_SQUIRCLE_STL}/Squircle Top/Top Plate Snap-In Diffuser Ring.stl",
        f"{_SQUIRCLE_STEP}/Squircle Top/Top Plate Snap-In Diffuser Ring.step",
        "snap-in LED diffuser for the single-material top plate",
    ),
)

OFFICIAL_PRINT_PARTS_OPTIONAL_MM = (
    OfficialPrintPart(
        "O07",
        "official_top_plate_mm_buttons",
        "official_top_plate_mm_buttons.stl",
        f"{_SQUIRCLE_STL}/Squircle Top/Top Plate MM Buttons.stl",
        f"{_SQUIRCLE_STEP}/Squircle Top/Top Plate MM Buttons.step",
        "optional multi-material button inserts",
        required=False,
    ),
    OfficialPrintPart(
        "O08",
        "official_top_plate_mm_diffuser_ring",
        "official_top_plate_mm_diffuser_ring.stl",
        f"{_SQUIRCLE_STL}/Squircle Top/Top Plate MM Diffuser Ring.stl",
        f"{_SQUIRCLE_STEP}/Squircle Top/Top Plate MM Diffuser Ring.step",
        "optional multi-material diffuser; replaces O06",
        required=False,
    ),
)
OFFICIAL_PRINT_PARTS = OFFICIAL_PRINT_PARTS_REQUIRED + OFFICIAL_PRINT_PARTS_OPTIONAL_MM

#: Boards whose placement in the master system is established.
PLACED_BOARDS = {"public_batch_1": (BATCH1_HAT,), "public_batch_2": (BATCH2_HAT,)}
#: Boards whose placement is not established; size only.
UNPLACED_BOARDS = {"public_batch_1": (BATCH1_CORE,), "public_batch_2": (BATCH2_CORE,)}


@cache
def load_part(part: OfficialPart) -> cq.Shape:
    """Load and place an official STEP asset without modifying source bytes."""
    if not part.path.is_file():
        raise FileNotFoundError(part.path)
    shape = cast(cq.Shape, importers.importStep(str(part.path)).val())
    return shape.translate(cq.Vector(*part.translation))


@cache
def load_official_mesh(part: OfficialPart) -> trimesh.Trimesh:
    """Load and place the official STL twin of ``part``."""
    if part.mesh is None or not part.mesh.is_file():
        raise FileNotFoundError(part.mesh or part.relative_path)
    mesh = trimesh.load_mesh(str(part.mesh), process=False)
    mesh.apply_translation(np.asarray(part.translation, dtype=np.float64))
    assert isinstance(mesh, trimesh.Trimesh)
    return mesh


def _band_hull_prism(points: NDArray[np.float64], z0: float, z1: float) -> cq.Shape | None:
    """Convex hull of ``points`` in XY, extruded from ``z0`` to ``z1``."""
    from scipy.spatial import ConvexHull, QhullError  # type: ignore[import-untyped]

    if len(points) < 3:
        return None
    try:
        hull = ConvexHull(points[:, :2])
    except (QhullError, ValueError):
        return None
    loop: list[tuple[float, float]] = [
        (float(points[index, 0]), float(points[index, 1])) for index in hull.vertices
    ]
    if len(loop) < 3:
        return None
    return cast(
        cq.Shape,
        cq.Workplane("XY", origin=(0.0, 0.0, z0)).polyline(loop).close().extrude(z1 - z0).val(),
    )


@cache
def board_keepout(part: OfficialPart, bands: int = 10) -> cq.Shape:
    """Conservative convex-band B-rep envelope around an official board.

    Every vertex of the official mesh lies inside the returned solid, so any
    clearance proved against this solid holds for the real board.
    """
    mesh = load_official_mesh(part)
    vertices = np.asarray(mesh.vertices, dtype=np.float64)
    z_min, z_max = float(vertices[:, 2].min()), float(vertices[:, 2].max())
    edges = np.linspace(z_min, z_max, bands + 1)
    solid: cq.Shape | None = None
    for index in range(bands):
        low, high = float(edges[index]), float(edges[index + 1])
        mask = (vertices[:, 2] >= low - 1e-9) & (vertices[:, 2] <= high + 1e-9)
        prism = _band_hull_prism(vertices[mask], low, high)
        if prism is None:
            continue
        solid = prism if solid is None else solid.fuse(prism)
    if solid is None:  # pragma: no cover - an empty official mesh is a data fault
        raise ValueError(f"no usable geometry in {part.name}")
    return solid


def upper_reference_assembly(board_revision: str = "public_batch_1") -> cq.Assembly:
    """Return the official upper stack and the selected official board set."""
    assembly = cq.Assembly(name="satellite1_official_upper_reference")
    for part in UPPER_STACK:
        assembly.add(load_part(part), name=part.name, color=cq.Color(*part.color))
    for board in PLACED_BOARDS[board_revision]:
        assembly.add(load_part(board), name=board.name, color=cq.Color(*board.color))
    return assembly


def official_board_envelopes(board_revision: str = "public_batch_1") -> dict[str, cq.Shape]:
    """Conservative envelopes for the placed official boards of ``board_revision``."""
    return {board.name: board_keepout(board) for board in PLACED_BOARDS[board_revision]}


def official_upper_solids(board_revision: str = "public_batch_1") -> dict[str, cq.Shape]:
    """Every official upper-stack solid a printed part must clear."""
    solids = {part.name: load_part(part) for part in UPPER_STACK}
    solids.update(official_board_envelopes(board_revision))
    return solids


def core_clearance_extent(
    board_revision: str = "public_batch_1",
    margin: tuple[float, float, float] = (5.0, 5.0, 3.0),
) -> tuple[float, float, float]:
    """Core bounding size plus service margin, measured from the official mesh."""
    (core,) = UNPLACED_BOARDS[board_revision]
    bounds = load_official_mesh(core).bounds
    size = bounds[1] - bounds[0]
    return (
        float(size[0]) + margin[0],
        float(size[1]) + margin[1],
        float(size[2]) + margin[2],
    )


def wiring_service_volume(
    divider_top_z: float, interface_z: float = OFFICIAL_INTERFACE_Z
) -> cq.Shape:
    """Rear corridor in the electronics bay reserved for wiring and service access."""
    return cq.Solid.makeBox(
        40.0,
        20.0,
        interface_z - divider_top_z,
        cq.Vector(-20.0, 52.0, divider_top_z),
    )
