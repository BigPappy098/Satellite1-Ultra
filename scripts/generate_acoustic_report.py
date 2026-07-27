#!/usr/bin/env python3
"""Generate deterministic acoustic simulations, tables, and sensitivity plots."""

from __future__ import annotations

import csv
import json
from dataclasses import replace
from pathlib import Path

import matplotlib
import numpy as np
import yaml

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from satellite1_ultra.acoustics import (
    Driver,
    PassiveRadiator,
    System,
    required_pr_moving_mass,
    sealed_response,
    simulate,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "acoustics"


def load_model() -> tuple[Driver, PassiveRadiator, System, dict[str, float]]:
    with (ROOT / "config" / "components.yaml").open(encoding="utf-8") as source:
        components = yaml.safe_load(source)
    active = components["active_drivers"][components["selection"]["active_driver_primary"]]
    passive = components["passive_radiators"][components["selection"]["passive_radiator_primary"]]
    net_volume_l = 3.20
    target_tuning_hz = 50.0
    radiator = PassiveRadiator(
        count=2,
        mms_kg=passive["mms_g"] / 1000.0,
        cms_m_per_n=passive["cms_mm_per_n"] / 1000.0,
        rms_kg_per_s=passive["rms_kg_per_s"],
        sd_m2=passive["sd_cm2"] / 10000.0,
        design_excursion_m=passive["design_excursion_mm"] / 1000.0,
    )
    required_mass = required_pr_moving_mass(radiator, net_volume_l / 1000.0, target_tuning_hz)
    radiator = replace(radiator, mms_kg=required_mass)
    driver = Driver(
        re_ohm=active["re_ohm"],
        le_h=active["le_mh"] / 1000.0,
        mms_kg=active["mms_g"] / 1000.0,
        cms_m_per_n=active["cms_mm_per_n"] / 1000.0,
        rms_kg_per_s=active["rms_kg_per_s"],
        bl_tm=active["bl_tm"],
        sd_m2=active["sd_cm2"] / 10000.0,
        xmax_m=active["xmax_mm"] / 1000.0,
        thermal_power_w=active["rated_power_w"],
    )
    system = System(
        volume_m3=net_volume_l / 1000.0,
        leak_q=7.0,
        target_tuning_hz=target_tuning_hz,
        amplifier_voltage_rms=10.0,
        amplifier_peak_current_a=6.0,
    )
    facts = {
        "preliminary_net_volume_l": net_volume_l,
        "target_tuning_hz": target_tuning_hz,
        "required_mass_each_g": required_mass * 1000.0,
        "added_mass_each_g": (required_mass - passive["mms_g"] / 1000.0) * 1000.0,
    }
    return driver, radiator, system, facts


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    driver, radiator, system, facts = load_model()
    frequency = np.geomspace(20.0, 20000.0, 1000)
    response = simulate(driver, radiator, system, frequency)
    sealed = sealed_response(driver, system, frequency)

    with (OUTPUT / "response.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target)
        writer.writerow(
            [
                "frequency_hz",
                "spl_1v_db",
                "sealed_spl_1v_db",
                "impedance_magnitude_ohm",
                "driver_excursion_1v_mm",
                "pr_excursion_each_1v_mm",
                "maximum_spl_db",
                "limiting_factor",
            ]
        )
        writer.writerows(
            zip(
                frequency,
                response.spl_db,
                sealed,
                np.abs(response.impedance_ohm),
                response.driver_excursion_m * 1000.0,
                response.passive_excursion_m * 1000.0,
                response.maximum_spl_db,
                response.limiting_factor,
                strict=True,
            )
        )

    minimum_impedance = float(np.min(np.abs(response.impedance_ohm)))
    facts |= {
        "minimum_modeled_impedance_ohm": minimum_impedance,
        "minimum_impedance_frequency_hz": float(
            frequency[np.argmin(np.abs(response.impedance_ohm))]
        ),
        "maximum_spl_at_50_hz_db": float(response.maximum_spl_db[np.argmin(abs(frequency - 50))]),
        "maximum_spl_at_100_hz_db": float(response.maximum_spl_db[np.argmin(abs(frequency - 100))]),
        "recommended_high_pass_hz": 38.0,
        "recommended_high_pass_order": 4,
        "evidence_label": "ENGINEERING_ESTIMATE",
        "physical_validation": "REQUIRES_PHYSICAL_VALIDATION",
    }
    (OUTPUT / "summary.json").write_text(json.dumps(facts, indent=2) + "\n", encoding="utf-8")

    figure, axes = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)
    axes[0, 0].semilogx(frequency, response.spl_db, label="2x opposed PR")
    axes[0, 0].semilogx(frequency, sealed, label="sealed comparison", linestyle="--")
    axes[0, 0].set(title="Half-space response at 1 V RMS", ylabel="SPL at 1 m (dB)")
    axes[0, 0].legend()
    axes[0, 1].semilogx(frequency, np.abs(response.impedance_ohm))
    axes[0, 1].axhline(3.2, color="red", linestyle=":", label="TAS2780 minimum load")
    axes[0, 1].set(title="Estimated electrical impedance", ylabel="Ohm")
    axes[0, 1].legend()
    axes[1, 0].loglog(frequency, response.driver_excursion_m * 1000.0, label="active")
    axes[1, 0].loglog(frequency, response.passive_excursion_m * 1000.0, label="each PR")
    axes[1, 0].set(title="Excursion at 1 V RMS", ylabel="mm")
    axes[1, 0].legend()
    axes[1, 1].semilogx(frequency, response.maximum_spl_db)
    axes[1, 1].set(title="Modeled maximum SPL by first limit", ylabel="SPL at 1 m (dB)")
    for axis in axes.flat:
        axis.set(xlabel="Frequency (Hz)")
        axis.grid(True, which="both", alpha=0.25)
        axis.set_xlim(20, 20000)
    figure.suptitle("Satellite1 Ultra lumped-parameter simulation — not a measurement")
    figure.savefig(OUTPUT / "system_response.png", dpi=180)
    plt.close(figure)

    figure, axes = plt.subplots(1, 3, figsize=(15, 4.8), constrained_layout=True)
    for volume_l in (2.8, 3.2, 3.6):
        variant = replace(system, volume_m3=volume_l / 1000.0)
        mass = required_pr_moving_mass(radiator, variant.volume_m3, variant.target_tuning_hz)
        curve = simulate(driver, replace(radiator, mms_kg=mass), variant, frequency).spl_db
        axes[0].semilogx(frequency, curve, label=f"{volume_l:.1f} L")
    for leak_q in (3.0, 7.0, 15.0):
        curve = simulate(driver, radiator, replace(system, leak_q=leak_q), frequency).spl_db
        axes[1].semilogx(frequency, curve, label=f"Qleak {leak_q:g}")
    for mass_scale in (0.85, 1.0, 1.15):
        curve = simulate(
            driver,
            replace(radiator, mms_kg=radiator.mms_kg * mass_scale),
            system,
            frequency,
        ).spl_db
        axes[2].semilogx(frequency, curve, label=f"mass {mass_scale:.0%}")
    titles = ("Net-volume sensitivity", "Leakage sensitivity", "PR-mass sensitivity")
    for axis, title in zip(axes, titles, strict=True):
        axis.set(title=title, xlabel="Frequency (Hz)", ylabel="SPL at 1 V/1 m (dB)")
        axis.set_xlim(20, 300)
        axis.grid(True, which="both", alpha=0.25)
        axis.legend()
    figure.suptitle("Sensitivity analysis — ENGINEERING_ESTIMATE")
    figure.savefig(OUTPUT / "sensitivity.png", dpi=180)
    plt.close(figure)


if __name__ == "__main__":
    main()
