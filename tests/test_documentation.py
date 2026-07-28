"""Builder documentation must be complete and internally consistent."""

from __future__ import annotations

from satellite1_ultra.doc_validation import validate_documentation


def test_generated_documentation_is_complete() -> None:
    assert validate_documentation()["status"] == "PASS"
