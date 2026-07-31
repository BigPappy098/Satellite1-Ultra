"""Builder documentation must be complete and internally consistent."""

from __future__ import annotations

import shutil
from pathlib import Path

from satellite1_ultra.configuration import ROOT
from satellite1_ultra.doc_validation import (
    _hand_written_image_errors,
    _rendered_names,
    validate_documentation,
)


def test_generated_documentation_is_complete() -> None:
    assert validate_documentation()["status"] == "PASS"


def test_readme_images_come_from_the_render_pass(tmp_path: Path) -> None:
    """A README image that no pipeline step regenerates has to fail the gate.

    The README once pointed at a render produced only by a side script.  It was
    present locally, so an existence check passed, and then ``clean`` deleted it
    and the published page lost its image.  Existing is not enough: the render
    pass has to name the file.
    """
    root = tmp_path
    (root / "src" / "satellite1_ultra").mkdir(parents=True)
    (root / "reports" / "renders").mkdir(parents=True)
    shutil.copy(
        ROOT / "src" / "satellite1_ultra" / "renders.py",
        root / "src" / "satellite1_ultra" / "renders.py",
    )
    produced = sorted(_rendered_names(root))
    assert produced, "expected the render pass to declare some file names"
    orphan = "reports/renders/not_in_the_pipeline.png"
    for reference in (f"reports/renders/{produced[0]}", orphan):
        (root / reference).write_bytes(b"")

    (root / "README.md").write_text(f"![ok](reports/renders/{produced[0]})\n")
    assert _hand_written_image_errors(root) == []

    # Present on disk, but nothing regenerates it.
    (root / "README.md").write_text(f"![stale]({orphan})\n")
    assert any("does not produce" in error for error in _hand_written_image_errors(root))

    # Referenced and absent.
    (root / "README.md").write_text("![gone](reports/renders/absent.png)\n")
    assert any("missing image" in error for error in _hand_written_image_errors(root))
