"""Reproducible lumped-parameter driver/passive-radiator acoustic model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

RHO_AIR = 1.204
SPEED_OF_SOUND = 343.0
REFERENCE_PRESSURE = 20e-6


@dataclass(frozen=True)
class Driver:
    """Electro-mechanical small-signal driver parameters in SI units."""

    re_ohm: float
    le_h: float
    mms_kg: float
    cms_m_per_n: float
    rms_kg_per_s: float
    bl_tm: float
    sd_m2: float
    xmax_m: float
    thermal_power_w: float


@dataclass(frozen=True)
class PassiveRadiator:
    """Mechanical passive-radiator parameters in SI units."""

    count: int
    mms_kg: float
    cms_m_per_n: float
    rms_kg_per_s: float
    sd_m2: float
    design_excursion_m: float


@dataclass(frozen=True)
class System:
    """Enclosure and amplifier parameters."""

    volume_m3: float
    leak_q: float
    target_tuning_hz: float
    amplifier_voltage_rms: float
    amplifier_peak_current_a: float
    distance_m: float = 1.0


@dataclass(frozen=True)
class Response:
    """Complex small-signal solution and derived engineering quantities."""

    frequency_hz: NDArray[np.float64]
    impedance_ohm: NDArray[np.complex128]
    driver_excursion_m: NDArray[np.float64]
    passive_excursion_m: NDArray[np.float64]
    spl_db: NDArray[np.float64]
    driver_electrical_power_w: NDArray[np.float64]
    maximum_spl_db: NDArray[np.float64]
    limiting_factor: NDArray[np.str_]


def required_pr_moving_mass(
    radiator: PassiveRadiator,
    volume_m3: float,
    tuning_hz: float,
) -> float:
    """Return required total moving mass for each identical opposed radiator."""
    suspension_stiffness = 1.0 / radiator.cms_m_per_n
    box_stiffness = radiator.count * RHO_AIR * SPEED_OF_SOUND**2 * radiator.sd_m2**2 / volume_m3
    return (suspension_stiffness + box_stiffness) / (2.0 * np.pi * tuning_hz) ** 2


def box_acoustic_impedance(
    frequency_hz: NDArray[np.float64],
    system: System,
) -> NDArray[np.complex128]:
    """Return compliance and leakage in parallel as acoustic impedance."""
    omega = 2.0 * np.pi * frequency_hz
    compliance = system.volume_m3 / (RHO_AIR * SPEED_OF_SOUND**2)
    leak_resistance = system.leak_q / (2.0 * np.pi * system.target_tuning_hz * compliance)
    admittance = 1j * omega * compliance + 1.0 / leak_resistance
    return np.asarray(1.0 / admittance, dtype=np.complex128)


def simulate(
    driver: Driver,
    radiator: PassiveRadiator,
    system: System,
    frequency_hz: NDArray[np.float64],
    *,
    input_voltage_rms: float = 1.0,
) -> Response:
    """Solve coupled electrical, driver, PR, enclosure-compliance equations."""
    frequency_hz = np.asarray(frequency_hz, dtype=np.float64)
    omega = 2.0 * np.pi * frequency_hz
    ze = driver.re_ohm + 1j * omega * driver.le_h
    zmd = driver.rms_kg_per_s + 1j * omega * driver.mms_kg + 1.0 / (1j * omega * driver.cms_m_per_n)
    zmpr = (
        radiator.rms_kg_per_s
        + 1j * omega * radiator.mms_kg
        + 1.0 / (1j * omega * radiator.cms_m_per_n)
    )
    zab = box_acoustic_impedance(frequency_hz, system)

    current = np.empty_like(ze)
    driver_velocity = np.empty_like(ze)
    radiator_velocity = np.empty_like(ze)
    for index in range(frequency_hz.size):
        matrix = np.array(
            [
                [ze[index], driver.bl_tm, 0.0],
                [
                    -driver.bl_tm,
                    zmd[index] + zab[index] * driver.sd_m2**2,
                    zab[index] * driver.sd_m2 * radiator.count * radiator.sd_m2,
                ],
                [
                    0.0,
                    zab[index] * radiator.sd_m2 * driver.sd_m2,
                    zmpr[index] + zab[index] * radiator.count * radiator.sd_m2**2,
                ],
            ],
            dtype=np.complex128,
        )
        solution = np.linalg.solve(
            matrix,
            np.array([input_voltage_rms, 0.0, 0.0], dtype=np.complex128),
        )
        current[index], driver_velocity[index], radiator_velocity[index] = solution

    impedance = np.asarray(input_voltage_rms / current, dtype=np.complex128)
    driver_excursion = np.abs(driver_velocity) / omega
    radiator_excursion = np.abs(radiator_velocity) / omega
    outward_volume_velocity = -(
        driver.sd_m2 * driver_velocity + radiator.count * radiator.sd_m2 * radiator_velocity
    )
    pressure = 1j * omega * RHO_AIR * outward_volume_velocity / (2.0 * np.pi * system.distance_m)
    spl = 20.0 * np.log10(np.maximum(np.abs(pressure), 1e-20) / REFERENCE_PRESSURE)
    electrical_power = np.abs(current) ** 2 * driver.re_ohm

    amplifier_scale = np.full_like(frequency_hz, system.amplifier_voltage_rms)
    current_scale = system.amplifier_peak_current_a / (
        np.sqrt(2.0) * np.maximum(np.abs(current), 1e-12)
    )
    thermal_scale = np.sqrt(driver.thermal_power_w / np.maximum(electrical_power, 1e-12))
    driver_scale = driver.xmax_m / np.maximum(driver_excursion, 1e-12)
    radiator_scale = radiator.design_excursion_m / np.maximum(radiator_excursion, 1e-12)
    scales = np.vstack(
        (amplifier_scale, current_scale, thermal_scale, driver_scale, radiator_scale)
    )
    factor_names = np.array(
        ["amplifier_voltage", "amplifier_current", "driver_thermal", "driver_xmax", "pr_xmax"]
    )
    limit_index = np.argmin(scales, axis=0)
    scale = np.maximum(np.min(scales, axis=0), 1e-12)
    maximum_spl = spl + 20.0 * np.log10(scale / input_voltage_rms)

    return Response(
        frequency_hz=frequency_hz,
        impedance_ohm=impedance,
        driver_excursion_m=driver_excursion,
        passive_excursion_m=radiator_excursion,
        spl_db=spl,
        driver_electrical_power_w=electrical_power,
        maximum_spl_db=maximum_spl,
        limiting_factor=factor_names[limit_index],
    )


def sealed_response(
    driver: Driver,
    system: System,
    frequency_hz: NDArray[np.float64],
    *,
    input_voltage_rms: float = 1.0,
) -> NDArray[np.float64]:
    """Return a half-space sealed-box response for comparison."""
    omega = 2.0 * np.pi * frequency_hz
    ze = driver.re_ohm + 1j * omega * driver.le_h
    zmd = driver.rms_kg_per_s + 1j * omega * driver.mms_kg + 1.0 / (1j * omega * driver.cms_m_per_n)
    zab = box_acoustic_impedance(frequency_hz, system)
    total_mechanical = zmd + zab * driver.sd_m2**2
    impedance = ze + driver.bl_tm**2 / total_mechanical
    current = input_voltage_rms / impedance
    velocity = driver.bl_tm * current / total_mechanical
    volume_velocity = driver.sd_m2 * velocity
    pressure = 1j * omega * RHO_AIR * volume_velocity / (2.0 * np.pi * system.distance_m)
    return np.asarray(
        20.0 * np.log10(np.maximum(np.abs(pressure), 1e-20) / REFERENCE_PRESSURE),
        dtype=np.float64,
    )
