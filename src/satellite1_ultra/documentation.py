"""Generate the task-oriented builder documentation and authoritative schedules."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from satellite1_ultra.builder_files import (
    CALIBRATION_PRINT_ORDER,
    OFFICIAL_TOP_PRINT_ORDER,
    ULTRA_PRINT_ORDER,
)
from satellite1_ultra.configuration import (
    ROOT,
    load_design_parameters,
    selected_components,
)
from satellite1_ultra.exporting import PARTS, source_commit
from satellite1_ultra.geometry import DesignParameters, ballast_plate_extent
from satellite1_ultra.official import (
    OFFICIAL_PRINT_PARTS,
    OFFICIAL_PRINT_PARTS_REQUIRED,
)

EVIDENCE_DIGITAL = "VERIFIED_DIGITALLY"
EVIDENCE_OFFICIAL = "DERIVED_FROM_OFFICIAL_CAD"
EVIDENCE_DRAWING = "DERIVED_FROM_MANUFACTURER_DRAWING"
EVIDENCE_ESTIMATE = "ENGINEERING_ESTIMATE"
EVIDENCE_PHYSICAL = "REQUIRES_PHYSICAL_VALIDATION"


@dataclass(frozen=True)
class Risk:
    """One release risk with a closure action."""

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
        "Driver and radiator flange thicknesses are not dimensioned",
        "The clamp hard stop can under-compress or over-compress a gasket.",
        "Measure both purchased components, enter the values in "
        "config/physical_calibration.yaml, and pass both component coupons.",
        "builder",
        "OPEN",
        EVIDENCE_PHYSICAL,
    ),
    Risk(
        "R-02",
        "HIGH",
        "Core board placement is absent from the official assembled CAD",
        "A source-only claim of exact Core placement would be unsupported.",
        "The CAD reserves a Core-sized service volume. Confirm the official Core/HAT "
        "stack against the physical Batch 1 kit before closing the upper stack.",
        "builder",
        "OPEN",
        EVIDENCE_PHYSICAL,
    ),
    Risk(
        "R-03",
        "HIGH",
        "Low-frequency output is excursion limited",
        "Full amplifier voltage below tuning can exceed driver or radiator travel.",
        "Start with the documented fourth-order high-pass, verify polarity and tuning "
        "with an impedance sweep, then set DSP from measurements.",
        "builder",
        "OPEN",
        EVIDENCE_ESTIMATE,
    ),
    Risk(
        "R-04",
        "MEDIUM",
        "Printed walls and compressed seals have not been leak tested",
        "A leak can remove the expected passive-radiator bass response.",
        "Use the temporary leak-test adapter at 100-250 Pa, inspect every joint, and "
        "then confirm the final cable gland by impedance measurement.",
        "builder",
        "OPEN",
        EVIDENCE_PHYSICAL,
    ),
    Risk(
        "R-05",
        "MEDIUM",
        "Printer dimensional performance is unknown",
        "Nominal CAD clearances may become interference or loose fits.",
        "Complete all eight calibration checks and regenerate with "
        "make calibrated-release before any full-size print.",
        "builder",
        "OPEN",
        EVIDENCE_PHYSICAL,
    ),
    Risk(
        "R-06",
        "MEDIUM",
        "Wake-word, Wi-Fi, LED, and button performance are unmeasured",
        "The final enclosure can affect radio and acoustic behavior even when openings clear.",
        "Run the controlled bare-kit versus enclosed-kit commissioning tests.",
        "builder",
        "OPEN",
        EVIDENCE_PHYSICAL,
    ),
    Risk(
        "R-07",
        "MEDIUM",
        "Closed-shroud thermal behavior is unmeasured",
        "The Core or amplifier may throttle or exceed a safe temperature margin.",
        "Perform the documented 25 C and 35 C thermal soaks with instrumented hardware.",
        "builder",
        "OPEN",
        EVIDENCE_PHYSICAL,
    ),
    Risk(
        "R-08",
        "LOW",
        "Insert pullout strength depends on printer, material, and installation",
        "An insert can rotate or pull free during service.",
        "Select the coupon bore that installs square, torque-test it cold, and reserve "
        "the 250 N pull test for formal physical validation.",
        "builder",
        "OPEN",
        EVIDENCE_PHYSICAL,
    ),
    Risk(
        "R-09",
        "LOW",
        "Satellite1.1 / Batch 2 is not supported by this release",
        "Its external Wi-Fi antenna and service interfaces are not accommodated.",
        "Use only Batch 1 rev4.1 Core + rev4.1 HAT. Add a validated adapter before "
        "claiming Batch 2 compatibility.",
        "maintainer",
        "OPEN",
        EVIDENCE_OFFICIAL,
    ),
)


GASKETS: tuple[dict[str, str], ...] = (
    {
        "id": "G01",
        "name": "divider_gasket",
        "quantity": "1",
        "material": "2.0 mm closed-cell EPDM, soft, smooth skin",
        "hardness_density": "ASTM D1056 2A1 or equivalent; 6-11 lb/ft3",
        "target": "25% compression; allowed physical range 15%-45%",
        "cutting": "knife/plotter from GASKET_TEMPLATES/divider_gasket.dxf",
        "orientation": "continuous rounded rectangle; no cuts or splices",
        "replacement": "replace whenever the pressure divider is reopened",
    },
    {
        "id": "G02",
        "name": "driver_gasket",
        "quantity": "1",
        "material": "2.0 mm closed-cell EPDM, soft, smooth skin",
        "hardness_density": "ASTM D1056 2A1 or equivalent; 6-11 lb/ft3",
        "target": "25% compression; allowed physical range 15%-45%",
        "cutting": "knife/plotter from GASKET_TEMPLATES/driver_gasket.dxf",
        "orientation": "single annulus; center it behind the driver flange",
        "replacement": "replace whenever the active driver is removed",
    },
    {
        "id": "G03",
        "name": "passive_radiator_gasket",
        "quantity": "2",
        "material": "2.0 mm closed-cell EPDM, soft, smooth skin",
        "hardness_density": "ASTM D1056 2A1 or equivalent; 6-11 lb/ft3",
        "target": "25% compression; allowed physical range 15%-45%",
        "cutting": "knife/plotter from GASKET_TEMPLATES/passive_radiator_gasket.dxf",
        "orientation": "one continuous annulus behind each radiator flange",
        "replacement": "replace whenever that radiator is removed",
    },
    {
        "id": "G04",
        "name": "cable_gland",
        "quantity": "1",
        "material": "TPU 95A printed part",
        "hardness_density": "95A nominal",
        "target": "radial interference in divider and on both insulated conductors",
        "cutting": "not cut; print 3MF/cable_gland.3mf",
        "orientation": "flange toward electronics bay; slit faces rear",
        "replacement": "replace if torn, loose, or permanently distorted",
    },
)


def _validation(root: Path) -> dict[str, Any]:
    reports: dict[str, Any] = {}
    for path in sorted((root / "reports" / "validation").glob("*.json")):
        reports[path.stem] = json.loads(path.read_text(encoding="utf-8"))
    return reports


def _acoustics(root: Path) -> dict[str, Any]:
    path = root / "reports" / "acoustics" / "summary.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    lines.extend("| " + " | ".join(value.replace("|", "/") for value in row) + " |" for row in rows)
    return "\n".join(lines)


def fastener_rows(root: Path = ROOT) -> list[dict[str, Any]]:
    return list(_validation(root).get("fasteners", {}).get("schedule", []))


def bill_of_materials(parameters: DesignParameters, root: Path = ROOT) -> list[dict[str, str]]:
    """Return the user-facing purchasing and manufactured-parts list."""
    driver, radiator = selected_components(root)
    fasteners = fastener_rows(root)
    plate_w, plate_d, plate_t = ballast_plate_extent(parameters)
    added_mass = _acoustics(root).get("added_pr_mass_each_g", 0.0)
    total_inserts = sum(
        int(row["quantity"]) * (2 if "(each)" in str(row["joint"]) else 1)
        for row in fasteners
        if str(row["insert"]).startswith("M3 heat-set")
    )
    rows: list[dict[str, str]] = []
    for index, (name, definition) in enumerate(PARTS.items(), start=1):
        if name in {"divider_gasket", "driver_gasket", "passive_radiator_gasket"}:
            continue
        category = "calibration part" if name.startswith("coupon_") else "printed part"
        if name == "leak_test_adapter":
            category = "service tool"
        rows.append(
            {
                "id": f"P{index:02d}",
                "category": category,
                "item": name,
                "specification": f"{definition.material}; exact file 3MF/{name}.3mf",
                "quantity": str(definition.quantity),
                "required": "yes",
                "evidence": EVIDENCE_DIGITAL,
                "source": "this release",
            }
        )
    rows.extend(
        [
            {
                "id": "A01",
                "category": "active driver",
                "item": f"{driver['manufacturer']} {driver['model']}",
                "specification": "4 ohm full-range driver; manufacturer model ND91-4",
                "quantity": "1",
                "required": "yes",
                "evidence": EVIDENCE_DRAWING,
                "source": str(driver["source"]),
            },
            {
                "id": "A02",
                "category": "passive radiator",
                "item": f"{radiator['manufacturer']} {radiator['model']}",
                "specification": "4 inch aluminum passive radiator with M6 mass post",
                "quantity": "2",
                "required": "yes",
                "evidence": EVIDENCE_DRAWING,
                "source": str(radiator["source"]),
            },
            {
                "id": "E01",
                "category": "official electronics",
                "item": "FutureProofHomes Satellite1 Batch 1 development kit",
                "specification": "Core rev4.1 + HAT rev4.1 / R2024.12.06; not Satellite1.1",
                "quantity": "1",
                "required": "yes",
                "evidence": EVIDENCE_OFFICIAL,
                "source": "reference-assets/MANIFEST.csv",
            },
            {
                "id": "H01",
                "category": "insert",
                "item": "CNC Kitchen M3 x 5.7 heat-set insert",
                "specification": "M3x0.5 internal thread, 5.7 mm length, 4.6 mm maximum OD",
                "quantity": str(total_inserts + 4),
                "required": "yes; includes four spares",
                "evidence": EVIDENCE_DRAWING,
                "source": "CNCKitchen M3 x 5.7 standard insert",
            },
            {
                "id": "H02",
                "category": "speaker cable",
                "item": "2-pin JST-XH 2.54 mm speaker lead",
                "specification": "22 AWG stranded red/black, each insulated conductor OD <=1.8 mm, 350 mm minimum",
                "quantity": "1",
                "required": "yes",
                "evidence": EVIDENCE_OFFICIAL,
                "source": "official Squircle enclosure documentation",
            },
            {
                "id": "H03",
                "category": "speaker terminals",
                "item": "2.8 mm fully insulated female quick-disconnects",
                "specification": "for 22-18 AWG wire; verify fit on the purchased ND91-4 before crimping",
                "quantity": "2",
                "required": "recommended; direct solder is acceptable",
                "evidence": EVIDENCE_ESTIMATE,
                "source": "builder supplied",
            },
            {
                "id": "B01",
                "category": "ballast",
                "item": "mild-steel plate",
                "specification": (
                    f"{plate_w:.0f} x {plate_d:.0f} x {plate_t / 2.0:.0f} mm, "
                    "edges deburred, dry, light oil removed"
                ),
                "quantity": "2",
                "required": "yes",
                "evidence": EVIDENCE_ESTIMATE,
                "source": "local metal supplier",
            },
            {
                "id": "B02",
                "category": "radiator tuning",
                "item": "M6 stainless flat washers",
                "specification": f"identical stacks totaling {added_mass:.2f} g per radiator",
                "quantity": "2 matched stacks",
                "required": "yes; final mass requires physical tuning",
                "evidence": EVIDENCE_ESTIMATE,
                "source": "weigh on 0.01 g scale",
            },
            {
                "id": "G00",
                "category": "gasket stock",
                "item": "closed-cell EPDM foam sheet",
                "specification": "2.0 mm nominal, soft, smooth skin, ASTM D1056 2A1 or equivalent",
                "quantity": "one 300 x 300 mm sheet",
                "required": "yes",
                "evidence": EVIDENCE_ESTIMATE,
                "source": "industrial rubber supplier",
            },
            {
                "id": "D01",
                "category": "optional acoustic material",
                "item": "polyester acoustic batting",
                "specification": "not installed in RC1; reserve for measurement-led development only",
                "quantity": "0",
                "required": "no",
                "evidence": EVIDENCE_PHYSICAL,
                "source": "not applicable",
            },
        ]
    )
    for part in OFFICIAL_PRINT_PARTS:
        rows.append(
            {
                "id": part.identifier,
                "category": "official printed part",
                "item": part.name,
                "specification": (
                    f"{part.material}; exact file OFFICIAL_PARTS/"
                    f"{'REQUIRED_SINGLE_MATERIAL' if part.required else 'OPTIONAL_MULTI_MATERIAL'}"
                    f"/{part.filename}; preserved official STL"
                ),
                "quantity": str(part.quantity),
                "required": "yes" if part.required else "optional alternative",
                "evidence": EVIDENCE_OFFICIAL,
                "source": part.stl_relative_path,
            }
        )
    for row in fasteners:
        multiplier = 2 if "(each)" in str(row["joint"]) else 1
        rows.append(
            {
                "id": str(row["id"]),
                "category": "fastener",
                "item": f"M3 x {int(row['length_mm'])} {row['head']} screw",
                "specification": f"{row['standard']}, A2-70 stainless, M3x0.5",
                "quantity": str(int(row["quantity"]) * multiplier),
                "required": "yes",
                "evidence": EVIDENCE_DIGITAL,
                "source": "industrial fastener supplier",
            }
        )
    return rows


ASSEMBLY_STEPS: tuple[dict[str, str], ...] = (
    {
        "number": "1",
        "title": "Identify and inspect the hardware",
        "parts": (
            "Batch 1 Core rev4.1 and HAT rev4.1; O01 official_mid_plate; "
            "O02 official_mid_plate_threads; O03 official_pcb_spacer; O04 "
            "official_lock_ring; O05 official_top_plate; O06 "
            "official_top_plate_snap_in_diffuser_ring"
        ),
        "fasteners": "none",
        "tools": "bright light; calipers",
        "gasket": "none",
        "action": "Confirm the board revision labels. Reject Batch 2 / Satellite1.1. Check off all six required official filenames in OFFICIAL_PARTS/REQUIRED_SINGLE_MATERIAL and every required custom 3MF in the Printing Guide. Inspect every sealing face and remove strings without rounding an edge.",
        "pass": "Correct Batch 1 hardware and every required printed part are present; no crack, warp, blocked bore, or damaged gasket land.",
        "warning": "Do not force or approximately place the Core. Its exact stack placement requires the physical official hardware.",
        "image": "IMAGES/assembly_stage_01_identify.png",
    },
    {
        "number": "2",
        "title": "Install and cold-check all M3 inserts",
        "parts": "main_cabinet, pressure_divider, base_skirt, ballast_cartridge, outer_shell",
        "fasteners": "H01 inserts",
        "tools": "temperature-controlled iron; M3 insert tip; square",
        "gasket": "none",
        "action": "At 250-270 C, press each insert into its labeled blind bore until flush and square. Let every insert cool for five minutes. Thread an M3 screw by hand for three turns.",
        "pass": "No insert spins, tilts, protrudes, or blocks before three turns.",
        "warning": "Do not torque a hot insert. Fumes and the iron can burn; ventilate and use eye protection.",
        "image": "IMAGES/assembly_stage_02_inserts.png",
    },
    {
        "number": "3",
        "title": "Wire and clamp the active driver",
        "parts": "main_cabinet, Dayton ND91-4, driver_gasket, active_driver_clamp_ring, JST-XH lead",
        "fasteners": "F04, 4 screws",
        "tools": "2.0 mm hex; crimper or soldering iron; polarity tester",
        "gasket": "G02",
        "action": "Mark the red conductor positive. Connect red to the terminal marked + and black to -. Face the terminals upward. Center G02, seat the driver from the -Y/front side, fit the clamp ring, and tighten F04 in two diagonal passes to 0.35 N m; never exceed 0.45 N m.",
        "pass": "Ring bottoms evenly; gasket is not visible in the bore; cone moves outward on a brief 1.5 V positive polarity pulse.",
        "warning": "Use only a brief low-voltage polarity pulse. Never connect a loose driver to the powered HAT.",
        "image": "IMAGES/assembly_stage_03_driver.png",
    },
    {
        "number": "4",
        "title": "Mass-match and clamp both passive radiators",
        "parts": "2 SB12PACR-00, 2 passive_radiator_gaskets, 2 clamp rings, matched M6 washer stacks",
        "fasteners": "F05, 8 screws total",
        "tools": "0.01 g scale; 2.0 mm hex",
        "gasket": "G03, one per side",
        "action": "Weigh two identical tuning stacks to the value in reports/acoustics/summary.json. Secure one to each M6 post. Install radiators on +/-X with matching orientation, then tighten each F05 crosswise to 0.35 N m; never exceed 0.45 N m.",
        "pass": "Added masses match within 0.02 g; both rings bottom evenly; surrounds move freely and do not touch the shell keep-out.",
        "warning": "Unequal mass defeats reaction-force cancellation. Do not press on either cone.",
        "image": "IMAGES/assembly_stage_04_radiators.png",
    },
    {
        "number": "5",
        "title": "Route the cable, close the divider, and leak-check",
        "parts": "pressure_divider, divider_gasket, leak_test_adapter, cable_gland",
        "fasteners": "F03, 8 screws",
        "tools": "2.0 mm hex; hand bulb; 0-500 Pa gauge; leak-detection solution",
        "gasket": "G01; temporary adapter then G04",
        "action": "Pass both conductors through the divider. Fit the temporary adapter over them, place G01 without twists, and tighten F03 in a star pattern to 0.35 N m. Apply only 100-250 Pa with a hand bulb. Brush leak solution on external gasket seams; no bubbles are allowed. Vent, pull the adapter upward, and install G04 with its flange toward the electronics bay.",
        "pass": "No growing bubbles, abnormal diaphragm displacement, or audible leak; final gland cannot rotate or lift by finger force.",
        "warning": "Never use shop air, never exceed 250 Pa, and keep liquid away from electronics. This is a gross-leak screen, not an acoustic-Q measurement.",
        "image": "IMAGES/assembly_stage_05_sealing.png",
    },
    {
        "number": "6",
        "title": "Install the base and retained ballast",
        "parts": "base_skirt, ballast_cartridge, 2 steel plates, ballast lid, bottom_service_plate",
        "fasteners": "F06, F07, F08",
        "tools": "2.0 mm hex; scale",
        "gasket": "none",
        "action": "Attach the base skirt with F07. Place both deburred dry plates flat in the cartridge; there must be no rocking. Install the lid with F06, insert the cartridge from below, and capture it with the bottom service plate using F08.",
        "pass": "Cartridge mass is approximately 1054 g; no plate moves when shaken gently; all four lid screws engage at least 3 mm.",
        "warning": "The steel stack is heavy. Keep fingers clear and do not operate the unit without the retained lid and service plate.",
        "image": "IMAGES/assembly_stage_06_ballast.png",
    },
    {
        "number": "7",
        "title": "Install and lock the outer shell",
        "parts": "outer_shell; lower assembly",
        "fasteners": "F09, 4 screws with nylon washers",
        "tools": "2.0 mm hex",
        "gasket": "none",
        "action": "Align FRONT with -Y and slide the shell downward without touching either surround. Invert on a soft mat and install F09 through the bottom service plate into the shell bosses.",
        "pass": "Every slot is clear; shell has an even reveal and at least 2 mm moving-part clearance; no wire is visible near a cone.",
        "warning": "Stop if the shell contacts a clamp ring or surround. Do not flex the shell over an obstruction.",
        "image": "IMAGES/assembly_stage_07_shell.png",
    },
    {
        "number": "8",
        "title": "Install the shroud and official Batch 1 upper stack",
        "parts": "electronics_shroud; O01-O06 official prints; Batch 1 HAT/Core",
        "fasteners": "F01, F02, F10, and F11; 4 of each",
        "tools": "2.0 mm hex; ESD-safe bench",
        "gasket": "none; electronics bay is outside the acoustic chamber",
        "action": "Bolt the shroud to its four outboard bosses with F02. Seat O01 on the four measured divider bosses and install F01. Snap O06 into O05 (or use both O07/O08 during a multi-material O05 print; never install O06 and O08 together). Align O03's taller standoffs with the I/O side and locate the HAT. Install the Core/HAT using the official Batch 1 sequence. Align the logos and I/O on O04/O05, engage the snaps, and rotate the lock ring. Align O02's four nubs with O01 and keep I/O toward rear/+Y. Connect the keyed JST-XH speaker plug before closure.",
        "pass": "Mid-plate sits on all four bosses; USB-C remains reachable; cable has service slack and cannot enter a moving-part envelope; buttons click and diffuser/LED apertures remain clear.",
        "warning": "Core placement is REQUIRES_PHYSICAL_VALIDATION. Follow the official Batch 1 instructions and stop at any collision; do not improvise a transform from the CAD envelope.",
        "image": "IMAGES/assembly_stage_08_upper.png",
    },
    {
        "number": "9",
        "title": "Fit the anti-slip ring and complete inspection",
        "parts": "anti_slip_ring; complete assembly",
        "fasteners": "none",
        "tools": "hands; flashlight",
        "gasket": "inspect G01-G04",
        "action": "Stretch the TPU ring evenly around the bottom rim. Set the unit upright and inspect all seams, fastener heads, slots, cable exits, buttons, and moving components.",
        "pass": "Unit stands without rocking; no rattle is heard during gentle handling; every fastener is present and every seal is continuously compressed.",
        "warning": "Do not power the unit until the commissioning checklist is ready.",
        "image": "IMAGES/assembly_stage_09_final.png",
    },
)


def _phase_table() -> str:
    """The whole build on one page, so a builder always knows where they are."""
    return _markdown_table(
        ["Phase", "What you do", "Roughly how long"],
        [
            ["1", "Check your printer and buy the parts", "ordering time"],
            ["2", "Print 8 small calibration pieces", "4-6 hours"],
            ["3", "Measure them and correct the files", "1 hour"],
            ["4", "Print 12 Ultra parts and 6 Satellite top parts", "3-5 days"],
            ["5", "Cut 3 foam gaskets from the templates", "30 minutes"],
            ["6", "Lay out and check every part", "30 minutes"],
            ["7", "Assemble, in 9 numbered steps", "3-4 hours"],
            ["8", "Test before you use it normally", "2 hours"],
        ],
    )


def _build_book(parameters: DesignParameters, root: Path) -> str:
    """The single front-to-back builder document.

    Everything a builder needs, in the order they need it.  The specialist
    guides stay as reference; this book never says "look it up elsewhere" for a
    step you must actually perform.
    """
    acoustics = _acoustics(root)
    calibration_rows = [
        [filename, str(quantity), "ASA" if source != "cable_gland" else "TPU 95A"]
        for source, filename, quantity in CALIBRATION_PRINT_ORDER
    ]
    ultra_rows = [
        [filename, str(quantity), "TPU 95A" if source == "anti_slip_ring" else "ASA"]
        for source, filename, quantity in ULTRA_PRINT_ORDER
    ]
    official_rows = [
        [filename, str(quantity), "ASA"] for _source, filename, quantity in OFFICIAL_TOP_PRINT_ORDER
    ]
    gasket_rows = [
        [
            row["id"],
            row["name"],
            row["quantity"],
            row["material"],
            row["cutting"].split(" from ")[-1],
        ]
        for row in GASKETS
        if row["id"] != "G04"
    ]
    assembly_lines: list[str] = []
    for step in ASSEMBLY_STEPS:
        assembly_lines.extend(
            [
                f"### Step {step['number']} of 9 — {step['title']}",
                "",
                f"![Build step {step['number']}: {step['title']}]({step['image']})",
                "",
                f"**You need:** {step['parts']}",
                "",
                f"**Screws:** {step['fasteners']}   **Seal:** {step['gasket']}   "
                f"**Tools:** {step['tools']}",
                "",
                f"**Do this:** {step['action']}",
                "",
                f"**It is right when:** {step['pass']}",
                "",
                f"> Careful: {step['warning']}",
                "",
            ]
        )
    assembly_block = "\n".join(assembly_lines)
    return f"""# The Satellite1 Ultra Build Book

