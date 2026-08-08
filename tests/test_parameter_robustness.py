"""Representative parameter changes must regenerate or fail with a clear gate."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

import cadquery as cq
import pytest

from satellite1_ultra.configuration import load_design_parameters
from satellite1_ultra.geometry import (
    DesignParameters,
    main_cabinet,
    pressure_divider,
    validate_design_parameters,
)
from satellite1_ultra.validation import clearance_report, sealing_report, wall_thickness_report

_NOMINAL = load_design_parameters()


@pytest.mark.parametrize(
    ("changes", "builder"),
    [
        ({"wall_thickness": 4.8}, main_cabinet),
        ({"outer_width": 166.0, "outer_depth": 186.0}, main_cabinet),
        ({"acoustic_bottom_z": -200.0}, main_cabinet),
        ({"divider_thickness": 5.0}, pressure_divider),
        ({"gasket_thickness": 2.2, "gasket_compression_fraction": 0.25}, main_cabinet),
        ({"print_clearance": 0.4}, main_cabinet),
        ({"insert_bore_diameter": 4.1}, main_cabinet),
        # Relative to the selected components. These were absolute figures
        # near the old 88.5 driver cutout; when that turned out to be a frame
        # dimension and the real cutout is 76.45, the variation asked for a
        # bore wider than the flange and the design validator rightly refused
        # to build it.
        ({"driver_cutout_diameter": _NOMINAL.driver_cutout_diameter + 0.5}, main_cabinet),
        ({"pr_cutout_diameter": _NOMINAL.pr_cutout_diameter + 0.5}, main_cabinet),
        ({"ballast_mass_g": 1000.0}, main_cabinet),
    ],
)
def test_supported_parameter_variations_build(
    changes: dict[str, float], builder: Callable[[DesignParameters], cq.Shape]
) -> None:
    parameters = replace(load_design_parameters(), **changes)
    validate_design_parameters(parameters)
    shape = builder(parameters)
    assert shape.isValid()
    assert len(shape.Solids()) == 1
    assert shape.Volume() > 0.0


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"wall_thickness": 2.0}, "wall_thickness"),
        ({"outer_width": 250.0}, "outer_width"),
        ({"gasket_compression_fraction": 0.60}, "gasket_compression"),
        ({"insert_bore_diameter": 4.8}, "insert bore"),
        ({"driver_cutout_diameter": 110.0}, "active-driver bore"),
        ({"pr_cutout_diameter": 126.0}, "passive-radiator bore"),
    ],
)
def test_impossible_parameter_variations_fail_early(
    changes: dict[str, float], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_design_parameters(replace(load_design_parameters(), **changes))


def test_nominal_geometry_gates_still_pass() -> None:
    parameters = load_design_parameters()
    assert wall_thickness_report(parameters)["status"] == "PASS"
    assert sealing_report(parameters)["status"] == "PASS"
    assert clearance_report(parameters)["status"] == "PASS"
