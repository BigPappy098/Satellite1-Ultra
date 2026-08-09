"""A filtered export must describe only itself, and touch nothing else.

export_parts gained an `only` filter so the round-one Colab notebook could
build seven coupons instead of the whole catalogue. The first version still
wrote the catalogue-wide validation report afterwards, so a one-part run
replaced a 28-part record with a one-part one. Nothing in the export path
complained; it surfaced two suites away as 27 parts having vanished, and as a
KeyError in the reader that indexes that report.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from satellite1_ultra.configuration import ROOT, load_design_parameters
from satellite1_ultra.exporting import PARTS, export_parts

REPORT = ROOT / "reports" / "validation" / "export_validation.json"
MANIFEST = ROOT / "exports" / "MANIFEST.csv"


def _digest(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


@pytest.mark.geometry
def test_a_filtered_export_leaves_the_catalogue_reports_alone(tmp_path: Path) -> None:
    before = {path: _digest(path) for path in (REPORT, MANIFEST)}
    export_parts(tmp_path, load_design_parameters(), only=["cable_gland"])
    for path, digest in before.items():
        assert _digest(path) == digest, (
            f"a one-part export rewrote {path.relative_to(ROOT)}, which describes "
            "the whole catalogue"
        )


@pytest.mark.geometry
def test_a_filtered_export_writes_only_what_was_asked_for(tmp_path: Path) -> None:
    wanted = ["cable_gland", "coupon_gasket_cap"]
    export_parts(tmp_path, load_design_parameters(), only=wanted)
    for folder, suffix in (("step", ".step"), ("stl", ".stl"), ("3mf", ".3mf")):
        written = sorted(path.stem for path in (tmp_path / folder).glob(f"*{suffix}"))
        assert written == sorted(wanted), f"{folder} holds {written}, expected {sorted(wanted)}"


def test_an_unknown_part_is_refused_rather_than_silently_skipped() -> None:
    """Asking for a name that does not exist must not quietly export nothing."""
    with pytest.raises(KeyError, match="unknown parts"):
        export_parts(ROOT / "exports", load_design_parameters(), only=["not_a_part"])


def test_the_committed_report_still_covers_every_part() -> None:
    """The damage the filter used to do, checked against what ships."""
    assert REPORT.is_file(), "the export validation report is missing"
    recorded = {record["part"] for record in json.loads(REPORT.read_text(encoding="utf-8"))}
    missing = sorted(set(PARTS) - recorded)
    assert not missing, (
        f"the committed export report is missing {len(missing)} parts: {missing[:5]}"
    )
