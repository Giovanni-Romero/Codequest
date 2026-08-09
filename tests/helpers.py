"""Shared constants and builders, importable from any suite.

These used to live in ``tests/conftest.py`` and be reached with ``from conftest import
...``. That worked only by accident: ``conftest`` is not a stable module name. The moment
a suite grows its own ``conftest.py`` — as ``tests/integration/`` did — pytest puts that
directory first on ``sys.path`` and the name resolves to the *nearest* conftest, not the
shared one, and every sibling import breaks.

``tests`` is on ``pythonpath`` (see ``pyproject.toml``), so ``from helpers import ...``
means the same file no matter which directory pytest was pointed at. Fixtures still live
in ``conftest.py``, which is where pytest looks for them; only the plain values and
functions moved here.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any

import yaml

from codequest.models.mission import (
    Difficulty,
    Hint,
    Mission,
    Signature,
    Teaching,
    TestCase,
)

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

SAMPLE_SOLUTION = textwrap.dedent("""
    def double(n):
        return n * 2
""").strip()


def write_mission(directory: Path, document: dict[str, Any], name: str = "mission.yaml") -> Path:
    """Write ``document`` as a mission YAML file and return its path."""
    path = directory / name
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


def make_mission(**overrides: Any) -> Mission:
    """Build a minimal valid Mission in memory, overriding only what a test cares about.

    Deliberately a plain function rather than only a fixture: the runner tests build
    missions inside helpers that pytest does not inject into.
    """
    defaults: dict[str, Any] = {
        "id": "py-foundations-06",
        "title": "Sum of a list",
        "track": "python",
        "island": "foundations",
        "order": 2,
        "difficulty": Difficulty.ELEMENTARY,
        "xp": 10,
        "concepts": ("accumulator-pattern",),
        "teaching": Teaching("analogy", "explanation", "example", ("point",)),
        "brief": "brief",
        "signature": Signature("sum_list", "def sum_list(numbers):\n    pass\n"),
        "tests": (
            TestCase(args=([1, 2, 3],), expect=6, visible=True),
            TestCase(args=([],), expect=0, visible=False),
            TestCase(args=([7],), expect=7, visible=False),
        ),
        "hints": (Hint(1, "question"), Hint(2, "construct"), Hint(3, "pattern")),
        "solution": "def sum_list(numbers):\n    return 0\n",
    }
    return Mission(**{**defaults, **overrides})
