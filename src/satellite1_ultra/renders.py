"""CAD-derived renders, cross-sections and technical views.

Every image produced here is rasterised from the authoritative OpenCascade
B-rep by tessellating it at export time.  No concept art, no external model and
no hand-drawn illustration is used anywhere in this project's deliverables.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

import cadquery as cq
import matplotlib
import numpy as np
from numpy.typing import NDArray

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle
from mpl_toolkits.mplot3d import proj3d  # type: ignore[import-untyped]
from mpl_toolkits.mplot3d.art3d import (  # type: ignore[import-untyped]
    Poly3DCollection,
)

from satellite1_ultra.assemblies import _placement, release_parts
from satellite1_ultra.configuration import ROOT
from satellite1_ultra.geometry import (
    DEFAULT_PARAMETERS,
    DesignParameters,
    ballast_plate_extent,
)

TESSELLATION_TOLERANCE = 0.35
ANGULAR_TOLERANCE = 0.35
LIGHT = np.array([-0.45, -0.75, 0.49])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
_TESSELLATION_CACHE: dict[
    tuple[int, float, float, float, float],
    tuple[NDArray[np.float64], NDArray[np.int64]],
] = {}


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

#: Plain-English name and the exact builder file (or purchased item) for every
#: solid that can appear in an instructional scene.  The second element is what
#: the builder physically holds, so a diagram balloon always resolves to one
#: unambiguous thing on the bench.
PART_LABELS: dict[str, tuple[str, str]] = {
    "main_cabinet": ("Main speaker body", "01_MAIN_SPEAKER_BODY.3mf"),
    "pressure_divider": ("Electronics divider", "02_ELECTRONICS_DIVIDER.3mf"),
    "active_driver_clamp_ring": ("Speaker clamp ring", "03_SPEAKER_CLAMP_RING.3mf"),
    "pr_-1_clamp_ring": ("Radiator clamp ring (left, -X)", "04_RADIATOR_CLAMP_RING_PRINT_TWO.3mf"),
    "pr_+1_clamp_ring": ("Radiator clamp ring (right, +X)", "04_RADIATOR_CLAMP_RING_PRINT_TWO.3mf"),
    "base_skirt": ("Bottom base", "05_BOTTOM_BASE.3mf"),
    "ballast_cartridge": ("Weight tray", "06_WEIGHT_TRAY.3mf"),
    "ballast_cartridge_lid": ("Weight tray lid", "07_WEIGHT_TRAY_LID.3mf"),
    "bottom_service_plate": ("Bottom access panel", "08_BOTTOM_ACCESS_PANEL.3mf"),
    "electronics_shroud": ("Electronics cover", "09_ELECTRONICS_COVER.3mf"),
    "outer_shell": ("Outer shell", "10_OUTER_SHELL.3mf"),
    "anti_slip_ring": ("Flexible bottom grip", "11_FLEXIBLE_BOTTOM_GRIP_TPU.3mf"),
    "leak_test_adapter": ("Leak-test tool", "12_LEAK_TEST_TOOL.3mf"),
    "divider_gasket": ("Divider gasket", "G01, cut from divider_gasket.dxf"),
    "active_driver_gasket": ("Speaker gasket", "G02, cut from driver_gasket.dxf"),
    "pr_-1_gasket": ("Radiator gasket (left, -X)", "G03, cut from passive_radiator_gasket.dxf"),
    "pr_+1_gasket": ("Radiator gasket (right, +X)", "G03, cut from passive_radiator_gasket.dxf"),
    "wire_gland": ("Flexible cable seal", "G04, 08_FLEXIBLE_CABLE_SEAL_TPU.3mf"),
    "driver_envelope": ("Dayton ND91-4 speaker", "purchased, A01"),
    "pr_-1_envelope": ("SB12PACR-00 radiator (left, -X)", "purchased, A02"),
    "pr_+1_envelope": ("SB12PACR-00 radiator (right, +X)", "purchased, A02"),
    "steel_plate_lower": ("Steel ballast plate (lower)", "purchased, B01"),
    "steel_plate_upper": ("Steel ballast plate (upper)", "purchased, B01"),
    "official_mid_plate": ("Satellite mid plate", "01_SATELLITE_MID_PLATE.stl"),
    "official_mid_plate_threads": ("Satellite threaded plate", "02_SATELLITE_THREADED_PLATE.stl"),
    "official_pcb_spacer": ("Circuit board spacer", "03_CIRCUIT_BOARD_SPACER.stl"),
    "official_lock_ring": ("Top lock ring", "04_TOP_LOCK_RING.stl"),
    "official_top_plate": ("Button and light top", "05_BUTTON_AND_LIGHT_TOP.stl"),
    "official_top_plate_snap_in_diffuser_ring": (
        "Snap-in light ring",
        "06_SNAP_IN_LIGHT_RING.stl",
    ),
    "official_hat_batch1_rev4_1_envelope": ("Satellite1 HAT rev4.1 (space reserved)", "kit, E01"),
    "official_core_batch1_rev4_1_envelope": ("Satellite1 Core rev4.1 (space reserved)", "kit, E01"),
}

#: Instructional colours.  These are deliberately not the product colours: a
#: build diagram has to separate adjacent parts at a glance, so every family
#: gets its own hue and the greys are reserved for official/purchased items.
DOC_PALETTE: dict[str, tuple[float, float, float]] = {
    "main_cabinet": (0.20, 0.42, 0.66),
    "pressure_divider": (0.30, 0.57, 0.78),
    "electronics_shroud": (0.47, 0.70, 0.86),
    "outer_shell": (0.36, 0.50, 0.60),
    "base_skirt": (0.16, 0.34, 0.52),
    "ballast_cartridge": (0.55, 0.42, 0.72),
    "ballast_cartridge_lid": (0.68, 0.56, 0.83),
    "bottom_service_plate": (0.44, 0.32, 0.62),
    "anti_slip_ring": (0.22, 0.24, 0.28),
    "active_driver_clamp_ring": (0.86, 0.52, 0.18),
    "pr_-1_clamp_ring": (0.92, 0.66, 0.24),
    "pr_+1_clamp_ring": (0.92, 0.66, 0.24),
    "leak_test_adapter": (0.60, 0.62, 0.65),
    "divider_gasket": (0.78, 0.26, 0.28),
    "active_driver_gasket": (0.78, 0.26, 0.28),
    "pr_-1_gasket": (0.78, 0.26, 0.28),
    "pr_+1_gasket": (0.78, 0.26, 0.28),
    "wire_gland": (0.86, 0.38, 0.40),
    "driver_envelope": (0.24, 0.56, 0.44),
    "pr_-1_envelope": (0.32, 0.66, 0.52),
    "pr_+1_envelope": (0.32, 0.66, 0.52),
    "steel_plate_lower": (0.38, 0.43, 0.50),
    "steel_plate_upper": (0.50, 0.55, 0.62),
}
OFFICIAL_DOC_COLOR = (0.74, 0.75, 0.78)
CONTEXT_DOC_COLOR = (0.80, 0.81, 0.83)
BALLOON_FACE = "#12395c"
ACCENT = "#c2410c"


def triangles(shape: cq.Shape) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    """Tessellate a B-rep solid into vertices and triangle indices."""
    center = shape.Center()
    key = (
        id(shape.wrapped),
        round(shape.Volume(), 5),
        round(center.x, 5),
        round(center.y, 5),
        round(center.z, 5),
    )
    cached = _TESSELLATION_CACHE.get(key)
    if cached is not None:
        return cached
    vertices, faces = shape.tessellate(TESSELLATION_TOLERANCE, ANGULAR_TOLERANCE)
    points = np.array([[v.x, v.y, v.z] for v in vertices], dtype=np.float64)
    indices = np.array(faces, dtype=np.int64)
    _TESSELLATION_CACHE[key] = (points, indices)
    return points, indices


def _view_direction(view: View) -> NDArray[np.float64]:
    """Unit vector from the model toward the camera, matching mpl3d's convention."""
    elevation = np.radians(view.elevation)
    azimuth = np.radians(view.azimuth)
    return np.array(
        [
            np.cos(elevation) * np.cos(azimuth),
            np.cos(elevation) * np.sin(azimuth),
            np.sin(elevation),
        ],
        dtype=np.float64,
    )


