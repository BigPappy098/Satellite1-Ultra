"""CAD-derived renders, cross-sections and technical views.

Every image produced here is rasterised from the authoritative OpenCascade
B-rep by tessellating it at export time.  No concept art, no external model and
no hand-drawn illustration is used anywhere in this project's deliverables.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cadquery as cq
import matplotlib
import numpy as np
from numpy.typing import NDArray

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import (  # type: ignore[import-untyped]
    Poly3DCollection,
)

from satellite1_ultra.assemblies import _placement, release_parts
from satellite1_ultra.configuration import ROOT
from satellite1_ultra.geometry import (
    DEFAULT_PARAMETERS,
    DesignParameters,
)

TESSELLATION_TOLERANCE = 0.35
ANGULAR_TOLERANCE = 0.35
LIGHT = np.array([-0.45, -0.75, 0.49])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


@dataclass(frozen=True)
class View:
    """A named camera for a render sheet."""

    name: str
    elevation: float
    azimuth: float


VIEWS = (
    View("iso", 22.0, -55.0),
    View("front", 4.0, -90.0),
    View("side", 4.0, 0.0),
    View("top", 78.0, -90.0),
)


def triangles(shape: cq.Shape) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    """Tessellate a B-rep solid into vertices and triangle indices."""
    vertices, faces = shape.tessellate(TESSELLATION_TOLERANCE, ANGULAR_TOLERANCE)
    points = np.array([[v.x, v.y, v.z] for v in vertices], dtype=np.float64)
    indices = np.array(faces, dtype=np.int64)
    return points, indices


def _shaded_faces(
    points: NDArray[np.float64], indices: NDArray[np.int64], color: tuple[float, float, float]
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return triangle corner arrays and per-triangle Lambert-shaded colours."""
    corners = points[indices]
    normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    lengths[lengths == 0.0] = 1.0
    normals = normals / lengths[:, None]
    lambert = np.abs(normals @ LIGHT)
    intensity = 0.28 + 0.72 * lambert
    base = np.array(color, dtype=np.float64)
    shaded = np.clip(intensity[:, None] * base[None, :], 0.0, 1.0)
    return corners, shaded


