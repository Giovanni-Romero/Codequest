"""Verdict and FailureReason: the outcome taxonomy of an attempt.

The taxonomy is the product of this module, not the boolean. "Test 3 failed" teaches
nothing; "expected 0 for an empty list, got None — your function returns nothing when
the loop never runs" teaches the lesson. Every failure mode gets its own name so the
evaluator can say something specific about it.
"""

from dataclasses import dataclass, field
from enum import StrEnum


class FailureReason(StrEnum):
    """Why an attempt did not pass.

    # [AI-ENG:failure-taxonomy] A graded taxonomy of failure is the core of any eval
    # harness. An LLM eval that only reports "correct / incorrect" cannot tell a
    # refusal from a hallucination from a malformed tool call, so it cannot tell you
    # what to fix. Same principle: name each failure mode before you count them.
    """

    PASSED = "passed"
    WRONG_ANSWER = "wrong_answer"
    RUNTIME_ERROR = "runtime_error"
    TIMEOUT = "timeout"
    MEMORY_EXCEEDED = "memory_exceeded"
    FORBIDDEN_CONSTRUCT = "forbidden_construct"
    SYNTAX_ERROR = "syntax_error"
    MISSING_ENTRYPOINT = "missing_entrypoint"
    HARNESS_ERROR = "harness_error"


@dataclass(frozen=True, slots=True)
class CaseOutcome:
    """The result of running one test case.

    ``detail`` is the player-facing sentence. For a hidden case it must describe the
    failure without disclosing the expected value, otherwise hidden tests stop being
    hidden the first time someone fails one.
    """

    index: int
    visible: bool
    passed: bool
    reason: FailureReason
    detail: str = ""
    stdout: str = ""


@dataclass(frozen=True, slots=True)
class Verdict:
    """The full outcome of one submission against one mission."""

    mission_id: str
    passed: bool
    reason: FailureReason
    summary: str
    outcomes: tuple[CaseOutcome, ...] = ()
    xp_awarded: int = 0
    stdout: str = ""
    diagnostics: dict[str, str] = field(default_factory=dict)

    @property
    def failed_outcomes(self) -> tuple[CaseOutcome, ...]:
        """Only the cases that did not pass, in the order they ran."""
        return tuple(outcome for outcome in self.outcomes if not outcome.passed)

    @property
    def first_failure(self) -> CaseOutcome | None:
        """The earliest failing case, which is the one worth showing first."""
        failures = self.failed_outcomes
        return failures[0] if failures else None

    @property
    def passed_count(self) -> int:
        """How many cases passed. Used for the "3 of 8" line in the results panel."""
        return sum(1 for outcome in self.outcomes if outcome.passed)
