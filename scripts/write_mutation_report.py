#!/usr/bin/env python3
"""Summarise the just-completed fail-to-pass mutation test run."""

from __future__ import annotations

import json
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
JUNIT = ROOT / "reports" / "validation" / "mutation-junit.xml"


def main() -> None:
    if not JUNIT.is_file():
        raise FileNotFoundError("mutation JUnit report is missing; run the mutation suite first")
    root = ET.parse(JUNIT).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    tests = sum(int(suite.attrib.get("tests", "0")) for suite in suites)
    failures = sum(int(suite.attrib.get("failures", "0")) for suite in suites)
    errors = sum(int(suite.attrib.get("errors", "0")) for suite in suites)
    skipped = sum(int(suite.attrib.get("skipped", "0")) for suite in suites)
    result = {
        "status": "PASS" if tests > 0 and failures == errors == skipped == 0 else "FAIL",
        "evidence": "VERIFIED_DIGITALLY",
        "mutations_exercised": tests,
        "test_failures": failures,
        "test_errors": errors,
        "skipped": skipped,
        "meaning": (
            "Each test injects a deliberate defect and passes only when the "
            "corresponding validation gate rejects it."
        ),
    }
    output = ROOT / "reports" / "validation" / "mutation_test.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    markdown = ROOT / "reports" / "validation" / "mutation_test.md"
    markdown.write_text(
        "# Mutation-test report\n\n"
        f"- Status: `{result['status']}`\n"
        f"- Deliberate defects rejected: {tests}\n"
        f"- Failures/errors/skips: {failures}/{errors}/{skipped}\n"
        "- Evidence: `VERIFIED_DIGITALLY`\n\n"
        f"{result['meaning']}\n",
        encoding="utf-8",
    )
    if result["status"] != "PASS":
        raise SystemExit(f"mutation report is not clean: {result}")


if __name__ == "__main__":
    main()