def _cull_backfaces(
    corners: NDArray[np.float64],
    colors: NDArray[np.float64],
    view: View,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Drop triangles facing away from the camera.

    Every part here is a closed solid, so a back face is always hidden by the
    front of the same solid.  Discarding them halves the work and removes the
    interior surfaces that most often sorted in front of nearer parts.
    """
    normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    lengths[lengths == 0.0] = 1.0
    facing = (normals / lengths[:, None]) @ _view_direction(view)
    visible = facing > -1e-6
    if not bool(visible.any()):
        return corners, colors
    return corners[visible], colors[visible]


def _subdivide(
    corners: NDArray[np.float64],
    colors: NDArray[np.float64],
    max_edge: float = 9.0,
    max_passes: int = 5,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Split oversized triangles so the depth sort can order them correctly.

    A planar wall tessellates to a handful of very large triangles no matter
    how tight the tolerance is.  Painter's-algorithm sorting ranks each of
    those by a single depth value, which is wrong across a triangle spanning
    most of the model, and small parts behind a wall bleed through it.
    Subdividing until every triangle is locally small makes one depth value
    per triangle an accurate description of it.
    """
    for _ in range(max_passes):
        edges = np.stack(
            [
                np.linalg.norm(corners[:, 1] - corners[:, 0], axis=1),
                np.linalg.norm(corners[:, 2] - corners[:, 1], axis=1),
                np.linalg.norm(corners[:, 0] - corners[:, 2], axis=1),
            ],
            axis=1,
        )
        oversized = edges.max(axis=1) > max_edge
        if not bool(oversized.any()):
            break
        big, big_colors = corners[oversized], colors[oversized]
        a, b, c = big[:, 0], big[:, 1], big[:, 2]
        ab, bc, ca = (a + b) / 2.0, (b + c) / 2.0, (c + a) / 2.0
        split = np.concatenate(
            [
                np.stack([a, ab, ca], axis=1),
                np.stack([ab, b, bc], axis=1),
                np.stack([ca, bc, c], axis=1),
                np.stack([ab, bc, ca], axis=1),
            ]
        )
        corners = np.concatenate([corners[~oversized], split])
        colors = np.concatenate([colors[~oversized], np.tile(big_colors, (4, 1))])
    return corners, colors


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
    view: View | None = None,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Draw every part as one depth-sorted collection.

    Matplotlib composites separate ``Poly3DCollection`` objects by artist
    order, not by depth, so one collection per part makes near parts render
    behind far ones.  Merging every triangle into a single collection lets the
    painter's-algorithm sort run across parts and puts the layering right.
    """
    lows: list[NDArray[np.float64]] = []
    highs: list[NDArray[np.float64]] = []
    all_corners: list[NDArray[np.float64]] = []
    all_shaded: list[NDArray[np.float64]] = []
    for name, shape in parts.items():
        if shape.Volume() <= 0.0:
            continue
        points, indices = triangles(shape)
        if indices.size == 0:
            continue
        corners, shaded = _shaded_faces(points, indices, colors.get(name, (0.55, 0.56, 0.58)))
        if view is not None:
            corners, shaded = _cull_backfaces(corners, shaded, view)
            corners, shaded = _subdivide(corners, shaded)
        all_corners.append(corners)
        all_shaded.append(shaded)
        lows.append(points.min(axis=0))
        highs.append(points.max(axis=0))
    if not all_corners:
        raise ValueError("scene contains no drawable geometry")
    corners_all = np.concatenate(all_corners)
    shaded_all = np.concatenate(all_shaded)
    if view is not None:
        # Depth cue.  These parts are open boxes seen from above, so a reader
        # looks straight through a bore or an open top onto interior walls.
        # Fading distance makes near and far surfaces separate at a glance
        # instead of flattening into one ambiguous silhouette.
        depth = corners_all.mean(axis=1) @ _view_direction(view)
        span = float(depth.max() - depth.min())
        if span > 1e-9:
            nearness = (depth - depth.min()) / span
            shaded_all = shaded_all * (0.55 + 0.45 * nearness)[:, None]
    face_colors = np.clip(shaded_all, 0.0, 1.0)
    # Draw each triangle's outline in its own fill colour.  With linewidth 0 the
    # antialiased edges of adjacent triangles leave a pale seam, which is what
    # makes a solid surface read as a wireframe; a hairline in the fill colour
    # covers the seam without introducing any visible mesh.
    collection = Poly3DCollection(
        corners_all,
        facecolors=face_colors,
        edgecolors=face_colors,
        linewidths=0.35,
        zsort="average",
    )
    collection.set_alpha(1.0)
    axis.add_collection3d(collection)  # type: ignore[attr-defined]
    return np.min(lows, axis=0), np.max(highs, axis=0)


def _finish(
    figure: Figure,
    axis: object,
    low: NDArray[np.float64],
    high: NDArray[np.float64],
    view: View,
    zoom: float = 1.0,
) -> None:
    centre = (low + high) / 2.0
    radius = float(np.max(high - low)) / 2.0 * 1.06
    axis.set_xlim(centre[0] - radius, centre[0] + radius)  # type: ignore[attr-defined]
    axis.set_ylim(centre[1] - radius, centre[1] + radius)  # type: ignore[attr-defined]
    axis.set_zlim(centre[2] - radius, centre[2] + radius)  # type: ignore[attr-defined]
    axis.set_box_aspect((1.0, 1.0, 1.0), zoom=zoom)  # type: ignore[attr-defined]
    axis.view_init(elev=view.elevation, azim=view.azimuth)  # type: ignore[attr-defined]
    axis.set_axis_off()  # type: ignore[attr-defined]
    figure.patch.set_facecolor("#f4f4f5")


def _colors(parts: dict[str, cq.Shape]) -> dict[str, tuple[float, float, float]]:
    colors: dict[str, tuple[float, float, float]] = {}
    for name in parts:
        if name.startswith("official"):
            colors[name] = (0.70, 0.71, 0.74)
        else:
            colors[name] = cast(
                tuple[float, float, float],
                tuple(0.25 + 0.75 * channel for channel in _placement(name).color),
            )
    return colors


def _doc_colors(
    parts: dict[str, cq.Shape],
    highlight: tuple[str, ...] = (),
) -> dict[str, tuple[float, float, float]]:
    """Instructional colours; when *highlight* is given, everything else recedes.

    Assembly-stage sheets use this so the one part being installed reads
    immediately against the parts that are already on the bench.
    """
    colors: dict[str, tuple[float, float, float]] = {}
    for name in parts:
        if highlight and name not in highlight:
            colors[name] = CONTEXT_DOC_COLOR
        elif name in DOC_PALETTE:
            colors[name] = DOC_PALETTE[name]
        elif name.startswith("official"):
            colors[name] = OFFICIAL_DOC_COLOR
        else:
            colors[name] = (0.45, 0.50, 0.56)
    return colors


def _label_for(name: str) -> tuple[str, str]:
    """Plain-English name and exact file/item for one solid."""
    if name in PART_LABELS:
        return PART_LABELS[name]
    return (name.replace("_", " "), "")


def _balloon_points(
    figure: Figure,
    axis: object,
    parts: dict[str, cq.Shape],
) -> dict[str, tuple[float, float]]:
    """Project each part's centre into figure fractions for balloon placement."""
    figure.canvas.draw()
    projection = axis.get_proj()  # type: ignore[attr-defined]
    points: dict[str, tuple[float, float]] = {}
    for name, shape in parts.items():
        if shape.Volume() <= 0.0:
            continue
        box = shape.BoundingBox()
        centre = (
            (box.xmin + box.xmax) / 2.0,
            (box.ymin + box.ymax) / 2.0,
            (box.zmin + box.zmax) / 2.0,
        )
        flat_x, flat_y, _ = proj3d.proj_transform(centre[0], centre[1], centre[2], projection)
        display = axis.transData.transform((flat_x, flat_y))  # type: ignore[attr-defined]
        points[name] = cast(
            tuple[float, float],
            tuple(figure.transFigure.inverted().transform(display)),
        )
    return points


def _spread(
    anchors: list[tuple[float, float]],
    separation: float,
    iterations: int = 260,
) -> list[tuple[float, float]]:
    """Push overlapping balloons apart while holding them near their anchors.

    Parts stacked along the view axis project to nearly the same point, so the
    raw centroids collide.  A short relaxation keeps every balloon legible and
    still visibly attached to the solid it names.
    """
    placed = [list(point) for point in anchors]
    for _ in range(iterations):
        moved = False
        for i in range(len(placed)):
            for j in range(i + 1, len(placed)):
                dx = placed[j][0] - placed[i][0]
                dy = placed[j][1] - placed[i][1]
                distance = (dx * dx + dy * dy) ** 0.5
                if distance >= separation:
                    continue
                if distance < 1e-6:
                    dx, dy, distance = 0.0, 1e-3, 1e-3
                push = (separation - distance) / 2.0
                ux, uy = dx / distance, dy / distance
                placed[i][0] -= ux * push
                placed[i][1] -= uy * push
                placed[j][0] += ux * push
                placed[j][1] += uy * push
                moved = True
        # Weak spring back to the true centroid keeps balloons on their parts.
        for index, (ax, ay) in enumerate(anchors):
            placed[index][0] += (ax - placed[index][0]) * 0.06
            placed[index][1] += (ay - placed[index][1]) * 0.06
        if not moved:
            break
    return [(point[0], point[1]) for point in placed]


def _draw_callouts(
    figure: Figure,
    axis: object,
    parts: dict[str, cq.Shape],
    legend_left: float,
) -> None:
    """Number every part in the scene and print the matching key panel.

    Balloons are numbered top-to-bottom in the rendered image so the key reads
    in the same order the eye travels down the drawing.
    """
    points = _balloon_points(figure, axis, parts)
    if not points:
        return
    ordered = sorted(points.items(), key=lambda item: -item[1][1])
    overlay = figure.add_axes((0.0, 0.0, 1.0, 1.0), frameon=False, zorder=5)
    overlay.set_axis_off()
    overlay.set_xlim(0.0, 1.0)
    overlay.set_ylim(0.0, 1.0)

    rows = len(ordered)
    top = 0.885
    step = min(0.038, (top - 0.070) / max(rows, 1))
    compact = step < 0.030
    anchors = [point for _name, point in ordered]
    balloon_radius = 0.0128
    balloons = _spread(anchors, separation=balloon_radius * 2.25)
    for index, ((name, anchor), (x, y)) in enumerate(zip(ordered, balloons, strict=True), start=1):
        label_y = top - (index - 1) * step
        offset = ((x - anchor[0]) ** 2 + (y - anchor[1]) ** 2) ** 0.5
        if offset > balloon_radius:
            # The balloon had to move off its part; show where it really points.
            overlay.annotate(
                "",
                xy=anchor,
                xytext=(x, y),
                arrowprops={
                    "arrowstyle": "-",
                    "color": "#3d4147",
                    "linewidth": 0.8,
                    "shrinkA": 7.0,
                    "shrinkB": 0.0,
                },
            )
            overlay.add_patch(
                Circle(anchor, 0.0022, facecolor="#3d4147", edgecolor="none", zorder=6)
            )
        overlay.annotate(
            "",
            xy=(x, y),
            xytext=(legend_left - 0.012, label_y),
            arrowprops={
                "arrowstyle": "-",
                "color": "#9aa0a8",
                "linewidth": 0.7,
                "shrinkA": 2.0,
                "shrinkB": 8.0,
                "connectionstyle": "arc3,rad=0.08",
            },
        )
        overlay.add_patch(
            Circle(
                (x, y),
                balloon_radius,
                facecolor=BALLOON_FACE,
                edgecolor="white",
                linewidth=1.1,
                zorder=6,
            )
        )
        overlay.text(
            x,
            y,
            str(index),
            ha="center",
            va="center",
            fontsize=7.2,
            color="white",
            weight="bold",
            zorder=7,
        )
        plain, source = _label_for(name)
        overlay.add_patch(
            Circle(
                (legend_left + 0.012, label_y),
                0.0115,
                facecolor=BALLOON_FACE,
                edgecolor="none",
                zorder=6,
            )
        )
        overlay.text(
            legend_left + 0.012,
            label_y,
            str(index),
            ha="center",
            va="center",
            fontsize=6.8,
            color="white",
            weight="bold",
            zorder=7,
        )
        overlay.text(
            legend_left + 0.030,
            label_y + (0.005 if compact else 0.006),
            plain,
            ha="left",
            va="center",
            fontsize=7.4 if compact else 8.2,
            color="#15181c",
            zorder=7,
        )
        if source:
            overlay.text(
                legend_left + 0.030,
                label_y - (0.008 if compact else 0.009),
                source,
                ha="left",
                va="center",
                fontsize=5.9 if compact else 6.5,
                color="#5a6169",
                family="monospace",
                zorder=7,
            )


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
        low, high = _draw(axis, parts, colors, view)
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
        low, high = _draw(axis, parts, colors, view)
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
        low, high = _draw(axis, {name: shape}, {name: (0.42, 0.45, 0.50)}, VIEWS[0])
        _finish(figure, axis, low, high, VIEWS[0])
        axis.set_title(name, fontsize=7)
    figure.suptitle("Satellite1 Ultra — manufactured parts in print orientation", fontsize=11)
    path = output / "part_sheet.png"
    figure.savefig(path, bbox_inches="tight", facecolor="#f4f4f5")
    plt.close(figure)
    return path


def _scene(
    path: Path,
    parts: dict[str, cq.Shape],
    title: str,
    note: str,
    view: View = VIEWS[0],
    colors: dict[str, tuple[float, float, float]] | None = None,
    measurement: str | None = None,
    callouts: bool = False,
    step_badge: str | None = None,
) -> Path:
    """Render a high-resolution, captioned technical scene.

    With *callouts* the scene gains a numbered balloon on every solid plus a
    matching key panel, so a reader can name each part and its exact print file
    without cross-checking another document.
    """
    figure = plt.figure(figsize=(10.4, 7.2), dpi=180)
    legend_left = 0.660
    drawing_right = 0.640 if callouts else 0.985
    axis = figure.add_subplot(111, projection="3d")
    low, high = _draw(axis, parts, colors or _colors(parts), view)
    _finish(figure, axis, low, high, view, zoom=1.30 if callouts else 1.18)
    axis.set_position((0.005, 0.035, drawing_right - 0.005, 0.860))
    figure.patch.set_facecolor("#ffffff")

    if step_badge:
        badge = figure.add_axes((0.0, 0.0, 1.0, 1.0), frameon=False, zorder=4)
        badge.set_axis_off()
        badge.set_xlim(0.0, 1.0)
        badge.set_ylim(0.0, 1.0)
        badge.add_patch(
            FancyBboxPatch(
                (0.026, 0.928),
                0.070,
                0.046,
                boxstyle="round,pad=0.004,rounding_size=0.010",
                facecolor=ACCENT,
                edgecolor="none",
            )
        )
        badge.text(
            0.061,
            0.951,
            step_badge,
            ha="center",
            va="center",
            fontsize=12.5,
            weight="bold",
            color="white",
        )
    title_x = 0.112 if step_badge else 0.026
    figure.text(title_x, 0.972, title, ha="left", va="top", fontsize=17, weight="bold")
    figure.text(title_x, 0.933, note, ha="left", va="top", fontsize=9.5, color="#33363a")
    figure.text(
        0.026,
        0.018,
        "FRONT = -Y   |   TOP = +Z   |   units: mm   |   generated from the release B-rep",
        ha="left",
        fontsize=7.6,
        color="#5a6169",
    )
    if callouts:
        _draw_callouts(figure, axis, parts, legend_left)
    if measurement:
        overlay = figure.add_axes((0.0, 0.0, 1.0, 1.0), frameon=False, zorder=3)
        overlay.set_axis_off()
        overlay.annotate(
            "",
            xy=(0.60, 0.50),
            xytext=(0.08, 0.50),
            xycoords="axes fraction",
            arrowprops={"arrowstyle": "<->", "color": "#c23b32", "linewidth": 2.2},
        )
        overlay.text(
            0.34,
            0.525,
            measurement,
            ha="center",
            va="bottom",
            color="#a52f28",
            fontsize=10.5,
            weight="bold",
            transform=overlay.transAxes,
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, facecolor=figure.get_facecolor())
    plt.close(figure)
    return path


def render_print_orientations(
    output: Path,
    parameters: DesignParameters,
) -> list[Path]:
    """Render every released part in the exact orientation encoded in its 3MF."""
    from satellite1_ultra.exporting import PARTS, print_oriented

    written: list[Path] = []
    for name, definition in PARTS.items():
        shape = print_oriented(definition.builder(parameters))
        path = output / f"print_orientation_{name}.png"
        written.append(
            _scene(
                path,
                {name: shape},
                f"Print orientation — {name}",
                f"BED = Z=0. {definition.print_orientation}. "
                "Keep sealing and insert faces free of support scars.",
                View("print", 23.0, -52.0),
                {name: (0.30, 0.46, 0.64)},
            )
        )
    from cadquery import importers

    from satellite1_ultra.official import OFFICIAL_PRINT_PARTS

    for part in OFFICIAL_PRINT_PARTS:
        shape = cast(cq.Shape, importers.importStep(str(part.step_path)).val())
        bounds = shape.BoundingBox()
        shape = shape.translate(cq.Vector(0, 0, -bounds.zmin))
        path = output / f"print_orientation_{part.name}.png"
        written.append(
            _scene(
                path,
                {part.name: shape},
                f"Official print orientation — {part.name}",
                "BED = lowest native-Z face, as shown. Preserve the official file unchanged; "
                "inspect all snap features and screw passages.",
                View("print", 23.0, -52.0),
                {part.name: (0.42, 0.44, 0.48)},
            )
        )
    return written


def render_calibration_diagrams(
    output: Path,
    parameters: DesignParameters,
) -> list[Path]:
    """Render the actual calibration B-reps with unambiguous measurement notes."""
    from satellite1_ultra.coupons import COUPONS
    from satellite1_ultra.exporting import print_oriented
    from satellite1_ultra.geometry import cable_gland

    diagrams: tuple[tuple[str, tuple[str, ...], str, str], ...] = (
        (
            "calibration_official_interface",
            ("coupon_official_interface",),
            "Inside jaws: engraved 110.60 mm XY span. Outside jaws: four clean 3.00 mm edges.",
            "CALIPER JAWS: 110.60 mm SPAN",
        ),
        (
            "calibration_fasteners",
            ("coupon_heat_set_insert",),
            "Functional gauges: M3 screw in 3.4/3.5/3.6 holes; insert in 4.0–4.3 blind bores.",
            "USE SCREW / INSERT AS GAUGES",
        ),
        (
            "calibration_driver",
            ("coupon_active_driver",),
            "Seat the purchased ND91-4 by hand. Measure its flange thickness at four quadrants.",
            "SEAT DRIVER BY HAND",
        ),
        (
            "calibration_radiator",
            ("coupon_passive_radiator",),
            "Seat one SB12PACR-00 by hand. Measure its flange thickness at four quadrants.",
            "SEAT RADIATOR BY HAND",
        ),
        (
            "calibration_gasket",
            ("coupon_gasket_base", "coupon_gasket_cap"),
            "Measure sheet thickness; tighten until both hard stops touch; inspect the closed light path.",
            "GASKET BETWEEN BASE AND CAP",
        ),
        (
            "calibration_cable",
            ("coupon_cable_passage", "cable_gland"),
            "Fit the two actual 22 AWG conductors. The gland must seat by hand and resist rotation.",
            "INSERT GLAND WITH TWO WIRES",
        ),
    )
    written: list[Path] = []
    for stem, names, note, measurement in diagrams:
        parts: dict[str, cq.Shape] = {}
        x_offset = 0.0
        for name in names:
            shape = cable_gland(parameters) if name == "cable_gland" else COUPONS[name](parameters)
            shape = print_oriented(shape)
            box = shape.BoundingBox()
            parts[name] = shape.translate(cq.Vector(x_offset - box.xmin, 0.0, 0.0))
            x_offset += box.xlen + 12.0
        written.append(
            _scene(
                output / f"{stem}.png",
                parts,
                stem.replace("_", " ").title(),
                note,
                View("calibration", 68.0, -90.0),
                {name: (0.33, 0.48, 0.66) for name in parts},
                measurement,
            )
        )
    return written


def render_assembly_stages(
    output: Path,
    parameters: DesignParameters,
) -> list[Path]:
    """Render one uncluttered CAD-derived view for every assembly stage."""
    from satellite1_ultra.documentation import ASSEMBLY_STEPS

    # Titles come from the guide itself, so a sheet can never disagree with the
    # step it illustrates.
    titles = {step["number"]: step["title"] for step in ASSEMBLY_STEPS}
    # Keep the purchased driver/radiator envelopes: a step that says "seat the
    # driver" has to show the driver.  Board keep-outs stay out, because a bare
    # box would read as a part the builder is meant to fit.
    all_parts = {
        name: shape
        for name, shape in release_parts(parameters, include_official=True).items()
        if not (name.startswith("official") and "envelope" in name)
    }
    stage_names: tuple[tuple[str, tuple[str, ...], str, tuple[str, ...]], ...] = (
        (
            "assembly_stage_01_identify",
            ("main_cabinet", "official_mid_plate", "official_top_plate"),
            "Confirm Batch 1 hardware and inspect every printed sealing land.",
            (),
        ),
        (
            "assembly_stage_02_inserts",
            ("main_cabinet", "pressure_divider", "base_skirt", "ballast_cartridge"),
            "Install every insert square in its blind bore; let it cool before checking.",
            (),
        ),
        (
            "assembly_stage_03_driver",
            (
                "main_cabinet",
                "active_driver_gasket",
                "driver_envelope",
                "active_driver_clamp_ring",
            ),
            "FRONT is -Y. Red wire to +; tighten F04 diagonally to 0.35 N m.",
            ("active_driver_gasket", "driver_envelope", "active_driver_clamp_ring"),
        ),
        (
            "assembly_stage_04_radiators",
            (
                "main_cabinet",
                "pr_-1_gasket",
                "pr_-1_envelope",
                "pr_-1_clamp_ring",
                "pr_+1_gasket",
                "pr_+1_envelope",
                "pr_+1_clamp_ring",
            ),
            "Install equal measured mass on both ±X radiators; cross-tighten F05.",
            (
                "pr_-1_gasket",
                "pr_-1_envelope",
                "pr_-1_clamp_ring",
                "pr_+1_gasket",
                "pr_+1_envelope",
                "pr_+1_clamp_ring",
            ),
        ),
        (
            "assembly_stage_05_sealing",
            ("main_cabinet", "divider_gasket", "pressure_divider", "wire_gland"),
            "Close G01, gross-screen at only 100–250 Pa, then fit G04 flange-up.",
            ("divider_gasket", "pressure_divider", "wire_gland"),
        ),
        (
            "assembly_stage_06_ballast",
            (
                "base_skirt",
                "ballast_cartridge",
                "ballast_cartridge_lid",
                "bottom_service_plate",
            ),
            "Two steel plates from BOM item B01 are enclosed by the four-screw lid.",
            ("steel_plate_lower", "steel_plate_upper", "ballast_cartridge_lid"),
        ),
        (
            "assembly_stage_07_shell",
            ("main_cabinet", "outer_shell", "bottom_service_plate"),
            "Align FRONT=-Y and lower the shell without contacting a surround.",
            ("outer_shell",),
        ),
        (
            "assembly_stage_08_upper",
            (
                "pressure_divider",
                "electronics_shroud",
                "official_mid_plate",
                "official_mid_plate_threads",
                "official_pcb_spacer",
                "official_top_plate",
                "official_lock_ring",
            ),
            "Mount the official mid-plate to the measured four-point interface; preserve USB-C.",
            (
                "electronics_shroud",
                "official_mid_plate",
                "official_mid_plate_threads",
                "official_pcb_spacer",
                "official_top_plate",
                "official_lock_ring",
            ),
        ),
        (
            "assembly_stage_09_final",
            tuple(all_parts),
            "Final inspection: all seams even, all openings clear, no loose hardware.",
            (),
        ),
    )
    written: list[Path] = []
    for index, (stem, names, note, highlight) in enumerate(stage_names, start=1):
        parts = {name: all_parts[name] for name in names if name in all_parts}
        if not parts:
            raise ValueError(f"assembly-stage render {index} resolved no CAD parts")
        if index == 6:
            plate_width, plate_depth, _ = ballast_plate_extent(parameters)
            plate_z = parameters.base_bottom_z + parameters.bottom_plate_thickness + 2.0
            steel = cast(
                cq.Shape,
                cq.Workplane("XY", origin=(0.0, 0.0, plate_z))
                .box(plate_width, plate_depth, 5.0, centered=(True, True, False))
                .val(),
            )
            parts = {
                "base_skirt": all_parts["base_skirt"],
                "ballast_cartridge": all_parts["ballast_cartridge"],
                "steel_plate_lower": steel.translate(cq.Vector(0.0, 0.0, 22.0)),
                "steel_plate_upper": steel.translate(cq.Vector(0.0, 0.0, 35.0)),
                "ballast_cartridge_lid": all_parts["ballast_cartridge_lid"].translate(
                    cq.Vector(0.0, 0.0, 52.0)
                ),
                "bottom_service_plate": all_parts["bottom_service_plate"].translate(
                    cq.Vector(0.0, 0.0, -22.0)
                ),
            }
        elif 2 <= index <= 8:
            official_lift = 0.0
            lifted: dict[str, cq.Shape] = {}
            for name, shape in parts.items():
                if name.startswith("official"):
                    official_lift += 26.0
                    offset = cq.Vector(0.0, 0.0, 40.0 + official_lift)
                else:
                    offset = cq.Vector(*_placement(name).direction) * max(
                        12.0, _placement(name).distance * 0.65
                    )
                lifted[name] = shape.translate(offset)
            parts = lifted
        written.append(
            _scene(
                output / f"{stem}.png",
                parts,
                titles.get(str(index), f"Assembly stage {index}"),
                note,
                VIEWS[0] if index != 4 else View("side", 12.0, -88.0),
                _doc_colors(parts, highlight),
                callouts=True,
                step_badge=f"STEP {index}",
            )
        )
    return written


def render_fastener_identification(output: Path) -> Path:
    """Render the authoritative visual fastener schedule without loading CAD."""
    output.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(11.0, 5.5), dpi=180)
    axis.set_aspect("equal")
    axis.set_xlim(0, 78)
    axis.set_ylim(0, 38)
    axis.axis("off")
    screw_specs = (
        ("F01", 6.0, "M3 × 6 ISO 4762 socket cap"),
        (
            "F02 / F06 / F08 / F09",
            8.0,
            "M3 × 8 ISO 7380-1 button head; F09 adds washer",
        ),
        ("F10 / F11", 8.0, "M3 × 8 ISO 4762 socket cap; official upper stack"),
        ("F03 / F04 / F05 / F07", 10.0, "M3 × 10 ISO 4762 socket cap"),
    )
    for index, (identifier, length, label) in enumerate(screw_specs):
        y = 32.0 - index * 8.5
        axis.add_patch(
            Rectangle((8.0, y - 1.5), length, 3.0, facecolor="#617b96", edgecolor="#24313d")
        )
        axis.add_patch(Circle((8.0, y), 2.75, facecolor="#617b96", edgecolor="#24313d"))
        axis.annotate(
            "",
            xy=(8.0, y - 4.0),
            xytext=(8.0 + length, y - 4.0),
            arrowprops={"arrowstyle": "<->", "color": "#bd3b32", "linewidth": 1.5},
        )
        axis.text(8.0 + length / 2.0, y - 5.8, f"{length:.0f} mm", ha="center", fontsize=9)
        axis.text(30.0, y + 0.8, identifier, fontsize=10, weight="bold")
        axis.text(30.0, y - 2.0, label, fontsize=9)
    axis.text(
        4.0,
        36.0,
        "Fastener identification - proportional dimensions",
        fontsize=15,
        weight="bold",
    )
    axis.text(
        4.0,
        0.5,
        "All screws: M3 × 0.5, A2-70 stainless. Use a 2.0 mm hex tool. "
        "Torque 0.35 N m target; never exceed 0.45 N m. Use stated dimensions, "
        "not printed-page scale.",
        fontsize=9,
    )
    fastener_path = output / "fastener_identification.png"
    figure.savefig(fastener_path, bbox_inches="tight", facecolor="#f4f4f5")
    plt.close(figure)
    return fastener_path


