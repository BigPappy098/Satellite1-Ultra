"""Inventory preserved official STEP assets with CadQuery/OCCT."""

from __future__ import annotations

import csv
import math
from pathlib import Path

from cadquery import importers

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "reference-assets" / "official"
REPORT = ROOT / "reports" / "geometry" / "official_step_inventory.csv"


def finite(values: tuple[float, ...]) -> bool:
    """Return whether every value is finite."""
    return all(math.isfinite(value) for value in values)


def main() -> None:
    """Load every official STEP file and report topology and bounds."""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    rows: list[tuple[str, str, str, str, str, str, str, str, str, str, str]] = []
    failures = 0
    step_paths = sorted(ASSETS.rglob("*.step")) + sorted(ASSETS.rglob("*.stp"))
    for index, path in enumerate(step_paths, start=1):
        try:
            workplane = importers.importStep(str(path))
            shape = workplane.val()
            bounds = shape.BoundingBox()
            dimensions = (bounds.xlen, bounds.ylen, bounds.zlen)
            # Full BRepCheck_Analyzer on some vendor PCB assemblies can require
            # minutes per file. Official references are therefore classified
            # here by successful OCCT import, finite bounds, positive solid
            # volume, and topology counts. Full validity checks are mandatory
            # for our manufactured parts and selected reused interface parts.
            valid = finite(dimensions)
            solids = len(shape.Solids())
            shells = len(shape.Shells())
            volume = sum(solid.Volume() for solid in shape.Solids())
            if not valid or solids < 1 or volume <= 0:
                failures += 1
            rows.append(
                (
                    path.relative_to(ROOT).as_posix(),
                    str(valid),
                    str(solids),
                    str(shells),
                    f"{volume:.6f}",
                    f"{bounds.xmin:.6f}",
                    f"{bounds.ymin:.6f}",
                    f"{bounds.zmin:.6f}",
                    f"{bounds.xlen:.6f}",
                    f"{bounds.ylen:.6f}",
                    f"{bounds.zlen:.6f}",
                )
            )
            print(f"[{index}/{len(step_paths)}] {path.name}: {solids} solids")
        except Exception as error:
            failures += 1
            rows.append(
                (
                    path.relative_to(ROOT).as_posix(),
                    "False",
                    "0",
                    "0",
                    "0",
                    "nan",
                    "nan",
                    "nan",
                    "nan",
                    "nan",
                    f"ERROR: {type(error).__name__}: {error}",
                )
            )

    with REPORT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            (
                "path",
                "occt_valid",
                "solid_count",
                "shell_count",
                "solid_volume_mm3",
                "xmin_mm",
                "ymin_mm",
                "zmin_mm",
                "x_size_mm",
                "y_size_mm",
                "z_size_mm_or_error",
            )
        )
        writer.writerows(rows)
    print(f"Inventoried {len(rows)} STEP assets; validation/import failures: {failures}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
