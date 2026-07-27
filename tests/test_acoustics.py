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
        mms_kg=0.03934,
        cms_m_per_n=0.00121,
        rms_kg_per_s=0.32,
        sd_m2=0.005,
        design_excursion_m=0.0072,
    )


@pytest.fixture
def system() -> System:
    return System(
        volume_m3=0.0021,
        leak_q=7.0,
        target_tuning_hz=52.0,
        amplifier_voltage_rms=10.0,
        amplifier_peak_current_a=6.0,
    )


def test_required_pr_mass(radiator: PassiveRadiator) -> None:
    mass = required_pr_moving_mass(radiator, 0.0021, 52.0)
    assert mass == pytest.approx(0.03934, rel=0.002)
    assert mass - 0.0192 == pytest.approx(0.02014, rel=0.003)


def test_coupled_response_is_finite(
    driver: Driver, radiator: PassiveRadiator, system: System
) -> None:
    frequency = np.geomspace(20.0, 20000.0, 500)
    response = simulate(driver, radiator, system, frequency)
    assert np.all(np.isfinite(response.spl_db))
    assert np.all(np.isfinite(response.maximum_spl_db))
    assert np.all(np.abs(response.impedance_ohm) > 0)
    assert np.min(np.abs(response.impedance_ohm)) > 3.0
    assert set(response.limiting_factor) <= {
        "amplifier_voltage",
        "amplifier_current",
        "driver_thermal",
        "driver_xmax",
        "pr_xmax",
    }


def test_passive_radiator_extends_low_frequency_response(
    driver: Driver, radiator: PassiveRadiator, system: System
) -> None:
    frequency = np.array([45.0, 52.0, 60.0, 100.0])
    passive = simulate(driver, radiator, system, frequency).spl_db
    sealed = sealed_response(driver, system, frequency)
    assert passive[1] > sealed[1] + 3.0
