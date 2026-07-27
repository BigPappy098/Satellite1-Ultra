#!/usr/bin/env python3
"""Create a checksum manifest for preserved manufacturer primary sources."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "references" / "manufacturer"
OUTPUT = SOURCE_DIR / "MANIFEST.csv"
RETRIEVED = "2026-07-27"

URLS = {
    "Dayton_DMA105-PR_spec.pdf": "https://www.daytonaudio.com/images/resources/295-590--dayton-audio-dma105-pr-spec-sheet.pdf",
    "Dayton_ND91-4_Klippel.pdf": "https://www.daytonaudio.com/images/resources/290-226--nd91-4-klippel-data.pdf",
    "Dayton_ND91-4_spec_2026-02-26.pdf": "https://www.daytonaudio.com/images/resources/290-226--dayton-audio-nd91-4-specifications.pdf",
    "SB_Acoustics_SB12PACR-00.pdf": "https://sbacoustics.com/wp-content/uploads/2020/02/SB12PACR-00.pdf",
    "SB_Acoustics_SB12PFCR-00.pdf": "https://sbacoustics.com/wp-content/uploads/2020/02/SB12PFCR-00.pdf",
    "ScanSpeak_10F-4424G00_advanced.pdf": "https://www.scan-speak.dk/datasheet/pdf/10f-4424g00.pdf",
    "TI_TAS2780_revB.pdf": "https://www.ti.com/lit/ds/symlink/tas2780.pdf",
    "Tectonic_TEBM65C20F-4_rev1.2.pdf": "https://www.tectonicaudiolabs.com/wp-content/uploads/2022/10/TEBM65C20F-4-Rev-1.2.pdf",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    rows = []
    for path in sorted(SOURCE_DIR.glob("*.pdf")):
        rows.append(
            {
                "file": path.name,
                "source_url": URLS[path.name],
                "retrieval_date": RETRIEVED,
                "sha256": sha256(path),
                "evidence_label": "DERIVED_FROM_MANUFACTURER_DRAWING",
            }
        )
    with OUTPUT.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
