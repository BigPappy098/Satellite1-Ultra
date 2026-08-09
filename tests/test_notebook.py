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
from pathlib import Path

import pytest

from satellite1_ultra.builder_files import CALIBRATION_STAGE_TWO, ULTRA_PRINT_ORDER
from satellite1_ultra.configuration import CALIBRATION_LIMITS, ROOT

TEST_PIECES = ROOT / "notebooks" / "make_my_test_pieces.ipynb"
PARTS = ROOT / "notebooks" / "make_my_parts.ipynb"
NOTEBOOKS = (TEST_PIECES, PARTS)
WIZARD = ROOT / "wizard" / "wizard.js"


def _cells(notebook: Path = PARTS) -> list[str]:
    loaded = json.loads(notebook.read_text(encoding="utf-8"))
    return ["".join(cell["source"]) for cell in loaded["cells"]]


def _source(notebook: Path = PARTS) -> str:
    return "\n".join(_cells(notebook))


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=lambda p: p.stem)
def test_notebook_reads_the_same_keys_the_wizard_writes(notebook: Path) -> None:
    """The code is a positional list; a key order mismatch silently misassigns."""
    match = re.search(r"^KEYS = \[(.*?)\]", _source(notebook), re.MULTILINE | re.DOTALL)
    assert match, f"{notebook.stem} no longer declares KEYS"
    keys = re.findall(r'"([a-z_]+)"', match.group(1))
    assert keys == list(CALIBRATION_LIMITS), (
        "the notebook decodes the correction code into a different key order "
        "than the validator defines, so every value lands on the wrong parameter"
    )


def test_each_notebook_wants_its_own_code_and_refuses_the_other() -> None:
    """Two notebooks, two codes. Pasting the wrong one must stop, not proceed.

    A round-one code carries scale and nothing else, so building the enclosure
    from it would size every hole, seat and gasket gap to a value the builder
    has not measured yet -- and it would look like it worked.
    """
    wizard = WIZARD.read_text(encoding="utf-8")
    prefixes = {}
    for name, pattern in (
        ("round_one", r'PREFIX_ROUND_ONE = "([^"]+)"'),
        ("final", r'PREFIX_FINAL = "([^"]+)"'),
    ):
        found = re.search(pattern, wizard)
        assert found, f"wizard.js no longer defines the {name} prefix"
        prefixes[name] = found.group(1)
    assert prefixes["round_one"] != prefixes["final"]

    for notebook, wanted, refused in (
        (TEST_PIECES, prefixes["round_one"], prefixes["final"]),
        (PARTS, prefixes["final"], prefixes["round_one"]),
    ):
        source = _source(notebook)
        assert f'WANT = "{wanted}"' in source, (
            f"{notebook.stem} does not accept {wanted!r}, the code the website "
            "sends builders here with"
        )
        assert f'OTHER = "{refused}"' in source, (
            f"{notebook.stem} does not recognise {refused!r} as the other "
            "notebook's code, so pasting it would fall through to a generic error"
        )
        assert "raise SystemExit" in source, f"{notebook.stem} does not stop on a bad code"


