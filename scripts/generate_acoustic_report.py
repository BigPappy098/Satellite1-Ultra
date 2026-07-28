#!/usr/bin/env python3
"""Compatibility entry point for the authoritative CAD-coupled acoustic report."""

from satellite1_ultra.analysis import generate_acoustic_reports


def main() -> None:
    summary = generate_acoustic_reports()
    if summary["status"] != "PASS":
        raise SystemExit(f"acoustic validation failed: {summary}")


if __name__ == "__main__":
    main()
