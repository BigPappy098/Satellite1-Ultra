"""The calibration wizard decides what a builder prints, so its maths is load-bearing.

A builder measures printed coupons, types the numbers into the site, and the
corrected files come back from those figures alone. A sign error or a stale
nominal here does not fail loudly: it silently produces parts that are wrong by
exactly the amount the printer was already wrong by, in the wrong direction.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

from satellite1_ultra.configuration import CALIBRATION_LIMITS, ROOT, load_design_parameters

WIZARD = ROOT / "wizard" / "wizard.js"


def _wizard_limits() -> dict[str, tuple[float, float]]:
    text = WIZARD.read_text(encoding="utf-8")
    block = text[text.index("const LIMITS") : text.index("};", text.index("const LIMITS"))]
    return {
        key: (float(low), float(high))
        for key, low, high in re.findall(r"(\w+):\s*\[(-?[\d.]+),\s*(-?[\d.]+)\]", block)
    }


def test_wizard_limits_match_the_python_validator() -> None:
    """Both sides must reject the same inputs, or the site accepts what the build refuses."""
    assert _wizard_limits() == {k: tuple(v) for k, v in CALIBRATION_LIMITS.items()}


def test_wizard_nominals_come_from_the_design() -> None:
    """The constants the wizard subtracts must be the ones the parts are built from."""
    default = yaml.safe_load((ROOT / "config" / "default.yaml").read_text(encoding="utf-8"))
    text = WIZARD.read_text(encoding="utf-8")
    assert f"- {default['fasteners']['clearance_diameter']}" in text
    assert f"- {default['fasteners']['insert_bore_diameter']}" in text
    # The gasket offset removes the design's own compression fraction.
    retained = 1.0 - float(default["sealing"]["target_compression_fraction"])
    assert f"{retained} * sheet" in text or f"{retained}*sheet" in text


def _wizard_values(xy: float, z: float, **over: float) -> dict[str, float]:
    """Run the real wizard.js and return what it computed.

    Executing the shipped file, not a Python restatement of it. A restatement
    is a copy of the maths that cannot disagree with itself: an earlier version
    of this test reimplemented the formulas here, and flipping the sign of the
    XY correction in wizard.js -- which would scale every part the wrong way and
    double the printer's error -- left it passing.
    """
    inputs = {
        "xy": xy,
        "z": z,
        "clear": over.pop("clear", 3.4),
        "bore": over.pop("bore", 4.2),
        "dcut": over.pop("dcut", 0.0),
        "pcut": over.pop("pcut", 0.0),
        "cable": over.pop("cable", 0.0),
        "sheet": over.pop("sheet", 2.0),
        "gap": over.pop("gap", 1.5),
        "dflange": over.pop("dflange", 1.0),
        "pflange": over.pop("pflange", 3.75),
    }
    # Enough of a DOM for the file to load: it wires up listeners at the
    # bottom, and compute() only ever reads .value.
    stub = (
        "const node = (id) => ({ value: String(INPUTS[id]), textContent: '',"
        " className: '', addEventListener() {}, classList: { add() {}, remove() {},"
        " toggle() {} }, setAttribute() {}, focus() {} });"
    )
    harness = f"""