def _fan_out(scene: dict[str, cq.Shape], gap: float = 26.0) -> dict[str, cq.Shape]:
    """Explode a scene so that no part visually nests inside another.

    Fixed explosion distances are tuned for a service diagram, where parts only
    have to suggest a removal direction.  An identification sheet has a harder
    requirement: every part must be separately visible.  So instead of scaling
    the service distances, walk each removal direction outward and place parts
    end to end using their real bounding boxes, leaving a constant gap.
    """
    groups: dict[tuple[float, float, float], list[str]] = {}
    for name in scene:
        placement = _placement(name)
        if name.startswith("official"):
            direction = (0.0, 0.0, 1.0)
        elif placement.distance <= 0.0:
            continue  # the cabinet is the fixed datum everything moves away from
        else:
            direction = placement.direction
        groups.setdefault(direction, []).append(name)

    datum = scene["main_cabinet"].BoundingBox()
    exploded: dict[str, cq.Shape] = {"main_cabinet": scene["main_cabinet"]}
    for direction, names in groups.items():
        index = next(i for i, value in enumerate(direction) if value != 0.0)
        sign = direction[index]
        # Official parts sit above the divider, so order them by their own
        # height; everything else follows its documented removal order.
        names.sort(
            key=lambda name: (
                scene[name].BoundingBox().zmin
                if name.startswith("official")
                else _placement(name).distance
            )
        )
        frontier = (datum.xlen, datum.ylen, datum.zlen)[index] / 2.0 + gap
        for name in names:
            box = scene[name].BoundingBox()
            extent = (box.xlen, box.ylen, box.zlen)[index]
            frontier += extent / 2.0
            centre = (
                (box.xmin + box.xmax) / 2.0,
                (box.ymin + box.ymax) / 2.0,
                (box.zmin + box.zmax) / 2.0,
            )[index]
            datum_centre = (
                (datum.xmin + datum.xmax) / 2.0,
                (datum.ymin + datum.ymax) / 2.0,
                (datum.zmin + datum.zmax) / 2.0,
            )[index]
            shift = [0.0, 0.0, 0.0]
            shift[index] = datum_centre + sign * frontier - centre
            exploded[name] = scene[name].translate(cq.Vector(*shift))
            frontier += extent / 2.0 + gap
    return exploded


