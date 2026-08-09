"""Shared fixtures.

A fixture is the setup you would otherwise paste into every test. Copied setup is how
a test suite rots: the day the Mission schema gains a field, one edit here beats forty
edits spread across the suite.

The values and builders these wrap live in ``tests/helpers.py``. They are imported from
there rather than defined here because ``conftest`` is not a name a sibling test module
can safely import — see that file's docstring.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

from helpers import (
    CONTENT_ROOT,
    PROJECT_ROOT,
    SAMPLE_SOLUTION,
    VALID_MISSION,
    make_mission,
    write_mission,
)

__all__ = ["CONTENT_ROOT", "PROJECT_ROOT", "make_mission", "write_mission"]


@pytest.fixture
def valid_mission_doc() -> dict[str, Any]:
    """A deep-ish copy of the canonical valid document, safe to mutate in a test."""
    return copy.deepcopy(VALID_MISSION)


@pytest.fixture
def tmp_mission(tmp_path: Path, valid_mission_doc: dict[str, Any]) -> Path:
    """Path to a minimal valid mission file inside a per-test temp directory."""
    return write_mission(tmp_path, valid_mission_doc)


@pytest.fixture
def mission_factory(tmp_path: Path, valid_mission_doc: dict[str, Any]):
    """Return a callable that writes a mission with targeted mutations applied.

    Usage::

        path = mission_factory(difficulty="bogus")
        path = mission_factory(remove=["solution"])
    """
    counter = {"n": 0}

    def _factory(*, remove: list[str] | None = None, **overrides: Any) -> Path:
        document = {**valid_mission_doc, **overrides}
        for field_name in remove or []:
            document.pop(field_name, None)
        counter["n"] += 1
        return write_mission(tmp_path, document, f"mission-{counter['n']}.yaml")

    return _factory


@pytest.fixture
def build_mission():
    """Fixture wrapper around :func:`helpers.make_mission`, for tests that prefer injection."""
    return make_mission


@pytest.fixture
def sample_solution() -> str:
    """A submission that solves the ``double`` mission used across the suite."""
    return SAMPLE_SOLUTION