def _draw(
    axis: object,
    parts: dict[str, cq.Shape],
    colors: dict[str, tuple[float, float, float]],
    alpha: float = 1.0,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    lows: list[NDArray[np.float64]] = []
    highs: list[NDArray[np.float64]] = []
    for name, shape in parts.items():
        if shape.Volume() <= 0.0:
            continue
        points, indices = triangles(shape)
        if indices.size == 0:
            continue
        corners, shaded = _shaded_faces(points, indices, colors.get(name, (0.55, 0.56, 0.58)))
        collection = Poly3DCollection(corners, facecolors=shaded, linewidths=0.0)
        collection.set_alpha(alpha if "envelope" in name else 1.0)
        axis.add_collection3d(collection)  # type: ignore[attr-defined]
        lows.append(points.min(axis=0))
        highs.append(points.max(axis=0))
    return np.min(lows, axis=0), np.max(highs, axis=0)


def _finish(
    figure: Figure,
    axis: object,
    low: NDArray[np.float64],
    high: NDArray[np.float64],
    view: View,
) -> None:
    centre = (low + high) / 2.0
    radius = float(np.max(high - low)) / 2.0 * 1.06
    axis.set_xlim(centre[0] - radius, centre[0] + radius)  # type: ignore[attr-defined]
    axis.set_ylim(centre[1] - radius, centre[1] + radius)  # type: ignore[attr-defined]
    axis.set_zlim(centre[2] - radius, centre[2] + radius)  # type: ignore[attr-defined]
    axis.set_box_aspect((1.0, 1.0, 1.0))  # type: ignore[attr-defined]
    axis.view_init(elev=view.elevation, azim=view.azimuth)  # type: ignore[attr-defined]
    axis.set_axis_off()  # type: ignore[attr-defined]
    figure.patch.set_facecolor("#f4f4f5")


def _colors(parts: dict[str, cq.Shape]) -> dict[str, tuple[float, float, float]]:
    colors: dict[str, tuple[float, float, float]] = {}
    for name in parts:
        if name.startswith("official"):
            colors[name] = (0.70, 0.71, 0.74)
        else:
            colors[name] = _placement(name).color
    return colors


def render_views(
    output: Path = ROOT / "reports" / "renders",
    parameters: DesignParameters = DEFAULT_PARAMETERS,
    exploded: bool = False,
) -> list[Path]:
    """Render the assembly from every documented camera."""
    output.mkdir(parents=True, exist_ok=True)
    parts = release_parts(parameters, include_official=True)
    parts = {name: shape for name, shape in parts.items() if "envelope" not in name}
    if exploded:
        parts = {
            name: shape.translate(
                cq.Vector(*_placement(name).direction) * _placement(name).distance
                if not name.startswith("official")
                else cq.Vector(0.0, 0.0, 95.0)
            )
            for name, shape in parts.items()
        }
    colors = _colors(parts)
    written: list[Path] = []
    suffix = "_exploded" if exploded else ""
    for view in VIEWS:
        figure = plt.figure(figsize=(7.5, 8.5), dpi=170)
        axis = figure.add_subplot(111, projection="3d")
        low, high = _draw(axis, parts, colors)
        _finish(figure, axis, low, high, view)
        path = output / f"assembly_{view.name}{suffix}.png"
        figure.savefig(path, bbox_inches="tight", facecolor=figure.get_facecolor())
        plt.close(figure)
        written.append(path)
    return written


def cross_section_parts(
    parameters: DesignParameters,
    plane: str,
) -> dict[str, cq.Shape]:
    """Cut every part with a half-space so the interior is visible."""
    p = parameters
    reach = 400.0
    if plane == "xz":
        cutter = cq.Solid.makeBox(
            2.0 * reach, reach, 2.0 * reach, cq.Vector(-reach, 0.0, -reach - 100.0)
        )
    elif plane == "yz":
        cutter = cq.Solid.makeBox(
            reach, 2.0 * reach, 2.0 * reach, cq.Vector(0.0, -reach, -reach - 100.0)
        )
    else:
        raise ValueError("plane must be 'xz' or 'yz'")
    parts = release_parts(p, include_official=True)
    cut: dict[str, cq.Shape] = {}
    for name, shape in parts.items():
        try:
            remainder = shape.cut(cutter)
        except Exception:  # pragma: no cover - OCCT edge case on a degenerate cut
            remainder = shape
        if remainder.Volume() > 1.0:
            cut[name] = remainder
    return cut


def render_cross_sections(
    output: Path = ROOT / "reports" / "renders",
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> list[Path]:
    """Render the two principal cross-sections of the complete assembly."""
    output.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for plane, view in (("xz", VIEWS[0]), ("yz", View("iso_yz", 18.0, -145.0))):
        parts = cross_section_parts(parameters, plane)
        colors = _colors(parts)
        figure = plt.figure(figsize=(7.5, 8.5), dpi=170)
        axis = figure.add_subplot(111, projection="3d")
        low, high = _draw(axis, parts, colors)
        _finish(figure, axis, low, high, view)
        path = output / f"cross_section_{plane}.png"
        figure.savefig(path, bbox_inches="tight", facecolor=figure.get_facecolor())
        plt.close(figure)
        written.append(path)
    return written


def render_part_sheet(
    output: Path = ROOT / "reports" / "renders",
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> Path:
    """One contact sheet showing every manufactured part in print orientation."""
    from satellite1_ultra.exporting import PARTS, print_oriented

    output.mkdir(parents=True, exist_ok=True)
    names = list(PARTS)
    columns = 5
    rows = (len(names) + columns - 1) // columns
    figure = plt.figure(figsize=(3.1 * columns, 3.3 * rows), dpi=140)
    for index, name in enumerate(names):
        shape = print_oriented(PARTS[name].builder(parameters))
        axis = figure.add_subplot(rows, columns, index + 1, projection="3d")
        low, high = _draw(axis, {name: shape}, {name: (0.42, 0.45, 0.50)})
        _finish(figure, axis, low, high, VIEWS[0])
        axis.set_title(name, fontsize=7)
    figure.suptitle("Satellite1 Ultra — manufactured parts in print orientation", fontsize=11)
    path = output / "part_sheet.png"
    figure.savefig(path, bbox_inches="tight", facecolor="#f4f4f5")
    plt.close(figure)
    return path


def generate_renders(
    output: Path = ROOT / "reports" / "renders",
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> list[Path]:
    """Produce the complete render deliverable set."""
    written = render_views(output, parameters, exploded=False)
    written += render_views(output, parameters, exploded=True)
    written += render_cross_sections(output, parameters)
    written.append(render_part_sheet(output, parameters))
    return written