> **DO NOT PRINT THE FULL ENCLOSURE YET.**
> **PRINT AND MEASURE THE 8 SMALL CALIBRATION PIECES FIRST.**

This is the only document you need to follow from start to finish. Work through
the phases in order. Every other guide in this package is reference material
that this book points you to at the moment you need it.

You are building a serviceable passive-radiator speaker enclosure around the
FutureProofHomes Satellite1 **Batch 1** development kit: Core rev4.1 and HAT
rev4.1 / R2024.12.06. Satellite1.1 / Batch 2 does not fit and is not supported.

Expected difficulty is 4 out of 5. Nothing here is glued; every joint is a
screw into a brass insert, so you can open the unit again later.

![The finished Satellite1 Ultra, assembled](IMAGES/assembly_iso.png)

## The whole build at a glance

{_phase_table()}

## Status you should know before you start

Every gate in this repository is a **digital** check: geometry, clearances,
volumes, exports, and documents. No physical unit has been built and measured.
Fit, sealing, acoustic output, thermals, Wi-Fi, microphones, buttons, LEDs, and
wake-word behaviour are all `REQUIRES_PHYSICAL_VALIDATION`. Your calibration,
leak, and commissioning checks in phases 3 and 8 are part of the build, not
optional extras.

---

# Phase 1 — Check your printer and buy the parts

