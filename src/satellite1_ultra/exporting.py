"""Manufacturing export, round-trip, and mesh-validation pipeline."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from xml.etree import ElementTree as ET

import cadquery as cq
import numpy as np
import trimesh
from cadquery import exporters, importers

from satellite1_ultra.coupons import COUPONS
from satellite1_ultra.geometry import (
    DEFAULT_PARAMETERS,
    DesignParameters,
    active_driver_clamp_ring,
    anti_slip_ring,
    ballast_cartridge,
    ballast_cartridge_lid,
    base_skirt,
    bottom_service_plate,
    cable_gland,
    divider_gasket,
    driver_gasket,
    leak_test_adapter,
    main_cabinet,
    mic_isolation_bushing,
    passive_radiator_clamp_ring,
    passive_radiator_gasket,
    pressure_divider,
    shell_base,
    shell_base_fabric,
    shell_crown,
    shell_crown_fabric,
    shell_grille,
    shell_grille_fabric,
)

ROOT = Path(__file__).resolve().parents[2]
THREE_MF_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
EXPORT_SOURCE_PATHS = (
    "src/satellite1_ultra",
    "config",
    "reference-assets/official",
    "reference-assets/MANIFEST.csv",
    "pyproject.toml",
    "requirements.lock",
)


@dataclass(frozen=True)
class PartDefinition:
    """One manufactured B-rep part and its release metadata."""

    builder: Callable[[DesignParameters], cq.Shape]
    quantity: int
    material: str
    print_orientation: str
    evidence_label: str = "VERIFIED_DIGITALLY"
    #: Linear/angular tessellation tolerances for the derived mesh outputs.
    mesh_tolerance: float = 0.02
    mesh_angular_tolerance: float = 0.10


PARTS: dict[str, PartDefinition] = {
    "anti_slip_ring": PartDefinition(anti_slip_ring, 1, "TPU 95A", "flat"),
    # The skin, split into three lapped segments.  Smooth is the default
    # finish; the *_fabric variants add the wrap-retention channels.
    "shell_base": PartDefinition(shell_base, 1, "ASA", "inverted, cut face on the bed"),
    "shell_grille": PartDefinition(shell_grille, 1, "ASA", "upright, lower cut face on bed"),
    "shell_crown": PartDefinition(shell_crown, 1, "ASA", "upright, flat top uppermost"),
    "shell_base_fabric": PartDefinition(
        shell_base_fabric, 1, "ASA", "inverted, cut face on the bed"
    ),
    "shell_grille_fabric": PartDefinition(
        shell_grille_fabric, 1, "ASA", "upright, lower cut face on bed"
    ),
    "shell_crown_fabric": PartDefinition(
        shell_crown_fabric, 1, "ASA", "upright, flat top uppermost"
    ),
    "main_cabinet": PartDefinition(main_cabinet, 1, "ASA", "upright, acoustic floor on bed"),
    "pressure_divider": PartDefinition(pressure_divider, 1, "ASA", "flat, acoustic face on bed"),
    "mic_isolation_bushing": PartDefinition(
        mic_isolation_bushing, 4, "TPU 95A", "flange face on bed"
    ),
    "active_driver_clamp_ring": PartDefinition(
        active_driver_clamp_ring, 1, "ASA", "lip face on bed"
    ),
    "passive_radiator_clamp_ring": PartDefinition(
        passive_radiator_clamp_ring, 2, "ASA", "lip face on bed"
    ),
    "divider_gasket": PartDefinition(divider_gasket, 1, "2 mm closed-cell EPDM", "flat"),
    "driver_gasket": PartDefinition(driver_gasket, 1, "2 mm closed-cell EPDM", "flat"),
    "passive_radiator_gasket": PartDefinition(
        passive_radiator_gasket, 2, "2 mm closed-cell EPDM", "flat"
    ),
    "cable_gland": PartDefinition(cable_gland, 1, "TPU 95A", "body end on bed"),
    "leak_test_adapter": PartDefinition(
        leak_test_adapter,
        1,
        "TPU 95A",
        "flange on bed; temporary service tool, not installed in service",
    ),
    "base_skirt": PartDefinition(base_skirt, 1, "ASA", "service opening on bed"),
    "bottom_service_plate": PartDefinition(bottom_service_plate, 1, "ASA", "exterior face on bed"),
    "ballast_cartridge": PartDefinition(ballast_cartridge, 1, "ASA", "tray floor on bed"),
    "ballast_cartridge_lid": PartDefinition(ballast_cartridge_lid, 1, "ASA", "tongue face on bed"),
}
for coupon_name, coupon_builder in COUPONS.items():
    PARTS[coupon_name] = PartDefinition(
        coupon_builder,
        1,
        "ASA",
        "largest flat face on bed",
        "VERIFIED_DIGITALLY",
    )


def source_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def export_sources_match(recorded_commit: str) -> bool:
    """Return whether exports still match their recorded source revision.

    Generated files cannot truthfully record the commit that first contains
    those same files: committing them necessarily creates a newer revision.
    A recorded ancestor is therefore current only when every input that can
    affect geometry or export serialization is unchanged in the checked-out
    tree. This also rejects dirty tracked inputs and untracked source files.
    """
    if not re.fullmatch(r"[0-9a-f]{40}", recorded_commit):
        return False
    try:
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", recorded_commit, "HEAD"],
            cwd=ROOT,
            check=False,
            capture_output=True,
        )
        if ancestor.returncode != 0:
            return False
        changed = subprocess.run(
            ["git", "diff", "--quiet", recorded_commit, "--", *EXPORT_SOURCE_PATHS],
            cwd=ROOT,
            check=False,
            capture_output=True,
        )
        if changed.returncode != 0:
            return False
        untracked = subprocess.run(
            [
                "git",
                "ls-files",
                "--others",
                "--exclude-standard",
                "--",
                *EXPORT_SOURCE_PATHS,
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return not untracked.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return recorded_commit == source_commit()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def print_oriented(shape: cq.Shape) -> cq.Shape:
    """Place the documented print orientation on Z=0 without changing axes."""
    box = shape.BoundingBox()
    return shape.translate(cq.Vector(0.0, 0.0, -box.zmin))


def bounds(shape: cq.Shape) -> tuple[float, float, float]:
    box = shape.BoundingBox()
    return box.xlen, box.ylen, box.zlen


def _bounds_error(
    expected: tuple[float, float, float],
    actual: tuple[float, float, float],
) -> float:
    return max(abs(left - right) for left, right in zip(expected, actual, strict=True))


def write_3mf(mesh: trimesh.Trimesh, path: Path, name: str, commit: str) -> None:
    """Write a standards-based, millimetre-unit single-object 3MF package."""
    model = ET.Element(f"{{{THREE_MF_NS}}}model", {"unit": "millimeter", "xml:lang": "en-US"})
    ET.SubElement(model, f"{{{THREE_MF_NS}}}metadata", {"name": "Title"}).text = name
    ET.SubElement(
        model,
        f"{{{THREE_MF_NS}}}metadata",
        {"name": "satellite1-ultra:source-commit"},
    ).text = commit
    resources = ET.SubElement(model, f"{{{THREE_MF_NS}}}resources")
    object_node = ET.SubElement(
        resources,
        f"{{{THREE_MF_NS}}}object",
        {"id": "1", "type": "model", "name": name},
    )
    mesh_node = ET.SubElement(object_node, f"{{{THREE_MF_NS}}}mesh")
    vertices_node = ET.SubElement(mesh_node, f"{{{THREE_MF_NS}}}vertices")
    for vertex in np.asarray(mesh.vertices):
        ET.SubElement(
            vertices_node,
            f"{{{THREE_MF_NS}}}vertex",
            {"x": f"{vertex[0]:.9g}", "y": f"{vertex[1]:.9g}", "z": f"{vertex[2]:.9g}"},
        )
    triangles_node = ET.SubElement(mesh_node, f"{{{THREE_MF_NS}}}triangles")
    for face in np.asarray(mesh.faces):
        ET.SubElement(
            triangles_node,
            f"{{{THREE_MF_NS}}}triangle",
            {"v1": str(face[0]), "v2": str(face[1]), "v3": str(face[2])},
        )
    build = ET.SubElement(model, f"{{{THREE_MF_NS}}}build")
    ET.SubElement(build, f"{{{THREE_MF_NS}}}item", {"objectid": "1"})

    content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
</Types>
"""
    relationships = f"""<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="{REL_NS}">
  <Relationship Target="/3D/3dmodel.model" Id="rel0"
    Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""
    model_xml = ET.tostring(model, encoding="utf-8", xml_declaration=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("3D/3dmodel.model", model_xml)


def read_3mf(path: Path) -> trimesh.Trimesh:
    """Read the subset emitted by :func:`write_3mf` for independent validation."""
    with zipfile.ZipFile(path) as archive:
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
    if model.attrib.get("unit") != "millimeter":
        raise ValueError(f"3MF must declare millimeter units: {path}")
    namespace = {"m": THREE_MF_NS}
    vertex_nodes = model.findall(".//m:vertices/m:vertex", namespace)
    triangle_nodes = model.findall(".//m:triangles/m:triangle", namespace)
    vertices = np.array(
        [[float(node.attrib[key]) for key in ("x", "y", "z")] for node in vertex_nodes],
        dtype=np.float64,
    )
    faces = np.array(
        [[int(node.attrib[key]) for key in ("v1", "v2", "v3")] for node in triangle_nodes],
        dtype=np.int64,
    )
    return trimesh.Trimesh(vertices=vertices, faces=faces, process=False)


def validate_mesh(
    mesh: trimesh.Trimesh, expected_bounds: tuple[float, float, float]
) -> dict[str, object]:
    extents = (
        float(mesh.extents[0]),
        float(mesh.extents[1]),
        float(mesh.extents[2]),
    )
    areas = np.asarray(mesh.area_faces)
    result: dict[str, object] = {
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "connected_components": len(mesh.split(only_watertight=False)),
        "degenerate_triangles": int(np.count_nonzero(areas < 1e-10)),
        "bounds_error_mm": _bounds_error(expected_bounds, extents),
        "triangle_count": len(mesh.faces),
    }
    if not result["watertight"] or not result["winding_consistent"]:
        raise ValueError(f"invalid mesh topology: {result}")
    if result["connected_components"] != 1 or result["degenerate_triangles"] != 0:
        raise ValueError(f"invalid mesh components: {result}")
    if cast(float, result["bounds_error_mm"]) > 0.08:
        raise ValueError(f"mesh bounds differ from B-rep: {result}")
    return result


def export_parts(
    output: Path = ROOT / "exports",
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> list[dict[str, object]]:
    """Export every manufactured part and reject failed round trips."""
    step_dir = output / "step"
    stl_dir = output / "stl"
    three_mf_dir = output / "3mf"
    report_dir = ROOT / "reports" / "validation"
    for directory in (step_dir, stl_dir, three_mf_dir, report_dir):
        directory.mkdir(parents=True, exist_ok=True)
    # Remove orphans first: a renamed or deleted part must not survive in the
    # release package as a stale file that still looks current.
    expected = {
        (directory, f"{name}{suffix}")
        for name in PARTS
        for directory, suffix in ((step_dir, ".step"), (stl_dir, ".stl"), (three_mf_dir, ".3mf"))
    }
    for directory, suffix in ((step_dir, "*.step"), (stl_dir, "*.stl"), (three_mf_dir, "*.3mf")):
        for existing in directory.glob(suffix):
            if (directory, existing.name) not in expected:
                existing.unlink()
    commit = source_commit()
    records: list[dict[str, object]] = []

    for name, definition in PARTS.items():
        source_shape = definition.builder(parameters)
        oriented = print_oriented(source_shape)
        expected_volume = source_shape.Volume()
        expected_bounds = bounds(source_shape)
        step_path = step_dir / f"{name}.step"
        stl_path = stl_dir / f"{name}.stl"
        three_mf_path = three_mf_dir / f"{name}.3mf"

        exporters.export(source_shape, str(step_path), exportType="STEP")
        reopened = cast(cq.Shape, importers.importStep(str(step_path)).val())
        step_volume_error = abs(reopened.Volume() - expected_volume)
        step_bounds_error = _bounds_error(expected_bounds, bounds(reopened))
        if not reopened.isValid() or step_volume_error > max(1e-3, expected_volume * 5e-8):
            raise ValueError(f"STEP round trip failed for {name}")
        if step_bounds_error > 1e-6:
            raise ValueError(f"STEP bounds round trip failed for {name}")

        exporters.export(
            oriented,
            str(stl_path),
            exportType="STL",
            tolerance=definition.mesh_tolerance,
            angularTolerance=definition.mesh_angular_tolerance,
        )
        stl_mesh = trimesh.load_mesh(stl_path, process=False)
        stl_mesh.merge_vertices()
        stl_mesh.remove_unreferenced_vertices()
        stl_result = validate_mesh(stl_mesh, expected_bounds)
        write_3mf(stl_mesh, three_mf_path, name, commit)
        three_mf_result = validate_mesh(read_3mf(three_mf_path), expected_bounds)

        record: dict[str, object] = {
            "part": name,
            "quantity": definition.quantity,
            "material": definition.material,
            "print_orientation": definition.print_orientation,
            "source_commit": commit,
            "brep_volume_mm3": expected_volume,
            "bounds_x_mm": expected_bounds[0],
            "bounds_y_mm": expected_bounds[1],
            "bounds_z_mm": expected_bounds[2],
            "step_volume_error_mm3": step_volume_error,
            "step_bounds_error_mm": step_bounds_error,
            "stl_sha256": sha256(stl_path),
            "step_sha256": sha256(step_path),
            "three_mf_sha256": sha256(three_mf_path),
            "stl_validation": stl_result,
            "three_mf_validation": three_mf_result,
            "evidence_label": definition.evidence_label,
        }
        records.append(record)

    (report_dir / "export_validation.json").write_text(
        json.dumps(records, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest_fields = [
        "part",
        "quantity",
        "material",
        "print_orientation",
        "source_commit",
        "step_sha256",
        "stl_sha256",
        "three_mf_sha256",
    ]
    with (output / "MANIFEST.csv").open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=manifest_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    return records


def export_gasket_templates(
    output: Path = ROOT / "exports" / "gasket_templates",
    parameters: DesignParameters = DEFAULT_PARAMETERS,
) -> list[Path]:
    """Export 1:1 DXF cutting profiles from the authoritative gasket B-reps."""
    output.mkdir(parents=True, exist_ok=True)
    gasket_builders = {
        "divider_gasket": divider_gasket,
        "driver_gasket": driver_gasket,
        "passive_radiator_gasket": passive_radiator_gasket,
    }
    written: list[Path] = []
    expected_names = {f"{name}.dxf" for name in gasket_builders}
    for existing in output.glob("*.dxf"):
        if existing.name not in expected_names:
            existing.unlink()
    for name, builder in gasket_builders.items():
        solid = builder(parameters)
        bottom = min(solid.Faces(), key=lambda face: face.Center().z)
        profile = cq.Workplane("XY").add(list(bottom.Wires()))
        path = output / f"{name}.dxf"
        exporters.exportDXF(profile, str(path))  # type: ignore[attr-defined]
        if not path.is_file() or path.stat().st_size < 200:
            raise ValueError(f"DXF template export failed for {name}")
        written.append(path)
    return written
