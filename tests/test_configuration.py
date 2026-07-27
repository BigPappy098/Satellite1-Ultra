"""Single-source configuration and compensation tests."""

from __future__ import annotations

from dataclasses import fields

import pytest

from satellite1_ultra.configuration import load_design_parameters
from satellite1_ultra.geometry import DEFAULT_PARAMETERS


def test_checked_in_configuration_matches_authoritative_defaults() -> None:
    loaded = load_design_parameters()
    for field in fields(DEFAULT_PARAMETERS):
        expected = getattr(DEFAULT_PARAMETERS, field.name)
        actual = getattr(loaded, field.name)
        if isinstance(expected, float):
            assert actual == pytest.approx(expected)
        else:
            assert actual == expected


def test_selected_components_drive_mechanical_interfaces() -> None:
    loaded = load_design_parameters()
    assert loaded.driver_cutout_diameter == pytest.approx(88.5)
    assert loaded.driver_bolt_circle == pytest.approx(93.3)
    assert loaded.pr_cutout_diameter == pytest.approx(102.0)
    assert loaded.pr_bolt_circle == pytest.approx(111.5)
    assert loaded.board_revision == "public_batch_1"
