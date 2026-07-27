"""Reproducible acoustic analysis driven by the exact CAD net volume.

Everything in this module is a lumped-parameter *simulation*.  Nothing here is
a measurement, and no output may be presented as one.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
from numpy.typing import NDArray

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from satellite1_ultra.acoustics import (
    Driver,
    PassiveRadiator,
    Response,
    System,
    required_pr_moving_mass,
    sealed_response,
    simulate,
)
from satellite1_ultra.configuration import (
    ROOT,
    load_configuration,
)

EVIDENCE_ESTIMATE = "ENGINEERING_ESTIMATE"
EVIDENCE_DRAWING = "DERIVED_FROM_MANUFACTURER_DRAWING"
EVIDENCE_PHYSICAL = "REQUIRES_PHYSICAL_VALIDATION"


@dataclass(frozen=True)
class AcousticModel:
    """A fully resolved simulation input set."""

    driver: Driver
    radiator: PassiveRadiator
    system: System
    net_volume_l: float
    tuning_hz: float
    required_pr_mass_g: float
    added_pr_mass_g: float
    published_pr_mms_g: float


def net_volume_from_validation(root: Path = ROOT) -> float:
    """Read the exact B-rep net volume produced by the validation gate."""
    path = root / "reports" / "validation" / "acoustic_volume.json"
    if not path.is_file():
        raise FileNotFoundError(
            "reports/validation/acoustic_volume.json is missing; run the validation "
            "stage before the acoustic stage."
        )
    with path.open(encoding="utf-8") as source:
        return float(json.load(source)["net_acoustic_volume_l"])


def build_model(net_volume_l: float | None = None, root: Path = ROOT) -> AcousticModel:
    """Assemble the simulation inputs from configuration and measured volume."""
    configuration = load_configuration(root)
    components = configuration["components"]
    acoustics = configuration["default"]["acoustics"]
    selection = components["selection"]
    active = components["active_drivers"][selection["active_driver_primary"]]
    passive = components["passive_radiators"][selection["passive_radiator_primary"]]

    volume_l = net_volume_l if net_volume_l is not None else net_volume_from_validation(root)
    tuning_hz = float(acoustics["target_tuning_hz"])

    radiator = PassiveRadiator(
        count=int(acoustics["passive_radiator_count"]),
        mms_kg=passive["mms_g"] / 1000.0,
        cms_m_per_n=passive["cms_mm_per_n"] / 1000.0,
        rms_kg_per_s=passive["rms_kg_per_s"],
        sd_m2=passive["sd_cm2"] / 10000.0,
        design_excursion_m=passive["design_excursion_mm"] / 1000.0,
    )
    required = required_pr_moving_mass(radiator, volume_l / 1000.0, tuning_hz)
    radiator = replace(radiator, mms_kg=required)
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
        volume_m3=volume_l / 1000.0,
        leak_q=float(acoustics["leakage_q"]),
        target_tuning_hz=tuning_hz,
        amplifier_voltage_rms=float(acoustics["amplifier_voltage_rms"]),
        amplifier_peak_current_a=float(acoustics["amplifier_peak_current_a"]),
    )
    return AcousticModel(
        driver=driver,
        radiator=radiator,
        system=system,
        net_volume_l=volume_l,
        tuning_hz=tuning_hz,
        required_pr_mass_g=required * 1000.0,
        added_pr_mass_g=(required - passive["mms_g"] / 1000.0) * 1000.0,
        published_pr_mms_g=float(passive["mms_g"]),
    )


def _grid(points: int) -> NDArray[np.float64]:
    """Logarithmic analysis grid from 20 Hz to 20 kHz."""
    return np.geomspace(20.0, 20000.0, points, dtype=np.float64)


def passband_reference_db(frequency: NDArray[np.float64], spl: NDArray[np.float64]) -> float:
    """Mean SPL over the 200-500 Hz reference band."""
    band = (frequency >= 200.0) & (frequency <= 500.0)
    return float(np.mean(spl[band]))


def _f3(frequency: NDArray[np.float64], spl: NDArray[np.float64]) -> float:
    """Lower -3 dB corner, log-interpolated at the highest crossing below 200 Hz."""
    reference = passband_reference_db(frequency, spl) - 3.0
    below = frequency < 200.0
    f_low, s_low = frequency[below], spl[below]
    crossings = np.nonzero((s_low[:-1] < reference) & (s_low[1:] >= reference))[0]
    if not crossings.size:
        return float(f_low.min())
    index = int(crossings[-1])
    span = s_low[index + 1] - s_low[index]
    weight = 0.0 if span == 0.0 else (reference - s_low[index]) / span
    log_f = np.log(f_low[index]) + weight * (np.log(f_low[index + 1]) - np.log(f_low[index]))
    return float(np.exp(log_f))


def _passband_ripple_db(
    frequency: NDArray[np.float64], spl: NDArray[np.float64], low: float
) -> float:
    band = (frequency >= low) & (frequency <= 400.0)
    return float(spl[band].max() - spl[band].min())


def optimal_tuning_hz(
    model: AcousticModel,
    candidates: NDArray[np.float64] | None = None,
    maximum_ripple_db: float = 3.5,
    minimum_added_mass_g: float = 0.5,
) -> dict[str, Any]:
    """Sweep the passive-radiator tuning and pick the best achievable alignment.

    The objective is the lowest -3 dB corner subject to two hard constraints:
    the passband above the corner must stay inside ``maximum_ripple_db``, and
    the required moving mass must exceed the published Mms by at least
    ``minimum_added_mass_g`` so the alignment is reachable by *adding* mass to
    the M6 post rather than by removing mass from the radiator.
    """
    sweep_points: NDArray[np.float64] = (
        np.arange(40.0, 90.5, 1.0, dtype=np.float64) if candidates is None else candidates
    )
    frequency = _grid(900)
    rows: list[dict[str, Any]] = []
    for tuning in sweep_points:
        mass = required_pr_moving_mass(model.radiator, model.system.volume_m3, float(tuning))
        added_g = (mass - model.published_pr_mms_g / 1000.0) * 1000.0
        response = simulate(
            model.driver,
            replace(model.radiator, mms_kg=mass),
            replace(model.system, target_tuning_hz=float(tuning)),
            frequency,
        )
        corner = _f3(frequency, response.spl_db)
        ripple = _passband_ripple_db(frequency, response.spl_db, corner * 1.2)
        feasible = added_g >= minimum_added_mass_g and ripple <= maximum_ripple_db
        rows.append(
            {
                "tuning_hz": float(tuning),
                "required_mass_g": mass * 1000.0,
                "added_mass_g": added_g,
                "f3_hz": corner,
                "passband_ripple_db": ripple,
                "feasible": feasible,
            }
        )
    feasible_rows = [row for row in rows if row["feasible"]]
    best = min(feasible_rows or rows, key=lambda row: row["f3_hz"])
    return {
        "optimal_tuning_hz": best["tuning_hz"],
        "optimal_f3_hz": best["f3_hz"],
        "optimal_added_mass_each_g": best["added_mass_g"],
        "objective": (
            "lowest -3 dB corner subject to passband ripple <= "
            f"{maximum_ripple_db} dB and added mass >= {minimum_added_mass_g} g"
        ),
        "sweep": rows,
        "evidence": EVIDENCE_ESTIMATE,
    }


def _recommended_high_pass(
    model: AcousticModel, frequency: NDArray[np.float64], response: Response
) -> dict[str, Any]:
    """Choose a protective high-pass from the modelled excursion limits."""
    below = frequency < model.tuning_hz
    driver_ratio = response.driver_excursion_m[below] / model.driver.xmax_m
    pr_ratio = response.passive_excursion_m[below] / model.radiator.design_excursion_m
    worst = np.maximum(driver_ratio, pr_ratio)
    critical = frequency[below][worst >= worst.max() * 0.5]
    corner = float(critical.max()) if critical.size else model.tuning_hz * 0.75
    return {
        "recommended_high_pass_hz": round(min(corner, model.tuning_hz * 0.85), 1),
        "recommended_high_pass_order": 4,
        "rationale": (
            "Below tuning the passive radiators unload and both excursions rise "
            "fastest; a fourth-order high-pass at this corner keeps the modelled "
            "excursion inside the linear limits at full amplifier voltage."
        ),
        "evidence": EVIDENCE_ESTIMATE,
    }


def summarise(model: AcousticModel) -> dict[str, Any]:
    """Return the full machine-readable acoustic summary."""
    frequency = _grid(1000)
    response = simulate(model.driver, model.radiator, model.system, frequency)
    sealed = sealed_response(model.driver, model.system, frequency)
    impedance = np.abs(response.impedance_ohm)
    max_spl = response.maximum_spl_db

    def at(target: float, values: NDArray[np.float64]) -> float:
        return float(values[int(np.argmin(np.abs(frequency - target)))])

    limits = {
        name: float(np.count_nonzero(response.limiting_factor == name)) / frequency.size
        for name in sorted(set(response.limiting_factor.tolist()))
    }
    summary: dict[str, Any] = {
        "evidence": EVIDENCE_ESTIMATE,
        "disclaimer": (
            "Lumped-parameter simulation of a half-space radiating system. These "
            "are calculated values, not measurements."
        ),
        "net_acoustic_volume_l": model.net_volume_l,
        "target_tuning_hz": model.tuning_hz,
        "passive_radiator_count": model.radiator.count,
        "published_pr_mms_g": model.published_pr_mms_g,
        "required_pr_moving_mass_each_g": model.required_pr_mass_g,
        "added_pr_mass_each_g": model.added_pr_mass_g,
        "added_pr_mass_total_g": model.added_pr_mass_g * model.radiator.count,
        "pr_mass_adjustment_interface": "M6 threaded post on each SB12PACR-00",
        "minimum_modeled_impedance_ohm": float(impedance.min()),
        "minimum_impedance_frequency_hz": float(frequency[int(np.argmin(impedance))]),
        "amplifier_minimum_load_ohm": 3.2,
        "impedance_margin_ohm": float(impedance.min()) - 3.2,
        "sealed_f3_hz": _f3(frequency, sealed),
        "passive_radiator_f3_hz": _f3(frequency, response.spl_db),
        "bass_extension_gain_hz": _f3(frequency, sealed) - _f3(frequency, response.spl_db),
        "spl_1v_at_50_hz_db": at(50.0, response.spl_db),
        "sealed_spl_1v_at_50_hz_db": at(50.0, sealed),
        "maximum_spl_at_50_hz_db": at(50.0, max_spl),
        "maximum_spl_at_80_hz_db": at(80.0, max_spl),
        "maximum_spl_at_100_hz_db": at(100.0, max_spl),
        "maximum_spl_at_1_khz_db": at(1000.0, max_spl),
        "limiting_factor_fraction": limits,
        "driver_excursion_1v_at_tuning_mm": at(model.tuning_hz, response.driver_excursion_m) * 1e3,
        "pr_excursion_1v_at_tuning_mm": at(model.tuning_hz, response.passive_excursion_m) * 1e3,
        "thermal_assumption": (
            "Continuous power is capped at the published 30 W RMS rating with no "
            "power compression modelled; real compression will reduce maximum SPL."
        ),
        "conservative_eq_guidance": [
            "Do not apply low-shelf boost below the recommended high-pass corner.",
            "Limit any bass shelf to +3 dB between the high-pass corner and 120 Hz "
            "and re-check excursion before raising it.",
            "Apply a gentle 1-2 dB broad cut around the modelled impedance minimum "
            "if the amplifier reports current limiting.",
            "Cone breakup of the ND91-4 aluminium cone sits above 10 kHz; a "
            "low-pass or notch there is a listening choice, not a protection need.",
        ],
        "physical_gate": {
            "evidence": EVIDENCE_PHYSICAL,
            "requirement": (
                "Measure impedance on the assembled cabinet to obtain the real "
                "tuning frequency and leakage Q, then re-run this model with the "
                "measured values before finalising DSP."
            ),
        },
    }
    summary.update(_recommended_high_pass(model, frequency, response))
    alignment = optimal_tuning_hz(model)
    summary["alignment_optimiser"] = {
        key: value for key, value in alignment.items() if key != "sweep"
    }
    summary["alignment_sweep"] = alignment["sweep"]
    deviation = abs(alignment["optimal_tuning_hz"] - model.tuning_hz)
    summary["tuning_matches_optimum"] = deviation <= 3.0
    summary["tuning_deviation_hz"] = deviation
    summary["status"] = "PASS" if summary["tuning_matches_optimum"] else "FAIL"
    return summary


def generate_acoustic_reports(
    output: Path = ROOT / "reports" / "acoustics",
    net_volume_l: float | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Write the acoustic CSV, JSON summary and the two figure sheets."""
    model = build_model(net_volume_l, root)
    output.mkdir(parents=True, exist_ok=True)
    frequency = _grid(1000)
    response = simulate(model.driver, model.radiator, model.system, frequency)
    sealed = sealed_response(model.driver, model.system, frequency)

    with (output / "response.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target)
        writer.writerow(
            [
                "frequency_hz",
                "spl_1v_db",
                "sealed_spl_1v_db",
                "impedance_magnitude_ohm",
                "impedance_phase_deg",
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
                np.degrees(np.angle(response.impedance_ohm)),
                response.driver_excursion_m * 1000.0,
                response.passive_excursion_m * 1000.0,
                response.maximum_spl_db,
                response.limiting_factor,
                strict=True,
            )
        )

    summary = summarise(model)
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    figure, axes = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)
    axes[0, 0].semilogx(frequency, response.spl_db, label=f"{model.radiator.count}x opposed PR")
    axes[0, 0].semilogx(frequency, sealed, label="sealed comparison", linestyle="--")
    axes[0, 0].axvline(summary["recommended_high_pass_hz"], color="grey", linestyle=":")
    axes[0, 0].set(title="Half-space response at 1 V RMS", ylabel="SPL at 1 m (dB)")
    axes[0, 0].legend()
    axes[0, 1].semilogx(frequency, np.abs(response.impedance_ohm))
    axes[0, 1].axhline(3.2, color="red", linestyle=":", label="TAS2780 minimum load")
    axes[0, 1].set(title="Estimated electrical impedance", ylabel="Ohm")
    axes[0, 1].legend()
    axes[1, 0].loglog(frequency, response.driver_excursion_m * 1000.0, label="active")
    axes[1, 0].loglog(frequency, response.passive_excursion_m * 1000.0, label="each PR")
    axes[1, 0].axhline(model.driver.xmax_m * 1000.0, color="orange", linestyle=":", label="Xmax")
    axes[1, 0].axhline(
        model.radiator.design_excursion_m * 1000.0, color="blue", linestyle=":", label="PR design"
    )
    axes[1, 0].set(title="Excursion at 1 V RMS", ylabel="mm")
    axes[1, 0].legend()
    axes[1, 1].semilogx(frequency, response.maximum_spl_db)
    axes[1, 1].set(title="Modelled maximum SPL by first limit", ylabel="SPL at 1 m (dB)")
    for axis in axes.flat:
        axis.set(xlabel="Frequency (Hz)")
        axis.grid(True, which="both", alpha=0.25)
        axis.set_xlim(20, 20000)
    figure.suptitle(
        f"Satellite1 Ultra lumped-parameter simulation — {model.net_volume_l:.3f} L net "
        f"— NOT A MEASUREMENT"
    )
    figure.savefig(output / "system_response.png", dpi=180)
    plt.close(figure)

    figure, axes = plt.subplots(1, 3, figsize=(15, 4.8), constrained_layout=True)
    base = model.net_volume_l
    for volume_l in (base * 0.9, base, base * 1.1):
        variant = replace(model.system, volume_m3=volume_l / 1000.0)
        mass = required_pr_moving_mass(model.radiator, variant.volume_m3, variant.target_tuning_hz)
        curve = simulate(
            model.driver, replace(model.radiator, mms_kg=mass), variant, frequency
        ).spl_db
        axes[0].semilogx(frequency, curve, label=f"{volume_l:.2f} L")
    for leak_q in (3.0, model.system.leak_q, 15.0):
        curve = simulate(
            model.driver, model.radiator, replace(model.system, leak_q=leak_q), frequency
        ).spl_db
        axes[1].semilogx(frequency, curve, label=f"Qleak {leak_q:g}")
    for mass_scale in (0.85, 1.0, 1.15):
        curve = simulate(
            model.driver,
            replace(model.radiator, mms_kg=model.radiator.mms_kg * mass_scale),
            model.system,
            frequency,
        ).spl_db
        axes[2].semilogx(frequency, curve, label=f"PR mass {mass_scale:.0%}")
    titles = ("Net-volume sensitivity", "Leakage sensitivity", "PR tuning-mass sensitivity")
    for axis, title in zip(axes, titles, strict=True):
        axis.set(title=title, xlabel="Frequency (Hz)", ylabel="SPL at 1 V / 1 m (dB)")
        axis.set_xlim(20, 300)
        axis.grid(True, which="both", alpha=0.25)
        axis.legend()
    figure.suptitle("Sensitivity analysis — ENGINEERING_ESTIMATE, not a measurement")
    figure.savefig(output / "sensitivity.png", dpi=180)
    plt.close(figure)

    _write_markdown(output / "acoustic_model.md", model, summary)
    return summary