def render_special_views(output: Path, parameters: DesignParameters) -> list[Path]:
    """Render identification, service, gasket, and wall-thickness views."""
    parts = {
        name: shape
        for name, shape in release_parts(parameters, include_official=True).items()
        if "envelope" not in name
    }
    exploded = {
        name: shape.translate(
            cq.Vector(*_placement(name).direction) * _placement(name).distance
            if not name.startswith("official")
            else cq.Vector(0.0, 0.0, 95.0)
        )
        for name, shape in parts.items()
    }
    # The identification sheet is the one place the purchased driver and both
    # radiators must appear: a builder checking parts off holds them too.  It
    # also explodes much further than the service view, because a part nested
    # inside the cabinet cannot be identified at all.
    scene = {
        name: shape
        for name, shape in release_parts(parameters, include_official=True).items()
        if not (name.startswith("official") and "envelope" in name)
    }
    identification = _fan_out(scene)
    gasket_parts = {
        name: shape
        for name, shape in parts.items()
        if "gasket" in name or name in {"main_cabinet", "pressure_divider", "wire_gland"}
    }
    service_parts = {
        name: shape
        for name, shape in exploded.items()
        if name
        in {
            "anti_slip_ring",
            "outer_shell",
            "bottom_service_plate",
            "ballast_cartridge_lid",
            "ballast_cartridge",
            "base_skirt",
            "main_cabinet",
        }
    }
    return [
        _scene(
            output / "exploded_parts_identification.png",
            identification,
            "Every part, named",
            "Numbered key gives the plain name and the exact file or purchased item for each piece.",
            colors=_doc_colors(identification),
            callouts=True,
        ),
        _scene(
            output / "gasket_placement.png",
            gasket_parts,
            "Acoustic pressure-boundary seals",
            "G01 divider, G02 driver, two G03 radiator annuli, and G04 wire gland.",
            colors=_doc_colors(
                gasket_parts,
                tuple(name for name in gasket_parts if "gasket" in name or name == "wire_gland"),
            ),
            callouts=True,
        ),
        _scene(
            output / "service_disassembly.png",
            service_parts,
            "Bottom-up service access",
            "Remove anti-slip ring, F09 shell screws, F08 plate, F06 lid, then lift ballast safely.",
            colors=_doc_colors(service_parts),
            callouts=True,
        ),
        _scene(
            output / "wall_thickness_sections.png",
            cross_section_parts(parameters, "xz"),
            "Principal wall-thickness section",
            f"Nominal shell wall {parameters.wall_thickness:.2f} mm; gasket lands and bosses "
            "are checked by solid-fraction and local-wall validation gates.",
        ),
        render_fastener_identification(output),
    ]


def generate_renders(
    output: Path = ROOT / "reports" / "renders",
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> list[Path]:
    """Produce the complete render deliverable set."""
    written = render_views(output, parameters, exploded=False)
    written += render_views(output, parameters, exploded=True)
    written += render_cross_sections(output, parameters)
    written.append(render_part_sheet(output, parameters))
    written += render_print_orientations(output, parameters)
    written += render_calibration_diagrams(output, parameters)
    written += render_assembly_stages(output, parameters)
    written += render_special_views(output, parameters)
    return written
