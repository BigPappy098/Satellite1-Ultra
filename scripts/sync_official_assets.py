"""Copy official FutureProofHomes source assets and generate immutable provenance.

The upstream clones are read-only inputs under ``references/upstream-repos``.
Files are copied byte-for-byte into ``reference-assets/official``.
"""

from __future__ import annotations

import csv
import hashlib
import shutil
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "references" / "upstream-repos"
DESTINATION = ROOT / "reference-assets" / "official"
MANIFEST = ROOT / "reference-assets" / "MANIFEST.csv"
REPOSITORIES = ROOT / "references" / "FUTUREPROOFHOMES_REPOSITORIES.csv"
RETRIEVAL_DATE = date(2026, 7, 27)

RELEVANT_REPOSITORIES = (
    "Satellite1-Hardware",
    "Satellite1-ESPHome",
    "Documentation",
    "Satellite1-XMOS",
    "Satellite1-Enclosures",
    "home-assistant-voice-pe",
    "Satellite1-HA-Automations",
    "Satellite1-RPi",
    "Satellite1-RPi-SDK",
    "Satellite1-RPi-Image",
    "Satellite1-RPi-Setup",
)

ASSET_REPOSITORIES = {
    "Satellite1-Enclosures": {
        "license": "CERN-OHL-S-2.0",
        "extensions": {".step", ".stp", ".stl", ".3mf"},
    },
    "Satellite1-Hardware": {
        "license": "CERN-OHL-S-2.0",
        "extensions": {".step", ".stp", ".kicad_pcb", ".kicad_sch"},
    },
}


@dataclass(frozen=True)
class Repository:
    """Pinned upstream repository metadata."""

    name: str
    commit: str
    branch: str
    license_id: str
    relevant_reason: str


REASONS = {
    "Satellite1-Hardware": "Authoritative board source and exported board STEP models",
    "Satellite1-ESPHome": "Amplifier configuration, DSP controls, power and firmware behavior",
    "Documentation": "Official assembly, enclosure, firmware, and hardware documentation",
    "Satellite1-XMOS": "XMOS audio pipeline, microphones, AEC, and DSP firmware",
    "Satellite1-Enclosures": "Authoritative enclosure, upper stack, and board reference CAD",
    "home-assistant-voice-pe": "Satellite1 firmware integration fork and audio pipeline context",
    "Satellite1-HA-Automations": "Official Satellite1 user/control integration context",
    "Satellite1-RPi": "Alternative core integration and mechanical expansion context",
    "Satellite1-RPi-SDK": "Alternative core software constraints",
    "Satellite1-RPi-Image": "Alternative core deployment context",
    "Satellite1-RPi-Setup": "Alternative core deployment and hardware setup context",
}


def git(repo: Path, *args: str) -> str:
    """Run a read-only git query."""
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def sha256(path: Path) -> str:
    """Return a streaming SHA-256 checksum."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository_license(repo: Path) -> str:
    """Resolve SPDX-like repository license from known project files."""
    if repo.name in ASSET_REPOSITORIES:
        return str(ASSET_REPOSITORIES[repo.name]["license"])
    candidates = sorted(repo.glob("LICENSE*")) + sorted(repo.glob("COPYING*"))
    if not candidates:
        return "NOASSERTION"
    text = candidates[0].read_text(encoding="utf-8", errors="ignore").lower()
    if "gnu general public license" in text and "version 3" in text:
        return "GPL-3.0"
    if "apache license" in text and "version 2.0" in text:
        return "Apache-2.0"
    if "mit license" in text:
        return "MIT"
    if "cern open hardware licence version 2" in text:
        return "CERN-OHL-S-2.0"
    return "NOASSERTION"


def collect_repositories() -> list[Repository]:
    """Collect pinned metadata for each relevant repository."""
    rows: list[Repository] = []
    for name in RELEVANT_REPOSITORIES:
        repo = UPSTREAM / name
        if not (repo / ".git").exists():
            raise FileNotFoundError(f"Missing upstream clone: {repo}")
        rows.append(
            Repository(
                name=name,
                commit=git(repo, "rev-parse", "HEAD"),
                branch=git(repo, "branch", "--show-current"),
                license_id=repository_license(repo),
                relevant_reason=REASONS[name],
            )
        )
    return rows


def write_repository_inventory(repositories: list[Repository]) -> None:
    """Write organization research inventory."""
    REPOSITORIES.parent.mkdir(parents=True, exist_ok=True)
    with REPOSITORIES.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            (
                "repository",
                "url",
                "branch",
                "commit",
                "license",
                "retrieval_date",
                "relevance",
            )
        )
        for repo in repositories:
            writer.writerow(
                (
                    repo.name,
                    f"https://github.com/FutureProofHomes/{repo.name}",
                    repo.branch,
                    repo.commit,
                    repo.license_id,
                    RETRIEVAL_DATE.isoformat(),
                    repo.relevant_reason,
                )
            )


def copy_assets(repositories: list[Repository]) -> int:
    """Copy official assets byte-for-byte and write their manifest."""
    by_name = {repo.name: repo for repo in repositories}
    DESTINATION.mkdir(parents=True, exist_ok=True)
    manifest_rows: list[tuple[str, ...]] = []

    for repo_name, specification in ASSET_REPOSITORIES.items():
        source_root = UPSTREAM / repo_name
        destination_root = DESTINATION / repo_name
        extensions = specification["extensions"]
        assert isinstance(extensions, set)
        assets = sorted(
            path
            for path in source_root.rglob("*")
            if path.is_file() and path.suffix.lower() in extensions
        )
        for source in assets:
            relative = source.relative_to(source_root)
            destination = destination_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            if sha256(source) != sha256(destination):
                raise RuntimeError(f"Checksum changed while copying {source}")
            repo = by_name[repo_name]
            manifest_rows.append(
                (
                    destination.relative_to(ROOT).as_posix(),
                    repo_name,
                    f"https://github.com/FutureProofHomes/{repo_name}",
                    repo.commit,
                    relative.as_posix(),
                    str(specification["license"]),
                    RETRIEVAL_DATE.isoformat(),
                    str(destination.stat().st_size),
                    sha256(destination),
                )
            )

        for license_file in sorted(source_root.glob("LICENSE*")):
            license_dest = destination_root / license_file.name
            shutil.copy2(license_file, license_dest)

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            (
                "preserved_path",
                "source_repository",
                "source_url",
                "source_commit",
                "original_path",
                "license",
                "retrieval_date",
                "bytes",
                "sha256",
            )
        )
        writer.writerows(manifest_rows)
    return len(manifest_rows)


def main() -> None:
    """Synchronize and inventory official sources."""
    repositories = collect_repositories()
    write_repository_inventory(repositories)
    count = copy_assets(repositories)
    print(f"Preserved {count} official assets in {DESTINATION}")


if __name__ == "__main__":
    main()