## Your printer must actually fit the shell

The outer shell is the limiting part at **192 x 212 x 189 mm**, printed
upright. You therefore need **212 x 192 x 189 mm of genuinely usable travel**
(X and Y may be swapped).

- A 220 x 220 x 200 mm printer works only if the whole bed is usable. That
  leaves about 4 mm per long-side edge and limits the shell brim to 3 mm.
- Purge lines, bed clips, and firmware exclusion zones all steal usable travel.
  Measure what your machine really reaches before you commit.
- Rotating the shell in-plane does not make it fit a 210 x 210 mm bed, and
  printing it on its side is not supported.

You also need an enclosed printer, a 0.4 mm nozzle, and dry filament.

## Materials

- **ASA** for every rigid part. **PETG** is a documented alternative.
- **TPU 95A** for the two flexible parts: the cable seal and the bottom grip.
- **PLA+** is only acceptable for a display mock-up, never a finished unit.

## Tools

Digital calipers reading 0.01 mm, a scale reading 0.01 g, a 2.0 mm hex driver,
a temperature-controlled soldering iron with an M3 heat-set-insert tip,
wire strippers and a crimper or soldering iron, ESD protection, a hand bulb
with a 0-500 Pa gauge, and leak-detection solution.

## What to buy

Buy every item marked required in `BOM.csv`. The essentials are:

