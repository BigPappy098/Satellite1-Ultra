"""Every review finding must satisfy the schema the review contract names.

Findings are the project's record of what is wrong and what was done about it,
and unresolved CRITICAL and HIGH ones are release blockers. Nothing checked
them until a finding was written with an evidence_label outside the enum and
only an ad-hoc script noticed. A malformed finding is worse than a missing one:
it looks filed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from satellite1_ultra.configuration import ROOT

REVIEW_DIR = ROOT / "reports" / "review"
SCHEMA = json.loads((REVIEW_DIR / "finding.schema.json").read_text(encoding="utf-8"))
FILES = sorted(path for path in REVIEW_DIR.glob("*.json") if path.name != "finding.schema.json")


def _findings(path: Path) -> list[dict[str, object]]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, list) else [loaded]


def test_there_are_findings_to_check() -> None:
    """A glob that silently matches nothing would pass every test below."""
    assert FILES, "no review findings found"


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_findings_match_the_schema(path: Path) -> None:
    properties = SCHEMA["properties"]
    for finding in _findings(path):
        where = f"{path.name}:{finding.get('id', '?')}"
        for key in SCHEMA.get("required", []):
            assert key in finding, f"{where} is missing {key}"
        for key in finding:
            assert key in properties, f"{where} has unknown key {key}"
        for key, spec in properties.items():
            if key in finding and "enum" in spec:
                assert finding[key] in spec["enum"], (
                    f"{where} has {key}={finding[key]!r}, not one of {spec['enum']}"
                )


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_open_findings_carry_an_owner_and_say_where_they_stand(path: Path) -> None:
    """An open blocker with no owner is a note, not a finding."""
    for finding in _findings(path):
        if finding.get("status") != "OPEN":
            continue
        where = f"{path.name}:{finding.get('id', '?')}"
        assert finding.get("owner"), f"{where} is OPEN with no owner"
        assert finding.get("verification_method"), f"{where} is OPEN with no way to verify it"


def test_finding_ids_are_unique_across_the_review_record() -> None:
    """Two findings sharing an id makes one of them unciteable."""
    seen: dict[str, str] = {}
    for path in FILES:
        for finding in _findings(path):
            key = str(finding.get("id"))
            assert key not in seen, f"{key} appears in both {seen[key]} and {path.name}"
            seen[key] = path.name
