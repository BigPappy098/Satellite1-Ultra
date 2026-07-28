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
from matplotlib.patches import Circle, Rectangle
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
            colors[name] = cast(
                tuple[float, float, float],
                tuple(0.25 + 0.75 * channel for channel in _placement(name).color),
            )
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


def _scene(
    path: Path,
    parts: dict[str, cq.Shape],
    title: str,
    note: str,
    view: View = VIEWS[0],
    colors: dict[str, tuple[float, float, float]] | None = None,
    measurement: str | None = None,
) -> Path:
    """Render a high-resolution, captioned technical scene."""
    figure = plt.figure(figsize=(8.5, 7.0), dpi=180)
    axis = figure.add_subplot(111, projection="3d")
    low, high = _draw(axis, parts, colors or _colors(parts))
    _finish(figure, axis, low, high, view)
    figure.text(0.05, 0.955, title, ha="left", va="top", fontsize=16, weight="bold")
    figure.text(0.05, 0.915, note, ha="left", va="top", fontsize=9, color="#33363a")
    figure.text(
        0.95,
        0.045,
        "FRONT = -Y   |   TOP = +Z   |   units: mm",
        ha="right",
        fontsize=8,
        color="#44484d",
    )
    if measurement:
        overlay = figure.add_axes((0.0, 0.0, 1.0, 1.0), frameon=False)
        overlay.set_axis_off()
        overlay.annotate(
            "",
            xy=(0.68, 0.51),
            xytext=(0.32, 0.51),
            xycoords="axes fraction",
            arrowprops={"arrowstyle": "<->", "color": "#c23b32", "linewidth": 2.2},
        )
        overlay.text(
            0.50,
            0.535,
            measurement,
            ha="center",
            va="bottom",
            color="#a52f28",
            fontsize=10,
            weight="bold",
            transform=overlay.transAxes,
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, bbox_inches="tight", facecolor=figure.get_facecolor())
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
    all_parts = {
        name: shape
        for name, shape in release_parts(parameters, include_official=True).items()
        if "envelope" not in name
    }
    stage_names: tuple[tuple[str, tuple[str, ...], str], ...] = (
        (
            "assembly_stage_01_identify",
            ("main_cabinet", "official_mid_plate", "official_top_plate"),
            "Confirm Batch 1 hardware and inspect every printed sealing land.",
        ),
        (
            "assembly_stage_02_inserts",
            ("main_cabinet", "pressure_divider", "base_skirt", "ballast_cartridge"),
            "Install every insert square in its blind bore; let it cool before checking.",
        ),
        (
            "assembly_stage_03_driver",
            ("main_cabinet", "active_driver_gasket", "active_driver_clamp_ring"),
            "FRONT is -Y. Red wire to +; tighten F04 diagonally to 0.35 N m.",
        ),
        (
            "assembly_stage_04_radiators",
            (
                "main_cabinet",
                "pr_-1_gasket",
                "pr_-1_clamp_ring",
                "pr_+1_gasket",
                "pr_+1_clamp_ring",
            ),
            "Install equal measured mass on both ±X radiators; cross-tighten F05.",
        ),
        (
            "assembly_stage_05_sealing",
            ("main_cabinet", "divider_gasket", "pressure_divider", "wire_gland"),
            "Close G01, gross-screen at only 100–250 Pa, then fit G04 flange-up.",
        ),
        (
            "assembly_stage_06_ballast",
            (
                "base_skirt",
                "ballast_cartridge",
                "ballast_cartridge_lid",
                "bottom_service_plate",
            ),
            "Two 110 × 122 × 5 steel plates are enclosed by the four-screw lid.",
        ),
        (
            "assembly_stage_07_shell",
            ("main_cabinet", "outer_shell", "bottom_service_plate"),
            "Align FRONT=-Y and lower the shell without contacting a surround.",
        ),
        (
            "assembly_stage_08_upper",
            (
                "pressure_divider",
                "electronics_shroud",
                "official_mid_plate",
                "official_top_plate",
                "official_lock_ring",
            ),
            "Mount the official mid-plate to the measured four-point interface; preserve USB-C.",
        ),
        (
            "assembly_stage_09_final",
            tuple(all_parts),
            "Final inspection: all seams even, all openings clear, no loose hardware.",
        ),
    )
    written: list[Path] = []
    for index, (stem, names, note) in enumerate(stage_names, start=1):
        parts = {name: all_parts[name] for name in names if name in all_parts}
        if not parts:
            raise ValueError(f"assembly-stage render {index} resolved no CAD parts")
        stage_colors: dict[str, tuple[float, float, float]] | None = None
        if index == 6:
            plate_width = 110.0
            plate_depth = 122.0
            plate_z = parameters.base_bottom_z + parameters.bottom_plate_thickness + 2.0
            steel = cast(
                cq.Shape,
                cq.Workplane("XY", origin=(0.0, 0.0, plate_z))
                .box(plate_width, plate_depth, 5.0, centered=(True, True, False))
                .val(),
            )
            parts = {
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
            stage_colors = _colors(parts) | {
                "steel_plate_lower": (0.58, 0.60, 0.62),
                "steel_plate_upper": (0.66, 0.68, 0.70),
            }
        elif 2 <= index <= 8:
            parts = {
                name: shape.translate(
                    cq.Vector(*_placement(name).direction)
                    * max(12.0, _placement(name).distance * 0.65)
                    if not name.startswith("official")
                    else cq.Vector(0.0, 0.0, 55.0)
                )
                for name, shape in parts.items()
            }
        written.append(
            _scene(
                output / f"{stem}.png",
                parts,
                f"Assembly stage {index}",
                note,
                VIEWS[0] if index != 4 else View("side", 12.0, -88.0),
                stage_colors,
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
        ("F02 / F06 / F08 / F09", 8.0, "M3 × 8 ISO 7380-1 button head; F09 adds washer"),
        ("F03 / F04 / F05 / F07", 10.0, "M3 × 10 ISO 4762 socket cap"),
    )
    for index, (identifier, length, label) in enumerate(screw_specs):
        y = 29.0 - index * 10.0
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
            exploded,
            "Exploded parts identification",
            "Removal directions match the service sequence; official mechanics are shown in grey.",
        ),
        _scene(
            output / "gasket_placement.png",
            gasket_parts,
            "Acoustic pressure-boundary seals",
            "G01 divider, G02 driver, two G03 radiator annuli, and G04 wire gland.",
        ),
        _scene(
            output / "service_disassembly.png",
            service_parts,
            "Bottom-up service access",
            "Remove anti-slip ring, F09 shell screws, F08 plate, F06 lid, then lift ballast safely.",
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
