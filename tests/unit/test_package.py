"""Sentinel tests for the package skeleton built in Phase 0.

These do not test game logic — there is none yet. They prove the packaging works:
the package imports, and the version the code reports is the version declared in
``pyproject.toml``. A drift between those two is a real bug that ships silently.
"""

import tomllib
from pathlib import Path

import codequest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_package_exposes_a_version() -> None:
    """The installed package reports a version, not the uninstalled fallback."""
    assert codequest.__version__ != "0.0.0+unknown", (
        "codequest is not installed. Run: pip install -e '.[dev]'"
    )


def test_version_matches_pyproject() -> None:
    """The runtime version equals the one declared in pyproject.toml."""
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert codequest.__version__ == pyproject["project"]["version"]
