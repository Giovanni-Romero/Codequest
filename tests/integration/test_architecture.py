"""Executable enforcement of the layer rules in CLAUDE.md section 3.

An architecture rule that only lives in a document decays. This walks the real source
tree with ``ast`` and fails the build the moment a forbidden import appears, which is
the only way the boundary survives contact with a deadline.
"""

import ast
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src" / "codequest"

# layer -> package names it must never import from
FORBIDDEN_IMPORTS: dict[str, tuple[str, ...]] = {
    "tui": ("engine", "storage"),
    "engine": ("tui",),
    "services": ("tui",),
    "models": ("tui", "engine", "storage", "services", "mentor"),
}


def _imported_codequest_subpackages(source: str) -> set[str]:
    """Return the ``codequest.<name>`` subpackages imported by a module.

    Handles both ``import codequest.engine.loader`` and ``from codequest.engine import x``,
    including the relative form ``from ..engine import x`` used inside the package.
    """
    found: set[str] = set()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                if parts[0] == "codequest" and len(parts) > 1:
                    found.add(parts[1])
        elif isinstance(node, ast.ImportFrom) and node.module:
            parts = node.module.split(".")
            if parts[0] == "codequest" and len(parts) > 1:
                found.add(parts[1])
            elif node.level > 0:
                # Relative import: "from ..engine import x" -> parts[0] == "engine"
                found.add(parts[0])

    return found


def _modules_in(layer: str) -> list[Path]:
    return sorted((PACKAGE_ROOT / layer).rglob("*.py"))


@pytest.mark.parametrize("layer", sorted(FORBIDDEN_IMPORTS))
def test_layer_does_not_import_forbidden_packages(layer: str) -> None:
    """No module in ``layer`` imports a package it is not allowed to depend on."""
    forbidden = FORBIDDEN_IMPORTS[layer]
    violations: list[str] = []

    for module in _modules_in(layer):
        imported = _imported_codequest_subpackages(module.read_text(encoding="utf-8"))
        for banned in forbidden:
            if banned in imported:
                rel = module.relative_to(PACKAGE_ROOT.parent.parent)
                violations.append(f"{rel} imports codequest.{banned}")

    assert not violations, "Layer violation (see CLAUDE.md section 3):\n" + "\n".join(violations)


def test_expected_layers_exist() -> None:
    """The skeleton still has every layer this test is meant to police.

    Without this, deleting or renaming a package would make the checks above pass
    vacuously — a green test that verifies nothing.
    """
    missing = [layer for layer in FORBIDDEN_IMPORTS if not (PACKAGE_ROOT / layer).is_dir()]
    assert not missing, f"Missing packages: {missing}"
