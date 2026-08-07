"""Mission, TestCase, Hint and Constraints dataclasses.

Pure data. Everything here is frozen, so a Mission loaded once can be handed to the
guard, the runner, the evaluator and the TUI with no risk that one of them mutates it
under the others. The schema these mirror lives in ``docs/mission-schema.md``.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Difficulty(StrEnum):
    """How hard a mission is. The value doubles as the YAML spelling."""

    ELEMENTARY = "elementary"
    SIMPLE = "simple"
    MODERATE = "moderate"
    CHALLENGING = "challenging"
    EXPERT = "expert"


#: XP awarded per difficulty, from docs/mission-schema.md. The loader validates a
#: mission's declared ``xp`` against this table so content cannot drift from the rules.
XP_BY_DIFFICULTY: dict[Difficulty, int] = {
    Difficulty.ELEMENTARY: 10,
    Difficulty.SIMPLE: 20,
    Difficulty.MODERATE: 30,
    Difficulty.CHALLENGING: 45,
    Difficulty.EXPERT: 60,
}


@dataclass(frozen=True, slots=True)
class TestCase:
    """One input/expected-output pair for a mission.

    Args:
        args: Positional arguments passed to the entrypoint, in order.
        kwargs: Keyword arguments passed to the entrypoint.
        expect: The value the entrypoint must return. Ignored when ``raises`` is set.
        raises: The exact name of the exception type the entrypoint must raise, e.g.
            ``"ValueError"``. Mutually exclusive with ``expect`` — a case either has a
            return value or an error, never both. Matched by **exact type name** rather
            than by subclass: for a teaching game "expected ValueError, got TypeError"
            is the useful message, and accepting any ``Exception`` subclass would let an
            accidental crash pass as if it were the intended answer.
        tolerance: Absolute tolerance for float comparison. ``None`` means the
            evaluator requires exact equality — the right default, because a mission
            about integers should fail when it returns something that merely looks close.
        visible: Whether the player sees this case. Visible cases teach the shape of
            the problem; hidden cases catch the shortcut that fakes it.
    """

    # pytest collects any class named Test* as a test suite. This is a domain model
    # that happens to share the prefix, so opt out explicitly rather than rename it
    # away from the spelling used in docs/mission-schema.md.
    __test__ = False

    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)
    expect: Any = None
    raises: str | None = None
    tolerance: float | None = None
    visible: bool = True

    @property
    def expects_error(self) -> bool:
        """Whether this case passes by raising rather than by returning."""
        return self.raises is not None


@dataclass(frozen=True, slots=True)
class Hint:
    """One rung of the hint ladder.

    Level 1 asks a question, level 2 names the construct, level 3 shows the pattern
    applied to a *different* problem. See ``docs/mission-schema.md`` for the rule that
    hint 3 must never be pasteable into the editor as an answer.
    """

    level: int
    text: str


@dataclass(frozen=True, slots=True)
class Constraints:
    """Limits applied to a submission before and during execution.

    Defaults match ``docs/mission-schema.md``. ``forbidden_builtins`` is what keeps a
    mission honest: a mission that teaches you to build a sum must forbid ``sum``,
    otherwise it teaches nothing.
    """

    forbidden_builtins: frozenset[str] = frozenset()
    forbidden_imports: frozenset[str] = frozenset()
    max_runtime_ms: int = 2000
    max_memory_mb: int = 128


@dataclass(frozen=True, slots=True)
class Signature:
    """The function the engine will call, and the editor's starting content."""

    entrypoint: str
    stub: str


@dataclass(frozen=True, slots=True)
class Teaching:
    """The lesson shown before the player writes anything.

    ``worked_example`` must solve a *different* problem from the mission. If the mission
    sums numbers, the example joins strings — otherwise the lesson hands over the answer.
    """

    analogy: str
    explanation: str
    worked_example: str
    key_points: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Mission:
    """A complete mission: the lesson, the task, the limits and the tests.

    This is the contract between ``content/`` and the engine. Nothing in the engine may
    reach into the YAML directly; it goes through this object, which is why the loader
    is the only place that knows the file format.
    """

    id: str
    title: str
    track: str
    island: str
    order: int
    difficulty: Difficulty
    xp: int
    concepts: tuple[str, ...]
    teaching: Teaching
    brief: str
    signature: Signature
    tests: tuple[TestCase, ...]
    hints: tuple[Hint, ...]
    solution: str
    constraints: Constraints = field(default_factory=Constraints)
    tags: tuple[str, ...] = ()
    source_path: str | None = None

    @property
    def visible_tests(self) -> tuple[TestCase, ...]:
        """Cases the player is allowed to see."""
        return tuple(case for case in self.tests if case.visible)

    @property
    def hidden_tests(self) -> tuple[TestCase, ...]:
        """Cases that verify without teaching. Their values must never be shown."""
        return tuple(case for case in self.tests if not case.visible)

    def hint_at(self, level: int) -> Hint | None:
        """Return the hint for ``level``, or ``None`` when the mission has no such rung."""
        for hint in self.hints:
            if hint.level == level:
                return hint
        return None