- One FutureProofHomes Satellite1 Batch 1 kit (E01).
- One Dayton Audio ND91-4 speaker (A01).
- Two SB Acoustics SB12PACR-00 passive radiators (A02).
- M3 heat-set inserts, with four spares (H01).
- Every M3 screw in `FASTENERS.csv`.
- One 300 x 300 mm sheet of 2.0 mm closed-cell EPDM foam (G00).
- Two mild-steel ballast plates (B01).
- Two matched M6 washer stacks for radiator tuning (B02).
- One 2-pin JST-XH speaker lead (H02).

`HARDWARE_AND_MATERIALS_GUIDE.pdf` gives the full specification for each line.

> Do not print the official original speaker chamber, speaker plate, or
> anti-slip ring. The Ultra parts replace all three.

---

# Phase 2 — Print the 8 calibration pieces

These are small. They exist so you discover your printer's real dimensional
behaviour before you spend days of filament on the big parts.

Open `PRINT_THESE_FILES/1_CALIBRATION_FIRST` and print every file, one at a
time, using the exact settings you will use for the enclosure:

{_markdown_table(["File", "Print this many", "Material"], calibration_rows)}

Baseline settings: 0.4 mm nozzle, 0.20 mm layers, five walls, six top and six
bottom layers, 35% gyroid infill, no supports, 5 mm brim on the rigid pieces.
ASA runs 250-260 C nozzle and 100-110 C bed with the enclosure closed. PETG
runs 235-250 C nozzle and 75-85 C bed.

---

# Phase 3 — Measure the pieces and correct the files

This is the step that makes the big parts fit. `CALIBRATION_GUIDE.pdf` shows
exactly where each caliper jaw goes; the images below name each check.

![Where to measure the Satellite top fit piece](IMAGES/calibration_official_interface.png)

![Using the screw and insert as go/no-go gauges](IMAGES/calibration_fasteners.png)

![Checking the speaker seats by hand](IMAGES/calibration_driver.png)

![Checking a radiator seats by hand](IMAGES/calibration_radiator.png)

![Squeezing the foam between the two gasket pieces](IMAGES/calibration_gasket.png)

![Fitting the two real wires through the cable seal](IMAGES/calibration_cable.png)

