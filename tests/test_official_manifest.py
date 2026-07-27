"""Official-source provenance tests."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "reference-assets" / "MANIFEST.csv"


def digest(path: Path) -> str:
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


@pytest.mark.requires_official_assets
def test_official_manifest_checksums() -> None:
    with MANIFEST.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) >= 100
    for row in rows:
        path = ROOT / row["preserved_path"]
        assert path.is_file()
        assert path.stat().st_size == int(row["bytes"])
        assert digest(path) == row["sha256"]
        assert len(row["source_commit"]) == 40
        assert row["license"] != "NOASSERTION"
