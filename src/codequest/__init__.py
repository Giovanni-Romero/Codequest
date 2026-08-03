"""CodeQuest: a terminal game that teaches programming through missions.

The version is read from the installed package metadata rather than hardcoded here,
so ``pyproject.toml`` stays the single source of truth. The fallback covers the case
where the package is imported from a source tree that was never installed.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("codequest")
except PackageNotFoundError:  # pragma: no cover - only hit without an install
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