def test_the_two_notebooks_build_different_things() -> None:
    """The split is the point: round one must not hand back the enclosure."""
    tests_source = _source(TEST_PIECES)
    parts_source = _source(PARTS)
    assert "CALIBRATION_STAGE_TWO" in tests_source
    assert "ULTRA_PRINT_ORDER" not in tests_source, (
        "the test-piece notebook packages enclosure parts; a builder would get "
        "a 45-hour print sized from two measurements"
    )
    assert "ULTRA_PRINT_ORDER" in parts_source
    assert "only=WANTED" in tests_source, (
        "the test-piece notebook builds the whole catalogue to hand back seven "
        "coupons, costing a builder ten minutes of Colab time for nothing"
    )


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=lambda p: p.stem)
def test_notebook_imports_orders_that_exist(notebook: Path) -> None:
    """It imported CALIBRATION_PRINT_ORDER, which is no longer the staged name."""
    from satellite1_ultra import builder_files

    imported = set()
    for match in re.finditer(
        r"from satellite1_ultra\.builder_files import \(?([^)\n]+)\)?", _source(notebook)
    ):
        imported.update(name.strip().rstrip(",") for name in match.group(1).split(","))
    assert imported, f"{notebook.stem} no longer imports any print order"
    for name in imported:
        assert hasattr(builder_files, name), (
            f"{notebook.stem} imports builder_files.{name}, which does not exist"
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


def test_both_notebooks_install_the_same_environment() -> None:
    """A builder runs both. Two different pins means two different builds.

    Colab pre-installs numba, which wants numpy below 2.1; pinning above it made
    pip print a red dependency ERROR partway through a first-time build. Nothing
    here imports numba, so it was cosmetic, but the two notebooks must at least
    agree with each other or the test pieces and the enclosure come off
    different toolchains.
    """
    installs = []
    for notebook in NOTEBOOKS:
        cell = next(c for c in _cells(notebook) if "pip install" in c)
        installs.append(next(line for line in cell.splitlines() if "pip install" in line))
    assert installs[0] == installs[1], (
        f"the notebooks install different environments:\n  {installs[0]}\n  {installs[1]}"
    )
    assert "numpy<2.1" in installs[0], (
        "numpy is no longer held below Colab's numba constraint; a first-time "
        "builder will see a red dependency ERROR mid-build"
    )


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=lambda p: p.stem)
def test_the_fetch_step_does_not_depend_on_an_editable_install(notebook: Path) -> None:
    """`pip install -e .` refuses on any Python outside the pyproject pin.

    pyproject requires >=3.12,<3.13, which describes CI rather than the source:
    every module here parses as 3.11. Colab moves its Python from time to time,
    so on the wrong day the install failed and the next cell died with a bare
    "No module named 'satellite1_ultra'" that named nothing useful. The package
    is pure Python, so putting src on sys.path is equivalent and cannot fail for
    a version reason.
    """
    fetch = next(
        cell for cell in _cells(notebook) if "clone" in cell and "Satellite1-Ultra.git" in cell
    )
    # Comments in this cell explain what was removed and why, so match on the
    # lines that actually run rather than on the prose describing them.
    executable = [
        line for line in fetch.splitlines() if line.strip() and not line.lstrip().startswith("#")
    ]
    for line in executable:
        assert "-e ." not in line, (
            "the fetch step installs the package as editable again; it will "
            f"refuse on any Colab Python outside the pyproject pin: {line.strip()}"
        )
    assert any("sys.path.insert" in line for line in executable), (
        "the fetch step no longer puts src on the path"
    )
    assert any("src" in line for line in executable)


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=lambda p: p.stem)
def test_setup_failures_are_not_piped_into_silence(notebook: Path) -> None:
    """A hidden failure becomes an unexplained crash two cells later."""
    for cell in _cells(notebook):
        if "Satellite1-Ultra.git" not in cell:
            continue
        assert "| tail" not in cell, (
            "the fetch step pipes its output through tail, which is how a "
            "failed install got hidden and surfaced as a bare ModuleNotFoundError"
        )
        assert "returncode" in cell and "SystemExit" in cell, (
            "the fetch step does not check whether the download succeeded"
        )


def test_the_source_really_is_importable_below_the_pyproject_pin() -> None:
    """The claim the fetch step rests on, checked rather than asserted.

    If a module ever adopts 3.12-only syntax, putting src on the path stops
    being equivalent to installing, and the notebooks need a different fix.
    """
    import ast

    offenders = []
    for path in sorted((ROOT / "src" / "satellite1_ultra").glob("*.py")):
        try:
            ast.parse(path.read_text(encoding="utf-8"), feature_version=(3, 11))
        except SyntaxError as error:
            offenders.append(f"{path.name}: {error.msg}")
    assert not offenders, (
        "these modules need Python 3.12 syntax, so the notebooks can no longer "
        "rely on sys.path alone: " + "; ".join(offenders)
    )


