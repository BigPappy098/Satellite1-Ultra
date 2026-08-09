"""Declared dependencies must be ones this project actually needs.

Four runtime dependencies and one dev dependency were declared and imported
nowhere: pydantic, rich, numpy-stl and pytest-cov had no consumer at all, and
shapely looked the same but is not -- trimesh's base install requires numpy
alone, and networkx, Pillow, scipy and shapely are its "easy" extra, imported
when trimesh loads. Removing shapely on the strength of a grep would have
quietly degraded trimesh instead of failing loudly.

Every exact pin also becomes a conflict on any machine that already has the
package, which is how a builder ended up staring at a red pip ERROR in the
middle of their first Colab run.
"""

from __future__ import annotations

import ast
import re
import tomllib

import pytest

from satellite1_ultra.configuration import ROOT

#: Distribution name -> the module names it provides, where they differ.
PROVIDES = {
    "numpy-stl": {"stl"},
    "Pillow": {"PIL"},
    "PyYAML": {"yaml"},
}

#: Declared but never imported here, and deliberately so. Each needs a reason,
#: because "nothing imports it" is exactly what a stale dependency looks like.
INDIRECT = {
    "networkx": "trimesh 'easy' extra, imported when trimesh loads",
    "Pillow": "trimesh 'easy' extra, imported when trimesh loads",
    "shapely": "trimesh 'easy' extra, imported when trimesh loads",
}

#: Invoked as commands, not imported.
COMMAND_LINE = {"mypy", "ruff", "pytest"}


def _declared() -> dict[str, list[str]]:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]
    return {
        "runtime": project["dependencies"],
        "dev": project.get("optional-dependencies", {}).get("dev", []),
    }


def _imported() -> set[str]:
    found: set[str] = set()
    for folder in ("src", "tests"):
        for path in (ROOT / folder).rglob("*.py"):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:  # pragma: no cover - a broken file fails elsewhere
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    found.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    found.add(node.module.split(".")[0])
    return {name.lower() for name in found}


@pytest.mark.parametrize("group", ["runtime", "dev"])
def test_every_declared_dependency_is_used_or_explained(group: str) -> None:
    imported = _imported()
    unexplained = []
    for requirement in _declared()[group]:
        name = re.split(r"[=<>!~\[;]", requirement)[0].strip()
        modules = PROVIDES.get(name, {name.replace("-", "_")})
        if {module.lower() for module in modules} & imported:
            continue
        if name in COMMAND_LINE or name in INDIRECT:
            continue
        unexplained.append(name)
    assert not unexplained, (
        f"these {group} dependencies are imported nowhere and have no recorded "
        f"reason: {sorted(unexplained)}. Either drop them, or add them to "
        "INDIRECT with the reason they are needed anyway."
    )


def test_the_indirect_dependencies_are_still_declared() -> None:
    """The allowlist must not outlive the pins it excuses.

    If one of trimesh's extras is dropped from pyproject, the entry here would
    go on silently excusing a dependency that no longer exists.
    """
    declared = {
        re.split(r"[=<>!~\[;]", requirement)[0].strip() for requirement in _declared()["runtime"]
    }
    stale = sorted(set(INDIRECT) - declared)
    assert not stale, f"INDIRECT excuses dependencies that are no longer declared: {stale}"


def test_trimesh_extras_are_declared_because_trimesh_does_not_declare_them() -> None:
    """The reason INDIRECT exists, asserted against trimesh's own metadata.

    If a future trimesh moves these into its base requirements, carrying our own
    pins stops being necessary and starts being a source of conflicts.
    """
    import importlib.metadata as metadata

    requires = metadata.distribution("trimesh").requires or []
    base = {
        re.split(r"[=<>!~\[; ]", requirement)[0].strip().lower()
        for requirement in requires
        if "extra ==" not in requirement
    }
    for name in INDIRECT:
        assert name.lower() not in base, (
            f"trimesh now requires {name} itself, so this project no longer "
            "needs to pin it separately"
        )
