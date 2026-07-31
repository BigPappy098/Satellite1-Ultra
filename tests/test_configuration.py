"""Single-source configuration and compensation tests."""

from __future__ import annotations

from dataclasses import fields

import pytest

from satellite1_ultra.configuration import (
    CALIBRATION_LIMITS,
    load_design_parameters,
    selected_components,
    validate_physical_calibration,
)
from satellite1_ultra.geometry import DEFAULT_PARAMETERS


def test_checked_in_configuration_matches_authoritative_defaults() -> None:
    loaded = load_design_parameters()
    for field in fields(DEFAULT_PARAMETERS):
        expected = getattr(DEFAULT_PARAMETERS, field.name)
        actual = getattr(loaded, field.name)
        if isinstance(expected, float):
            assert actual == pytest.approx(expected), field.name
        else:
            assert actual == expected, field.name


def test_selected_components_drive_mechanical_interfaces() -> None:
    """The selected component records must reach the mechanical parameters.

    Read the expected cutouts from the selected components rather than pinning
    literals: this test is about the record reaching the parameter, and hard
    numbers here only encode which part was selected the day it was written.
    A component swap then leaves a stale literal that fails for the wrong
    reason.  Pinning the selection is
    test_checked_in_configuration_matches_authoritative_defaults' job.
    """
    active, passive = selected_components()
    loaded = load_design_parameters()
    assert loaded.driver_cutout_diameter == pytest.approx(active["cutout_diameter_mm"])
    assert loaded.pr_cutout_diameter == pytest.approx(passive["cutout_diameter_mm"])
    assert loaded.board_revision == "public_batch_1"


def test_insert_bore_is_smaller_than_the_insert_it_receives() -> None:
    """A bore drawn at the insert's outside diameter has no interference."""
    p = load_design_parameters()
    assert p.insert_bore_diameter < p.insert_outer_diameter
    assert p.insert_bore_depth > p.insert_depth


def test_calibration_limits_accept_nominal_values_and_reject_absurd_inputs() -> None:
    nominal = {key: 0.0 for key in CALIBRATION_LIMITS}
    nominal |= {
        "gasket_sheet_thickness_mm": 2.0,
        "active_driver_flange_thickness_mm": 3.0,
        "passive_radiator_flange_thickness_mm": 4.0,
    }
    validate_physical_calibration(nominal)
    nominal["xy_scale_correction_fraction"] = 0.5
    with pytest.raises(ValueError, match="outside the safe range"):
        validate_physical_calibration(nominal)