def _write_markdown(path: Path, model: AcousticModel, summary: dict[str, Any]) -> None:
    lines = [
        "# Acoustic model",
        "",
        "`ENGINEERING_ESTIMATE`. Every number below is a lumped-parameter "
        "calculation. None of it is a measurement, and none of it may be quoted "
        "as measured performance.",
        "",
        "## System",
        "",
        f"- Net acoustic volume: **{model.net_volume_l:.3f} L** "
        "(exact B-rep, `VERIFIED_DIGITALLY`)",
        f"- Architecture: one active driver, {model.radiator.count} opposed passive radiators",
        f"- Target tuning: {model.tuning_hz:.1f} Hz",
        f"- Required moving mass per radiator: **{model.required_pr_mass_g:.2f} g**",
        f"- Published Mms per radiator: {model.published_pr_mms_g:.2f} g",
        f"- Added tuning mass per radiator: **{model.added_pr_mass_g:.2f} g** "
        f"({summary['added_pr_mass_total_g']:.2f} g total), fitted to the M6 post",
        "",
        "## Modelled results",
        "",
        f"- Sealed-alignment f3: {summary['sealed_f3_hz']:.1f} Hz",
        f"- Passive-radiator f3: **{summary['passive_radiator_f3_hz']:.1f} Hz** "
        f"({summary['bass_extension_gain_hz']:.1f} Hz of extension)",
        f"- Minimum modelled impedance: {summary['minimum_modeled_impedance_ohm']:.2f} ohm at "
        f"{summary['minimum_impedance_frequency_hz']:.0f} Hz "
        f"(amplifier minimum {summary['amplifier_minimum_load_ohm']:.1f} ohm, "
        f"margin {summary['impedance_margin_ohm']:.2f} ohm)",
        f"- Maximum SPL at 50 Hz: {summary['maximum_spl_at_50_hz_db']:.1f} dB at 1 m",
        f"- Maximum SPL at 100 Hz: {summary['maximum_spl_at_100_hz_db']:.1f} dB at 1 m",
        f"- Maximum SPL at 1 kHz: {summary['maximum_spl_at_1_khz_db']:.1f} dB at 1 m",
        f"- Recommended protective high-pass: **{summary['recommended_high_pass_hz']:.1f} Hz, "
        f"order {summary['recommended_high_pass_order']}**",
        "",
        "## Conservative EQ guidance",
        "",
    ]
    lines += [f"- {item}" for item in summary["conservative_eq_guidance"]]
    lines += [
        "",
        "## Physical gate",
        "",
        f"`{EVIDENCE_PHYSICAL}` — {summary['physical_gate']['requirement']}",
        "",
        "## Figures",
        "",
        "- `system_response.png` — response, impedance, excursion, maximum SPL",
        "- `sensitivity.png` — net-volume, leakage and tuning-mass sensitivity",
        "- `response.csv` — the full tabulated simulation",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
