"""Shared fixtures.

A fixture is the setup you would otherwise paste into every test. Copied setup is how
a test suite rots: the day the Mission schema gains a field, one edit here beats forty
edits spread across the suite.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTENT_ROOT = PROJECT_ROOT / "content"

#: The smallest document that satisfies docs/mission-schema.md. Tests deep-copy this
#: and break exactly one thing, so a failure names one cause instead of several.
VALID_MISSION: dict[str, Any] = {
    "id": "py-test-01",
    "title": "Double a number",
    "track": "python",
    "island": "foundations",
    "order": 1,
    "difficulty": "elementary",
    "tags": ["arithmetic"],
    "xp": 10,
    "concepts": ["variables"],
    "teaching": {
        "analogy": "Doubling is putting a second identical bag on the scale.",
        "explanation": "Multiplication repeats an addition a fixed number of times.",
        "worked_example": "greeting = 'hi' * 2\nprint(greeting)",
        "key_points": ["Multiplying by two is the same as adding a value to itself."],
    },
    "brief": "Write double(n) returning twice n.",
    "signature": {
        "entrypoint": "double",
        "stub": "def double(n):\n    pass\n",
    },
    "constraints": {
        "forbidden_builtins": ["pow"],
        "forbidden_imports": ["math"],
        "max_runtime_ms": 1000,
        "max_memory_mb": 64,
    },
    "tests": {
        "visible": [{"args": [2], "expect": 4}],
        "hidden": [{"args": [0], "expect": 0}, {"args": [-3], "expect": -6}],
    },
    "hints": [
        {"level": 1, "text": "What operation repeats a value?"},
        {"level": 2, "text": "You need the multiplication operator."},
        {"level": 3, "text": "letters = 'ab' * 2 gives 'abab'."},
    ],
    "solution": "def double(n):\n    return n * 2\n",
}


def write_mission(directory: Path, document: dict[str, Any], name: str = "mission.yaml") -> Path:
    """Write ``document`` as a mission YAML file and return its path."""
    path = directory / name
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


@pytest.fixture
def valid_mission_doc() -> dict[str, Any]:
    """A deep-ish copy of the canonical valid document, safe to mutate in a test."""
    import copy

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
def sample_solution() -> str:
    """A submission that solves the ``double`` mission used across the suite."""
    return textwrap.dedent("""
        def double(n):
            return n * 2
    """).strip()