## The eight checks

{
        _markdown_table(
            ["Check", "What you do", "It passes when"],
            [
                [
                    "XY scale",
                    "Inside caliper jaws across the engraved 110.60 mm recess, at three heights",
                    "110.40-110.80 mm after correction",
                ],
                [
                    "Z scale",
                    "Outside jaws across a clean 3.00 mm edge, at four corners",
                    "2.90-3.10 mm",
                ],
                [
                    "Screw clearance",
                    "Try a clean M3 screw in the 3.4, 3.5 and 3.6 mm holes",
                    "smallest hole the screw falls through without force",
                ],
                [
                    "Insert bore",
                    "Install identical inserts into the 4.0-4.3 mm blind bores",
                    "square and flush, no crack, no spin",
                ],
                [
                    "Speaker fit",
                    "Seat the real ND91-4 in its test ring",
                    "drops in by hand, flange lies flat, play under 0.30 mm",
                ],
                [
                    "Radiator fit",
                    "Seat one real SB12PACR-00 in its test ring",
                    "drops in by hand, flange lies flat, play under 0.30 mm",
                ],
                [
                    "Gasket squeeze",
                    "Clamp a strip of your actual foam until both hard stops touch",
                    "15%-45% compression, no light path, foam not cut",
                ],
                [
                    "Cable seal",
                    "Push the two real conductors and the TPU seal into the test hole",
                    "moderate finger force, seal cannot rotate or lift",
                ],
            ],
        )
    }

Do not measure a 3-4 mm hole with caliper tips. The screw and the insert are
the gauges.

## Enter your numbers

You have three ways to turn those measurements into corrected files. All three
produce the same `physical_calibration.yaml`.

1. **In your browser (easiest).** Open the calibration wizard page listed in
   the project README, type in what you measured, and it computes and
   downloads the file for you. Nothing to install.
2. **On GitHub.** Paste the file contents into the "Calibrated build" workflow
   and GitHub rebuilds the whole corrected package for you to download.
3. **On your own computer.** Run `python scripts/calibrate.py`, which asks the
   same questions and then runs `make calibrated-release`.

Reprint every calibration piece affected by a correction you entered, and
re-check it. Continue only when all eight checks pass on corrected pieces.

> If a piece fails, do not sand it and do not "make it work". Correct the
> number, regenerate, and reprint. Sanding a sealing face destroys the seal.

---

# Phase 4 — Print every enclosure part

Now print the real parts. Open `PRINT_THESE_FILES/2_ULTRA_ENCLOSURE_PARTS`
and print every file:

{_markdown_table(["File", "Print this many", "Material"], ultra_rows)}

Note that the radiator clamp ring is the only part you print **twice**.

![The outer shell, positioned on the bed](IMAGES/print_orientation_outer_shell.png)

Then open `PRINT_THESE_FILES/3_SQUIRCLE_TOP_PARTS` and print all six official
Satellite top parts. These are not optional; they complete the normal
Satellite top:

{_markdown_table(["File", "Print this many", "Material"], official_rows)}

`PRINTING_GUIDE.pdf` holds the full slicer baseline, the per-part orientation
sheets, and the inspection checklist. Check each part as it comes off the bed:
gasket lands must be continuous and unbroken, shell slots must all be open,
clamp rings must be flat within 0.20 mm, and no insert bore may have opened
into the chamber.

---

# Phase 5 — Cut the three foam gaskets

The gaskets are not printed. You cut them from your 2.0 mm EPDM sheet using the
1:1 templates in `GASKET_TEMPLATES/`. Print each template at exactly 100% scale
(no "fit to page"), check the printed size against the sheet, then cut with a
sharp knife or a cutting plotter.

{
        _markdown_table(
            ["ID", "Seal", "How many", "Material", "Template"],
            gasket_rows,
        )
    }

The fourth seal, G04, is the flexible cable seal you already printed in TPU as
`08_FLEXIBLE_CABLE_SEAL_TPU.3mf`.

Each gasket must be one continuous piece. Do not splice, join, or stretch a
gasket to fit.

![Where each of the four seals sits](IMAGES/gasket_placement.png)

---

# Phase 6 — Lay out and check every part

Put everything on a clean table and account for it before you start. The
diagram below names every single piece and tells you which file it came from
or which item you purchased.

![Every part in the build, with its file name](IMAGES/exploded_parts_identification.png)

Check that you have all of it:

- All 12 printed Ultra parts, with two radiator clamp rings.
- All 6 printed Satellite top parts.
- One ND91-4 speaker and two SB12PACR-00 radiators.
- Three cut foam gaskets and one printed TPU cable seal.
- Every screw and insert in `FASTENERS.csv`.
- Two steel ballast plates, deburred and dry.
- Two matched radiator tuning stacks, weighed to
  {acoustics.get("added_pr_mass_each_g", 0):.2f} g each.
- One red/black speaker lead with the correct plug.

The screws all look similar, so identify them by length before you begin:

![Screw lengths and where each one is used](IMAGES/fastener_identification.png)

Do not begin assembly with a missing part.

---

# Phase 7 — Assemble

Nine steps, in this order. Each one shows what to install, which screws to use,
which seal it captures, and how to tell it is right.

Tighten every screw into a printed part gently, using the short arm of the
2 mm hex key: 0.35 N m is the target and 0.45 N m is the absolute maximum.
Stop as soon as the parts meet evenly. Do not keep turning "for luck".

{assembly_block}

---

# Phase 8 — Test before you use it

Complete every check in `TESTING_AND_COMMISSIONING_GUIDE.pdf`. The short
version:

- The gentle 100-250 Pa leak screen shows no growing bubble at any seal.
- The speaker cone moves outward on a brief positive polarity pulse.
- Both radiators move freely and never scrape.
- Every button clicks once and returns.
- Every LED segment lights evenly.
- All four microphones work.
- USB-C plugs in and out without touching the shell.
- Wi-Fi connects, and you have recorded the signal beside a bare kit.
- There is no buzz, rattle, air whistle, overheating, or softened plastic.

Never use shop air on this enclosure, and never exceed 250 Pa.

Stop using the unit if any check fails. Fix the cause and repeat the test.

---

# Phase 9 — Opening it again later

Disconnect power and wait five minutes. `MAINTENANCE_GUIDE.pdf` gives the safe
removal order for each subassembly.

![The order things come apart in](IMAGES/service_disassembly.png)

Replace any gasket you disturb. Never cut a wire to get a part out, and never
reuse a torn or permanently flattened seal.

---

# If something goes wrong

{
        _markdown_table(
            ["Symptom", "Most likely cause", "What to do"],
            [
                [
                    "Calibration piece is warped",
                    "chamber too cool, or bed not clean",
                    "fix the printer and reprint; never compensate for a warped part",
                ],
                [
                    "Every hole is too small",
                    "over-extrusion or elephant-foot compensation",
                    "fix flow and first-layer compensation before adding a CAD offset",
                ],
                [
                    "Insert cracks the boss",
                    "bore too small or iron too hot",
                    "choose a larger bore or reduce dwell; never add torque",
                ],
                [
                    "Speaker will not sit flat",
                    "print strings, or cutout too small",
                    "remove strings only; correct the cutout and reprint the coupon",
                ],
                [
                    "Cable seal leaks or spins",
                    "conductor too thick, or wet TPU",
                    "confirm conductor OD is 1.8 mm or less, dry the TPU, reprint",
                ],
                [
                    "Shell will not slide on",
                    "clamp ring or surround contact",
                    "stop immediately; find the contact rather than forcing the shell",
                ],
                [
                    "Bubbles during the leak check",
                    "gasket twisted, pinched, or a screw left loose",
                    "vent, reopen, replace the gasket, and reseat evenly",
                ],
                [
                    "One radiator moves more than the other",
                    "unequal tuning mass",
                    "reweigh both stacks; they must match within 0.02 g",
                ],
            ],
        )
    }

