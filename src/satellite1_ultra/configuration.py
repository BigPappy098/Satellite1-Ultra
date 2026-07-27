"""Load the single design configuration and physical coupon compensation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]

from satellite1_ultra.geometry import DesignParameters

ROOT = Path(__file__).resolve().parents[2]


def _yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        return cast(dict[str, Any], yaml.safe_load(source))


def load_design_parameters(root: Path = ROOT) -> DesignParameters:
    """Resolve enclosure, component, and measured-compensation values."""
    default = _yaml(root / "config" / "default.yaml")
    components = _yaml(root / "config" / "components.yaml")
    correction = _yaml(root / "config" / "physical_compensation.yaml")
    enclosure = default["enclosure"]
    sealing = default["sealing"]
    fasteners = default["fasteners"]
    selection = components["selection"]
    active = components["active_drivers"][selection["active_driver_primary"]]
    passive = components["passive_radiators"][selection["passive_radiator_primary"]]

    xy = 1.0 + float(correction["xy_scale_correction_fraction"])
    z = 1.0 + float(correction["z_scale_correction_fraction"])
    hole_offset = float(correction["hole_diameter_offset"])
    insert_offset = float(correction["insert_hole_diameter_offset"])
    cable_offset = float(correction["cable_passage_offset"])
    boss_offset = float(correction["boss_outer_diameter_offset"])

    def number(value: object) -> float:
        if not isinstance(value, int | float):
            raise TypeError(f"Expected numeric configuration value, got {value!r}")
        return float(value)

    def planar(value: object) -> float:
        return number(value) * xy

    def vertical(value: object) -> float:
        return number(value) * z

    return DesignParameters(
        outer_width=planar(enclosure["outer_width"]),
        outer_depth=planar(enclosure["outer_depth"]),
        corner_radius=planar(enclosure["corner_radius"]),
        wall_thickness=planar(enclosure["wall_thickness"]),
        acoustic_top_z=vertical(enclosure["acoustic_top_z"]),
        acoustic_bottom_z=vertical(enclosure["acoustic_bottom_z"]),
        acoustic_floor_thickness=vertical(enclosure["acoustic_floor_thickness"]),
        divider_thickness=vertical(enclosure["divider_thickness"]),
        base_bottom_z=vertical(enclosure["base_bottom_z"]),
        bottom_plate_thickness=vertical(enclosure["bottom_plate_thickness"]),
        driver_axis_z=vertical(enclosure["driver_axis_z"]),
        driver_cutout_diameter=planar(active["cutout_diameter_mm"]) + hole_offset,
        driver_outer_diameter=planar(active["outer_diameter_mm"]),
        driver_carrier_diameter=planar(active["outer_diameter_mm"] + 4.8),
        driver_bolt_circle=planar(active["bolt_circle_mm"]),
        driver_mount_hole_diameter=planar(3.4) + hole_offset,
        driver_depth=planar(active["depth_mm"]),
        pr_axis_z=vertical(enclosure["passive_radiator_axis_z"]),
        pr_cutout_diameter=planar(passive["cutout_diameter_mm"]) + hole_offset,
        pr_outer_diameter=planar(passive["outer_diameter_mm"]),
        pr_carrier_diameter=planar(passive["outer_diameter_mm"] + 6.0),
        pr_bolt_circle=planar(passive["bolt_circle_mm"]),
        pr_mount_hole_diameter=planar(3.4) + hole_offset,
        pr_depth=planar(passive["depth_mm"]),
        pr_rear_excursion=planar(passive["xmech_mm"]),
        carrier_thickness=vertical(enclosure["baffle_thickness"]),
        carrier_recess=planar(enclosure["carrier_recess"]),
        insert_outer_diameter=planar(fasteners["insert_outer_diameter"]) + insert_offset,
        insert_depth=vertical(fasteners["insert_length"]),
        boss_outer_diameter=planar(
            fasteners["insert_outer_diameter"] + 2.0 * fasteners["minimum_boss_wall"]
        )
        + boss_offset,
        gasket_thickness=vertical(sealing["gasket_thickness"]),
        gasket_land_width=planar(sealing["gasket_land_width"]),
        cable_passage_diameter=planar(8.0) + cable_offset,
        official_mount_x=planar(45.0534),
        official_mount_y=planar(31.5467),
        gasket_compression_fraction=float(sealing["target_compression_fraction"]),
        print_clearance=planar(enclosure["print_clearance"]),
        board_revision=str(default["hardware"]["board_revision"]),
        ballast_mass_g=float(default["ballast"]["target_mass_g"]),
    )
