"""The Colab notebook is the only way a builder gets corrected parts.

Nothing checked it. It went on importing CALIBRATION_PRINT_ORDER and writing
folders named 1_PRINT_THESE_TEST_PIECES_AGAIN long after calibration was split
into two rounds, so a round-one code silently returned all eight test pieces
and the whole enclosure. It ran without error the entire time, which is exactly
why a test is needed rather than a read-through.
"""

from __future__ import annotations

import json
import re

import pytest

from satellite1_ultra.builder_files import CALIBRATION_STAGE_TWO, ULTRA_PRINT_ORDER
from satellite1_ultra.configuration import CALIBRATION_LIMITS, ROOT

NOTEBOOK = ROOT / "notebooks" / "make_my_parts.ipynb"
WIZARD = ROOT / "wizard" / "wizard.js"


def _cells() -> list[str]:
    loaded = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    return ["".join(cell["source"]) for cell in loaded["cells"]]


def _source() -> str:
    return "\n".join(_cells())


def test_notebook_reads_the_same_keys_the_wizard_writes() -> None:
    """The code is a positional list; a key order mismatch silently misassigns."""
    match = re.search(r"^KEYS = \[(.*?)\]", _source(), re.MULTILINE | re.DOTALL)
    assert match, "the notebook no longer declares KEYS"
    keys = re.findall(r'"([a-z_]+)"', match.group(1))
    assert keys == list(CALIBRATION_LIMITS), (
        "the notebook decodes the correction code into a different key order "
        "than the validator defines, so every value lands on the wrong parameter"
    )


def test_notebook_and_wizard_agree_on_the_round_prefixes() -> None:
    """A prefix the other side does not know about is a rejected code."""
    wizard = WIZARD.read_text(encoding="utf-8")
    for name, pattern in (
        ("round one", r'PREFIX_ROUND_ONE = "([^"]+)"'),
        ("final", r'PREFIX_FINAL = "([^"]+)"'),
    ):
        found = re.search(pattern, wizard)
        assert found, f"wizard.js no longer defines the {name} prefix"
        assert f'"{found.group(1)}"' in _source(), (
            f"the notebook does not recognise the {name} prefix {found.group(1)!r} "
            "that wizard.js emits"
        )


def test_notebook_branches_on_the_round() -> None:
    """Round one must not hand back the enclosure, which is the bug this had."""
    source = _source()
    assert "ROUND_ONE" in source, "the notebook does not distinguish the two rounds"
    packaging = next(cell for cell in _cells() if "make_archive" in cell)
    assert re.search(r"if ROUND_ONE:", packaging), (
        "the packaging cell does not branch on the round, so round one returns "
        "whatever the final code returns"
    )


def test_notebook_imports_orders_that_exist() -> None:
    """It imported CALIBRATION_PRINT_ORDER, which is no longer the staged name."""
    from satellite1_ultra import builder_files

    imported = set()
    for match in re.finditer(r"from satellite1_ultra\.builder_files import \(([^)]*)\)", _source()):
        imported.update(name.strip().rstrip(",") for name in match.group(1).split())
    assert imported, "the notebook no longer imports any print order"
    for name in imported:
        assert hasattr(builder_files, name), (
            f"the notebook imports builder_files.{name}, which does not exist"
        )
    assert "CALIBRATION_STAGE_TWO" in imported, (
        "round one must package the staged round-two set, not the whole calibration list"
    )


@pytest.mark.parametrize(
    "order,label",
    [(CALIBRATION_STAGE_TWO, "round two test pieces"), (ULTRA_PRINT_ORDER, "enclosure")],
)
def test_every_packaged_part_has_an_export(
    order: tuple[tuple[str, str, int], ...], label: str
) -> None:
    """The notebook copies exports/3mf and exports/stl by source name."""
    for source, _friendly, _quantity in order:
        for folder, suffix in (("3mf", ".3mf"), ("stl", ".stl")):
            path = ROOT / "exports" / folder / f"{source}{suffix}"
            assert path.is_file(), f"{label}: the notebook would copy a missing {path.name}"
