"""Every file the website offers must exist in the release package.

The published site linked downloads at PRINT_THESE_FILES/1_CALIBRATION_FIRST and
two sibling folders, none of which have ever existed in the package. Every
download on every page was a 404, and nothing checked it, because the site was
generated from one set of names and the package written from another.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from satellite1_ultra.builder_files import (
    CALIBRATION_PRINT_ORDER,
    FABRIC_WRAP_PRINT_ORDER,
    ULTRA_PRINT_ORDER,
)
from satellite1_ultra.configuration import ROOT
from satellite1_ultra.exporting import PARTS
from satellite1_ultra.release import RELEASE_NAME
from satellite1_ultra.site import RAW, generate_site

RELEASE = ROOT / "release" / RELEASE_NAME


def _download_links(pages: list[Path]) -> set[str]:
    """Every href on the site that points into the release package."""
    found: set[str] = set()
    for page in pages:
        for href in re.findall(r'href="([^"]+)"', page.read_text(encoding="utf-8")):
            if href.startswith(RAW):
                found.add(href[len(RAW) :].lstrip("/"))
    return found


@pytest.fixture(scope="module")
def site_pages(tmp_path_factory: pytest.TempPathFactory) -> list[Path]:
    output = tmp_path_factory.mktemp("site")
    generate_site(output)
    return sorted(output.glob("*.html"))


def test_every_download_link_resolves_to_a_packaged_file(site_pages: list[Path]) -> None:
    links = _download_links(site_pages)
    assert links, "the site offered no downloads at all"
    missing = sorted(link for link in links if not (RELEASE / link).is_file())
    assert not missing, "site links with no file in the release package:\n  " + "\n  ".join(missing)


def test_the_site_offers_every_enclosure_part(site_pages: list[Path]) -> None:
    """Including the fabric-wrap skins, which were described but never linked."""
    links = _download_links(site_pages)
    names = {Path(link).name for link in links}
    for expected in (
        "01_MAIN_SPEAKER_BODY.3mf",
        "09_MIC_ISOLATORS_TPU_PRINT_FOUR.3mf",
        "10F_OUTER_SKIN_BOTTOM_FOR_FABRIC.3mf",
        "11F_OUTER_SKIN_MIDDLE_FOR_FABRIC.3mf",
        "12F_OUTER_SKIN_TOP_FOR_FABRIC.3mf",
        "driver_gasket.dxf",
    ):
        assert expected in names, f"the site never offers {expected}"


def test_both_formats_are_offered(site_pages: list[Path]) -> None:
    links = _download_links(site_pages)
    assert any(link.endswith(".3mf") for link in links)
    assert any(link.endswith(".stl") for link in links), "no STL download is offered anywhere"


def test_printed_parts_are_labelled_with_the_material_they_export_as(
    site_pages: list[Path],
) -> None:
    """The page hard-coded ASA for the mic isolators, which are TPU.

    Printing those rigid removes the decoupling they exist to provide, so a
    wrong label here is a build defect, not a typo.
    """
    combined = "\n".join(page.read_text(encoding="utf-8") for page in site_pages)
    # Builder file name -> source part, so a row can be checked against PARTS.
    by_filename = {
        filename: source
        for order in (CALIBRATION_PRINT_ORDER, ULTRA_PRINT_ORDER, FABRIC_WRAP_PRINT_ORDER)
        for source, filename, _quantity in order
    }
    # Each row is: <a ...>FILENAME</a> ... <span class="mat KIND">MATERIAL</span>
    rows = re.findall(
        r'<a href="[^"]+/([^/"]+)">\1</a>.*?<span class="mat [a-z]+">([^<]+)</span>',
        combined,
        flags=re.DOTALL,
    )
    checked = 0
    for filename, shown in rows:
        source = by_filename.get(filename)
        if source is None:  # official upstream parts are not in PARTS
            continue
        expected = str(PARTS[source].material)
        assert shown == expected, (
            f"{filename} is shown as {shown!r} but exports as {expected!r}; "
            "printing it in the wrong filament is a build defect"
        )
        checked += 1
    assert checked >= len(ULTRA_PRINT_ORDER), f"only {checked} rows were checked against PARTS"
