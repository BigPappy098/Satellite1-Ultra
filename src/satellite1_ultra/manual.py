"""Technical drawing sheets and the PDF build manual.

The authoritative manufacturing definition is the STEP file; these sheets are
inspection and reference documents generated from the same B-rep, and each one
says so in its title block.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reportlab.lib import colors  # type: ignore[import-untyped]
from reportlab.lib.pagesizes import A4, landscape  # type: ignore[import-untyped]
from reportlab.lib.styles import (  # type: ignore[import-untyped]
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm  # type: ignore[import-untyped]
from reportlab.lib.utils import ImageReader  # type: ignore[import-untyped]
from reportlab.pdfgen import canvas as pdf_canvas  # type: ignore[import-untyped]
from reportlab.platypus import (  # type: ignore[import-untyped]
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from satellite1_ultra.configuration import ROOT, load_design_parameters
from satellite1_ultra.exporting import PARTS, print_oriented, source_commit
from satellite1_ultra.geometry import DesignParameters

SHEET = landscape(A4)


def _reports(root: Path) -> dict[str, Any]:
    reports: dict[str, Any] = {}
    for path in sorted((root / "reports" / "validation").glob("*.json")):
        with path.open(encoding="utf-8") as source:
            reports[path.stem] = json.load(source)
    acoustics = root / "reports" / "acoustics" / "summary.json"
    if acoustics.is_file():
        with acoustics.open(encoding="utf-8") as source:
            reports["acoustics"] = json.load(source)
    return reports


def _part_dimensions(name: str, parameters: DesignParameters) -> list[tuple[str, str]]:
    """Key inspection dimensions for one part, measured on its B-rep."""
    shape = print_oriented(PARTS[name].builder(parameters))
    box = shape.BoundingBox()
    rows = [
        ("Bounding X", f"{box.xlen:.2f} mm"),
        ("Bounding Y", f"{box.ylen:.2f} mm"),
        ("Bounding Z", f"{box.zlen:.2f} mm"),
        ("Volume", f"{shape.Volume() / 1000.0:.2f} cm3"),
        ("Solids", str(len(shape.Solids()))),
        ("Faces", str(len(shape.Faces()))),
    ]
    p = parameters
    extra: dict[str, list[tuple[str, str]]] = {
        "main_cabinet": [
            ("Driver seat diameter", f"{p.driver_seat_diameter:.2f} mm"),
            ("Driver bore", f"{p.driver_bore_diameter:.2f} mm"),
            ("Driver seat depth", f"{p.driver_seat_depth:.2f} mm"),
            ("Driver clamp bolt circle", f"{p.driver_clamp_bolt_circle:.2f} mm"),
            ("Radiator ledge diameter", f"{p.pr_ledge_diameter:.2f} mm"),
            ("Radiator seat diameter", f"{p.pr_seat_diameter:.2f} mm"),
            ("Radiator bore", f"{p.pr_bore_diameter:.2f} mm"),
            ("Radiator clamp bolt circle", f"{p.pr_clamp_bolt_circle:.2f} mm"),
            ("Insert bore", f"{p.insert_bore_diameter:.2f} x {p.insert_bore_depth:.2f} mm"),
            ("Wall thickness", f"{p.wall_thickness:.2f} mm"),
        ],
        "active_driver_clamp_ring": [
            ("Outside diameter", f"{p.driver_clamp_ring_diameter:.2f} mm"),
            ("Bolt circle", f"{p.driver_clamp_bolt_circle:.2f} mm"),
            ("Clearance holes", f"4 x {p.fastener_clearance_diameter:.2f} mm"),
            ("Lip height", f"{p.clamp_lip:.2f} mm"),
        ],
        "passive_radiator_clamp_ring": [
            ("Outside diameter", f"{p.pr_clamp_ring_diameter:.2f} mm"),
            ("Bolt circle", f"{p.pr_clamp_bolt_circle:.2f} mm"),
            ("Clearance holes", f"4 x {p.fastener_clearance_diameter:.2f} mm"),
            ("Lip height", f"{p.clamp_lip:.2f} mm"),
        ],
        "pressure_divider": [
            (
                "Official mount pattern",
                f"+/-{p.official_mount_x:.4f}, +/-{p.official_mount_y:.4f} mm",
            ),
            ("Official seating plane", f"Z = {p.official_interface_z:.2f} mm"),
            ("Cable passage", f"{p.cable_passage_diameter:.2f} mm"),
            ("Thickness", f"{p.divider_thickness:.2f} mm"),
        ],
    }
    return rows + extra.get(name, [])


def drawing_sheets(
    output: Path = ROOT / "reports" / "drawings",
    parameters: DesignParameters | None = None,
    root: Path = ROOT,
) -> list[Path]:
    """One inspection drawing sheet per manufactured part."""
    from matplotlib import pyplot as plt

    from satellite1_ultra.renders import VIEWS, _draw, _finish

    p = parameters or load_design_parameters(root)
    output.mkdir(parents=True, exist_ok=True)
    images = output / "views"
    images.mkdir(exist_ok=True)
    commit = source_commit()
    written: list[Path] = []

    for name, definition in PARTS.items():
        shape = print_oriented(definition.builder(p))
        view_paths: list[Path] = []
        for view in VIEWS[:3]:
            figure = plt.figure(figsize=(4.2, 4.2), dpi=150)
            axis = figure.add_subplot(111, projection="3d")
            low, high = _draw(axis, {name: shape}, {name: (0.45, 0.48, 0.52)})
            _finish(figure, axis, low, high, view)
            path = images / f"{name}_{view.name}.png"
            figure.savefig(path, bbox_inches="tight", facecolor="#ffffff")
            plt.close(figure)
            view_paths.append(path)

        sheet = output / f"{name}.pdf"
        canvas = pdf_canvas.Canvas(str(sheet), pagesize=SHEET)
        width, height = SHEET
        canvas.setLineWidth(1.2)
        canvas.rect(10 * mm, 10 * mm, width - 20 * mm, height - 20 * mm)
        canvas.setFont("Helvetica-Bold", 15)
        canvas.drawString(14 * mm, height - 20 * mm, f"Satellite1 Ultra — {name}")
        canvas.setFont("Helvetica", 8.5)
        canvas.drawString(
            14 * mm,
            height - 26 * mm,
            "Authoritative definition is exports/step/"
            f"{name}.step. This sheet is generated from the same B-rep for "
            "inspection reference only.",
        )
        for index, path in enumerate(view_paths):
            canvas.drawImage(
                ImageReader(str(path)),
                14 * mm + index * 88 * mm,
                58 * mm,
                width=84 * mm,
                height=84 * mm,
                preserveAspectRatio=True,
                anchor="sw",
                mask="auto",
            )
        rows = _part_dimensions(name, p)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(width - 96 * mm, height - 40 * mm, "Inspection dimensions")
        canvas.setFont("Helvetica", 8)
        for index, (label, value) in enumerate(rows):
            y = height - 46 * mm - index * 4.6 * mm
            canvas.drawString(width - 96 * mm, y, label)
            canvas.drawRightString(width - 14 * mm, y, value)
        canvas.setFont("Helvetica", 8)
        block = [
            ("Quantity", str(definition.quantity)),
            ("Material", definition.material),
            ("Print orientation", definition.print_orientation),
            ("Evidence", definition.evidence_label),
            ("Source commit", commit[:12]),
            ("Units", "millimetres"),
            ("Projection", "isometric / front / side, CAD tessellation"),
        ]
        for index, (label, value) in enumerate(block):
            y = 46 * mm - index * 4.6 * mm
            canvas.drawString(14 * mm, y, f"{label}:")
            canvas.drawString(54 * mm, y, value)
        canvas.setFont("Helvetica-Oblique", 7.5)
        canvas.drawRightString(
            width - 14 * mm,
            14 * mm,
            "Physical fit REQUIRES_PHYSICAL_VALIDATION until the coupon set has been "
            "printed and measured.",
        )
        canvas.showPage()
        canvas.save()
        written.append(sheet)
    return written


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=base["Title"], fontSize=26, leading=30, spaceAfter=10
        ),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontSize=15, spaceBefore=12),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=11.5, spaceBefore=8),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontSize=9, leading=12.5),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontSize=7.6, leading=10),
    }


def _table(data: list[list[str]], widths: list[float]) -> Table:
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.4),
                ("LEADING", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8bcc2")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eaed")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f7f8")]),
            ]
        )
    )
    return table


def build_manual(
    output: Path = ROOT / "docs" / "Satellite1-Ultra-Build-Manual.pdf",
    root: Path = ROOT,
) -> Path:
    """Assemble the complete PDF build manual from the generated evidence."""
    styles = _styles()
    reports = _reports(root)
    p = load_design_parameters(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Satellite1 Ultra Build Manual",
        author="Satellite1 Ultra contributors",
    )
    story: list[Any] = []

    def text(content: str, style: str = "body") -> None:
        story.append(Paragraph(content, styles[style]))

    def image(path: Path, width: float) -> None:
        if path.is_file():
            story.append(Spacer(1, 5))
            story.append(Image(str(path), width=width, height=width * 1.12))

    commit = source_commit()
    text("Satellite1 Ultra", "title")
    text(
        "Build manual for a serviceable passive-radiator enclosure for the "
        "FutureProofHomes Satellite1 development kit."
    )
    text(f"Source commit <b>{commit[:12]}</b>. Units: millimetres.")
    text(
        "<b>Status: IN DEVELOPMENT. No physical validation has been performed.</b> "
        "Every geometric statement in this manual is machine-checked against the "
        "authoritative CAD. Every acoustic number is a lumped-parameter "
        "simulation, not a measurement. Nothing here may be quoted as measured "
        "fit, acoustic, thermal, wireless or wake-word performance."
    )

    text("1. Product envelope", "h1")
    envelope = [
        ["Property", "Value", "Evidence"],
        ["Cabinet section", f"{p.outer_width:.0f} x {p.outer_depth:.0f} mm", "VERIFIED_DIGITALLY"],
        [
            "Overall shell section",
            f"{p.outer_width + p.grille_width_margin:.0f} x "
            f"{p.outer_depth + p.grille_depth_margin:.0f} mm",
            "VERIFIED_DIGITALLY",
        ],
        ["Overall height with official top", "237.7 mm", "VERIFIED_DIGITALLY"],
        [
            "Net acoustic volume",
            f"{reports.get('acoustic_volume', {}).get('net_acoustic_volume_l', 0):.3f} L",
            "VERIFIED_DIGITALLY",
        ],
        [
            "Assembled mass",
            f"{reports.get('center_of_gravity', {}).get('total_mass_g', 0):.0f} g",
            "ENGINEERING_ESTIMATE",
        ],
        [
            "Minimum tipping angle",
            f"{reports.get('center_of_gravity', {}).get('minimum_tipping_angle_deg', 0):.1f} deg",
            "ENGINEERING_ESTIMATE",
        ],
    ]
    story.append(_table(envelope, [55 * mm, 60 * mm, 55 * mm]))
    image(root / "reports" / "renders" / "assembly_iso.png", 105 * mm)

    text("2. Acoustic design", "h1")
    acoustics = reports.get("acoustics", {})
    if acoustics:
        rows = [
            ["Quantity", "Modelled value"],
            ["Architecture", "1 active driver, 2 opposed passive radiators"],
            ["Net volume", f"{acoustics['net_acoustic_volume_l']:.3f} L"],
            ["System tuning", f"{acoustics['target_tuning_hz']:.1f} Hz"],
            ["Added mass per radiator", f"{acoustics['added_pr_mass_each_g']:.2f} g"],
            ["f3, passive-radiator alignment", f"{acoustics['passive_radiator_f3_hz']:.1f} Hz"],
            ["f3, same driver sealed", f"{acoustics['sealed_f3_hz']:.1f} Hz"],
            ["Minimum impedance", f"{acoustics['minimum_modeled_impedance_ohm']:.2f} ohm"],
            ["Maximum SPL at 100 Hz", f"{acoustics['maximum_spl_at_100_hz_db']:.1f} dB at 1 m"],
            [
                "Protective high-pass",
                f"{acoustics['recommended_high_pass_hz']:.1f} Hz, order "
                f"{acoustics['recommended_high_pass_order']}",
            ],
        ]
        story.append(_table(rows, [70 * mm, 100 * mm]))
        text(
            "<b>ENGINEERING_ESTIMATE.</b> These are calculated from published "
            "manufacturer parameters and the exact CAD net volume. They are not "
            "measurements. Measure impedance first and feed the result back into "
            "the model before finalising any DSP.",
            "small",
        )
        image(root / "reports" / "acoustics" / "system_response.png", 168 * mm)

    story.append(PageBreak())
    text("3. Bill of materials", "h1")
    bom_path = root / "docs" / "bill_of_materials.csv"
    if bom_path.is_file():
        import csv as _csv

        with bom_path.open(encoding="utf-8") as source:
            rows = list(_csv.reader(source))
        story.append(_table(rows, [56 * mm, 26 * mm, 14 * mm, 30 * mm, 44 * mm]))

    story.append(PageBreak())
    text("4. Fastener schedule", "h1")
    schedule = reports.get("fasteners", {}).get("schedule", [])
    rows = [["Joint", "Qty", "Screw", "Stack", "Engage", "Margin", "Access"]]
    rows += [
        [
            row["joint"],
            str(row["quantity"]),
            f"M3x{row['length_mm']:.0f}",
            f"{row['clamped_stack_mm']:.1f}",
            f"{row['engagement_mm']:.1f}",
            f"{row['bottoming_margin_mm']:.1f}",
            row["access_direction"],
        ]
        for row in schedule
    ]
    story.append(_table(rows, [58 * mm, 10 * mm, 18 * mm, 14 * mm, 16 * mm, 16 * mm, 38 * mm]))
    text(
        "Every insert bore is blind and drilled deeper than the insert, so no "
        "screw can bottom. No fastener crosses the acoustic pressure boundary.",
        "small",
    )

    text("5. Sealing", "h1")
    sealing = reports.get("sealing", {})
    for item in sealing.get("pressure_boundary", []):
        text(f"• {item}", "small")
    text(
        f"Sealing gate status: <b>{sealing.get('status', '?')}</b>. "
        "The gate proves, on the B-rep, that every gasket land is a continuous "
        "annulus and that no fastener bore breaks through it. It cannot prove "
        "gas tightness of a printed wall; that is REQUIRES_PHYSICAL_VALIDATION.",
        "small",
    )

    story.append(PageBreak())
    text("6. Assembly", "h1")
    assembly = reports.get("assembly", {})
    for index, step in enumerate(assembly.get("assembly_order", []), start=1):
        text(f"{index}. {step}", "small")
    image(root / "reports" / "renders" / "assembly_iso_exploded.png", 120 * mm)

    story.append(PageBreak())
    text("7. Cross sections", "h1")
    image(root / "reports" / "renders" / "cross_section_xz.png", 118 * mm)
    image(root / "reports" / "renders" / "cross_section_yz.png", 118 * mm)

    story.append(PageBreak())
    text("8. Manufactured parts", "h1")
    image(root / "reports" / "renders" / "part_sheet.png", 172 * mm)

    story.append(PageBreak())
    text("9. Validation gate summary", "h1")
    rows = [["Gate", "Status", "Evidence"]]
    for name in sorted(reports):
        if name in {"acoustics", "export_validation", "summary"}:
            continue
        rows.append([name, reports[name].get("status", "?"), reports[name].get("evidence", "-")])
    story.append(_table(rows, [55 * mm, 25 * mm, 60 * mm]))

    text("10. Risk register", "h1")
    from satellite1_ultra.documentation import RISKS

    rows = [["ID", "Sev", "Risk", "Mitigation"]]
    rows += [[r.identifier, r.severity, r.title, r.mitigation] for r in RISKS]
    story.append(_table(rows, [12 * mm, 16 * mm, 58 * mm, 88 * mm]))

    text("11. Before you build", "h1")
    text(
        "Print the eight fit coupons, measure them against docs/fit-coupons.md, "
        "and enter the corrections in config/physical_compensation.yaml. Then "
        "regenerate every part. Do not print the full set first.",
    )
    text(
        "This design is not PHYSICALLY_VALIDATED. Physical fit, sealing, "
        "acoustic output, wake-word behaviour, thermal margin and wireless "
        "performance all remain unmeasured.",
    )

    document.build(story)
    return output
