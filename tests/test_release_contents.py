"""The builder package must contain the complete required print set."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from satellite1_ultra.configuration import ROOT
from satellite1_ultra.official import (
    OFFICIAL_PRINT_PARTS_OPTIONAL_MM,
    OFFICIAL_PRINT_PARTS_REQUIRED,
)
from satellite1_ultra.release import RELEASE_NAME


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@pytest.mark.deep
def test_release_copies_official_printables_byte_for_byte() -> None:
    release = ROOT / "release" / RELEASE_NAME
    assert release.is_dir()
    for part in OFFICIAL_PRINT_PARTS_REQUIRED:
        copied = release / "OFFICIAL_PARTS" / "REQUIRED_SINGLE_MATERIAL" / part.filename
        assert copied.is_file()
        assert _sha256(copied) == _sha256(part.stl_path)
    for part in OFFICIAL_PRINT_PARTS_OPTIONAL_MM:
        copied = release / "OFFICIAL_PARTS" / "OPTIONAL_MULTI_MATERIAL" / part.filename
        assert copied.is_file()
        assert _sha256(copied) == _sha256(part.stl_path)
