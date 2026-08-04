"""Executable enforcement of the layer rules in CLAUDE.md section 3.

An architecture rule that only lives in a document decays. This walks the real source
tree with ``ast`` and fails the build the moment a forbidden import appears, which is
the only way the boundary survives contact with a deadline.
"""

import ast
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src" / "codequest"

# layer -> packages it must never import from, at any scope.
FORBIDDEN_IMPORTS: dict[str, tuple[str, ...]] = {
    "tui": ("engine", "storage"),
    "engine": ("tui",),
    "services": ("tui",),
    "storage": ("tui", "engine", "services"),
    "models": ("tui", "engine", "storage", "services", "mentor"),
}

#: Packages nothing may import **at module scope**, which is what makes them optional.
#: Deleting ``src/codequest/mentor/`` has to leave a working game, and that holds only
#: while no module pulls it in on the way up. An import inside a function is the correct
#: pattern and is what ``tui/widgets/mentor_chat.py`` does.
OPTIONAL_PACKAGES = ("mentor",)


def _imported_codequest_subpackages(source: str, module_scope_only: bool = False) -> set[str]:
    """Return the ``codequest.<name>`` subpackages imported by a module.

    Handles both ``import codequest.engine.loader`` and ``from codequest.engine import x``,
    including the relative form ``from ..engine import x`` used inside the package.

    ``module_scope_only`` is the difference between two questions that look alike:

    - *Does this layer depend on that one?* Any import counts, wherever it sits. Hiding a
      forbidden dependency inside a function does not make it not a dependency.
    - *Is that package optional?* Only a **module-scope** import counts, because an import
      inside a function is exactly how you make a package optional, and flagging it would
      forbid the pattern the rule is trying to require.
    """
    found: set[str] = set()
    tree = ast.parse(source)
    nodes = tree.body if module_scope_only else ast.walk(tree)

    for node in nodes:
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


@pytest.mark.parametrize("optional", OPTIONAL_PACKAGES)
def test_an_optional_package_is_never_imported_at_module_scope(optional: str) -> None:
    """Proves the feature can be deleted, without deleting it.

    The mentor is optional by design: no Ollama, no problem, and removing the folder
    entirely must leave the game working. That property is invisible in normal use and
    breaks the first time someone adds a convenient top-level import.
    """
    violations: list[str] = []

    for module in sorted(PACKAGE_ROOT.rglob("*.py")):
        if optional in module.parts:
            continue  # the package may of course import itself
        imported = _imported_codequest_subpackages(
            module.read_text(encoding="utf-8"), module_scope_only=True
        )
        if optional in imported:
            rel = module.relative_to(PACKAGE_ROOT.parent.parent)
            violations.append(f"{rel} imports codequest.{optional} at module scope")

    assert not violations, (
        f"'{optional}' is meant to be optional, so it must only be imported inside a "
        "function:\n" + "\n".join(violations)
    )


def test_printed_strings_are_ascii_only() -> None:
    """Non-ASCII in a ``print``ed string turns into mojibake on a Windows console.

    The Windows terminal defaults to cp1252, so an em dash in a CLI failure message
    reached the player as a black diamond. That bug was real and this test exists
    because of it.

    Two exemptions, both deliberate:

    - **Docstrings and comments.** Read in an editor, never printed.
    - **``tui/``.** Textual owns its output stream and writes UTF-8 regardless of the
      console codepage, and ``docs/art-direction.md`` deliberately chose Unicode
      box-drawing with no ASCII fallback — the thin rules *are* the chart aesthetic.
      Applying the CLI rule there would forbid the entire visual language.

    The distinction that matters: this is about ``print`` reaching a raw console, not
    about non-ASCII being unsafe in general.
    """
    offenders: list[str] = []
    printed_surface = [p for p in PACKAGE_ROOT.rglob("*.py") if "tui" not in p.parts]

    for module in sorted(printed_surface):
        tree = ast.parse(module.read_text(encoding="utf-8"))
        docstrings = {
            node.body[0].value
            for node in ast.walk(tree)
            if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
            and node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
        }

        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            if node in docstrings:
                continue
            if not node.value.isascii():
                rel = module.relative_to(PACKAGE_ROOT.parent.parent)
                offenders.append(f"{rel}:{node.lineno}: {node.value[:60]!r}")

    assert not offenders, "non-ASCII in a runtime string:\n" + "\n".join(offenders)


def test_expected_layers_exist() -> None:
    """The skeleton still has every layer this test is meant to police.

    Without this, deleting or renaming a package would make the checks above pass
    vacuously — a green test that verifies nothing.
    """
    missing = [layer for layer in FORBIDDEN_IMPORTS if not (PACKAGE_ROOT / layer).is_dir()]
    assert not missing, f"Missing packages: {missing}"
