"""Build orchestration command line."""

from __future__ import annotations

import json
import shutil

import click

from satellite1_ultra.configuration import ROOT, load_design_parameters

GENERATED = (
    ROOT / "exports",
    ROOT / "reports" / "validation",
    ROOT / "reports" / "acoustics",
    ROOT / "reports" / "renders",
    ROOT / "reports" / "drawings",
    ROOT / "build",
)


@click.group()
def main() -> None:
    """Build, validate, export and document Satellite1 Ultra."""


@main.command()
def build() -> None:
    """Build every authoritative CadQuery B-rep part and check validity."""
    from satellite1_ultra.exporting import PARTS

    parameters = load_design_parameters()
    build_dir = ROOT / "build"
    build_dir.mkdir(exist_ok=True)
    summary: dict[str, dict[str, object]] = {}
    for name, definition in PARTS.items():
        shape = definition.builder(parameters)
        box = shape.BoundingBox()
        if not shape.isValid() or len(shape.Solids()) != 1 or shape.Volume() <= 0.0:
            raise click.ClickException(f"{name} is not a single valid positive-volume solid")
        summary[name] = {
            "volume_mm3": shape.Volume(),
            "bounds_mm": [box.xlen, box.ylen, box.zlen],
            "faces": len(shape.Faces()),
            "quantity": definition.quantity,
        }
        click.echo(f"  built {name}")
    (build_dir / "parts.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    click.echo(f"Built {len(summary)} parts.")


@main.command()
def validate() -> None:
    """Run every quantitative validation gate."""
    from satellite1_ultra.validation import generate_validation_reports

    reports = generate_validation_reports()
    for name, report in reports.items():
        click.echo(f"  {name:20s} {report['status']}")
    click.echo("All validation gates passed.")


@main.command()
def acoustics() -> None:
    """Run the acoustic model against the measured CAD net volume."""
    from satellite1_ultra.analysis import generate_acoustic_reports

    summary = generate_acoustic_reports()
    if summary.get("status") != "PASS":
        raise click.ClickException(
            f"acoustic alignment deviates from the optimum by "
            f"{summary['tuning_deviation_hz']:.1f} Hz"
        )
    click.echo(
        f"  net volume {summary['net_acoustic_volume_l']:.3f} L, "
        f"tuning {summary['target_tuning_hz']:.1f} Hz, "
        f"f3 {summary['passive_radiator_f3_hz']:.1f} Hz"
    )


@main.command()
def export() -> None:
    """Export and round-trip validate every manufacturing file."""
    from satellite1_ultra.assemblies import export_assemblies
    from satellite1_ultra.exporting import export_parts

    parameters = load_design_parameters()
    records = export_parts(parameters=parameters)
    click.echo(f"  {len(records)} parts exported to STEP, STL and 3MF")
    written = export_assemblies(parameters=parameters)
    for label, path in written.items():
        click.echo(f"  assembly {label} -> {path.relative_to(ROOT)}")


@main.command()
def renders() -> None:
    """Generate CAD-derived renders and cross sections."""
    from satellite1_ultra.renders import generate_renders

    for path in generate_renders(parameters=load_design_parameters()):
        click.echo(f"  {path.relative_to(ROOT)}")


@main.command()
def drawings() -> None:
    """Generate one inspection drawing sheet per manufactured part."""
    from satellite1_ultra.manual import drawing_sheets

    sheets = drawing_sheets(parameters=load_design_parameters())
    click.echo(f"  {len(sheets)} drawing sheets generated")


@main.command()
def docs() -> None:
    """Generate the BOM, schedules, guides, risk register and checklist."""
    from satellite1_ultra.documentation import generate_documentation

    for path in generate_documentation(parameters=load_design_parameters()):
        click.echo(f"  {path.relative_to(ROOT)}")


@main.command("manual")
def manual_command() -> None:
    """Generate the PDF build manual."""
    from satellite1_ultra.manual import build_manual

    path = build_manual()
    click.echo(f"  {path.relative_to(ROOT)} ({path.stat().st_size // 1024} KiB)")


@main.command()
def clean() -> None:
    """Remove every generated artifact."""
    for directory in GENERATED:
        if directory.exists():
            shutil.rmtree(directory)
            click.echo(f"  removed {directory.relative_to(ROOT)}")
    manual_pdf = ROOT / "docs" / "Satellite1-Ultra-Build-Manual.pdf"
    if manual_pdf.exists():
        manual_pdf.unlink()


@main.command("all")
@click.pass_context
def run_all(context: click.Context) -> None:
    """Run the complete pipeline in dependency order."""
    for step in (build, validate, acoustics, export, renders, drawings, docs, manual_command):
        click.echo(f"== {step.name}")
        context.invoke(step)


def _entry() -> None:  # pragma: no cover - console-script shim
    main()


if __name__ == "__main__":  # pragma: no cover
    main()
