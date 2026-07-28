"""Technical drawing sheets and the PDF build manual.

The authoritative manufacturing definition is the STEP file; these sheets are
inspection and reference documents generated from the same B-rep, and each one
says so in its title block.
"""

from __future__ import annotations

import json
import re
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
    styles = _styles()
    wrapped = [[Paragraph(str(value), styles["small"]) for value in row] for row in data]
    table = Table(wrapped, colWidths=widths, repeatRows=1, splitByRow=1)
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


def _inline(text: str) -> str:
    """Convert the small Markdown subset used by generated guides to ReportLab markup."""
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", escaped)
    escaped = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1 (\2)", escaped)
    return escaped


def _page_number(canvas: Any, document: Any) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#555b61"))
    canvas.drawString(18 * mm, 9 * mm, "Satellite1 Ultra RC1 — DIGITAL_PROTOTYPE_READY")
    canvas.drawRightString(192 * mm, 9 * mm, f"Page {document.page}")
    canvas.restoreState()


def _markdown_pdf(source: Path, output: Path, root: Path) -> Path:
    """Render a generated task guide to a readable illustrated A4 PDF."""
    styles = _styles()
    output.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        title=source.stem.replace("_", " ").title(),
        author="Satellite1 Ultra contributors",
    )
    lines = source.read_text(encoding="utf-8").splitlines()
    story: list[Any] = []
    index = 0
    in_code = False
    code_lines: list[str] = []
    while index < len(lines):
        line = lines[index].rstrip()
        if line.startswith("```"):
            if in_code:
                story.append(
                    Paragraph(
                        "<font name='Courier'>"
                        + "<br/>".join(_inline(v) for v in code_lines)
                        + "</font>",
                        styles["small"],
                    )
                )
                code_lines = []
            in_code = not in_code
            index += 1
            continue
        if in_code:
            code_lines.append(line)
            index += 1
            continue
        image_match = re.fullmatch(r"!\[(.+?)\]\((.+?)\)", line)
        if image_match:
            image_ref = image_match.group(2)
            image_path = (
                root / "reports" / "renders" / Path(image_ref).name
                if image_ref.startswith("IMAGES/")
                else source.parent / image_ref
            )
            if not image_path.is_file():
                raise FileNotFoundError(f"{source.name} references missing image {image_ref}")
            reader = ImageReader(str(image_path))
            iw, ih = reader.getSize()
            width = min(176 * mm, 176 * mm * iw / max(iw, ih))
            height = width * ih / iw
            if height > 165 * mm:
                height = 165 * mm
                width = height * iw / ih
            story.extend(
                [
                    Spacer(1, 3 * mm),
                    Image(str(image_path), width=width, height=height),
                    Paragraph(_inline(image_match.group(1)), styles["small"]),
                    Spacer(1, 3 * mm),
                ]
            )
            index += 1
            continue
        if line.startswith("| ") and index + 1 < len(lines) and lines[index + 1].startswith("|"):
            table_lines = [line]
            index += 1
            while index < len(lines) and lines[index].startswith("|"):
                table_lines.append(lines[index])
                index += 1
            rows = [
                [cell.strip() for cell in row.strip("|").split("|")]
                for row in table_lines
                if "---" not in row
            ]
            column_count = len(rows[0])
            story.extend(
                [Spacer(1, 2 * mm), _table(rows, [176 * mm / column_count] * column_count)]
            )
            continue
        if line.startswith("# "):
            story.append(Paragraph(_inline(line[2:]), styles["title"]))
        elif line.startswith("## "):
            story.append(Paragraph(_inline(line[3:]), styles["h1"]))
        elif line.startswith("### "):
            story.append(Paragraph(_inline(line[4:]), styles["h2"]))
        elif line.startswith("> "):
            story.append(
                Table(
                    [[Paragraph(_inline(line[2:]), styles["body"])]],
                    colWidths=[176 * mm],
                    style=TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff0c9")),
                            ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#b05a00")),
                            ("LEFTPADDING", (0, 0), (-1, -1), 8),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                            ("TOPPADDING", (0, 0), (-1, -1), 6),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ]
                    ),
                )
            )
        elif re.match(r"^[-*] ", line):
            story.append(Paragraph("• " + _inline(line[2:]), styles["body"]))
        elif re.match(r"^\d+\. ", line):
            story.append(Paragraph(_inline(line), styles["body"]))
        elif line:
            paragraph = [line]
            while index + 1 < len(lines):
                following = lines[index + 1].rstrip()
                if not following or following.startswith(("#", "|", "!", ">", "```")):
                    break
                if re.match(r"^[-*] |^\d+\. ", following):
                    break
                paragraph.append(following)
                index += 1
            story.append(Paragraph(_inline(" ".join(paragraph)), styles["body"]))
        else:
            story.append(Spacer(1, 1.5 * mm))
        index += 1
    story.append(Spacer(1, 4 * mm))
    story.append(
        Paragraph(
            f"Source commit {_inline(source_commit()[:12])}. "
            "No physical validation has been performed.",
            styles["small"],
        )
    )
    document.build(story, onFirstPage=_page_number, onLaterPages=_page_number)
    if not output.is_file() or output.stat().st_size < 2_000:
        raise ValueError(f"PDF generation failed or produced an incomplete file: {output}")
    return output


def build_manuals(
    output: Path = ROOT / "docs",
    root: Path = ROOT,
) -> list[Path]:
    """Build the complete user-facing PDF set from current generated guides."""
    mapping = {
        "BEGINNER_BUILD_GUIDE.md": "BUILD_SATELLITE1_ULTRA_FOR_BEGINNERS.pdf",
        "START_HERE.md": "START_HERE.pdf",
        "CALIBRATION_GUIDE.md": "START_HERE_CALIBRATION_GUIDE.pdf",
        "PRINTING_GUIDE.md": "PRINTING_GUIDE.pdf",
        "ASSEMBLY_GUIDE.md": "ASSEMBLY_GUIDE.pdf",
        "TESTING_AND_COMMISSIONING_GUIDE.md": "TESTING_AND_COMMISSIONING_GUIDE.pdf",
        "MAINTENANCE_GUIDE.md": "MAINTENANCE_GUIDE.pdf",
    }
    written: list[Path] = []
    for source_name, output_name in mapping.items():
        source = root / "docs" / source_name
        if not source.is_file():
            raise FileNotFoundError(f"generate documentation before PDFs: {source}")
        written.append(_markdown_pdf(source, output / output_name, root))
    return written


def build_manual(
    output: Path = ROOT / "docs" / "ASSEMBLY_GUIDE.pdf",
    root: Path = ROOT,
) -> Path:
    """Compatibility wrapper returning the assembly PDF."""
    build_manuals(output.parent, root)
    return output