---

# What is still unproven

The geometry, exports, schedules, and documents in this release pass their
digital gates. No completed physical unit has been measured. That means your
own calibration, leak, acoustic, thermal, Wi-Fi, and microphone checks are the
first real evidence this design works. Record what you find.

`ENGINEERING_APPENDIX.md` lists every open risk, its consequence, and how to
close it.
"""


def _calibration_guide() -> str:
    return """# Mandatory Physical Calibration Guide

> **DO NOT PRINT THE FULL ENCLOSURE YET.**
> **PRINT AND COMPLETE THE CALIBRATION PARTS FIRST.**

Use the same material, nozzle, layer height, wall count, extrusion settings,
bed preparation, and chamber temperature that you will use for the enclosure.

## Print first

Print these exact files from `CALIBRATION_PARTS/`:

1. `coupon_official_interface.3mf`
2. `coupon_heat_set_insert.3mf`
3. `coupon_active_driver.3mf`
4. `coupon_passive_radiator.3mf`
5. `coupon_gasket_base.3mf`
6. `coupon_gasket_cap.3mf`
7. `coupon_cable_passage.3mf`
8. `cable_gland.3mf` in TPU 95A

ASA baseline: 0.4 mm nozzle, 0.20 mm layers, five walls, six top/bottom
layers, 35% gyroid, 100-110 C bed, 250-260 C nozzle, enclosure closed, no
supports, 5 mm brim. PETG alternative: 235-250 C nozzle, 75-85 C bed,
three-hour dry cycle if stringing is present.

## Measure and enter values

Use the engraved labels and `IMAGES/calibration_*.png`.

| Check | Where/how | Nominal | Pass | Input key |
|---|---|---:|---|---|
| XY scale | Inside jaws across `MEASURE XY 110.60` recess, three heights | 110.60 mm | 110.40-110.80 mm after correction | `xy_scale_correction_fraction = 110.60 / measured - 1` |
| Z scale | Outside jaws across clean 3.00 mm coupon edge, four corners | 3.00 mm | 2.90-3.10 mm | `z_scale_correction_fraction = 3.00 / measured - 1` |
| M3 clearance | Try a clean ISO M3 screw in labeled 3.4/3.5/3.6 holes | 3.4 mm | smallest hole that falls through without force | chosen diameter minus 3.4 |
| Insert bore | Install identical inserts in 4.0/4.1/4.2/4.3 blind bores | 4.2 mm | square, flush, no crack/spin at 0.35 N m | chosen diameter minus 4.2 |
| Driver fit | Seat the purchased ND91-4 in the labeled coupon | catalog interface | drops in by hand, <=0.30 mm radial play, flange lies flat | cutout correction and measured flange thickness |
| Radiator fit | Seat one SB12PACR-00 in the labeled coupon | catalog interface | drops in by hand, <=0.30 mm radial play, flange lies flat | cutout correction and measured flange thickness |
| Gasket | Tighten cap on a strip of the actual sheet until both stops contact | 2.00 to 1.50 mm | 15%-45% compression; no open light path | sheet thickness and compressed-thickness offset |
| Cable gland | Fit actual two 22 AWG conductors and gland in cable coupon | 8.0 mm passage | moderate finger force; gland cannot rotate or lift | cable-passage offset |

Do not use caliper tips to measure a 3-4 mm hole; the screw and insert are the
functional gauges. Enter only values you measured.

## CAD measurement illustrations

![Official-interface XY and Z measurement](IMAGES/calibration_official_interface.png)

![M3 screw and insert functional gauges](IMAGES/calibration_fasteners.png)

![Active-driver coupon fit check](IMAGES/calibration_driver.png)

![Passive-radiator coupon fit check](IMAGES/calibration_radiator.png)

![Gasket compression coupon stack](IMAGES/calibration_gasket.png)

![Cable passage and TPU gland check](IMAGES/calibration_cable.png)

## Edit one file

Copy `CALIBRATION_INPUT_TEMPLATE.yaml` to
`config/physical_calibration.yaml`, or run:

```text
python scripts/calibrate.py
```

The file exposes only user-facing corrections. Safe limits reject implausible
values before any full part is built.

## Regenerate

```text
make calibrated-release
```

Success ends with all validation, documentation, mutation, and package checks
passing. Output is in `release/Satellite1-Ultra-RC1/`.

Example successful finish:

```text
documentation PASS; 9 guides, 7 PDFs
release/Satellite1-Ultra-RC1 (all required files present)
```

Reprint every coupon affected by a nonzero correction. You are cleared for the
full enclosure only when all eight checks above pass on the corrected coupons.

## Common failures

- Warped official coupon: improve enclosure temperature, clean the bed, add the
  brim, and do not compensate a warped part.
- Every hole undersized: check flow and elephant-foot compensation before
  adding a large CAD offset.
- Insert cracks the boss: choose a larger coupon bore or reduce iron dwell; do
  not increase torque.
- Component will not sit flat: remove only print strings. Do not sand a sealing
  land; correct the cutout and reprint the coupon.
- Gland leaks or spins: verify conductor OD <=1.8 mm, dry TPU, then correct and
  reprint both the coupon and gland.
"""


def _printing_guide(parameters: DesignParameters, root: Path) -> str:
    report = _validation(root).get("printability", {})
    rows: list[list[str]] = []
    for record in report.get("parts", []):
        name = str(record["part"])
        if name in {"divider_gasket", "driver_gasket", "passive_radiator_gasket"}:
            continue
        group = (
            "calibration"
            if name.startswith("coupon_") or name == "cable_gland"
            else "service tool"
            if name == "leak_test_adapter"
            else "cosmetic"
            if name in {"outer_shell", "electronics_shroud", "anti_slip_ring"}
            else "structural"
        )
        brim = (
            "10 mm"
            if name == "main_cabinet"
            else "3 mm maximum on a 220 mm bed"
            if name == "outer_shell"
            else "5 mm"
            if group == "calibration"
            else "none"
        )
        difficulty = "5/5" if name == "outer_shell" else "4/5" if name == "main_cabinet" else "2/5"
        rows.append(
            [
                group,
                f"{name}.3mf",
                str(PARTS[name].quantity),
                str(record["material"]),
                str(record["print_orientation"]),
                "none",
                brim,
                difficulty,
                "yes" if group != "calibration" else "first",
            ]
        )
    orientation_images = "\n\n".join(
        f"![{name} print orientation](IMAGES/print_orientation_{name}.png)"
        for name in PARTS
        if name not in {"divider_gasket", "driver_gasket", "passive_radiator_gasket"}
    )
    official_rows = [
        [
            "official required",
            f"OFFICIAL_PARTS/REQUIRED_SINGLE_MATERIAL/{part.filename}",
            str(part.quantity),
            part.material,
            "lowest native-Z face on bed, as illustrated",
            "none",
            "none",
            "2/5",
            "after calibration",
        ]
        for part in OFFICIAL_PRINT_PARTS_REQUIRED
    ]
    rows.extend(official_rows)
    official_orientation_images = "\n\n".join(
        f"![{part.name} print orientation](IMAGES/print_orientation_{part.name}.png)"
        for part in OFFICIAL_PRINT_PARTS
    )
    return f"""# Printing Guide

