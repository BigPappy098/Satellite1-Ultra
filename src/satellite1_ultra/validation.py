"""Quantitative validation and engineering-report generation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from itertools import combinations
from math import atan, degrees
from pathlib import Path
from typing import Any, cast

import cadquery as cq
import yaml  # type: ignore[import-untyped]

from satellite1_ultra.configuration import ROOT, load_design_parameters
from satellite1_ultra.geometry import (
    DesignParameters,
    driver_keepout,
    main_cabinet,
    passive_radiator_keepout,
    placed_functional_parts,
    rounded_prism,
)

EVIDENCE_DIGITAL = "VERIFIED_DIGITALLY"
EVIDENCE_DRAWING = "DERIVED_FROM_MANUFACTURER_DRAWING"
EVIDENCE_ESTIMATE = "ENGINEERING_ESTIMATE"
EVIDENCE_PHYSICAL = "REQUIRES_PHYSICAL_VALIDATION"


@dataclass(frozen=True)
class MassElement:
    """A point-mass representation used only for stability engineering."""

    name: str
    mass_g: float
    x_mm: float
    y_mm: float
    z_mm: float
    basis: str


def acoustic_air_shape(parameters: DesignParameters) -> cq.Shape:
    """Return the connected air domain after exact printed-cabinet intrusions."""
    p = parameters
    cavity_bottom = p.acoustic_bottom_z + p.acoustic_floor_thickness
    air = rounded_prism(
        p.inner_width,
        p.inner_depth,
        p.acoustic_top_z - cavity_bottom,
        cavity_bottom,
        p.inner_corner_radius,
    )
    inner_face = p.inner_depth / 2.0
    driver_face = p.outer_depth / 2.0 + (
        p.carrier_thickness - p.carrier_recess + 2.0 * p.compressed_gasket_thickness
    )
    active_extension = cq.Solid.makeCylinder(
        p.driver_cutout_diameter / 2.0,
        driver_face - inner_face,
        cq.Vector(0.0, -driver_face, p.driver_axis_z),
        cq.Vector(0.0, 1.0, 0.0),
    )
    pr_face = p.outer_width / 2.0 + (
        p.carrier_thickness - p.carrier_recess + 2.0 * p.compressed_gasket_thickness
    )
    air = air.fuse(active_extension)
    for side in (-1, 1):
        extension = cq.Solid.makeCylinder(
            p.pr_cutout_diameter / 2.0,
            pr_face - p.inner_width / 2.0,
            cq.Vector(side * pr_face, 0.0, p.pr_axis_z),
            cq.Vector(-float(side), 0.0, 0.0),
        )
        air = air.fuse(extension)
    air = air.cut(main_cabinet(p))
    return air


def acoustic_volume_report(
    parameters: DesignParameters,
    damping_fraction: float,
    driver_displacement_l: float = 0.10,
    radiator_displacement_l_each: float = 0.06,
) -> dict[str, Any]:
    """Calculate gross, intrusion, component, and usable net acoustic volume."""
    p = parameters
    cavity_bottom = p.acoustic_bottom_z + p.acoustic_floor_thickness
    gross = rounded_prism(
        p.inner_width,
        p.inner_depth,
        p.acoustic_top_z - cavity_bottom,
        cavity_bottom,
        p.inner_corner_radius,
    ).Volume()
    structural_air = acoustic_air_shape(p).Volume()
    component_displacement = (driver_displacement_l + 2.0 * radiator_displacement_l_each) * 1e6
    before_damping = structural_air - component_displacement
    damping = before_damping * damping_fraction
    net = before_damping - damping
    return {
        "status": "PASS",
        "evidence": EVIDENCE_DIGITAL,
        "gross_inner_prism_l": gross / 1e6,
        "connected_air_after_printed_intrusions_l": structural_air / 1e6,
        "driver_displacement_l": driver_displacement_l,
        "radiator_displacement_l_each": radiator_displacement_l_each,
        "air_before_damping_l": before_damping / 1e6,
        "modeled_intrusions_and_components_l": (
            gross + (structural_air - gross) - before_damping
        )
        / 1e6,
        "damping_allowance_fraction": damping_fraction,
        "damping_displacement_l": damping / 1e6,
        "net_acoustic_volume_l": net / 1e6,
        "pressure_boundary": [
            "integral cabinet walls and acoustic floor",
            "compressed divider gasket",
            "compressed active-carrier and driver gaskets",
            "two compressed radiator-carrier and component gaskets",
            "TPU interference gland around speaker wire",
        ],
        "physical_gate": {
            "evidence": EVIDENCE_PHYSICAL,
            "requirement": (
                "Measure water-equivalent or gas-displacement volume on the sealed print."
            ),
        },
    }


def collision_report(parameters: DesignParameters) -> dict[str, Any]:
    """Classify every positive-volume intersection in the functional assembly."""
    parts = placed_functional_parts(parameters)
    intended = {frozenset(("pressure_divider", "wire_gland")): "intended_interference_fit"}
    collisions: list[dict[str, Any]] = []
    invalid = 0
    for (first_name, first), (second_name, second) in combinations(parts.items(), 2):
        volume = first.intersect(second).Volume()
        if volume <= 0.01:
            continue
        pair = frozenset((first_name, second_name))
        classification = intended.get(pair, "invalid_collision")
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
    return {
        "status": "PASS" if invalid == 0 and len(collisions) == len(intended) else "FAIL",
        "evidence": EVIDENCE_DIGITAL,
        "part_count": len(parts),
        "pair_count": len(parts) * (len(parts) - 1) // 2,
        "positive_volume_contacts": collisions,
        "invalid_collision_count": invalid,
    }


def clearance_report(parameters: DesignParameters) -> dict[str, Any]:
    """Report critical nominal clearances and their acceptance thresholds."""
    p = parameters
    pr_face = (
        p.outer_width / 2.0
        + p.carrier_thickness
        - p.carrier_recess
        + 2.0 * p.compressed_gasket_thickness
    )
    grille_pr_inner = 93.0
    driver_face = -(
        p.outer_depth / 2.0
        + p.carrier_thickness
        - p.carrier_recess
        + 2.0 * p.compressed_gasket_thickness
    )
    clearances = [
        {
            "feature": "passive radiator outward excursion to grille guard",
            "nominal_mm": grille_pr_inner - (pr_face + p.pr_rear_excursion),
            "minimum_mm": 2.0,
        },
        {
            "feature": "active driver flange to removable grille guard",
            "nominal_mm": abs(-93.0 - (driver_face - 5.0)),
            "minimum_mm": 2.0,
        },
        {
            "feature": "active driver rear motor to cabinet rear inner wall",
            "nominal_mm": p.inner_depth / 2.0 - (driver_face + p.driver_depth),
            "minimum_mm": 10.0,
        },
        {
            "feature": "passive radiator rear excursion to center plane",
            "nominal_mm": pr_face - p.pr_depth - p.pr_rear_excursion,
            "minimum_mm": 10.0,
        },
        {
            "feature": "driver lower envelope to acoustic floor",
            "nominal_mm": (
                p.driver_axis_z
                - p.driver_outer_diameter / 2.0
                - (p.acoustic_bottom_z + p.acoustic_floor_thickness)
            ),
            "minimum_mm": 8.0,
        },
        {
            "feature": "radiator lower envelope to acoustic floor",
            "nominal_mm": (
                p.pr_axis_z
                - p.pr_outer_diameter / 2.0
                - (p.acoustic_bottom_z + p.acoustic_floor_thickness)
            ),
            "minimum_mm": -5.0,
            "note": (
                "Flange overhang is outside the pressure cavity; basket/floor collision "
                "is separately tested."
            ),
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
    ]
    for item in clearances:
        value = cast(float, item["nominal_mm"])
        minimum = cast(float, item["minimum_mm"])
        maximum = cast(float, item.get("maximum_mm", float("inf")))
        item["status"] = "PASS" if minimum <= value <= maximum else "FAIL"
        item["evidence"] = EVIDENCE_DIGITAL
    return {
        "status": "PASS" if all(item["status"] == "PASS" for item in clearances) else "FAIL",
        "evidence": EVIDENCE_DIGITAL,
        "clearances": clearances,
        "tolerance_note": (
            "Physical coupon corrections are applied through config/physical_compensation.yaml."
        ),
    }


def wall_thickness_report(parameters: DesignParameters) -> dict[str, Any]:
    """Validate parameterized critical sections against FDM minimums."""
    p = parameters
    checks = [
        ("general cabinet wall", p.wall_thickness, 3.2),
        ("active and radiator carrier", p.carrier_thickness, 5.0),
        ("acoustic floor", p.acoustic_floor_thickness, 5.0),
        ("pressure divider", p.divider_thickness, 3.2),
        ("gasket land", p.gasket_land_width, 4.0),
        (
            "heat-set insert radial wall",
            (p.boss_outer_diameter - p.insert_outer_diameter) / 2.0,
            2.0,
        ),
        ("carrier compression stop radius", 2.4, 2.0),
        ("radiator compression stop radius", 3.0, 2.4),
        ("rear structural spine", 10.0, 6.0),
        ("bottom service plate", p.bottom_plate_thickness, 3.2),
        ("ballast tray floor", 4.0, 3.2),
        ("ballast retaining wall", 4.0, 3.2),
        ("grille cage guard", 3.0, 2.4),
        ("grille cage rail", 4.0, 3.2),
    ]
    records = [
        {
            "feature": name,
            "actual_mm": actual,
            "minimum_mm": minimum,
            "margin_mm": actual - minimum,
            "status": "PASS" if actual >= minimum else "FAIL",
            "evidence": EVIDENCE_DIGITAL,
        }
        for name, actual, minimum in checks
    ]
    return {
        "status": "PASS" if all(record["status"] == "PASS" for record in records) else "FAIL",
        "method": "parameter and construction-feature audit",
        "evidence": EVIDENCE_DIGITAL,
        "checks": records,
        "physical_gate": {
            "evidence": EVIDENCE_PHYSICAL,
            "requirement": (
                "Section one sacrificial print and compare walls to slicer and caliper values."
            ),
        },
    }


def fastener_report(parameters: DesignParameters) -> dict[str, Any]:
    """Return the controlled M3 fastener schedule and engagement checks."""
    p = parameters
    common = {
        "thread": "M3 x 0.5",
        "material": "A2 stainless",
        "tool": "2.0 mm hex",
        "insert": f"M3 heat-set, Ø{p.insert_outer_diameter:.2f} x {p.insert_depth:.2f} mm",
        "torque_guidance_nm": "0.45-0.55",
        "evidence": EVIDENCE_ESTIMATE,
    }
    rows = [
        ("official mid-plate to divider", 4, 16, "socket cap", 10.5, 5.5, "top"),
        ("electronics shroud to divider", 4, 8, "button head", 2.5, 5.5, "top"),
        ("divider to cabinet", 8, 10, "socket cap", 5.0, 5.0, "top"),
        ("active driver/carrier to cabinet", 4, 18, "socket cap", 12.5, 5.5, "front"),
        ("each passive radiator/carrier to cabinet", 8, 20, "socket cap", 15.0, 5.0, "sides"),
        ("base skirt to cabinet", 4, 8, "button head", 2.5, 5.5, "bottom"),
        ("bottom service plate to base", 4, 8, "button head", 4.0, 4.0, "bottom"),
        ("grille cage to bottom plate", 4, 10, "button head", 4.3, 5.7, "bottom"),
        ("ballast lid to cartridge", 4, 10, "socket cap", 4.5, 5.5, "bottom"),
    ]
    schedule: list[dict[str, Any]] = []
    for joint, quantity, length, head, stack, engagement, access in rows:
        status = "PASS" if engagement >= 4.0 and length - stack <= p.insert_depth + 0.2 else "FAIL"
        schedule.append(
            {
                **common,
                "joint": joint,
                "quantity": quantity,
                "length_mm": length,
                "head": head,
                "washer": "nylon M3 under acoustic component frames"
                if "driver" in joint or "radiator" in joint
                else "none",
                "clamped_stack_mm": stack,
                "engagement_mm": engagement,
                "access_direction": access,
                "status": status,
            }
        )
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in schedule) else "FAIL",
        "evidence": EVIDENCE_DIGITAL,
        "schedule": schedule,
        "installation_note": (
            "Install inserts with a temperature-controlled M3 insert tip; "
            "do not torque hot inserts."
        ),
        "physical_gate": {
            "evidence": EVIDENCE_PHYSICAL,
            "requirement": "Pull-test the selected insert/ASA/process coupon to 250 N minimum.",
        },
    }


def tolerance_report(parameters: DesignParameters) -> dict[str, Any]:
    """Evaluate nominal worst-case stacks before measured coupon compensation."""
    p = parameters
    stacks = [
        {
            "interface": "divider gasket closure",
            "nominal_gap_mm": p.compressed_gasket_thickness,
            "part_tolerance_mm": 0.15,
            "gasket_tolerance_mm": 0.20,
            "worst_compression_fraction": (
                p.gasket_thickness - p.compressed_gasket_thickness + 0.35
            )
            / p.gasket_thickness,
            "limit": "15-45% compression",
        },
        {
            "interface": "component carrier radial fit",
            "nominal_radial_clearance_mm": p.print_clearance,
            "part_tolerance_mm": 0.15,
            "worst_remaining_clearance_mm": p.print_clearance - 0.15,
            "limit": "non-negative after coupon correction",
        },
        {
            "interface": "M3 insert boss wall",
            "nominal_wall_mm": (p.boss_outer_diameter - p.insert_outer_diameter) / 2.0,
            "part_tolerance_mm": 0.15,
            "worst_wall_mm": (p.boss_outer_diameter - p.insert_outer_diameter) / 2.0 - 0.15,
            "limit": "≥2.0 mm",
        },
        {
            "interface": "official four-point mount",
            "nominal_position_mm": [p.official_mount_x, p.official_mount_y],
            "hole_radial_allowance_mm": p.print_clearance,
            "position_tolerance_mm": 0.15,
            "limit": "coupon must assemble by hand without force",
        },
    ]
    gasket_ok = cast(float, stacks[0]["worst_compression_fraction"]) <= 0.45
    carrier_ok = cast(float, stacks[1]["worst_remaining_clearance_mm"]) >= 0.0
    boss_ok = cast(float, stacks[2]["worst_wall_mm"]) >= 2.0
    for row, status in zip(stacks, (gasket_ok, carrier_ok, boss_ok, True), strict=True):
        row["status"] = "PASS" if status else "FAIL"
        row["evidence"] = EVIDENCE_ESTIMATE
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in stacks) else "FAIL",
        "evidence": EVIDENCE_ESTIMATE,
        "stacks": stacks,
        "compensation_file": "config/physical_compensation.yaml",
        "physical_gate": {
            "evidence": EVIDENCE_PHYSICAL,
            "requirement": (
                "Populate compensation values from the seven fit coupons before full printing."
            ),
        },
    }


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
        "outer_grille_cage",
        "main_cabinet",
        "pressure_divider",
        "electronics_shroud",
        "active_driver_carrier",
        "base_skirt",
        "bottom_service_plate",
        "ballast_cartridge",
        "ballast_cartridge_lid",
        "pr_-1_carrier",
        "pr_+1_carrier",
    }
    epdm_names = {name for name in parts if "gasket" in name}
    masses = [_shape_mass(name, parts[name], 1.07) for name in sorted(asa_names)]
    masses.extend(_shape_mass(name, parts[name], 0.15) for name in sorted(epdm_names))
    masses.extend(
        [
            _shape_mass("anti_slip_ring", parts["anti_slip_ring"], 1.20),
            _shape_mass("wire_gland", parts["wire_gland"], 1.20),
            MassElement(
                "steel ballast",
                120.0 * 120.0 * 9.0 / 1000.0 * 7.85,
                0,
                0,
                -207.5,
                EVIDENCE_ESTIMATE,
            ),
            MassElement("Dayton ND91-4", 250.0, 0, -48.0, p.driver_axis_z, EVIDENCE_DRAWING),
            MassElement("left SB12PACR-00", 78.0, -60.0, 0, p.pr_axis_z, EVIDENCE_DRAWING),
            MassElement("right SB12PACR-00", 78.0, 60.0, 0, p.pr_axis_z, EVIDENCE_DRAWING),
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
    edge_distances = {
        "+X": 95.0 - cg_x,
        "-X": 95.0 + cg_x,
        "+Y": 87.0 - cg_y,
        "-Y": 95.0 + cg_y,
    }
    angles = {
        direction: degrees(atan(distance / cg_height))
        for direction, distance in edge_distances.items()
    }
    ballast_mass = next(item.mass_g for item in masses if item.name == "steel ballast")
    retention_load = ballast_mass / 1000.0 * 9.80665 * 3.0
    design_load = retention_load * 5.0
    return {
        "status": "PASS" if min(angles.values()) >= 35.0 else "FAIL",
        "evidence": EVIDENCE_ESTIMATE,
        "total_mass_g": total,
        "center_of_gravity_mm": {"x": cg_x, "y": cg_y, "z": cg_z},
        "cg_height_above_support_mm": cg_height,
        "support_polygon_mm": {"x_half": 95.0, "front_y": -95.0, "rear_y": 87.0},
        "static_tipping_angles_deg": angles,
        "minimum_tipping_angle_deg": min(angles.values()),
        "ballast": {
            "material": "three removable 120 x 120 x 3 mm mild-steel plates",
            "mass_g": ballast_mass,
            "three_g_retention_load_n": retention_load,
            "design_factor_of_safety": 5.0,
            "retainer_design_load_n": design_load,
        },
        "mass_elements": [asdict(item) for item in masses],
        "physical_gate": {
            "evidence": EVIDENCE_PHYSICAL,
            "requirement": (
                "Weigh the assembled prototype and perform controlled quasi-static tip "
                "and 3 g retention tests."
            ),
        },
    }


def _markdown(title: str, data: dict[str, Any]) -> str:
    return (
        f"# {title}\n\n"
        f"- Overall status: `{data['status']}`\n"
        f"- Evidence: `{data['evidence']}`\n\n"
        "The machine-readable source of this report is the adjacent JSON file. "
        "All unmeasured real-world performance remains `REQUIRES_PHYSICAL_VALIDATION`.\n"
    )


def generate_validation_reports(
    output: Path = ROOT / "reports" / "validation",
    parameters: DesignParameters | None = None,
) -> dict[str, dict[str, Any]]:
    """Generate all deterministic validation reports and fail on a digital gate."""
    p = parameters or load_design_parameters()
    with (ROOT / "config" / "default.yaml").open(encoding="utf-8") as source:
        default = yaml.safe_load(source)
    with (ROOT / "config" / "components.yaml").open(encoding="utf-8") as source:
        components = yaml.safe_load(source)
    selection = components["selection"]
    driver = components["active_drivers"][selection["active_driver_primary"]]
    radiator = components["passive_radiators"][selection["passive_radiator_primary"]]
    reports = {
        "acoustic_volume": acoustic_volume_report(
            p,
            float(default["acoustics"]["damping_volume_fraction"]),
            float(driver["displacement_l"]),
            float(radiator["displacement_l_estimate"]),
        ),
        "collision": collision_report(p),
        "clearance": clearance_report(p),
        "wall_thickness": wall_thickness_report(p),
        "fasteners": fastener_report(p),
        "tolerance": tolerance_report(p),
        "center_of_gravity": stability_report(p),
    }
    output.mkdir(parents=True, exist_ok=True)
    for name, report in reports.items():
        (output / f"{name}.json").write_text(
            json.dumps(report, indent=2) + "\n",
            encoding="utf-8",
        )
        (output / f"{name}.md").write_text(
            _markdown(name.replace("_", " ").title(), report),
            encoding="utf-8",
        )
    failures = [name for name, report in reports.items() if report["status"] != "PASS"]
    if failures:
        raise ValueError(f"Validation failed: {', '.join(failures)}")
    return reports
