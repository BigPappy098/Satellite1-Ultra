"""Lumped acoustic-model tests."""

from __future__ import annotations

import numpy as np
import pytest

from satellite1_ultra.acoustics import (
    Driver,
    PassiveRadiator,
    System,
    required_pr_moving_mass,
    sealed_response,
    simulate,
)
from satellite1_ultra.analysis import _f3, build_model, optimal_tuning_hz


@pytest.fixture
def driver() -> Driver:
    return Driver(
        re_ohm=4.3,
        le_h=0.00083,
        mms_kg=0.0048,
        cms_m_per_n=0.00096,
        rms_kg_per_s=0.53,
        bl_tm=4.59,
        sd_m2=0.00304,
        xmax_m=0.0046,
        thermal_power_w=30.0,
    )


@pytest.fixture
def radiator() -> PassiveRadiator:
    return PassiveRadiator(
        count=2,
        mms_kg=0.0202,
        cms_m_per_n=0.00121,
        rms_kg_per_s=0.32,
        sd_m2=0.005,
        design_excursion_m=0.0072,
    )


@pytest.fixture
def system() -> System:
    return System(
        volume_m3=0.00345,
        leak_q=7.0,
        target_tuning_hz=60.0,
        amplifier_voltage_rms=10.0,
        amplifier_peak_current_a=6.0,
    )


def test_required_pr_mass_matches_the_closed_form(radiator: PassiveRadiator) -> None:
    mass = required_pr_moving_mass(radiator, 0.00345, 60.0)
    stiffness = 1.0 / radiator.cms_m_per_n + (
        radiator.count * 1.204 * 343.0**2 * radiator.sd_m2**2 / 0.00345
    )
    assert mass == pytest.approx(stiffness / (2.0 * np.pi * 60.0) ** 2, rel=1e-9)


def test_coupled_response_is_finite_and_amplifier_safe(
    driver: Driver, radiator: PassiveRadiator, system: System
) -> None:
    frequency = np.geomspace(20.0, 20000.0, 500)
    response = simulate(driver, radiator, system, frequency)
    assert np.all(np.isfinite(response.spl_db))
    assert np.all(np.isfinite(response.maximum_spl_db))
    assert np.min(np.abs(response.impedance_ohm)) > 3.2
    assert set(response.limiting_factor) <= {
        "amplifier_voltage",
        "amplifier_current",
        "driver_thermal",
        "driver_xmax",
        "pr_xmax",
    }


def test_passive_radiator_materially_extends_bass(
    driver: Driver, radiator: PassiveRadiator, system: System
) -> None:
    frequency = np.geomspace(20.0, 20000.0, 800)
    passive = simulate(driver, radiator, system, frequency).spl_db
    sealed = sealed_response(driver, system, frequency)
    assert _f3(frequency, passive) < _f3(frequency, sealed) - 40.0


@pytest.mark.requires_official_assets
def test_configured_tuning_matches_the_optimiser() -> None:
    model = build_model()
    alignment = optimal_tuning_hz(model)
    assert abs(alignment["optimal_tuning_hz"] - model.tuning_hz) <= 3.0
    assert alignment["optimal_added_mass_each_g"] > 0.0