#: Package name on PyPI for each importable module whose names differ.
_PYPI_NAME = {"yaml": "pyyaml", "PIL": "pillow", "stl": "numpy-stl"}


def _import_chain(entry_modules: set[str]) -> dict[str, set[str]]:
    """Every non-stdlib top-level import reachable from these modules."""
    import ast
    import sys

    stdlib = set(sys.stdlib_module_names)
    source_dir = ROOT / "src" / "satellite1_ultra"
    seen: set[str] = set()
    queue = list(entry_modules)
    external: dict[str, set[str]] = {}
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        path = source_dir / f"{name}.py"
        if not path.is_file():
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                modules = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                modules = [node.module.split(".")[0]]
            else:
                continue
            for module in modules:
                if module.startswith("satellite1_ultra"):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        queue.append(node.module.split(".")[-1])
                elif module not in stdlib:
                    external.setdefault(module, set()).add(path.name)
    return external


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=lambda p: p.stem)
def test_the_install_cell_covers_everything_the_notebook_imports(notebook: Path) -> None:
    """A hand-written install list drifts from the code it has to support.

    Removing the editable install took away the only thing that had ever
    mentioned this project's dependencies, and the install cell listed three
    packages by hand. trimesh was not among them, so the notebook downloaded the
    design, imported it happily, and died in the build cell on
    "No module named 'trimesh'" -- several minutes in, after the slow steps.

    This walks the real import chain from what each notebook imports, so the
    list cannot fall behind the code again.
    """
    source = _source(notebook)
    entry = set(re.findall(r"from satellite1_ultra\.(\w+) import", source))
    assert entry, f"{notebook.stem} imports nothing from the package"

    # Match the command, not a comment that mentions one: several cells discuss
    # `pip install -e .` in prose explaining why it was removed.
    install = next(line for line in source.splitlines() if line.lstrip().startswith("!pip install"))
    installed = set()
    for token in install.split():
        # Strip quoting before splitting on the specifier, or "numpy<2.1"
        # parses to an empty string and reads as "not installed".
        name = re.split(r"[=<>!~]", token.strip('"').strip("'"))[0].strip()
        if name and not name.startswith(("!", "-", "|", "2>")) and name not in {"install", "tail"}:
            installed.add(name.lower())

    missing = []
    for module in _import_chain(entry):
        package = _PYPI_NAME.get(module, module).lower()
        if package not in installed:
            missing.append(f"{module} (pip: {package})")
    assert not missing, (
        f"{notebook.stem} imports these but never installs them, so it will fail "
        f"partway through a build: {sorted(missing)}"
    )


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=lambda p: p.stem)
def test_the_fetch_step_leaves_the_directory_before_deleting_it(notebook: Path) -> None:
    """Re-running the cell must not saw off the branch it is sitting on.

    The cell ends with os.chdir(REPO), so a second run begins with the working
    directory inside the tree it is about to remove. Deleting it leaves the
    process with no cwd, and git dies with "Unable to read current working
    directory" before writing anything -- which reads as a download failure and
    is not one. Colab keeps one kernel across cell runs, so this is the normal
    case, not an edge case.
    """
    fetch = next(
        cell for cell in _cells(notebook) if "clone" in cell and "Satellite1-Ultra.git" in cell
    )
    lines = [
        line for line in fetch.splitlines() if line.strip() and not line.lstrip().startswith("#")
    ]
    step_out = next((i for i, line in enumerate(lines) if 'os.chdir("/content")' in line), None)
    remove = next((i for i, line in enumerate(lines) if "rmtree(REPO" in line), None)
    assert remove is not None, "the fetch step no longer clears the previous download"
    assert step_out is not None, (
        "the fetch step deletes the repository without stepping out of it first; "
        "a second run will fail with 'Unable to read current working directory'"
    )
    assert step_out < remove, (
        f"the fetch step steps out at line {step_out} but deletes at line {remove}; "
        "the order matters, not merely the presence"
    )
