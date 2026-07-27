"""Official FutureProofHomes geometry import and master-datum placement."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import cast

import cadquery as cq
from cadquery import importers

ROOT = Path(__file__).resolve().parents[2]
OFFICIAL = ROOT / "reference-assets" / "official" / "Satellite1-Enclosures"
MASTER_INTERFACE_Z = 140.8


@dataclass(frozen=True)
class OfficialPart:
    """An immutable official asset and its placement in the master system."""

    name: str
    relative_path: str
    color: tuple[float, float, float, float]
    translation: tuple[float, float, float] = (0.0, 0.0, -MASTER_INTERFACE_Z)

    @property
    def path(self) -> Path:
        return OFFICIAL / self.relative_path


MID_PLATE = OfficialPart(
    "official_mid_plate",
    "DIY Enclosures/Squircle Enclosures/Geometry Files/STEP/Mid-Plate/Mid-Plate.step",
    (0.25, 0.28, 0.32, 1.0),
)
MID_PLATE_THREADS = OfficialPart(
    "official_mid_plate_threads",
    ("DIY Enclosures/Squircle Enclosures/Geometry Files/STEP/Mid-Plate/Mid-Plate Threads.step"),
    (0.18, 0.20, 0.23, 1.0),
)
TOP_PLATE = OfficialPart(
    "official_top_plate",
    (
        "DIY Enclosures/Squircle Enclosures/Geometry Files/STEP/"
        "Squircle Top/Top Plate Combined MM.step"
    ),
    (0.83, 0.84, 0.86, 1.0),
)
PCB_SPACER = OfficialPart(
    "official_pcb_spacer",
    ("DIY Enclosures/Squircle Enclosures/Geometry Files/STEP/Squircle Top/PCB Spacer.step"),
    (0.70, 0.72, 0.75, 1.0),
)
LOCK_RING = OfficialPart(
    "official_lock_ring",
    ("DIY Enclosures/Squircle Enclosures/Geometry Files/STEP/Squircle Top/Lock Ring.step"),
    (0.15, 0.16, 0.18, 1.0),
)
SPEAKER_CHAMBER_25W = OfficialPart(
    "official_25w_speaker_chamber",
    (
        "DIY Enclosures/Squircle Enclosures/Geometry Files/STEP/"
        "Speaker Chamber/25-Watt Speaker Chamber.step"
    ),
    (0.25, 0.28, 0.32, 1.0),
)
BATCH1_HAT = OfficialPart(
    "official_hat_batch1_rev4_1",
    "assets/Hat R2024.12.06.step",
    (0.05, 0.34, 0.13, 1.0),
    (0.0, -0.999, 9.2),
)
BATCH2_HAT = OfficialPart(
    "official_hat_batch2_rev6_1",
    "assets/Hat R2025.03.18.step",
    (0.05, 0.34, 0.13, 1.0),
    (0.0, -0.999, 9.2),
)

UPPER_STACK = (MID_PLATE, MID_PLATE_THREADS, TOP_PLATE, PCB_SPACER, LOCK_RING)


@cache
def load_part(part: OfficialPart) -> cq.Shape:
    """Load and place an official STEP asset without modifying source bytes."""
    if not part.path.is_file():
        raise FileNotFoundError(part.path)
    shape = cast(cq.Shape, importers.importStep(str(part.path)).val())
    return shape.translate(cq.Vector(*part.translation))


def upper_reference_assembly(board_revision: str = "public_batch_1") -> cq.Assembly:
    """Return the official upper stack and selected official HAT assembly."""
    assembly = cq.Assembly(name="satellite1_official_upper_reference")
    for part in UPPER_STACK:
        assembly.add(load_part(part), name=part.name, color=cq.Color(*part.color))
    hat = BATCH1_HAT if board_revision == "public_batch_1" else BATCH2_HAT
    assembly.add(load_part(hat), name=hat.name, color=cq.Color(*hat.color))
    return assembly
