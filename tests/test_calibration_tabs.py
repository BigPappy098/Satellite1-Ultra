"""The calibration tabs are the flow control, so they are load-bearing.

Calibration used to be two pages joined by prose telling a builder to fill in
the first two boxes, leave, print seven parts, and come back to box three.
Missing that instruction is expensive: every later measurement reads a feature
the printer's scale error has already moved, so an uncorrected print gives
readings that cannot be untangled. The tabs enforce the order structurally.

These drive the real wizard.js against the real generated calibrate.html, not a
restatement of either. An earlier wizard test reimplemented the arithmetic in
Python and passed happily while the shipped file had an inverted sign.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from satellite1_ultra.configuration import ROOT
from satellite1_ultra.site import CALIBRATION_TABS, generate_site

HARNESS = Path(__file__).parent / "support" / "calibration_tabs_harness.js"
SCALE_INPUTS = {"xy", "z"}


@pytest.fixture(scope="module")
def harness(tmp_path_factory: pytest.TempPathFactory) -> dict[str, object]:
    if shutil.which("node") is None:
        pytest.skip("node is required to run the shipped wizard.js")
    output = tmp_path_factory.mktemp("tabsite")
    generate_site(output)
    result = subprocess.run(
        ["node", str(HARNESS), str(output / "calibrate.html"), str(ROOT / "wizard" / "wizard.js")],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    return json.loads(result.stdout)


def test_the_page_has_the_tabs_the_flow_declares(harness: dict[str, object]) -> None:
    assert harness["tabKeys"] == [key for key, _label in CALIBRATION_TABS]


@pytest.mark.parametrize(
    "check",
    [
        "gotoTargetsExist",
        "oneVisible",
        "correctVisible",
        "selectedMarked",
        "persisted",
        "staleFlagged",
        "staleClears",
        "unknownIgnored",
    ],
)
def test_tab_behaviour(harness: dict[str, object], check: str) -> None:
    checks = harness["checks"]
    assert isinstance(checks, dict)
    assert checks.get(check) is True, f"tab behaviour {check} failed in the shipped wizard.js"


def _panel_inputs(html: str, key: str) -> list[str]:
    import re

    start = html.index(f'id="panel-{key}"')
    following = html.find('<section class="panel"', start + 10)
    chunk = html[start : following if following != -1 else len(html)]
    return re.findall(r'<(?:input|select)[^>]*id="([^"]+)"', chunk)


@pytest.fixture(scope="module")
def calibrate_html(tmp_path_factory: pytest.TempPathFactory) -> str:
    output = tmp_path_factory.mktemp("panelsite")
    generate_site(output)
    return (output / "calibrate.html").read_text(encoding="utf-8")


def test_the_scale_round_asks_for_scale_and_nothing_else(calibrate_html: str) -> None:
    """The point of the split: round one cannot show round two's boxes.

    If a later measurement appears on this tab, a builder can fill it in from
    an uncorrected print, which is the exact failure the two rounds exist to
    prevent.
    """
    assert set(_panel_inputs(calibrate_html, "scale")) == SCALE_INPUTS


def test_the_printing_tabs_ask_for_nothing(calibrate_html: str) -> None:
    for key in ("print1", "print2", "done"):
        assert _panel_inputs(calibrate_html, key) == [], (
            f"the {key} tab has input boxes; it is a download-and-print step"
        )


def test_every_remaining_measurement_lives_on_the_measure_tab(calibrate_html: str) -> None:
    measured = set(_panel_inputs(calibrate_html, "measure"))
    assert measured, "the measuring tab lost its inputs"
    assert not measured & SCALE_INPUTS, "a scale box leaked onto the measuring tab"


def test_only_the_first_tab_is_open_on_arrival(calibrate_html: str) -> None:
    first = CALIBRATION_TABS[0][0]
    assert f'id="panel-{first}"' in calibrate_html
    for key, _label in CALIBRATION_TABS[1:]:
        start = calibrate_html.index(f'id="panel-{key}"')
        opening = calibrate_html[start : calibrate_html.index(">", start)]
        assert "hidden" in opening, f"panel {key} is open before the builder reaches it"


SCALE_HARNESS = Path(__file__).parent / "support" / "scale_panel_harness.js"


@pytest.fixture(scope="module")
def scale_states() -> list[dict[str, object]]:
    """Walk the round-one panel through the states a builder actually hits."""
    if shutil.which("node") is None:
        pytest.skip("node is required to run the shipped wizard.js")
    result = subprocess.run(
        ["node", str(SCALE_HARNESS), str(ROOT / "wizard" / "wizard.js")],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    return json.loads(result.stdout)


def test_the_scale_panel_waits_before_anything_is_typed(
    scale_states: list[dict[str, object]],
) -> None:
    """An empty box is not a measurement, and must not read as a verdict."""
    first = scale_states[0]
    assert first["waiting"] is True
    assert first["codeShown"] is False
    assert first["perfect"] is False, (
        "the panel declared the printer perfect before anything was measured"
    )


def test_the_scale_panel_recovers_after_reporting_a_perfect_printer(
    scale_states: list[dict[str, object]],
) -> None:
    """The bug this exists for: the panel used to die the first time it said
    "dead on".

    Announcing a perfect printer was done by overwriting the container's
    innerHTML, which deleted the code element, the percentage line and both
    buttons out of the document. Every later keystroke hit a null guard and
    returned, so the round-one code could never appear again. With the boxes
    pre-filled at nominal it fired on page load, leaving the tab inert: the
    project owner typed a real 109.60 and the page did nothing at all.
    """
    by_label = {str(state["label"]): state for state in scale_states}
    perfect = by_label["typed the perfect numbers"]
    assert perfect["perfect"] is True and perfect["codeShown"] is False

    corrected = by_label["then corrected xy to 109.60"]
    assert corrected["codeShown"] is True, (
        "after showing the perfect-printer message the panel never recovered; "
        "a builder who corrects a typo gets a page that does nothing"
    )
    assert str(corrected["code"]).startswith("S1U1-")
    assert "+0.91%" in str(corrected["pct"])

    # And it must keep toggling, not just recover once.
    assert by_label["back to perfect"]["perfect"] is True
    assert by_label["and off again"]["codeShown"] is True