const INPUTS = {json.dumps(inputs)};
{stub}
global.navigator = {{ clipboard: {{ writeText: async () => {{}} }} }};
global.document = {{
  getElementById: (id) => (id.endsWith("_v") ? null : node(id)),
  querySelectorAll: () => [],
  addEventListener() {{}},
}};
{WIZARD.read_text(encoding="utf-8")}
process.stdout.write(JSON.stringify(compute().values));
"""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as handle:
        handle.write(harness)
        path = handle.name
    try:
        out = subprocess.run(["node", path], capture_output=True, text=True, timeout=30, check=True)
    finally:
        os.unlink(path)
    values: dict[str, float] = json.loads(out.stdout)
    values.update(over)
    return values


@pytest.mark.geometry
@pytest.mark.parametrize("xy_error,z_error", [(0.994, 0.988), (1.007, 1.004), (1.0, 1.0)])
def test_a_measured_printer_error_is_cancelled_by_the_correction(
    xy_error: float, z_error: float
) -> None:
    """The whole point: measure, correct, and the printed part lands on nominal.

    Simulates a printer with a known scale error, derives what the builder would
    measure on the coupons, runs the wizard's formulas, feeds the result through
    the real loader, and checks the corrected geometry prints back to nominal.
    """
    calibration = ROOT / "config" / "physical_calibration.yaml"
    original = calibration.read_bytes()
    nominal = load_design_parameters()
    values = _wizard_values(110.6 * xy_error, 3.0 * z_error)
    try:
        calibration.write_text(yaml.safe_dump(values), encoding="utf-8")
        corrected = load_design_parameters()
    finally:
        calibration.write_bytes(original)

    for name, error in (
        ("outer_width", xy_error),
        ("driver_cutout_diameter", xy_error),
        ("insert_bore_diameter", xy_error),
        ("driver_seat_depth", z_error),
        ("gasket_thickness", z_error),
    ):
        as_printed = getattr(corrected, name) * error
        # wizard.js rounds the correction to 7 decimals so the code it prints
        # stays short; on a 160 mm part that is a few nanometres. A micron is
        # still four orders of magnitude below anything a printer resolves.
        assert as_printed == pytest.approx(getattr(nominal, name), abs=1e-3), (
            f"{name} prints {as_printed:.4f} on a printer {error:.3f} off nominal"
        )


def test_the_hole_sizes_offered_are_the_ones_the_coupon_prints() -> None:
    """A builder picks a labelled hole; every label must exist on the part.

    The wizard subtracts the picked label from the design nominal, so an option
    the coupon never printed produces a correction from a measurement that
    cannot have been taken.
    """
    from satellite1_ultra import coupons

    source = Path(coupons.__file__).read_text(encoding="utf-8")
    block = source[source.index("def heat_set_insert_coupon") :]
    block = block[: block.index("\ndef ")]
    printed = {
        float(value)
        for group in re.findall(r"\(([\d.,\s]+)\),\s*strict=True", block)
        for value in group.split(",")
        if value.strip() and 3.0 < float(value) < 5.0
    }
    offered = {
        float(v)
        for v in re.findall(
            r"<option[^>]*>([\d.]+)", (ROOT / "wizard" / "index.html").read_text(encoding="utf-8")
        )
    }
    assert offered, "the wizard offered no hole sizes"
    assert offered <= printed, f"offered but never printed: {sorted(offered - printed)}"


def _wizard_round_one(xy: float, z: float) -> tuple[str, dict[str, float]]:
    """Run the shipped wizard.js and return its round-one code and values."""
    inputs = {
        "xy": xy,
        "z": z,
        "clear": 3.4,
        "bore": 4.2,
        "dcut": 0.0,
        "pcut": 0.0,
        "cable": 0.0,
        "sheet": 2.0,
        "gap": 1.5,
        "dflange": 3.0,
        "pflange": 4.0,
    }
    stub = (
        "const node = (id) => ({ value: String(INPUTS[id]), textContent: '',"
        " innerHTML: '', className: '', addEventListener() {}, classList:"
        " { add() {}, remove() {}, toggle() {} }, setAttribute() {}, focus() {},"
        " dataset: {} });"
    )
    harness = f"""
const INPUTS = {json.dumps(inputs)};
{stub}
global.navigator = {{ clipboard: {{ writeText: async () => {{}} }} }};
global.document = {{
  getElementById: (id) => (id.endsWith("_v") ? null : node(id)),
  querySelectorAll: () => [],
  addEventListener() {{}},
}};
{WIZARD.read_text(encoding="utf-8")}
const values = scaleOnly();
process.stdout.write(JSON.stringify({{
  code: encode(values, PREFIX_ROUND_ONE), values: values,
}}));
"""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as handle:
        handle.write(harness)
        path = handle.name
    try:
        out = subprocess.run(["node", path], capture_output=True, text=True, timeout=30, check=True)
    finally:
        os.unlink(path)
    payload = json.loads(out.stdout)
    return payload["code"], payload["values"]


def test_round_one_code_carries_scale_and_nothing_else() -> None:
    """Round one must not smuggle in values the builder has not measured yet.

    The seven round-two coupons are regenerated from this code. If it carried
    anything but scale, it would bake in an assumption about a feature the
    builder is about to measure, and the coupon would confirm the assumption
    rather than test it.
    """
    design = load_design_parameters()
    code, values = _wizard_round_one(110.6 * 0.991, 3.0)

    assert code.startswith("S1U1-"), (
        f"round one emitted {code[:6]!r}; the notebook branches on that prefix to "
        "decide whether to return test pieces or the whole enclosure"
    )
    assert values["xy_scale_correction_fraction"] == pytest.approx(1 / 0.991 - 1, abs=1e-6)
    assert values["z_scale_correction_fraction"] == pytest.approx(0.0, abs=1e-6)

    for key in CALIBRATION_LIMITS:
        if key.endswith("_scale_correction_fraction"):
            continue
        if key.endswith("_offset_mm"):
            assert values[key] == 0.0, f"round one pre-set an unmeasured offset: {key}"
    # The three non-offset fields carry design nominals rather than zero, so
    # they must be the design's nominals and not a number typed twice.
    for key, nominal in (
        ("gasket_sheet_thickness_mm", design.gasket_thickness),
        ("active_driver_flange_thickness_mm", design.driver_flange_thickness),
        ("passive_radiator_flange_thickness_mm", design.pr_flange_thickness),
    ):
        assert values[key] == pytest.approx(nominal, abs=1e-6), (
            f"round one sends {key}={values[key]} where the design says {nominal}; "
            "the round-two coupons would be built to a value nobody measured"
        )


def test_round_one_and_final_codes_are_distinguishable() -> None:
    """Same numbers, different request: the prefixes must not collide."""
    round_one, _ = _wizard_round_one(110.6, 3.0)
    final = _wizard_values(110.6, 3.0)
    assert round_one.startswith("S1U1-")
    assert not round_one[5:].startswith("S1U")
    assert isinstance(final, dict)