`VERIFIED_DIGITALLY` for part geometry, stored 3MF units, and bounding boxes.
Actual print time, material use, shrinkage, warping, and airtightness are
`REQUIRES_PHYSICAL_VALIDATION`.

## Complete-part warning

You must print **both** the custom Ultra parts and the official Squircle upper
stack. The six mandatory official files are in
`OFFICIAL_PARTS/REQUIRED_SINGLE_MATERIAL/`; they are included in the release
and listed in the table below.

Do **not** print the official original speaker chamber, original speaker plate,
or original anti-slip ring. `main_cabinet.3mf`, the Ultra driver/radiator
hardware, `base_skirt.3mf`, and `anti_slip_ring.3mf` replace those parts.

O07 and O08 are optional multi-material inserts. If using them, load O05, O07,
and O08 together in the slicer and omit O06. For an ordinary single-material
printer, use O05 plus O06 and ignore the optional folder.

## Minimum printer volume

- Limiting part: `outer_shell.3mf`, exactly 192.0 x 212.0 x 189.0 mm in its
  required upright orientation.
- Absolute usable travel: 212 x 192 x 189 mm (X/Y may be swapped).
- Practical minimum: 220 x 220 x 200 mm only when the full 220 mm is usable;
  this leaves 4 mm per long-side edge and limits the shell brim to 3 mm.
- If purge lines, bed clips, firmware exclusions, or a wider shell brim reduce
  usable travel below 218 mm, use a larger printer. A 230 mm bed is preferable,
  but it is not the geometric minimum.
- In-plane rotation cannot fit the shell on a 210 x 210 mm bed. Side printing
  is unsupported because it creates extensive support contact and degrades
  slots and cosmetic surfaces.

## Authoritative slicer baseline

- ASA primary; PETG alternative. Do not mix materials within a bolted joint.
- 0.4 mm nozzle; 0.20 mm layer; 0.45 mm line width.
- Five walls; six top and six bottom layers; 35% gyroid.
- ASA: 250-260 C nozzle, 100-110 C bed, enclosed printer, low part cooling,
  draft shield if chamber is below 40 C.
- PETG: 235-250 C nozzle, 75-85 C bed, moderate cooling after layer three.
- Supports: disabled. The horizontal acoustic openings are self-progressing
  circular overhangs; inspect their upper arcs and never place support on a
  gasket seat.
- Seam: rear (+Y) for cabinet/shell/shroud; away from all gasket lands.
- Elephant-foot compensation: set in the slicer from your coupon, not by
  sanding the part.

## Print order and exact orientation

{_markdown_table(["Group", "Filename", "Qty", "Material", "Face/orientation", "Supports", "Brim", "Difficulty", "Calibration"], rows)}

The 3MF files already store millimetres and the documented orientation.

## CAD-derived orientation sheets

{orientation_images}

## Official Squircle orientation sheets

{official_orientation_images}

## Inspection before continuing

- Cabinet and divider: continuous, glossy-enough gasket lands; no seam gap,
  crack, under-extrusion, or insert bore opened into the chamber.
- Shell: all slots open, four retention bridges intact, no warp at either rim.
- Clamp rings: flat within 0.20 mm on a surface plate; lip clean and continuous.
- Ballast cartridge: lid holes align; both plates lie flat; four bosses sound.
- TPU parts: no tear, string in a wire bore, or layer split.

Approximate filament and time vary too much by slicer and machine to be
verified digitally. Your slicer estimate is authoritative for planning; record
it before starting each full-size print.
"""


def _hardware_guide(parameters: DesignParameters, root: Path) -> str:
    bom = bill_of_materials(parameters, root)
    rows = [
        [r["id"], r["category"], r["item"], r["specification"], r["quantity"], r["required"]]
        for r in bom
        if not r["id"].startswith("P")
    ]
    return f"""# Hardware and Materials Guide

Use Batch 1 only. The public Batch 1 pair is Core rev4.1 plus HAT rev4.1 /
R2024.12.06. If the board or packaging says Satellite1.1, rev5.1 Core, rev6.1
HAT, or requires an external Wi-Fi antenna, stop: that hardware is unsupported.

{_markdown_table(["ID", "Category", "Item", "Exact specification", "Qty", "Required"], rows)}

All purchasing availability and prices must be checked by the builder.
Manufacturer geometry and electrical parameters are
`DERIVED_FROM_MANUFACTURER_DRAWING`; supplier availability is an
`ENGINEERING_ESTIMATE`.

No structural glue is used. No damping material is installed in RC1. Gaskets
are replaceable mechanically compressed EPDM, and the cable seal is TPU 95A.
"""


def _assembly_guide() -> str:
    part_rows = [
        [name, str(definition.quantity), definition.material]
        for name, definition in PARTS.items()
        if not name.startswith("coupon_") and name != "leak_test_adapter"
    ]
    part_rows.extend(
        [part.name, str(part.quantity), part.material] for part in OFFICIAL_PRINT_PARTS_REQUIRED
    )
    lines = [
        "# Illustrated Assembly Guide",
        "",
        "Front is -Y, rear is +Y, left/right radiators are -X/+X, and +Z points",
        "toward the microphones. All torque values are `ENGINEERING_ESTIMATE`",
        "until the selected insert/process is pull-tested.",
        "",
        "![Exploded part identification](IMAGES/exploded_parts_identification.png)",
        "",
        "## Exploded-view part key",
        "",
        _markdown_table(["Exact part name", "Qty", "Material"], part_rows),
        "",
        "![Fastener identification](IMAGES/fastener_identification.png)",
        "",
    ]
    for step in ASSEMBLY_STEPS:
        lines.extend(
            [
                f"## Step {step['number']}: {step['title']}",
                "",
                f"- Parts: {step['parts']}",
                f"- Fasteners: {step['fasteners']}",
                f"- Tools: {step['tools']}",
                f"- Gasket/seal: {step['gasket']}",
                f"- Action: {step['action']}",
                f"- Pass: {step['pass']}",
                f"- Warning: {step['warning']}",
                "",
                f"![Step {step['number']} - {step['title']}]({step['image']})",
                "",
            ]
        )
    return "\n".join(lines)


def _testing_guide(root: Path) -> str:
    acoustics = _acoustics(root)
    return f"""# Testing and Commissioning Guide

Every result in this guide requires a physical unit and is
`REQUIRES_PHYSICAL_VALIDATION`.

![Seal locations](IMAGES/gasket_placement.png)

![Final assembled inspection](IMAGES/assembly_stage_09_final.png)

## Before power

1. Verify red driver lead to + and black to -.
2. Confirm both radiators carry equal added mass: model target
   {acoustics.get("added_pr_mass_each_g", 0):.2f} g each.
3. Confirm every screw ID and quantity against `FASTENERS.csv`.
4. Confirm G01-G04 are continuous and no wire touches a moving component.
5. Perform the 100-250 Pa gross-leak screen during assembly. Never use shop air.

## Controlled first power

Use a current-limited supported USB-C supply and the official Batch 1
firmware. Start muted, then at minimum volume.

