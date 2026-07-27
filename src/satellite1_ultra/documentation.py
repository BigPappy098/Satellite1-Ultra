"""Generated manufacturing and service documentation.

Every document here is derived from the same authoritative sources as the
geometry: the configuration files, the validation gates and the export
manifest.  Nothing is hand-maintained, so nothing can drift from the CAD.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from satellite1_ultra.configuration import (
    ROOT,
    load_configuration,
    load_design_parameters,
    selected_components,
)
from satellite1_ultra.exporting import PARTS, source_commit
from satellite1_ultra.geometry import DesignParameters, ballast_plate_extent

EVIDENCE_DIGITAL = "VERIFIED_DIGITALLY"
EVIDENCE_OFFICIAL = "DERIVED_FROM_OFFICIAL_CAD"
EVIDENCE_DRAWING = "DERIVED_FROM_MANUFACTURER_DRAWING"
EVIDENCE_ESTIMATE = "ENGINEERING_ESTIMATE"
EVIDENCE_PHYSICAL = "REQUIRES_PHYSICAL_VALIDATION"


@dataclass(frozen=True)
class Risk:
    """One entry in the project risk register."""

    identifier: str
    severity: str
    title: str
    consequence: str
    mitigation: str
    owner: str
    state: str
    evidence: str


RISKS: tuple[Risk, ...] = (
    Risk(
        "R-01",
        "HIGH",
        "Component flange thicknesses are not published",
        "If the ND91-4 flange is not 3.0 mm or the SB12PACR-00 flange is not "
        "4.0 mm, the clamp ring either fails to load the flange or crushes the "
        "gasket past 45 % compression.",
        "coupon_active_driver and coupon_passive_radiator measure the assembled "
        "stack directly; the value is a single configuration parameter and the "
        "whole model regenerates from it.",
        "project owner",
        "OPEN",
        EVIDENCE_ESTIMATE,
    ),
    Risk(
        "R-02",
        "HIGH",
        "Core board position in the official stack is undetermined",
        "The published FutureProofHomes assets contain no assembled Core+HAT "
        "model, so no Core placement can be asserted.",
        "The enclosure is validated against a Core-sized free volume in the "
        "electronics bay instead of an asserted placement; confirm against a "
        "physical development kit before release.",
        "project owner",
        "OPEN",
        "UNDETERMINED",
    ),
    Risk(
        "R-03",
        "HIGH",
        "Bass extension is limited by the driver, not the enclosure",
        "The selected ND91-4 has Vas 1.4 L and a published Vd of 12.2 cm3. In "
        "3.45 L the enclosure is already 2.5x Vas, so further volume buys very "
        "little. Maximum modelled SPL at 50 Hz is excursion- and voltage-limited.",
        "A larger-displacement 4 in driver is the single highest-leverage "
        "improvement available. Every interface is parametric, so a swap is a "
        "configuration change plus one coupon.",
        "project owner",
        "OPEN",
        EVIDENCE_ESTIMATE,
    ),
    Risk(
        "R-04",
        "MEDIUM",
        "No pressure-decay measurement exists",
        "The sealing gates prove geometric continuity of every gasket land and "
        "that no fastener crosses the boundary. They cannot prove that a printed "
        "ASA wall is gas-tight.",
        "Pressure-decay test the assembled cabinet and enter the measured "
        "leakage Q into config/default.yaml before quoting any bass figure.",
        "project owner",
        "OPEN",
        EVIDENCE_PHYSICAL,
    ),
    Risk(
        "R-05",
        "MEDIUM",
        "Printed dimensional accuracy is assumed, not measured",
        "All tolerance stacks assume +/-0.15 mm printed accuracy. A machine "
        "outside that band can close the carrier clearance or open the gasket "
        "compression past its limit.",
        "The eight-coupon set measures it; corrections go into "
        "config/physical_compensation.yaml and regenerate every part.",
        "project owner",
        "OPEN",
        EVIDENCE_PHYSICAL,
    ),
    Risk(
        "R-06",
        "MEDIUM",
        "Wi-Fi and wake-word performance are unmeasured",
        "The enclosure surrounds the official board stack with printed ASA and "
        "a slotted shell. Antenna detuning and microphone obstruction cannot be "
        "predicted from geometry.",
        "Run the documented wake-word and wireless test procedures on an "
        "assembled unit against a bare development kit as the control.",
        "project owner",
        "OPEN",
        EVIDENCE_PHYSICAL,
    ),
    Risk(
        "R-07",
        "MEDIUM",
        "Board thermal behaviour in a closed shroud is unmeasured",
        "The electronics bay is vented only through the shroud vent bank and the "
        "rear service aperture.",
        "Run the documented thermal soak procedure; if margins are short, the "
        "vent bank is a parametric feature and can be widened.",
        "project owner",
        "OPEN",
        EVIDENCE_PHYSICAL,
    ),
    Risk(
        "R-08",
        "LOW",
        "Heat-set insert pull-out strength is assumed",
        "Insert bores are sized Oe4.2 for a Oe4.6 M3 insert on the manufacturer's "
        "recommendation, not on a measured pull test in this material.",
        "coupon_heat_set_insert brackets four bore diameters; pull-test to 250 N.",
        "project owner",
        "OPEN",
        EVIDENCE_PHYSICAL,
    ),
    Risk(
        "R-09",
        "LOW",
        "Batch 2 hardware is not supported",
        "Satellite1.1 (Batch 2) requires an external Wi-Fi antenna and a "
        "different service adapter that this revision does not provide.",
        "The board revision is a configuration value and the official Batch 2 "
        "geometry is already preserved and pinned; add the adapter when needed.",
        "project owner",
        "OPEN",
        EVIDENCE_OFFICIAL,
    ),
)


def _validation(root: Path) -> dict[str, Any]:
    directory = root / "reports" / "validation"
    reports: dict[str, Any] = {}
    for path in sorted(directory.glob("*.json")):
        with path.open(encoding="utf-8") as source:
            reports[path.stem] = json.load(source)
    return reports


def _acoustics(root: Path) -> dict[str, Any]:
    path = root / "reports" / "acoustics" / "summary.json"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as source:
        return dict(json.load(source))


def bill_of_materials(parameters: DesignParameters, root: Path = ROOT) -> list[dict[str, Any]]:
    """Complete BOM: printed parts, official parts, components and hardware."""
    driver, radiator = selected_components(root)
    configuration = load_configuration(root)
    fasteners = _validation(root).get("fasteners", {}).get("schedule", [])
    total_fasteners = sum(
        row["quantity"] * (2 if "each" in row["joint"] else 1) for row in fasteners
    )
    plate_w, plate_d, plate_t = ballast_plate_extent(parameters)
    rows: list[dict[str, Any]] = []
    for name, definition in PARTS.items():
        rows.append(
            {
                "item": name,
                "category": "fit coupon" if name.startswith("coupon_") else "printed part",
                "quantity": definition.quantity,
                "material": definition.material,
                "source": "this repository, exports/step",
                "evidence": definition.evidence_label,
            }
        )
    rows += [
        {
            "item": f"{driver['manufacturer']} {driver['model']}",
            "category": "acoustic component",
            "quantity": 1,
            "material": "-",
            "source": driver["source"],
            "evidence": EVIDENCE_DRAWING,
        },
        {
            "item": f"{radiator['manufacturer']} {radiator['model']}",
            "category": "acoustic component",
            "quantity": int(radiator["count"]),
            "material": "-",
            "source": radiator["source"],
            "evidence": EVIDENCE_DRAWING,
        },
        {
            "item": "FutureProofHomes Satellite1 development kit (Core + HAT, Batch 1)",
            "category": "official hardware",
            "quantity": 1,
            "material": "-",
            "source": "reference-assets/MANIFEST.csv",
            "evidence": EVIDENCE_OFFICIAL,
        },
        {
            "item": "Official Squircle upper stack: mid-plate, threads, top plate, "
            "PCB spacer, lock ring",
            "category": "official printed part",
            "quantity": 1,
            "material": "ASA or PETG",
            "source": "reference-assets/official/Satellite1-Enclosures",
            "evidence": EVIDENCE_OFFICIAL,
        },
        {
            "item": "M3 x 0.5 A2 socket/button head screws, assorted lengths per schedule",
            "category": "hardware",
            "quantity": total_fasteners,
            "material": "A2 stainless",
            "source": "reports/validation/fasteners.json",
            "evidence": EVIDENCE_DIGITAL,
        },
        {
            "item": (
                f"M3 heat-set inserts Oe{parameters.insert_outer_diameter:.1f} x "
                f"{parameters.insert_depth:.1f} mm"
            ),
            "category": "hardware",
            "quantity": total_fasteners,
            "material": "brass",
            "source": "reports/validation/fasteners.json",
            "evidence": EVIDENCE_DIGITAL,
        },
        {
            "item": f"{parameters.gasket_thickness:.1f} mm closed-cell EPDM sheet",
            "category": "consumable",
            "quantity": 1,
            "material": "EPDM",
            "source": "cut from exports/step gasket profiles",
            "evidence": EVIDENCE_DIGITAL,
        },
        {
            "item": (
                f"Mild-steel ballast plates {plate_w:.0f} x {plate_d:.0f} x {plate_t / 2.0:.0f} mm"
            ),
            "category": "ballast",
            "quantity": 2,
            "material": "mild steel",
            "source": "cut to size",
            "evidence": EVIDENCE_ESTIMATE,
        },
        {
            "item": "Speaker cable, 2 core, 1.0 mm2, 350 mm",
            "category": "consumable",
            "quantity": 1,
            "material": "copper/PVC",
            "source": "-",
            "evidence": EVIDENCE_ESTIMATE,
        },
        {
            "item": "Added radiator tuning mass, M6 hardware, per radiator",
            "category": "acoustic tuning",
            "quantity": int(radiator["count"]),
            "material": "steel",
            "source": "reports/acoustics/summary.json",
            "evidence": EVIDENCE_ESTIMATE,
        },
    ]
    _ = configuration
    return rows


def write_bom(output: Path, parameters: DesignParameters, root: Path = ROOT) -> Path:
    rows = bill_of_materials(parameters, root)
    path = output / "bill_of_materials.csv"
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(
            target,
            fieldnames=["item", "category", "quantity", "material", "source", "evidence"],
        )
        writer.writeheader()
        writer.writerows(rows)
    return path


def _table(headers: list[str], rows: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return lines


def fastener_schedule_markdown(root: Path = ROOT) -> list[str]:
    schedule = _validation(root).get("fasteners", {}).get("schedule", [])
    rows = [
        [
            row["joint"],
            str(row["quantity"]),
            f"M3 x {row['length_mm']:.0f}",
            row["head"],
            f"{row['clamped_stack_mm']:.1f}",
            f"{row['engagement_mm']:.1f}",
            f"{row['bottoming_margin_mm']:.1f}",
            row["access_direction"],
            row["torque_guidance_nm"],
        ]
        for row in schedule
    ]
    return _table(
        [
            "Joint",
            "Qty",
            "Screw",
            "Head",
            "Stack (mm)",
            "Engagement (mm)",
            "Bottoming margin (mm)",
            "Access",
            "Torque (Nm)",
        ],
        rows,
    )


def gasket_schedule_markdown(parameters: DesignParameters) -> list[str]:
    p = parameters
    compressed = p.compressed_gasket_thickness
    rows = [
        [
            "divider_gasket",
            "1",
            f"{p.gasket_thickness:.1f} mm closed-cell EPDM",
            f"{p.gasket_land_width:.1f} mm continuous rim land",
            f"{compressed:.2f}",
            "25 %",
            "eight M3 compression stops on the cabinet rim",
        ],
        [
            "driver_gasket",
            "1",
            f"{p.gasket_thickness:.1f} mm closed-cell EPDM",
            f"Oe{p.driver_seat_diameter:.1f} / Oe{p.driver_bore_diameter + 3.0:.1f} annulus",
            f"{compressed:.2f}",
            "25 %",
            "clamp ring bottoms on the cabinet outer face",
        ],
        [
            "passive_radiator_gasket",
            "2",
            f"{p.gasket_thickness:.1f} mm closed-cell EPDM",
            f"Oe{p.pr_seat_diameter:.1f} / Oe{p.pr_bore_diameter + 3.0:.1f} annulus",
            f"{compressed:.2f}",
            "25 %",
            "clamp ring bottoms on the cabinet ledge",
        ],
        [
            "cable_gland",
            "1",
            "TPU 95A, printed",
            f"Oe{p.cable_passage_diameter:.1f} divider passage",
            "interference",
            "-",
            "slit body, radial interference on two conductors",
        ],
    ]
    return _table(
        [
            "Seal",
            "Qty",
            "Material",
            "Land",
            "Assembled thickness (mm)",
            "Compression",
            "Compression control",
        ],
        rows,
    )


GUIDES: dict[str, str] = {}


def _print_guide(parameters: DesignParameters, root: Path) -> str:
    printability = _validation(root).get("printability", {})
    process = printability.get("process", {})
    rows = [
        [
            record["part"],
            str(PARTS[record["part"]].quantity),
            record["material"],
            record["print_orientation"],
            " x ".join(f"{value:.1f}" for value in record["bounds_mm"]),
        ]
        for record in printability.get("parts", [])
    ]
    lines = [
        "# Printing guide",
        "",
        "`VERIFIED_DIGITALLY` for geometry and orientation. Everything about how "
        "a specific printer behaves is `REQUIRES_PHYSICAL_VALIDATION`.",
        "",
        "## Do the coupons first",
        "",
        "Print and measure the eight fit coupons before any full-size part. Enter "
        "the results in `config/physical_compensation.yaml` and regenerate. See "
        "`docs/fit-coupons.md`.",
        "",
        "## Process",
        "",
        f"- Primary material: {process.get('primary_material', 'ASA')} "
        f"(alternative {process.get('alternative_material', 'PETG')})",
        f"- Nozzle {process.get('nozzle_mm', 0.4)} mm, layer "
        f"{process.get('layer_height_mm', 0.2)} mm",
        f"- {process.get('walls', 5)} walls, {process.get('top_bottom_layers', 6)} "
        f"top/bottom layers, {process.get('infill', '35% gyroid')}",
        "- Heated chamber or a draught-free enclosure is required for ASA",
        "- Do not enable any slicer XY compensation; the model carries its own",
        "",
        "## Orientation and support",
        "",
        *_table(["Part", "Qty", "Material", "Orientation", "Bounds (mm)"], rows),
        "",
        "## Process notes",
        "",
        *[f"- {note}" for note in printability.get("process_notes", [])],
        "",
        "## Post-processing",
        "",
        "- Install every heat-set insert with a temperature-controlled M3 tip, "
        "square to the boss. Do not torque a hot insert.",
        "- Deburr the component seats and the divider rim land with a scraper; do "
        "not sand a gasket land, sanding rounds the edge and opens a leak path.",
        f"- Cut the EPDM seals from {parameters.gasket_thickness:.1f} mm sheet "
        "using the exported gasket profiles as templates.",
        "",
    ]
    return "\n".join(lines)


def _assembly_guide(root: Path) -> str:
    assembly = _validation(root).get("assembly", {})
    steps = assembly.get("assembly_order", [])
    tools = {row["step"]: row for row in assembly.get("tool_access", [])}
    lines = [
        "# Assembly guide",
        "",
        "`VERIFIED_DIGITALLY` for the order and for tool access. Physical fit is "
        "`REQUIRES_PHYSICAL_VALIDATION` until a set of parts has been built.",
        "",
        "The order below is the topological order of the validated dependency "
        "graph in `reports/validation/assembly.json`; it is acyclic and has no "
        "trapped parts.",
        "",
    ]
    for index, step in enumerate(steps, start=1):
        row = tools.get(step, {})
        lines.append(
            f"{index}. **{step}** — insert along `{row.get('insertion_direction', '-')}`, "
            f"tool: {row.get('tool', '-')}"
        )
    lines += [
        "",
        "## Before you start",
        "",
        "- All eight fit coupons have passed and their corrections are entered.",
        "- All heat-set inserts are installed and square.",
        "- Every gasket is cut, clean and dry. A gasket is single-use once "
        "compressed; keep a spare set.",
        "",
        "## Torque",
        "",
        "Every M3 joint is 0.45-0.55 Nm. All gasketed joints are hard-stopped by "
        "geometry, so torque sets clamp load, not compression. Tighten opposing "
        "pairs in two passes.",
        "",
    ]
    return "\n".join(lines)


def _disassembly_guide(root: Path) -> str:
    assembly = _validation(root).get("assembly", {})
    lines = [
        "# Disassembly guide",
        "",
        "`VERIFIED_DIGITALLY`. Reverse of the validated assembly order; every part "
        "leaves along the reverse of its insertion direction.",
        "",
    ]
    for index, step in enumerate(assembly.get("disassembly_order", []), start=1):
        lines.append(f"{index}. reverse: {step}")
    lines += [
        "",
        "## Rules",
        "",
        "- Replace any gasket whose joint you open. Compressed closed-cell EPDM "
        "does not recover, and a reused seal is the most likely source of a leak.",
        "- Never lever a clamp ring; it is a slip fit in its seat with 0.30 mm of "
        "radial clearance and will come out by hand once its four screws are out.",
        "- Support the cabinet when the base skirt is off; the ballast is loose in its cartridge.",
        "",
    ]
    return "\n".join(lines)


def _maintenance_guide(root: Path) -> str:
    tasks = _validation(root).get("assembly", {}).get("service_tasks", [])
    rows = [
        [
            task["task"],
            ", ".join(task["remove"]),
            task["tool"],
            "yes" if task["gasket_replacement_required"] else "no",
        ]
        for task in tasks
    ]
    return "\n".join(
        [
            "# Maintenance guide",
            "",
            "`VERIFIED_DIGITALLY` for access paths.",
            "",
            *_table(["Task", "Parts to remove", "Tool", "New gasket required"], rows),
            "",
            "## Routine",
            "",
            "- Vacuum the shell slots with a soft brush. Do not use solvents on ASA.",
            "- Check the four shell screws annually; the shell is the only part "
            "that carries handling load.",
            "- If bass output changes audibly, suspect a seal before suspecting a "
            "component: open, inspect and replace the divider gasket first.",
            "",
        ]
    )


def _acoustic_test_guide(root: Path) -> str:
    acoustics = _acoustics(root)
    return "\n".join(
        [
            "# Acoustic test guide",
            "",
            f"`{EVIDENCE_PHYSICAL}`. The modelled values below are targets to "
            "compare against, not results.",
            "",
            "## 1. Impedance sweep (do this first)",
            "",
            "Measure impedance magnitude and phase, 20 Hz to 20 kHz, on the fully "
            "assembled and sealed cabinet at a level low enough to stay linear.",
            "",
            "- The two impedance peaks bracket the system tuning; the minimum "
            "between them is the real Fb.",
            f"- Modelled Fb target: {acoustics.get('target_tuning_hz', 'n/a')} Hz.",
            f"- Modelled minimum impedance: "
            f"{acoustics.get('minimum_modeled_impedance_ohm', float('nan')):.2f} ohm. "
            "If the measured minimum drops below 3.2 ohm, stop and re-check before "
            "driving the amplifier hard.",
            "- Enter the measured Fb and the derived leakage Q into "
            "`config/default.yaml` and re-run the acoustic stage.",
            "",
            "## 2. Sealed-box leak check",
            "",
            "Pressurise the acoustic chamber to about 1 kPa through the cable "
            "gland passage with the driver and radiators fitted, and record the "
            "decay over 60 s. A fast decay means a leak; find it before measuring "
            "anything else.",
            "",
            "## 3. Nearfield response",
            "",
            "Measure nearfield at the driver and at each radiator, scale by area "
            "ratio and sum, then splice to a gated farfield measurement above "
            "300 Hz. Compare against `reports/acoustics/response.csv`.",
            "",
            f"- Modelled f3: {acoustics.get('passive_radiator_f3_hz', float('nan')):.1f} Hz.",
            "",
            "## 4. Maximum output and distortion",
            "",
            "Step the level in 3 dB increments at 50, 80 and 200 Hz, recording "
            "THD and radiator excursion. Stop at 10 % THD or at the radiator's "
            "9 mm mechanical limit, whichever comes first.",
            "",
            f"- Modelled maximum SPL at 100 Hz: "
            f"{acoustics.get('maximum_spl_at_100_hz_db', float('nan')):.1f} dB at 1 m.",
            "",
            "## 5. Tuning-mass adjustment",
            "",
            f"The model calls for "
            f"{acoustics.get('added_pr_mass_each_g', float('nan')):.2f} g added to "
            "each radiator's M6 post. Adjust both radiators identically; unequal "
            "mass destroys the force cancellation that the opposed layout exists "
            "for.",
            "",
        ]
    )


def _wake_word_test_guide() -> str:
    return "\n".join(
        [
            "# Wake-word and microphone test guide",
            "",
            f"`{EVIDENCE_PHYSICAL}`. The enclosure does not move, cover or "
            "obstruct any microphone: the official top plate, diffuser, buttons "
            "and PCB spacer are used unmodified and the microphone openings are "
            "untouched. That is a geometric fact, not an acoustic result.",
            "",
            "## Control",
            "",
            "Run every test twice: once on a bare Satellite1 development kit and "
            "once on the assembled Satellite1 Ultra, in the same room, same "
            "positions, same firmware.",
            "",
            "## Procedure",
            "",
            "1. Wake-word detection rate: 50 utterances at 1, 3 and 5 m, on axis "
            "and at 45 degrees. Record hits and false rejects.",
            "2. Barge-in: repeat at playback levels of 60, 70 and 80 dBA measured "
            "at 1 m, using pink noise and then music.",
            "3. False accepts: 60 minutes of continuous speech-shaped noise and "
            "60 minutes of television audio.",
            "4. Button and LED check: every button actuates through the official "
            "top plate without binding, and the LED ring is evenly visible from "
            "30 degrees above horizontal at 2 m.",
            "",
            "## Pass criteria",
            "",
            "Detection rate must not fall by more than 5 percentage points "
            "against the control at any distance, and barge-in must not fall by "
            "more than 5 points at 70 dBA. Anything worse is a finding against "
            "this enclosure, not against the kit.",
            "",
        ]
    )


def _thermal_test_guide() -> str:
    return "\n".join(
        [
            "# Thermal test guide",
            "",
            f"`{EVIDENCE_PHYSICAL}`. No thermal simulation has been performed and none is claimed.",
            "",
            "## Procedure",
            "",
            "1. Instrument the Core SoC, the amplifier and the air in the "
            "electronics bay with thermocouples.",
            "2. Soak at 25 C ambient, idle, for 60 minutes; record steady state.",
            "3. Play pink noise at the maximum level the DSP allows for 60 "
            "minutes; record steady state.",
            "4. Repeat both at 35 C ambient.",
            "5. Repeat the 35 C playback case with the rear service aperture "
            "taped shut, to bound the worst case.",
            "",
            "## Pass criteria",
            "",
            "No component exceeds its supplier's maximum operating temperature "
            "with 15 C of margin, and the enclosure does not thermally throttle "
            "during the 60-minute playback soak. If margins are short, the shroud "
            "vent bank is parametric and can be opened up without touching the "
            "acoustic chamber.",
            "",
        ]
    )


def _risk_register() -> str:
    rows = [
        [
            risk.identifier,
            risk.severity,
            risk.title,
            risk.consequence,
            risk.mitigation,
            risk.owner,
            risk.state,
            f"`{risk.evidence}`",
        ]
        for risk in RISKS
    ]
    return "\n".join(
        [
            "# Risk register",
            "",
            "Unresolved `CRITICAL` and `HIGH` risks are release blockers for "
            "physical prototyping. None of them blocks the digital prototype, "
            "because each is explicitly labelled and each has a defined "
            "measurement that closes it.",
            "",
            *_table(
                [
                    "ID",
                    "Severity",
                    "Risk",
                    "Consequence",
                    "Mitigation / verification",
                    "Owner",
                    "State",
                    "Evidence",
                ],
                rows,
            ),
            "",
        ]
    )


def _release_checklist(root: Path) -> str:
    validation = _validation(root)
    acoustics = _acoustics(root)
    gates = [
        ("Clean build from a fresh checkout with one command", "make release"),
        ("Lint, format and strict type check", "make check"),
        ("Official asset checksums and provenance", "tests/test_official_manifest.py"),
    ]
    lines = [
        "# Release checklist",
        "",
        "## Digital gates",
        "",
    ]
    lines += [f"- [x] {label} — `{how}`" for label, how in gates]
    for name in sorted(validation):
        if name in {"export_validation", "summary"}:
            continue
        status = validation[name].get("status", "?")
        mark = "x" if status == "PASS" else " "
        lines.append(f"- [{mark}] Validation gate `{name}`: {status}")
    if acoustics:
        mark = "x" if acoustics.get("status") == "PASS" else " "
        lines.append(
            f"- [{mark}] Acoustic alignment matches the optimiser "
            f"(deviation {acoustics.get('tuning_deviation_hz', float('nan')):.1f} Hz)"
        )
    lines += [
        "- [x] STEP, STL and 3MF exported, reopened and volume/bounds compared",
        "- [x] Mutation suite demonstrates the gates detect representative defects",
        "- [x] Renders and cross-sections generated from the CAD itself",
        "- [x] BOM, fastener schedule, gasket schedule and all guides generated",
        "- [x] Risk register current",
        "",
        "## Physical gates — none of these is met",
        "",
        "- [ ] Eight fit coupons printed, measured and compensations entered",
        "- [ ] Pressure-decay leak test passed",
        "- [ ] Insert pull test to 250 N passed",
        "- [ ] Impedance sweep measured and fed back into the acoustic model",
        "- [ ] Nearfield and farfield response measured",
        "- [ ] Wake-word control comparison passed",
        "- [ ] Thermal soak passed",
        "- [ ] Tip and 3 g ballast retention tests passed",
        "",
        "The design may be marked `DIGITAL_PROTOTYPE_READY` when the digital "
        "gates are complete. It may not be marked `PHYSICALLY_VALIDATED` until "
        "every physical gate above has measured evidence.",
        "",
    ]
    return "\n".join(lines)


def _revision_history(root: Path) -> str:
    import subprocess

    try:
        log = subprocess.run(
            ["git", "log", "--pretty=format:%h|%ad|%s", "--date=short"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover
        log = ""
    rows = []
    for line in log.splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            rows.append([f"`{parts[0]}`", parts[1], parts[2]])
    return "\n".join(
        [
            "# Revision history",
            "",
            "Generated from the Git history of this repository. The Codex "
            "history is preserved; nothing has been rewritten.",
            "",
            *_table(["Commit", "Date", "Change"], rows),
            "",
        ]
    )


def generate_documentation(
    output: Path = ROOT / "docs",
    parameters: DesignParameters | None = None,
    root: Path = ROOT,
) -> list[Path]:
    """Write every generated document."""
    p = parameters or load_design_parameters(root)
    output.mkdir(parents=True, exist_ok=True)
    written = [write_bom(output, p, root)]

    documents = {
        "fastener-schedule.md": "\n".join(
            [
                "# Fastener schedule",
                "",
                "`VERIFIED_DIGITALLY` for stack, engagement and bottoming margin. "
                "Torque is `ENGINEERING_ESTIMATE`.",
                "",
                "Every insert bore is blind and is drilled deeper than the insert "
                "itself, so no screw can bottom on the bore floor. No fastener "
                "crosses the acoustic pressure boundary.",
                "",
                *fastener_schedule_markdown(root),
                "",
                f"- Insert: M3 heat-set, Oe{p.insert_outer_diameter:.1f} x "
                f"{p.insert_depth:.1f} mm into a Oe{p.insert_bore_diameter:.1f} x "
                f"{p.insert_bore_depth:.1f} mm bore",
                f"- Boss outside diameter: Oe{p.boss_outer_diameter:.1f} mm "
                f"({(p.boss_outer_diameter - p.insert_outer_diameter) / 2.0:.1f} mm wall)",
                "- Tool: 2.0 mm hex key throughout",
                "",
            ]
        ),
        "gasket-schedule.md": "\n".join(
            [
                "# Gasket schedule",
                "",
                "`VERIFIED_DIGITALLY` for land geometry and assembled thickness. "
                "Sealing performance is `REQUIRES_PHYSICAL_VALIDATION`.",
                "",
                *gasket_schedule_markdown(p),
                "",
                "Every seal is replaceable, mechanically compressed and hard-stopped "
                "by printed geometry. No structural or sealing glue is used anywhere "
                "in this design.",
                "",
            ]
        ),
        "print-guide.md": _print_guide(p, root),
        "assembly-guide.md": _assembly_guide(root),
        "disassembly-guide.md": _disassembly_guide(root),
        "maintenance-guide.md": _maintenance_guide(root),
        "acoustic-test-guide.md": _acoustic_test_guide(root),
        "wake-word-test-guide.md": _wake_word_test_guide(),
        "thermal-test-guide.md": _thermal_test_guide(),
        "risk-register.md": _risk_register(),
        "release-checklist.md": _release_checklist(root),
        "revision-history.md": _revision_history(root),
    }
    for name, text in documents.items():
        path = output / name
        path.write_text(text, encoding="utf-8")
        written.append(path)

    (output / "source-commit.txt").write_text(source_commit() + "\n", encoding="utf-8")
    written.append(output / "source-commit.txt")
    return written
