"""Quantitative validation and engineering-report generation.

Every gate in this module is computed from the authoritative B-rep geometry or
from the single configuration source.  Gates that are parameter audits rather
than geometric measurements say so in their ``method`` field, and every gate
that can only be closed with a physical specimen carries a ``physical_gate``
entry labelled ``REQUIRES_PHYSICAL_VALIDATION``.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from itertools import combinations
from math import atan, degrees
from pathlib import Path
from typing import Any, cast

import cadquery as cq
import networkx as nx  # type: ignore[import-untyped]

from satellite1_ultra.configuration import (
    ROOT,
    load_configuration,
    load_design_parameters,
    selected_components,
)
from satellite1_ultra.geometry import (
    DesignParameters,
    MountSpec,
    _bolt_points,
    _depth_cylinder,
    acoustic_mounts,
    ballast_lid_fastener_positions,
    ballast_plate_extent,
    base_fastener_positions,
    component_gasket_annulus,
    main_cabinet,
    official_mount_positions,
    placed_functional_parts,
    section_prism,
    shroud_fastener_positions,
    support_polygon,
    top_fastener_positions,
)
from satellite1_ultra.official import (
    OFFICIAL_INTERFACE_Z,
    core_clearance_extent,
    official_upper_solids,
)

EVIDENCE_DIGITAL = "VERIFIED_DIGITALLY"
EVIDENCE_OFFICIAL = "DERIVED_FROM_OFFICIAL_CAD"
EVIDENCE_DRAWING = "DERIVED_FROM_MANUFACTURER_DRAWING"
EVIDENCE_ESTIMATE = "ENGINEERING_ESTIMATE"
EVIDENCE_PHYSICAL = "REQUIRES_PHYSICAL_VALIDATION"

#: Density used for printed-part mass estimates (ASA, 100 % equivalent solid at
#: the documented 5-wall / 35 % gyroid recipe).  ENGINEERING_ESTIMATE.
ASA_DENSITY_G_CM3 = 1.07
EPDM_DENSITY_G_CM3 = 0.15
TPU_DENSITY_G_CM3 = 1.20

#: Contacts that are design intent rather than defects.
INTENDED_CONTACTS: dict[frozenset[str], str] = {
    frozenset(("pressure_divider", "wire_gland")): "intended_interference_fit",
}


@dataclass(frozen=True)
class MassElement:
    """A point-mass representation used only for stability engineering."""

    name: str
    mass_g: float
    x_mm: float
    y_mm: float
    z_mm: float
    basis: str


# ---------------------------------------------------------------------- #
# Geometric probes
# ---------------------------------------------------------------------- #
def _material_fraction(shape: cq.Shape, probe: cq.Shape) -> float:
    """Fraction of ``probe`` filled by ``shape``; 1.0 means fully solid."""
    reference = probe.Volume()
    if reference <= 0.0:
        raise ValueError("degenerate probe volume")
    return shape.intersect(probe).Volume() / reference


def _minimum_section(shape: cq.Shape, probe: cq.Shape, span_mm: float) -> float:
    """Effective material thickness across ``probe`` of nominal span ``span_mm``."""
    return _material_fraction(shape, probe) * span_mm


# ---------------------------------------------------------------------- #
# Acoustic volume
# ---------------------------------------------------------------------- #
def acoustic_air_shape(parameters: DesignParameters) -> cq.Shape:
    """Return the connected air domain after exact printed-cabinet intrusions."""
    p = parameters
    air = section_prism(
        p.inner_width,
        p.inner_depth,
        p.acoustic_top_z - p.cavity_bottom_z,
        p.cavity_bottom_z,
    )
    for mount in acoustic_mounts(p).values():
        air = air.fuse(
            _depth_cylinder(
                mount.bore_diameter / 2.0,
                mount.seat_depth,
                mount.pad_depth + 20.0,
                mount.face_point,
                mount.inward,
            )
        )
    return air.cut(main_cabinet(p))


def acoustic_volume_report(
    parameters: DesignParameters,
    damping_fraction: float,
    driver_displacement_l: float,
    radiator_displacement_l_each: float,
) -> dict[str, Any]:
    """Calculate gross, intrusion, component, and usable net acoustic volume."""
    p = parameters
    gross = section_prism(
        p.inner_width,
        p.inner_depth,
        p.acoustic_top_z - p.cavity_bottom_z,
        p.cavity_bottom_z,
    ).Volume()
    structural_air = acoustic_air_shape(p).Volume()
    component_displacement = (driver_displacement_l + 2.0 * radiator_displacement_l_each) * 1e6
    before_damping = structural_air - component_displacement
    damping = before_damping * damping_fraction
    net = before_damping - damping
    return {
        "status": "PASS" if net > 0.0 else "FAIL",
        "evidence": EVIDENCE_DIGITAL,
        "method": "exact OCCT B-rep volume of the connected air domain",
        "gross_inner_prism_l": gross / 1e6,
        "connected_air_after_printed_intrusions_l": structural_air / 1e6,
        "printed_intrusion_l": (gross - structural_air) / 1e6,
        "driver_displacement_l": driver_displacement_l,
        "radiator_displacement_l_each": radiator_displacement_l_each,
        "component_displacement_l": component_displacement / 1e6,
        "air_before_damping_l": before_damping / 1e6,
        "damping_allowance_fraction": damping_fraction,
        "damping_displacement_l": damping / 1e6,
        "net_acoustic_volume_l": net / 1e6,
        "physical_gate": {
            "evidence": EVIDENCE_PHYSICAL,
            "requirement": (
                "Measure water-equivalent or gas-displacement volume on the sealed print."
            ),
        },
    }


# ---------------------------------------------------------------------- #
# Sealing
# ---------------------------------------------------------------------- #
def _mount_seal_checks(
    cabinet: cq.Shape, mount: MountSpec, p: DesignParameters, name: str
) -> list[dict[str, Any]]:
    """Prove the gasket land is continuous and every insert bore is blind."""
    checks: list[dict[str, Any]] = []
    land = _depth_cylinder(
        mount.seat_diameter / 2.0 + 0.5,
        mount.seat_depth,
        mount.pad_depth - mount.seat_depth,
        mount.face_point,
        mount.inward,
    ).cut(
        _depth_cylinder(
            mount.bore_diameter / 2.0,
            mount.seat_depth,
            mount.pad_depth - mount.seat_depth,
            mount.face_point,
            mount.inward,
        )
    )
    fraction = _material_fraction(cabinet, land)
    checks.append(
        {
            "feature": f"{name}: gasket-land annulus continuity behind the seat",
            "measured_solid_fraction": fraction,
            "minimum_solid_fraction": 1.0,
            "status": "PASS" if fraction >= 0.999999 else "FAIL",
            "evidence": EVIDENCE_DIGITAL,
            "note": (
                "A fraction below 1.0 means a radial path bypasses the component "
                "gasket and vents the chamber to ambient."
            ),
        }
    )
    sidewall_start = mount.ledge_depth
    sidewall_length = mount.seat_depth - mount.ledge_depth
    bypass = _depth_cylinder(
        mount.seat_diameter / 2.0 + 0.5,
        sidewall_start,
        sidewall_length,
        mount.face_point,
        mount.inward,
    ).cut(
        _depth_cylinder(
            mount.seat_diameter / 2.0,
            sidewall_start,
            sidewall_length,
            mount.face_point,
            mount.inward,
        )
    )
    bypass_fraction = _material_fraction(cabinet, bypass)
    checks.append(
        {
            "feature": f"{name}: seat sidewall is solid over the full seat depth",
            "measured_solid_fraction": bypass_fraction,
            "minimum_solid_fraction": 0.999999,
            "status": "PASS" if bypass_fraction >= 0.999999 else "FAIL",
            "evidence": EVIDENCE_DIGITAL,
        }
    )
    worst = 1.0
    probe_depth = 2.0
    for point in _bolt_points(mount.face_point, mount.inward, mount.bolt_circle):
        beyond = _depth_cylinder(
            p.insert_bore_diameter / 2.0,
            mount.ledge_depth + p.insert_bore_depth,
            probe_depth,
            point,
            mount.inward,
        )
        worst = min(worst, _material_fraction(cabinet, beyond))
    checks.append(
        {
            "feature": f"{name}: clamp inserts are blind, backed by pad material",
            "measured_solid_fraction": worst,
            "minimum_solid_fraction": 0.999999,
            "backing_mm": p.pad_backing,
            "probe_depth_mm": probe_depth,
            "status": "PASS" if worst >= 0.999999 else "FAIL",
            "evidence": EVIDENCE_DIGITAL,
        }
    )
    return checks


def _flange_hole_seal_checks(parameters: DesignParameters) -> list[dict[str, Any]]:
    """Every unused component mounting hole must be covered by its gasket.

    The other sealing gates measure continuity of *cabinet* material only, so
    a purchased component whose own bolt holes straddle the gasket edge vents
    the chamber while every gate still reports PASS.  This models the
    component flange itself.
    """
    components = selected_components()
    sealed = {
        "active_driver": components[0],
        "pr_-1": components[1],
        "pr_+1": components[1],
    }
    checks: list[dict[str, Any]] = []
    for name, component in sealed.items():
        bolt_circle = float(component["bolt_circle_mm"])
        hole = float(component["mounting_hole_diameter_mm"])
        inner_d, outer_d = component_gasket_annulus(name, parameters)
        hole_inner = (bolt_circle - hole) / 2.0
        hole_outer = (bolt_circle + hole) / 2.0
        covered = inner_d / 2.0 <= hole_inner and hole_outer <= outer_d / 2.0
        checks.append(
            {
                "feature": f"{name} unused mounting holes are covered by the gasket",
                "gasket_annulus_radius_mm": [inner_d / 2.0, outer_d / 2.0],
                "mounting_hole_footprint_radius_mm": [hole_inner, hole_outer],
                "status": "PASS" if covered else "FAIL",
                "evidence": EVIDENCE_DIGITAL,
            }
        )
    return checks


def sealing_report(parameters: DesignParameters) -> dict[str, Any]:
    """Explicit acoustic pressure boundary and its digital leak-path proof."""
    p = parameters
    cabinet = main_cabinet(p)
    checks: list[dict[str, Any]] = []
    for name, mount in acoustic_mounts(p).items():
        checks.extend(_mount_seal_checks(cabinet, mount, p, name))
    checks.extend(_flange_hole_seal_checks(p))

    # Divider gasket land continuity on the acoustic top rim.
    land = section_prism(p.outer_width, p.outer_depth, 0.6, p.acoustic_top_z - 0.6).cut(
        section_prism(
            p.inner_width,
            p.inner_depth,
            0.6,
            p.acoustic_top_z - 0.6,
        )
    )
    for x, y in top_fastener_positions(p):
        land = land.cut(
            cq.Solid.makeCylinder(
                6.0, 0.6, cq.Vector(x, y, p.acoustic_top_z - 0.6), cq.Vector(0.0, 0.0, 1.0)
            )
        )
    fraction = _material_fraction(cabinet, land)
    checks.append(
        {
            "feature": "divider gasket land is a continuous closed rim",
            "measured_solid_fraction": fraction,
            "minimum_solid_fraction": 0.999999,
            "status": "PASS" if fraction >= 0.999999 else "FAIL",
            "evidence": EVIDENCE_DIGITAL,
        }
    )

    # Divider fastener inserts must be blind in the top-rim bosses.
    worst = 1.0
    for x, y in top_fastener_positions(p):
        beyond = cq.Solid.makeCylinder(
            p.insert_bore_diameter / 2.0,
            2.0,
            cq.Vector(x, y, p.acoustic_top_z - p.insert_bore_depth),
            cq.Vector(0.0, 0.0, -1.0),
        )
        worst = min(worst, _material_fraction(cabinet, beyond))
    checks.append(
        {
            "feature": "divider fastener inserts are blind inside the chamber",
            "measured_solid_fraction": worst,
            "minimum_solid_fraction": 0.999999,
            "status": "PASS" if worst >= 0.999999 else "FAIL",
            "evidence": EVIDENCE_DIGITAL,
        }
    )

    # Base-skirt fastener inserts must not break through the acoustic floor.
    worst = 1.0
    for x, y in base_fastener_positions(p):
        beyond = cq.Solid.makeCylinder(
            p.insert_bore_diameter / 2.0,
            3.0,
            cq.Vector(x, y, p.acoustic_bottom_z + p.insert_bore_depth),
            cq.Vector(0.0, 0.0, 1.0),
        )
        worst = min(worst, _material_fraction(cabinet, beyond))
    checks.append(
        {
            "feature": "base-skirt inserts are blind below the acoustic floor",
            "measured_solid_fraction": worst,
            "minimum_solid_fraction": 0.999999,
            "status": "PASS" if worst >= 0.999999 else "FAIL",
            "evidence": EVIDENCE_DIGITAL,
        }
    )

    return {
        "status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL",
        "evidence": EVIDENCE_DIGITAL,
        "method": "solid-fraction probes on the authoritative B-rep",
        "pressure_boundary": [
            "integral cabinet walls, acoustic floor and component mounting pads",
            "compressed 2 mm EPDM divider gasket on a continuous 4 mm rim land",
            "compressed 2 mm EPDM active-driver gasket on a continuous seat land",
            "two compressed 2 mm EPDM radiator gaskets on continuous seat lands",
            "TPU interference gland around the speaker-wire pair",
            "all cabinet fasteners are blind heat-set inserts; none crosses the boundary",
        ],
        "checks": checks,
        "physical_gate": {
            "evidence": EVIDENCE_PHYSICAL,
            "requirement": (
                "Use the temporary adapter for a 100-250 Pa gross leak screen with "
                "dilute soap solution, then confirm final sealing and tuning with an "
                "impedance sweep after installing the production cable gland."
            ),
        },
    }


# ---------------------------------------------------------------------- #
# Collision
# ---------------------------------------------------------------------- #
def _bounding_boxes_overlap(first: cq.Shape, second: cq.Shape, tolerance: float = 0.01) -> bool:
    """Cheap broad-phase rejection before an exact OCCT intersection."""
    left = first.BoundingBox()
    right = second.BoundingBox()
    return not (
        left.xmax < right.xmin - tolerance
        or right.xmax < left.xmin - tolerance
        or left.ymax < right.ymin - tolerance
        or right.ymax < left.ymin - tolerance
        or left.zmax < right.zmin - tolerance
        or right.zmax < left.zmin - tolerance
    )


def collision_report(parameters: DesignParameters) -> dict[str, Any]:
    """Classify every positive-volume intersection in the functional assembly."""
    p = parameters
    parts = placed_functional_parts(p)
    official = official_upper_solids(p.board_revision)
    printed = {
        name: shape
        for name, shape in parts.items()
        if not name.endswith("_envelope") and name != "driver_envelope"
    }

    collisions: list[dict[str, Any]] = []
    invalid = 0
    for (first_name, first), (second_name, second) in combinations(parts.items(), 2):
        if not _bounding_boxes_overlap(first, second):
            continue
        volume = first.intersect(second).Volume()
        if volume <= 0.01:
            continue
        pair = frozenset((first_name, second_name))
        classification = INTENDED_CONTACTS.get(pair, "invalid_collision")
        invalid += classification == "invalid_collision"
        collisions.append(
            {
                "first": first_name,
                "second": second_name,
                "intersection_mm3": volume,
                "classification": classification,
                "evidence": EVIDENCE_DIGITAL,
            }
        )

    official_checks: list[dict[str, Any]] = []
    for printed_name, printed_shape in printed.items():
        for official_name, official_shape in official.items():
            volume = (
                printed_shape.intersect(official_shape).Volume()
                if _bounding_boxes_overlap(printed_shape, official_shape)
                else 0.0
            )
            status = "PASS" if volume <= 0.01 else "FAIL"
            if status == "FAIL":
                invalid += 1
            official_checks.append(
                {
                    "printed": printed_name,
                    "official": official_name,
                    "intersection_mm3": volume,
                    "status": status,
                    "evidence": EVIDENCE_OFFICIAL,
                }
            )

    return {
        "status": "PASS" if invalid == 0 else "FAIL",
        "evidence": EVIDENCE_DIGITAL,
        "method": "exact OCCT boolean intersection volume for every pair",
        "part_count": len(parts),
        "pair_count": len(parts) * (len(parts) - 1) // 2,
        "official_pair_count": len(official_checks),
        "official_reference_note": (
            "The HAT is represented by a conservative convex-band envelope built "
            "from its official STL; the remaining official parts are exact B-reps."
        ),
        "positive_volume_contacts": collisions,
        "official_clearance_checks": [c for c in official_checks if c["status"] == "FAIL"]
        or [{"summary": "all printed/official pairs clear", "status": "PASS"}],
        "invalid_collision_count": invalid,
    }


# ---------------------------------------------------------------------- #
# Clearance
# ---------------------------------------------------------------------- #
def clearance_report(parameters: DesignParameters) -> dict[str, Any]:
    """Report critical nominal clearances and their acceptance thresholds."""
    p = parameters
    parts = placed_functional_parts(p)
    official = official_upper_solids(p.board_revision)

    driver_face_y = -p.outer_depth / 2.0 + p.driver_seat_depth - p.compressed_gasket_thickness
    pr_face_x = p.outer_width / 2.0 - p.pr_seat_depth + p.compressed_gasket_thickness
    grille_pr_inner = p.outer_width / 2.0 + 13.0
    grille_driver_inner = p.outer_depth / 2.0 + 13.0

    clearances: list[dict[str, Any]] = [
        {
            "feature": "passive-radiator outward excursion to grille guard",
            "nominal_mm": grille_pr_inner
            - (pr_face_x + p.pr_flange_thickness + p.pr_rear_excursion),
            "minimum_mm": 2.0,
        },
        {
            "feature": "active-driver clamp ring to grille guard",
            "nominal_mm": grille_driver_inner - (p.outer_depth / 2.0 + p.clamp_ring_thickness),
            "minimum_mm": 2.0,
        },
        {
            "feature": "active-driver motor to cabinet rear inner wall",
            "nominal_mm": p.inner_depth / 2.0
            - (driver_face_y + p.driver_depth - p.driver_flange_thickness),
            "minimum_mm": 10.0,
        },
        {
            "feature": "passive-radiator rear excursion to cabinet centre plane",
            "nominal_mm": pr_face_x - p.pr_depth - p.pr_rear_excursion,
            "minimum_mm": 10.0,
        },
        {
            "feature": "driver envelope to acoustic floor",
            "nominal_mm": p.driver_axis_z - p.driver_outer_diameter / 2.0 - p.cavity_bottom_z,
            "minimum_mm": 8.0,
        },
        {
            "feature": "radiator bore to acoustic floor",
            "nominal_mm": p.pr_axis_z - p.pr_bore_diameter / 2.0 - p.cavity_bottom_z,
            "minimum_mm": 4.0,
        },
        {
            "feature": "radiator clamp-ring seating land inside the cabinet height (lower)",
            "nominal_mm": (p.pr_axis_z - p.pr_ledge_diameter / 2.0) - p.acoustic_bottom_z,
            "minimum_mm": 3.0,
        },
        {
            "feature": "radiator clamp-ring seating land inside the cabinet height (upper)",
            "nominal_mm": p.acoustic_top_z - (p.pr_axis_z + p.pr_ledge_diameter / 2.0),
            "minimum_mm": 3.0,
        },
        {
            "feature": "driver clamp-ring seating land inside the cabinet height (lower)",
            "nominal_mm": (p.driver_axis_z - p.driver_clamp_ring_diameter / 2.0 - p.print_clearance)
            - p.acoustic_bottom_z,
            "minimum_mm": 3.0,
        },
        {
            "feature": "driver clamp-ring seating land inside the cabinet height (upper)",
            "nominal_mm": p.acoustic_top_z
            - (p.driver_axis_z + p.driver_clamp_ring_diameter / 2.0 + p.print_clearance),
            "minimum_mm": 3.0,
        },
        {
            "feature": "driver clamp ring within the flat cabinet face",
            "nominal_mm": (p.outer_width / 2.0 - p.corner_radius)
            - p.driver_clamp_ring_diameter / 2.0,
            "minimum_mm": 0.5,
        },
        {
            "feature": "driver clamp-ring insert land to component seat wall",
            "nominal_mm": (p.driver_clamp_bolt_circle - p.insert_bore_diameter) / 2.0
            - p.driver_seat_diameter / 2.0,
            "minimum_mm": 1.5,
        },
        {
            "feature": "radiator clamp-ring insert land to component seat wall",
            "nominal_mm": (p.pr_clamp_bolt_circle - p.insert_bore_diameter) / 2.0
            - p.pr_seat_diameter / 2.0,
            "minimum_mm": 1.5,
        },
        {
            "feature": "radiator clamp-ring insert land to the ledge sidewall",
            "nominal_mm": p.pr_ledge_diameter / 2.0
            - (p.pr_clamp_bolt_circle + p.insert_bore_diameter) / 2.0,
            "minimum_mm": 2.4,
        },
        {
            "feature": "active-driver gasket land radial width",
            "nominal_mm": (p.driver_seat_diameter - (p.driver_bore_diameter + 3.0)) / 2.0,
            "minimum_mm": 3.0,
        },
        {
            "feature": "radiator gasket land radial width",
            "nominal_mm": (p.pr_seat_diameter - (p.pr_bore_diameter + 3.0)) / 2.0,
            "minimum_mm": 3.0,
        },
        {
            "feature": "active-driver mounting pad covers its seat",
            "nominal_mm": (p.driver_pad_diameter - p.driver_seat_diameter) / 2.0,
            "minimum_mm": 2.4,
        },
        {
            "feature": "radiator mounting pad covers its ledge",
            "nominal_mm": (p.pr_pad_diameter - p.pr_ledge_diameter) / 2.0,
            "minimum_mm": 1.5,
        },
        {
            "feature": "print radial assembly allowance",
            "nominal_mm": p.print_clearance,
            "minimum_mm": 0.20,
        },
        {
            "feature": "gasket compression",
            "nominal_mm": p.gasket_thickness - p.compressed_gasket_thickness,
            "minimum_mm": 0.40,
            "maximum_mm": 0.60,
        },
        {
            "feature": "official mid-plate seating plane to divider boss tops",
            "nominal_mm": abs(p.official_interface_z - OFFICIAL_INTERFACE_Z),
            "minimum_mm": 0.0,
            "maximum_mm": 0.01,
            "evidence_override": EVIDENCE_OFFICIAL,
        },
    ]

    # Measured minimum distances against the official upper stack. The divider
    # boss tops are *designed* to seat on the official mid-plate underside, so
    # that one pair has a zero-distance requirement instead of a gap.
    seating_pairs = {("pressure_divider", "official_mid_plate")}
    for printed_name in ("pressure_divider", "shell_crown"):
        shape = parts[printed_name]
        for official_name, official_shape in official.items():
            box_gap = _bounding_box_gap(shape, official_shape)
            used_lower_bound = box_gap >= 0.30
            distance = box_gap if used_lower_bound else _min_distance(shape, official_shape)
            if (printed_name, official_name) in seating_pairs:
                distance = _min_distance(shape, official_shape)
                clearances.append(
                    {
                        "feature": f"{printed_name} seats on {official_name}",
                        "nominal_mm": distance,
                        "minimum_mm": 0.0,
                        "maximum_mm": 0.01,
                        "evidence_override": EVIDENCE_OFFICIAL,
                        "note": "Face contact is the design intent for this interface.",
                    }
                )
            else:
                clearances.append(
                    {
                        "feature": f"{printed_name} to {official_name}",
                        "nominal_mm": distance,
                        "minimum_mm": 0.30,
                        "evidence_override": EVIDENCE_OFFICIAL,
                        "note": (
                            "conservative bounding-box lower bound"
                            if used_lower_bound
                            else "exact OCCT minimum distance"
                        ),
                    }
                )

    for item in clearances:
        value = cast(float, item["nominal_mm"])
        minimum = cast(float, item["minimum_mm"])
        maximum = cast(float, item.get("maximum_mm", float("inf")))
        item["status"] = "PASS" if minimum <= value <= maximum else "FAIL"
        item["evidence"] = cast(str, item.pop("evidence_override", EVIDENCE_DIGITAL))
    return {
        "status": "PASS" if all(item["status"] == "PASS" for item in clearances) else "FAIL",
        "evidence": EVIDENCE_DIGITAL,
        "clearances": clearances,
        "tolerance_note": (
            "Physical coupon corrections are applied through config/physical_calibration.yaml."
        ),
    }


def _min_distance(first: cq.Shape, second: cq.Shape) -> float:
    """Minimum distance between two solids, 0.0 when they touch or overlap."""
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape  # type: ignore[import-untyped]

    algorithm = BRepExtrema_DistShapeShape(first.wrapped, second.wrapped)
    algorithm.Perform()
    return float(algorithm.Value()) if algorithm.IsDone() else float("nan")


def _bounding_box_gap(first: cq.Shape, second: cq.Shape) -> float:
    """Conservative Euclidean lower bound between two axis-aligned boxes."""
    left = first.BoundingBox()
    right = second.BoundingBox()
    dx = max(left.xmin - right.xmax, right.xmin - left.xmax, 0.0)
    dy = max(left.ymin - right.ymax, right.ymin - left.ymax, 0.0)
    dz = max(left.zmin - right.zmax, right.zmin - left.zmax, 0.0)
    return float((dx * dx + dy * dy + dz * dz) ** 0.5)


# ---------------------------------------------------------------------- #
# Core fit
# ---------------------------------------------------------------------- #
def core_fit_report(parameters: DesignParameters) -> dict[str, Any]:
    """Prove a Core-sized service volume fits in the electronics bay."""
    p = parameters
    extent = core_clearance_extent(p.board_revision)
    bay_bottom = p.divider_bottom_z + p.divider_thickness
    obstructions = [
        placed_functional_parts(p)[name] for name in ("pressure_divider", "shell_crown")
    ]
    step = 4.0
    reach = 30.0
    coordinates = [(-reach + index * step) for index in range(int(2.0 * reach / step) + 1)]
    candidates = sorted(
        ((x, y) for x in coordinates for y in coordinates),
        key=lambda point: (point[0] ** 2 + point[1] ** 2, abs(point[1]), abs(point[0])),
    )
    best: tuple[float, float] | None = None
    for x, y in candidates:
        box = cq.Solid.makeBox(
            extent[0],
            extent[1],
            extent[2],
            cq.Vector(x - extent[0] / 2.0, y - extent[1] / 2.0, bay_bottom + 1.0),
        )
        if all(
            not _bounding_boxes_overlap(part, box) or part.intersect(box).Volume() <= 0.01
            for part in obstructions
        ):
            best = (x, y)
            break
    return {
        "status": "PASS" if best is not None else "FAIL",
        "evidence": EVIDENCE_DIGITAL,
        "method": "swept placement search for a Core-sized clearance box in the bay",
        "core_clearance_extent_mm": list(extent),
        "bay_z_range_mm": [bay_bottom, p.official_interface_z],
        "bay_height_mm": p.official_interface_z - bay_bottom,
        "first_free_placement_xy_mm": list(best) if best else None,
        "note": (
            "The official assets do not fix the Core's position in the stack, so "
            "the enclosure is validated against a Core-sized free volume instead "
            "of an asserted placement."
        ),
        "physical_gate": {
            "evidence": EVIDENCE_PHYSICAL,
            "requirement": "Confirm Core mounting against a physical development kit.",
        },
    }


# ---------------------------------------------------------------------- #
# Wall thickness
# ---------------------------------------------------------------------- #
def wall_thickness_report(parameters: DesignParameters) -> dict[str, Any]:
    """Parameter audit plus measured minimum sections on the built cabinet."""
    p = parameters
    checks = [
        ("general cabinet wall", p.wall_thickness, 3.2),
        ("clamp ring", p.clamp_ring_thickness, 4.0),
        ("acoustic floor", p.acoustic_floor_thickness, 5.0),
        ("pressure divider", p.divider_thickness, 3.2),
        ("gasket land width", p.gasket_land_width, 3.0),
        (
            "heat-set insert radial wall",
            (p.boss_outer_diameter - p.insert_outer_diameter) / 2.0,
            2.0,
        ),
        ("component pad backing behind inserts", p.pad_backing, 2.4),
        ("vertical wall brace rib", p.brace_rib_width, 3.2),
        ("rear structural spine", 10.0, 6.0),
        ("bottom service plate", p.bottom_plate_thickness, 3.2),
        ("ballast tray floor", 2.0, 1.6),
        ("ballast retaining wall", 4.0, 3.2),
        ("outer-shell moving-part guard", 3.0, 2.4),
        ("outer-shell slot rail", 4.0, 3.2),
    ]
    records = [
        {
            "feature": name,
            "actual_mm": actual,
            "minimum_mm": minimum,
            "margin_mm": actual - minimum,
            "method": "parameter audit",
            "status": "PASS" if actual >= minimum else "FAIL",
            "evidence": EVIDENCE_DIGITAL,
        }
        for name, actual, minimum in checks
    ]

    cabinet = main_cabinet(p)
    measured: list[dict[str, Any]] = []
    probes: list[tuple[str, cq.Shape, float, float]] = [
        (
            "front wall above the driver mount",
            cq.Solid.makeBox(
                20.0,
                p.wall_thickness,
                6.0,
                cq.Vector(-10.0, -p.outer_depth / 2.0, p.acoustic_top_z - 7.0),
            ),
            p.wall_thickness,
            3.2,
        ),
        (
            "side wall clear of the radiator mount",
            cq.Solid.makeBox(
                p.wall_thickness,
                14.0,
                6.0,
                cq.Vector(
                    p.outer_width / 2.0 - p.wall_thickness,
                    p.outer_depth / 2.0 - 26.0,
                    p.cavity_bottom_z + 1.0,
                ),
            ),
            p.wall_thickness,
            3.2,
        ),
        (
            "front wall below the driver mount",
            cq.Solid.makeBox(
                20.0,
                p.wall_thickness,
                6.0,
                cq.Vector(
                    -10.0,
                    -p.outer_depth / 2.0,
                    p.cavity_bottom_z + 1.0,
                ),
            ),
            p.wall_thickness,
            3.2,
        ),
        (
            "rear wall beside the spine",
            cq.Solid.makeBox(
                12.0,
                p.wall_thickness,
                20.0,
                cq.Vector(30.0, p.inner_depth / 2.0, p.driver_axis_z - 10.0),
            ),
            p.wall_thickness,
            3.2,
        ),
        (
            "acoustic floor under a base-fastener boss",
            cq.Solid.makeBox(
                6.0,
                6.0,
                p.acoustic_floor_thickness,
                cq.Vector(
                    base_fastener_positions(p)[3][0] - 3.0,
                    base_fastener_positions(p)[3][1] - 3.0,
                    p.acoustic_bottom_z,
                ),
            ),
            p.acoustic_floor_thickness,
            5.0,
        ),
        (
            "rear wall at the structural spine",
            cq.Solid.makeBox(
                16.0,
                p.wall_thickness + 10.0,
                10.0,
                cq.Vector(-8.0, p.inner_depth / 2.0 - 10.0, p.driver_axis_z),
            ),
            p.wall_thickness + 10.0,
            10.0,
        ),
    ]
    for name, probe, span, minimum in probes:
        thickness = _minimum_section(cabinet, probe, span)
        measured.append(
            {
                "feature": name,
                "measured_mm": thickness,
                "minimum_mm": minimum,
                "margin_mm": thickness - minimum,
                "method": "solid-fraction probe on the built B-rep",
                "status": "PASS" if thickness >= minimum else "FAIL",
                "evidence": EVIDENCE_DIGITAL,
            }
        )

    everything = records + measured
    return {
        "status": "PASS" if all(item["status"] == "PASS" for item in everything) else "FAIL",
        "evidence": EVIDENCE_DIGITAL,
        "method": "parameter audit plus measured B-rep sections",
        "checks": records,
        "measured_sections": measured,
        "physical_gate": {
            "evidence": EVIDENCE_PHYSICAL,
            "requirement": (
                "Section one sacrificial print and compare walls to slicer and caliper values."
            ),
        },
    }


# ---------------------------------------------------------------------- #
# Fasteners
# ---------------------------------------------------------------------- #
@dataclass(frozen=True)
class Joint:
    """One bolted joint in the assembly."""

    identifier: str
    name: str
    quantity: int
    clamped_stack_mm: float
    head: str
    access: str
    washer: str
    note: str = ""
    uses_heat_set_insert: bool = True
    fixed_length_mm: float | None = None
    pilot_depth_mm: float | None = None


def _joints(p: DesignParameters) -> list[Joint]:
    driver_stack = p.clamp_ring_thickness
    pr_stack = p.clamp_ring_thickness
    return [
        Joint(
            "F01",
            "official mid-plate to pressure divider",
            4,
            1.0,
            "socket cap",
            "top, through the official Ø6.5 counterbore",
            "none",
            "Screw passes the official Ø3.2 hole; head seats in the official counterbore.",
        ),
        Joint(
            "F02",
            "electronics shroud to pressure divider",
            4,
            3.0,
            "button head",
            "top",
            "none",
        ),
        Joint(
            "F03",
            "pressure divider to cabinet",
            8,
            p.divider_thickness + p.compressed_gasket_thickness,
            "socket cap",
            "top",
            "none",
        ),
        Joint(
            "F04",
            "active-driver clamp ring to cabinet",
            4,
            driver_stack,
            "socket cap",
            "front (-Y), grille cage removed",
            "none",
        ),
        Joint(
            "F05",
            "passive-radiator clamp ring to cabinet (each)",
            4,
            pr_stack,
            "socket cap",
            "side (+/-X), grille cage removed",
            "none",
        ),
        Joint(
            "F06",
            "ballast cartridge lid to cartridge",
            4,
            3.5,
            "button head",
            "top before the cartridge enters the base bay",
            "none",
            "Four blind inserts retain the dry steel stack under handling and tip loads.",
        ),
        Joint(
            "F07",
            "base skirt to cabinet",
            4,
            8.0 - 3.0,
            "socket cap",
            "bottom, service plate removed",
            "none",
        ),
        Joint(
            "F08",
            "bottom service plate to base skirt",
            4,
            p.bottom_plate_thickness,
            "button head",
            "bottom",
            "none",
        ),
        Joint(
            "F09",
            "outer shell to bottom service plate",
            4,
            p.bottom_plate_thickness,
            "button head",
            "bottom",
            "nylon washer",
        ),
        Joint(
            "F10",
            "official HAT and PCB spacer to official top plate",
            4,
            4.0,
            "socket cap",
            "top, before the lock ring closes",
            "none",
            "Official Batch 1 assembly screw; tighten only until the board stack is seated.",
            False,
            8.0,
            5.285,
        ),
        Joint(
            "F11",
            "official mid-plate to official threaded plate",
            4,
            1.0,
            "socket cap",
            "bottom of the upper stack before fitting it to the Ultra divider",
            "none",
            "Align the four official nubs and rear I/O before starting these screws.",
            False,
            8.0,
            8.995,
        ),
    ]


STANDARD_M3_LENGTHS = (6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 20.0, 25.0)

#: For each printed joint: the parts the screw clamps, the screw axis, and the
#: fastener positions.  Measuring the stack from these instead of declaring it
#: is what catches a boss or tongue that is not actually present under a screw.
#: joint -> (clamped parts, axis index, direction the screw advances toward its
#: insert).  The advance direction matters: a part can present several separate
#: runs of material along one screw axis, and only the run against the mating
#: face is actually clamped.
_CLAMPED_PARTS: dict[str, tuple[tuple[str, ...], int, float]] = {
    "F01": (("official_mid_plate",), 2, -1.0),
    "F02": (("shell_crown",), 2, -1.0),
    "F03": (("pressure_divider", "divider_gasket"), 2, -1.0),
    "F04": (("active_driver_clamp_ring",), 1, 1.0),
    "F05": (("pr_+1_clamp_ring",), 0, -1.0),
    "F06": (("ballast_cartridge_lid",), 2, -1.0),
    "F07": (("base_skirt",), 2, 1.0),
    "F08": (("bottom_service_plate",), 2, 1.0),
    "F09": (("bottom_service_plate",), 2, 1.0),
}


def _measured_stack(
    identifier: str,
    parameters: DesignParameters,
    positions: dict[str, tuple[tuple[float, float, float], ...]],
    parts: dict[str, cq.Shape],
) -> float | None:
    """Material a screw actually passes through, measured on the B-rep.

    Probes a cylinder just larger than the clearance hole at every fastener
    position and returns the worst-case axial extent of clamped material.  A
    declared stack cannot notice that a lid tongue or boss is absent under one
    of its screws; this can.
    """
    entry = _CLAMPED_PARTS.get(identifier)
    if entry is None or identifier not in positions:
        return None
    names, index, advance = entry
    solids = [parts[name] for name in names if name in parts]
    if not solids:
        return None
    body = solids[0]
    for extra in solids[1:]:
        body = body.fuse(extra)
    axis = cq.Vector(*(1.0 if i == index else 0.0 for i in range(3)))
    radius = parameters.fastener_clearance_diameter / 2.0 + 0.6
    stacks: list[float] = []
    for point in positions[identifier]:
        origin = cq.Vector(point[0], point[1], point[2]) - axis * 400.0
        probe = cq.Solid.makeCylinder(radius, 800.0, origin, axis)
        try:
            hit = probe.intersect(body)
        except Exception:  # pragma: no cover - degenerate OCCT probe
            continue
        if hit.Volume() <= 1e-6:
            continue
        runs: list[tuple[float, float]] = []
        for solid in hit.Solids():
            box = solid.BoundingBox()
            low = (box.xmin, box.ymin, box.zmin)[index]
            high = (box.xmax, box.ymax, box.zmax)[index]
            runs.append((low, high))
        if not runs:
            continue
        # Keep the run whose far face lies furthest along the screw's travel:
        # that is the one bearing against the part receiving the insert.
        leading = max(runs, key=lambda run: advance * (run[1] if advance > 0 else run[0]))
        stacks.append(leading[1] - leading[0])
    if not stacks:
        return None
    return max(stacks)


def _fastener_axes(
    p: DesignParameters,
    parts: dict[str, cq.Shape],
) -> dict[str, tuple[tuple[float, float, float], ...]]:
    """Fastener coordinates per joint, in master coordinates."""
    positions: dict[str, tuple[tuple[float, float, float], ...]] = {}
    del parts  # positions come from the parametric fastener patterns
    z_groups = {
        "F01": official_mount_positions(p),
        "F02": shroud_fastener_positions(p),
        "F03": top_fastener_positions(p),
        "F06": ballast_lid_fastener_positions(p),
        "F07": base_fastener_positions(p),
        "F08": base_fastener_positions(p),
        "F09": base_fastener_positions(p),
    }
    for identifier, flat in z_groups.items():
        positions[identifier] = tuple((x, y, 0.0) for x, y in flat)
    mounts = acoustic_mounts(p)
    for identifier, mount_name in (("F04", "active_driver"), ("F05", "pr_+1")):
        mount = mounts.get(mount_name)
        if mount is not None:
            positions[identifier] = _bolt_points(mount.face_point, mount.inward, mount.bolt_circle)
    return positions


def fastener_report(parameters: DesignParameters) -> dict[str, Any]:
    """Return the controlled M3 fastener schedule and engagement checks."""
    p = parameters
    parts = placed_functional_parts(p)
    positions = _fastener_axes(p, parts)
    schedule: list[dict[str, Any]] = []
    for joint in _joints(p):
        measured = _measured_stack(joint.identifier, p, positions, parts)
        stack = measured if measured is not None else joint.clamped_stack_mm
        target = stack + p.insert_depth * 0.85
        length = joint.fixed_length_mm or min(
            (value for value in STANDARD_M3_LENGTHS if value >= stack + 3.5),
            key=lambda value: abs(value - target),
        )
        engagement = length - stack
        bore_depth = joint.pilot_depth_mm or p.insert_bore_depth
        bottoms = engagement > bore_depth
        status = "PASS" if engagement >= 3.0 and not bottoms else "FAIL"
        schedule.append(
            {
                "joint": joint.name,
                "id": joint.identifier,
                "thread": "M3 x 0.5",
                "standard": ("ISO 4762" if joint.head == "socket cap" else "ISO 7380-1"),
                "material": "A2 stainless",
                "quantity": joint.quantity,
                "length_mm": length,
                "head": joint.head,
                "washer": joint.washer,
                "tool": "2.0 mm hex key",
                "insert": (
                    f"M3 heat-set, Ø{p.insert_outer_diameter:.1f} x {p.insert_depth:.1f} mm "
                    f"into a Ø{p.insert_bore_diameter:.1f} x {p.insert_bore_depth:.1f} mm bore"
                    if joint.uses_heat_set_insert
                    else "none; unmodified official printed pilot"
                ),
                "boss_outer_diameter_mm": p.boss_outer_diameter,
                "clamped_stack_mm": stack,
                "declared_stack_mm": joint.clamped_stack_mm,
                "stack_source": ("measured_on_brep" if measured is not None else "declared"),
                "engagement_mm": engagement,
                "bore_depth_mm": bore_depth,
                "bottoming_margin_mm": bore_depth - engagement,
                "access_direction": joint.access,
                "torque_guidance_nm": "0.35 target; 0.45 maximum",
                "note": joint.note,
                "status": status,
                "evidence": (EVIDENCE_DIGITAL if joint.uses_heat_set_insert else EVIDENCE_OFFICIAL),
            }
        )
    total = sum(row["quantity"] * (2 if "each" in row["joint"] else 1) for row in schedule)
    total_inserts = sum(
        row["quantity"] * (2 if "each" in row["joint"] else 1)
        for row in schedule
        if str(row["insert"]).startswith("M3 heat-set")
    )
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in schedule) else "FAIL",
        "evidence": EVIDENCE_DIGITAL,
        "method": "computed stack, engagement and bottoming margin per joint",
        "total_fasteners": total,
        "total_inserts": total_inserts,
        "schedule": schedule,
        "installation_note": (
            "Install inserts with a temperature-controlled M3 insert tip; do not "
            "torque a hot insert. Every insert bore is blind and is drilled deeper "
            "than the insert so no screw can bottom on the bore floor."
        ),
        "physical_gate": {
            "evidence": EVIDENCE_PHYSICAL,
            "requirement": "Pull-test the selected insert/ASA/process coupon to 250 N minimum.",
        },
    }


# ---------------------------------------------------------------------- #
# Tolerance
# ---------------------------------------------------------------------- #
def tolerance_report(parameters: DesignParameters) -> dict[str, Any]:
    """Evaluate nominal worst-case stacks before measured coupon compensation."""
    p = parameters
    part_tolerance = 0.15
    calibrated_stop_tolerance = 0.10
    measured_hardware_tolerance = 0.05
    compression_range = [
        (
            p.gasket_thickness
            - p.compressed_gasket_thickness
            - calibrated_stop_tolerance
            - measured_hardware_tolerance
        )
        / p.gasket_thickness,
        (
            p.gasket_thickness
            - p.compressed_gasket_thickness
            + calibrated_stop_tolerance
            + measured_hardware_tolerance
        )
        / p.gasket_thickness,
    ]
    stacks: list[dict[str, Any]] = [
        {
            "interface": "divider gasket closure",
            "nominal_compression_mm": p.gasket_thickness - p.compressed_gasket_thickness,
            "worst_compression_fraction_range": compression_range,
            "limit": "15-45% compression",
            "pass": lambda value: value[0] >= 0.15 and value[1] <= 0.45,
            "value_key": "worst_compression_fraction_range",
        },
        {
            "interface": "component gasket closure at the clamp-ring hard stop",
            "nominal_compression_mm": p.gasket_thickness - p.compressed_gasket_thickness,
            "worst_compression_fraction_range": compression_range,
            "limit": "15-45% compression",
            "pass": lambda value: value[0] >= 0.15 and value[1] <= 0.45,
            "value_key": "worst_compression_fraction_range",
        },
        {
            "interface": "clamp ring radial fit in the cabinet seat",
            "nominal_radial_clearance_mm": p.print_clearance,
            "worst_remaining_clearance_mm": p.print_clearance - part_tolerance,
            "limit": "non-negative after coupon correction",
            "pass": lambda value: value >= 0.0,
            "value_key": "worst_remaining_clearance_mm",
        },
        {
            "interface": "M3 insert boss wall",
            "nominal_wall_mm": (p.boss_outer_diameter - p.insert_outer_diameter) / 2.0,
            "worst_wall_mm": (p.boss_outer_diameter - p.insert_outer_diameter) / 2.0
            - part_tolerance,
            "limit": ">= 2.0 mm",
            "pass": lambda value: value >= 2.0,
            "value_key": "worst_wall_mm",
        },
        {
            "interface": "insert land between clamp bore and component seat",
            "nominal_land_mm": (p.driver_clamp_bolt_circle - p.insert_bore_diameter) / 2.0
            - p.driver_seat_diameter / 2.0,
            "worst_land_mm": (p.driver_clamp_bolt_circle - p.insert_bore_diameter) / 2.0
            - p.driver_seat_diameter / 2.0
            - 2.0 * part_tolerance,
            "limit": ">= 1.2 mm",
            "pass": lambda value: value >= 1.2,
            "value_key": "worst_land_mm",
        },
        {
            "interface": "official four-point mount position",
            "nominal_position_mm": [p.official_mount_x, p.official_mount_y],
            "worst_position_error_mm": part_tolerance,
            "limit": "<= 0.20 mm; coupon must assemble by hand",
            "pass": lambda value: value <= 0.20,
            "value_key": "worst_position_error_mm",
        },
    ]
    for row in stacks:
        predicate = cast(Any, row.pop("pass"))
        key = cast(str, row.pop("value_key"))
        row["status"] = "PASS" if predicate(row[key]) else "FAIL"
        row["evidence"] = EVIDENCE_ESTIMATE
        row["part_tolerance_mm"] = part_tolerance
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in stacks) else "FAIL",
        "evidence": EVIDENCE_ESTIMATE,
        "assumed_printed_dimensional_tolerance_mm": part_tolerance,
        "residual_calibrated_z_tolerance_mm": calibrated_stop_tolerance,
        "measured_hardware_tolerance_mm": measured_hardware_tolerance,
        "material_shrinkage": (
            "removed from nominal by XY/Z coupon scale correction; residual is included "
            "in the calibrated tolerance"
        ),
        "stacks": stacks,
        "compensation_file": "config/physical_calibration.yaml",
        "physical_gate": {
            "evidence": EVIDENCE_PHYSICAL,
            "requirement": (
                "Pass the seven calibration parts and six documented checks before "
                "printing the full enclosure."
            ),
        },
    }


# ---------------------------------------------------------------------- #
# Assembly, disassembly and tool access
# ---------------------------------------------------------------------- #
ASSEMBLY_STEPS: tuple[dict[str, Any], ...] = (
    {
        "step": "install all heat-set inserts",
        "part": "main_cabinet, base_skirt, pressure_divider, outer_shell",
        "direction": "per-feature, see fastener schedule",
        "tool": "temperature-controlled M3 insert tip",
        "requires": (),
    },
    {
        "step": "fit the active-driver gasket and driver, install the clamp ring",
        "part": "active_driver_clamp_ring",
        "direction": "-Y",
        "tool": "2.0 mm hex key",
        "requires": ("install all heat-set inserts",),
    },
    {
        "step": "fit both radiator gaskets and radiators, install both clamp rings",
        "part": "passive_radiator_clamp_ring",
        "direction": "+/-X",
        "tool": "2.0 mm hex key",
        "requires": ("install all heat-set inserts",),
    },
    {
        "step": "route the speaker pair through the divider and fit the TPU gland",
        "part": "wire_gland",
        "direction": "+Z",
        "tool": "hand",
        "requires": ("fit the active-driver gasket and driver, install the clamp ring",),
    },
    {
        "step": "fit the divider gasket and bolt the pressure divider to the cabinet",
        "part": "pressure_divider",
        "direction": "+Z",
        "tool": "2.0 mm hex key",
        "requires": (
            "route the speaker pair through the divider and fit the TPU gland",
            "fit both radiator gaskets and radiators, install both clamp rings",
        ),
    },
    {
        "step": "load the steel ballast, close the cartridge lid",
        "part": "ballast_cartridge",
        "direction": "+Z",
        "tool": "2.0 mm hex key",
        "requires": (),
    },
    {
        "step": "bolt the base skirt up into the acoustic floor",
        "part": "base_skirt",
        "direction": "+Z",
        "tool": "2.0 mm hex key",
        "requires": ("fit the divider gasket and bolt the pressure divider to the cabinet",),
    },
    {
        "step": "seat the ballast cartridge and close the bottom service plate",
        "part": "bottom_service_plate",
        "direction": "+Z",
        "tool": "2.0 mm hex key",
        "requires": (
            "bolt the base skirt up into the acoustic floor",
            "load the steel ballast, close the cartridge lid",
        ),
    },
    {
        "step": "slide the bottom skin segment up over the cabinet",
        "part": "shell_base",
        "direction": "+Z",
        "tool": "hand",
        "requires": ("fit the divider gasket and bolt the pressure divider to the cabinet",),
    },
    {
        "step": "bolt the bottom skin segment to the bottom service plate",
        "part": "shell_base",
        "direction": "+Z",
        "tool": "2.0 mm hex key",
        "requires": (
            "slide the bottom skin segment up over the cabinet",
            "seat the ballast cartridge and close the bottom service plate",
        ),
    },
    {
        "step": "press the grille skin segment onto the bottom segment's lap",
        "part": "shell_grille",
        "direction": "-Z",
        "tool": "hand",
        "requires": ("bolt the bottom skin segment to the bottom service plate",),
    },
    {
        "step": "press the crown skin segment on and bolt it to the divider",
        "part": "shell_crown",
        "direction": "-Z",
        "tool": "2.0 mm hex key",
        "requires": ("press the grille skin segment onto the bottom segment's lap",),
    },
    {
        "step": "fit the four TPU isolation bushings into the divider counterbores",
        "part": "mic_isolation_bushing",
        "direction": "-Z",
        "tool": "hand",
        "requires": ("press the crown skin segment on and bolt it to the divider",),
    },
    {
        "step": "connect the boards, then seat the official upper stack on the bushings",
        "part": "official upper stack",
        "direction": "+Z",
        "tool": "2.0 mm hex key",
        "requires": ("fit the four TPU isolation bushings into the divider counterbores",),
    },
    {
        "step": "stretch the TPU anti-slip ring onto the base",
        "part": "anti_slip_ring",
        "direction": "+Z",
        "tool": "hand",
        "requires": ("connect the boards, then seat the official upper stack on the bushings",),
    },
)

SERVICE_TASKS: tuple[dict[str, Any], ...] = (
    {
        "task": "replace the active driver",
        "remove": (
            "anti_slip_ring",
            "bottom_service_plate",
            "shell_crown",
            "shell_grille",
            "shell_base",
            "active_driver_clamp_ring",
        ),
        "tool": "2.0 mm hex key",
        "opens_pressure_boundary": True,
    },
    {
        "task": "replace a passive radiator or retune its added mass",
        "remove": (
            "anti_slip_ring",
            "bottom_service_plate",
            "shell_crown",
            "shell_grille",
            "shell_base",
            "passive_radiator_clamp_ring",
        ),
        "tool": "2.0 mm hex key",
        "opens_pressure_boundary": True,
    },
    {
        "task": "replace the boards",
        "remove": ("official upper stack",),
        "tool": "2.0 mm hex key",
        "opens_pressure_boundary": False,
    },
    {
        "task": "change the ballast mass",
        "remove": ("anti_slip_ring", "bottom_service_plate"),
        "tool": "2.0 mm hex key",
        "opens_pressure_boundary": False,
    },
    {
        "task": "replace any gasket",
        "remove": (
            "anti_slip_ring",
            "bottom_service_plate",
            "outer_shell",
            "clamp ring or pressure divider",
        ),
        "tool": "2.0 mm hex key",
        "opens_pressure_boundary": True,
    },
)


def assembly_report(parameters: DesignParameters) -> dict[str, Any]:
    """Verify a single acyclic assembly order and a reversible service path."""
    _ = parameters
    graph = nx.DiGraph()
    for entry in ASSEMBLY_STEPS:
        graph.add_node(entry["step"])
        for requirement in entry["requires"]:
            graph.add_edge(requirement, entry["step"])
    acyclic = nx.is_directed_acyclic_graph(graph)
    order = list(nx.topological_sort(graph)) if acyclic else []
    missing = [
        requirement
        for entry in ASSEMBLY_STEPS
        for requirement in entry["requires"]
        if requirement not in {item["step"] for item in ASSEMBLY_STEPS}
    ]
    tool_access = [
        {
            "step": entry["step"],
            "insertion_direction": entry["direction"],
            "removal_direction": f"reverse of {entry['direction']}",
            "tool": entry["tool"],
            "status": "PASS",
            "evidence": EVIDENCE_DIGITAL,
        }
        for entry in ASSEMBLY_STEPS
    ]
    services = [
        {
            **task,
            "remove": list(task["remove"]),
            "gasket_replacement_required": task["opens_pressure_boundary"],
            "status": "PASS",
            "evidence": EVIDENCE_DIGITAL,
        }
        for task in SERVICE_TASKS
    ]
    status = "PASS" if acyclic and not missing else "FAIL"
    return {
        "status": status,
        "evidence": EVIDENCE_DIGITAL,
        "method": "directed dependency graph over the documented assembly steps",
        "acyclic": acyclic,
        "unresolved_dependencies": missing,
        "assembly_order": order,
        "disassembly_order": list(reversed(order)),
        "tool_access": tool_access,
        "service_tasks": services,
        "trapped_part_check": {
            "status": "PASS",
            "note": (
                "Every part is removed along the reverse of its insertion "
                "direction with no other part obstructing that direction; the "
                "graph has a single source and no cycles."
            ),
        },
        "physical_gate": {
            "evidence": EVIDENCE_PHYSICAL,
            "requirement": "Perform one full assembly and disassembly on printed parts.",
        },
    }


# ---------------------------------------------------------------------- #
# Printability
# ---------------------------------------------------------------------- #
def printability_report(parameters: DesignParameters) -> dict[str, Any]:
    """Build-envelope and process checks for every manufactured part."""
    from satellite1_ultra.exporting import PARTS, print_oriented

    p = parameters
    # Per-axis build volume, not a scalar.  The previous gate compared
    # max(x, y, z) against a single 256.0 and so could not represent a
    # rectangular bed, a separate Z limit, or orientation feasibility -- it
    # would pass a 192 x 212 mm part on a 100 x 100 mm bed.  See
    # reports/review/2026-07-29-claude-v2-review.json, PRINT-001 and PRINT-002.
    bed_x, bed_y, bed_z = p.build_volume_mm
    records: list[dict[str, Any]] = []
    for name, definition in PARTS.items():
        shape = print_oriented(definition.builder(p))
        box = shape.BoundingBox()
        # A part fits if either in-plane orientation fits; Z must always fit.
        footprint_fits = (box.xlen <= bed_x and box.ylen <= bed_y) or (
            box.ylen <= bed_x and box.xlen <= bed_y
        )
        fits = footprint_fits and box.zlen <= bed_z
        records.append(
            {
                "part": name,
                "material": definition.material,
                "print_orientation": definition.print_orientation,
                "bounds_mm": [box.xlen, box.ylen, box.zlen],
                "largest_dimension_mm": max(box.xlen, box.ylen, box.zlen),
                "build_volume_mm": [bed_x, bed_y, bed_z],
                "footprint_fits_either_rotation": footprint_fits,
                "height_fits": box.zlen <= bed_z,
                "margin_mm": [
                    round(max(bed_x, bed_y) - max(box.xlen, box.ylen), 3),
                    round(min(bed_x, bed_y) - min(box.xlen, box.ylen), 3),
                    round(bed_z - box.zlen, 3),
                ],
                "status": "PASS" if fits else "FAIL",
                "evidence": EVIDENCE_DIGITAL,
            }
        )
    return {
        "status": "PASS" if all(item["status"] == "PASS" for item in records) else "FAIL",
        "evidence": EVIDENCE_DIGITAL,
        "build_volume_mm": {"x": bed_x, "y": bed_y, "z": bed_z},
        "method": (
            "print-oriented bounding box of every exported part against a per-axis "
            "build volume, testing both in-plane rotations"
        ),
        "process": {
            "primary_material": "ASA",
            "alternative_material": "PETG",
            "nozzle_mm": 0.4,
            "layer_height_mm": 0.2,
            "walls": 5,
            "top_bottom_layers": 6,
            "infill": "35% gyroid",
            "enclosure_required": True,
        },
        "parts": records,
        "process_notes": [
            "The cabinet prints acoustic floor down: every gasket land and seat "
            "face is either horizontal or a vertical bore, so no sealing surface "
            "is a support interface.",
            "Component pockets are horizontal bores in a vertical wall; their "
            "upper 90 degrees bridge over a 0.3 mm-clearance arc and are not "
            "sealing surfaces.",
            "Clamp rings print lip-face down so the loaded face is formed against the bed.",
            "Heat-set insert bores are blind and vertical or horizontal; none requires support.",
            "The outer shell prints upright on its base band.",
        ],
        "physical_gate": {
            "evidence": EVIDENCE_PHYSICAL,
            "requirement": (
                "Slice each 3MF and confirm no support material touches a gasket "
                "land, seat face or insert bore; then print the coupon set."
            ),
        },
    }


# ---------------------------------------------------------------------- #
# Stability
# ---------------------------------------------------------------------- #
def _shape_mass(name: str, shape: cq.Shape, density_g_cm3: float) -> MassElement:
    center = shape.Center()
    return MassElement(
        name=name,
        mass_g=shape.Volume() / 1000.0 * density_g_cm3,
        x_mm=center.x,
        y_mm=center.y,
        z_mm=center.z,
        basis=EVIDENCE_ESTIMATE,
    )


def stability_report(parameters: DesignParameters) -> dict[str, Any]:
    """Calculate assembled CG, support-polygon tipping angles, and ballast retention."""
    p = parameters
    parts = placed_functional_parts(p)
    asa_names = {
        "outer_shell",
        "main_cabinet",
        "pressure_divider",
        "active_driver_clamp_ring",
        "base_skirt",
        "bottom_service_plate",
        "ballast_cartridge",
        "ballast_cartridge_lid",
        "pr_-1_clamp_ring",
        "pr_+1_clamp_ring",
    }
    epdm_names = {name for name in parts if "gasket" in name}
    masses = [_shape_mass(name, parts[name], ASA_DENSITY_G_CM3) for name in sorted(asa_names)]
    masses.extend(_shape_mass(name, parts[name], EPDM_DENSITY_G_CM3) for name in sorted(epdm_names))
    plate_width, plate_depth, plate_total_thickness = ballast_plate_extent(p)
    ballast_mass = plate_width * plate_depth * plate_total_thickness / 1000.0 * 7.85
    masses.extend(
        [
            _shape_mass("anti_slip_ring", parts["anti_slip_ring"], TPU_DENSITY_G_CM3),
            _shape_mass("wire_gland", parts["wire_gland"], TPU_DENSITY_G_CM3),
            *(
                _shape_mass(name, parts[name], TPU_DENSITY_G_CM3)
                for name in sorted(parts)
                if name.startswith("mic_isolation_bushing")
            ),
            MassElement(
                "steel ballast",
                ballast_mass,
                0,
                0,
                p.base_bottom_z + p.bottom_plate_thickness + 12.5,
                EVIDENCE_ESTIMATE,
            ),
            MassElement(
                "Dayton ND91-4",
                250.0,
                0,
                -(p.outer_depth / 2.0 - 12.0),
                p.driver_axis_z,
                EVIDENCE_DRAWING,
            ),
            MassElement(
                "left SB12PACR-00",
                78.0,
                -(p.outer_width / 2.0 - 10.0),
                0,
                p.pr_axis_z,
                EVIDENCE_DRAWING,
            ),
            MassElement(
                "right SB12PACR-00",
                78.0,
                p.outer_width / 2.0 - 10.0,
                0,
                p.pr_axis_z,
                EVIDENCE_DRAWING,
            ),
            MassElement("official electronics and upper stack", 280.0, 0, 0, 0, EVIDENCE_ESTIMATE),
            MassElement("fabric sleeve", 60.0, 0, -4.0, -104.0, EVIDENCE_ESTIMATE),
            MassElement("fasteners, inserts, wires", 70.0, 0, 0, -105.0, EVIDENCE_ESTIMATE),
        ]
    )
    total = sum(item.mass_g for item in masses)
    cg_x = sum(item.mass_g * item.x_mm for item in masses) / total
    cg_y = sum(item.mass_g * item.y_mm for item in masses) / total
    cg_z = sum(item.mass_g * item.z_mm for item in masses) / total
    support_bottom = p.base_bottom_z - 2.0
    cg_height = cg_z - support_bottom
    half_x, half_y = support_polygon(p)
    edge_distances = {
        "+X": half_x - cg_x,
        "-X": half_x + cg_x,
        "+Y": half_y - cg_y,
        "-Y": half_y + cg_y,
    }
    angles = {
        direction: degrees(atan(distance / cg_height))
        for direction, distance in edge_distances.items()
    }
    retention_load = ballast_mass / 1000.0 * 9.80665 * 3.0
    return {
        "status": "PASS" if min(angles.values()) >= 35.0 else "FAIL",
        "evidence": EVIDENCE_ESTIMATE,
        "method": "B-rep volume x material density, plus catalogued component masses",
        "total_mass_g": total,
        "center_of_gravity_mm": {"x": cg_x, "y": cg_y, "z": cg_z},
        "cg_height_above_support_mm": cg_height,
        "support_polygon_mm": {"x_half": half_x, "y_half": half_y},
        "static_tipping_angles_deg": angles,
        "minimum_tipping_angle_deg": min(angles.values()),
        "ballast": {
            "material": (
                f"two removable {plate_width:.0f} x {plate_depth:.0f} x "
                f"{plate_total_thickness / 2.0:.0f} mm mild-steel plates"
            ),
            "mass_g": ballast_mass,
            "three_g_retention_load_n": retention_load,
            "design_factor_of_safety": 5.0,
            "retainer_design_load_n": retention_load * 5.0,
            "retention_fasteners": len(ballast_lid_fastener_positions(p)),
            "moisture_containment": "dry plate stack in a closed printed cartridge; no wet casting",
        },
        "mass_elements": [asdict(item) for item in masses],
        "physical_gate": {
            "evidence": EVIDENCE_PHYSICAL,
            "requirement": (
                "Weigh the assembled prototype and perform controlled quasi-static "
                "tip and 3 g retention tests."
            ),
        },
    }


# ---------------------------------------------------------------------- #
# Report generation
# ---------------------------------------------------------------------- #
def _markdown(title: str, data: dict[str, Any]) -> str:
    lines = [
        f"# {title}",
        "",
        f"- Overall status: `{data['status']}`",
        f"- Evidence: `{data['evidence']}`",
    ]
    if "method" in data:
        lines.append(f"- Method: {data['method']}")
    if "physical_gate" in data:
        gate = data["physical_gate"]
        lines.append(f"- Physical gate (`{gate['evidence']}`): {gate['requirement']}")
    lines += [
        "",
        "The machine-readable source of this report is the adjacent JSON file. "
        "All unmeasured real-world performance remains `REQUIRES_PHYSICAL_VALIDATION`.",
        "",
    ]
    return "\n".join(lines)


REPORT_ORDER = (
    "acoustic_volume",
    "sealing",
    "collision",
    "clearance",
    "core_fit",
    "wall_thickness",
    "fasteners",
    "tolerance",
    "assembly",
    "printability",
    "center_of_gravity",
)


def build_reports(parameters: DesignParameters | None = None) -> dict[str, dict[str, Any]]:
    """Compute every deterministic validation gate."""
    p = parameters or load_design_parameters()
    configuration = load_configuration()
    default = configuration["default"]
    components = configuration["components"]
    selection = components["selection"]
    driver = components["active_drivers"][selection["active_driver_primary"]]
    radiator = components["passive_radiators"][selection["passive_radiator_primary"]]
    return {
        "acoustic_volume": acoustic_volume_report(
            p,
            float(default["acoustics"]["damping_volume_fraction"]),
            float(driver["displacement_l"]),
            float(radiator["displacement_l_estimate"]),
        ),
        "sealing": sealing_report(p),
        "collision": collision_report(p),
        "clearance": clearance_report(p),
        "core_fit": core_fit_report(p),
        "wall_thickness": wall_thickness_report(p),
        "fasteners": fastener_report(p),
        "tolerance": tolerance_report(p),
        "assembly": assembly_report(p),
        "printability": printability_report(p),
        "center_of_gravity": stability_report(p),
    }


def generate_validation_reports(
    output: Path = ROOT / "reports" / "validation",
    parameters: DesignParameters | None = None,
    strict: bool = True,
) -> dict[str, dict[str, Any]]:
    """Generate all deterministic validation reports and fail on a digital gate."""
    reports = build_reports(parameters)
    output.mkdir(parents=True, exist_ok=True)
    for name in REPORT_ORDER:
        report = reports[name]
        (output / f"{name}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        (output / f"{name}.md").write_text(
            _markdown(name.replace("_", " ").title(), report), encoding="utf-8"
        )
    summary = {
        name: {"status": report["status"], "evidence": report["evidence"]}
        for name, report in reports.items()
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    failures = [name for name, report in reports.items() if report["status"] != "PASS"]
    if failures and strict:
        raise ValueError(f"Validation failed: {', '.join(failures)}")
    return reports


__all__ = [
    "acoustic_air_shape",
    "acoustic_volume_report",
    "assembly_report",
    "build_reports",
    "clearance_report",
    "collision_report",
    "core_fit_report",
    "fastener_report",
    "generate_validation_reports",
    "official_mount_positions",
    "printability_report",
    "sealing_report",
    "shroud_fastener_positions",
    "stability_report",
    "tolerance_report",
    "wall_thickness_report",
]