- LEDs: all segments visible and even.
- Buttons: each click registers once and returns freely.
- USB-C: plug inserts/removes without shell contact.
- Wi-Fi: connect and record RSSI beside a bare Batch 1 control.
- Microphones: verify all four channels, then run 50 wake-word trials at 1, 3,
  and 5 m on-axis and 45 degrees.
- Audio: play a polarity pulse, then a 100-500 Hz sweep at low level. Stop for
  rub, buzz, air noise, or asymmetric radiator motion.

## Acoustic commissioning

Measure impedance magnitude and phase from 20 Hz to 20 kHz at low level. The
two low-frequency peaks should bracket tuning; the minimum between them is the
real Fb. Model targets are {acoustics.get("target_tuning_hz", 0):.1f} Hz Fb,
{acoustics.get("minimum_modeled_impedance_ohm", 0):.2f} ohm minimum impedance,
and {acoustics.get("passive_radiator_f3_hz", 0):.1f} Hz f3. They are
`ENGINEERING_ESTIMATE`, not pass/fail measurements.

Start DSP with the modelled {acoustics.get("recommended_high_pass_hz", 0):.1f}
Hz fourth-order high-pass and no positive bass boost. Final EQ, limiter, and
tuning mass require measured response and excursion.

## Thermal and reliability

Instrument Core SoC, amplifier area, and electronics-bay air. Test 60 minutes
idle and 60 minutes pink noise at 25 C, then repeat at 35 C. Pass only if every
supplier limit retains 15 C margin, there is no throttling, and no printed part
softens. Perform a gentle rattle check and repeat the leak/impedance check after
five service cycles.

Record results; do not change the repository status to physically validated
without the measurements.
"""


def _maintenance_guide() -> str:
    return """# Maintenance and Service Guide

Disconnect power and wait five minutes before service. Work on a soft mat.

## Access order

- Electronics: remove official top/lock ring as documented by
  FutureProofHomes, disconnect JST-XH, remove F01, then F02 and the shroud.
- Driver/radiators: remove anti-slip ring, F09, outer shell, then the relevant
  F04/F05 clamp ring. Replace the opened G02/G03 gasket.
- Divider/cable gland: remove the upper stack and shroud, then F03. Replace G01
  whenever the divider is lifted.
- Ballast: remove anti-slip ring and F08 bottom plate; withdraw cartridge.
  Remove F06 lid screws while the cartridge is supported.

Never cut a wire for service; unplug or release its terminal. Never reuse a
torn, permanently flattened, or contaminated gasket. Never lever a clamp ring
against a cone.

After service, repeat polarity, gross leak, low-level sweep, buttons, LEDs,
microphones, Wi-Fi, and thermal spot checks. Store spare G01-G04 seals flat,
dark, and clean. Vacuum shell slots with a soft brush; do not use solvents on
ASA.

![Service disassembly direction](IMAGES/service_disassembly.png)
"""


def _engineering_appendix(root: Path) -> str:
    acoustics = _acoustics(root)
    reports = _validation(root)
    gates = [
        [name, str(value.get("status")), str(value.get("evidence"))]
        for name, value in sorted(reports.items())
        if isinstance(value, dict) and "status" in value
    ]
    risks = [[r.identifier, r.severity, r.title, r.mitigation, r.evidence] for r in RISKS]
    return f"""# Engineering Appendix

Source commit at generation: `{source_commit()}`.

## Coordinate system

- Origin: center of the measured official mid-plate interface plane.
- +Z: microphones/top; -Y: active-driver front; +/-X: opposed radiators.
- Units: millimetres.

## Current digital acoustic model

- Net acoustic volume: {acoustics.get("net_acoustic_volume_l", 0):.3f} L,
  `VERIFIED_DIGITALLY` from the connected OCCT air domain.
- Tuning: {acoustics.get("target_tuning_hz", 0):.1f} Hz.
- Added mass: {acoustics.get("added_pr_mass_each_g", 0):.2f} g per radiator.
- Modelled f3: {acoustics.get("passive_radiator_f3_hz", 0):.1f} Hz.
- Modelled minimum impedance:
  {acoustics.get("minimum_modeled_impedance_ohm", 0):.2f} ohm.

All acoustic performance values are `ENGINEERING_ESTIMATE`.

## Digital gates

{_markdown_table(["Gate", "Status", "Evidence"], gates)}

## Risk register

{_markdown_table(["ID", "Severity", "Risk", "Closure", "Evidence"], risks)}

Detailed machine-readable evidence remains under `reports/validation/`,
`reports/acoustics/`, `reports/research/`, and `reference-assets/MANIFEST.csv`.
"""


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    if not rows:
        raise ValueError(f"cannot write empty schedule {path}")
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def generate_documentation(
    output: Path = ROOT / "docs",
    parameters: DesignParameters | None = None,
    root: Path = ROOT,
) -> list[Path]:
    """Write every task-oriented guide and authoritative schedule."""
    p = parameters or load_design_parameters(root)
    output.mkdir(parents=True, exist_ok=True)

    documents = {
        "BUILD_BOOK.md": _build_book(p, root),
        "CALIBRATION_GUIDE.md": _calibration_guide(),
        "PRINTING_GUIDE.md": _printing_guide(p, root),
        "HARDWARE_AND_MATERIALS_GUIDE.md": _hardware_guide(p, root),
        "ASSEMBLY_GUIDE.md": _assembly_guide(),
        "TESTING_AND_COMMISSIONING_GUIDE.md": _testing_guide(root),
        "MAINTENANCE_GUIDE.md": _maintenance_guide(),
        "ENGINEERING_APPENDIX.md": _engineering_appendix(root),
    }
    written: list[Path] = []
    for name, content in documents.items():
        path = output / name
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        written.append(path)

    bom = bill_of_materials(p, root)
    written.append(_write_csv(output / "BOM.csv", bom))

    fasteners = fastener_rows(root)
    fastener_csv = [
        {
            "id": row["id"],
            "standard": row["standard"],
            "thread": row["thread"],
            "length_mm": row["length_mm"],
            "head": row["head"],
            "material": row["material"],
            "quantity": int(row["quantity"]) * (2 if "(each)" in row["joint"] else 1),
            "washer": row["washer"],
            "insert": row["insert"],
            "engagement_mm": row["engagement_mm"],
            "torque_guidance_nm": "0.35 target; 0.45 maximum",
            "tool": row["tool"],
            "assembly_joint": row["joint"],
            "seal_requirement": {
                "F03": "clamps G01",
                "F04": "clamps G02",
                "F05": "clamps G03",
            }.get(str(row["id"]), "none"),
            "purchasing_specification": f"{row['standard']} A2-70 stainless",
        }
        for row in fasteners
    ]
    written.append(_write_csv(output / "FASTENERS.csv", fastener_csv))
    written.append(_write_csv(output / "GASKETS.csv", [dict(row) for row in GASKETS]))

    risk_rows = [
        {
            "id": risk.identifier,
            "severity": risk.severity,
            "risk": risk.title,
            "consequence": risk.consequence,
            "mitigation": risk.mitigation,
            "owner": risk.owner,
            "state": risk.state,
            "evidence": risk.evidence,
        }
        for risk in RISKS
    ]
    written.append(_write_csv(output / "RISK_REGISTER.csv", risk_rows))
    (output / "source-commit.txt").write_text(source_commit() + "\n", encoding="utf-8")
    written.append(output / "source-commit.txt")
    return written
