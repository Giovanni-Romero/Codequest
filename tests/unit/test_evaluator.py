"""Tests for the evaluator.

Two things are being verified. That the taxonomy maps correctly — a timeout must not
be reported as a wrong answer — and that hidden cases never leak their expected value,
which is the only thing keeping them able to catch a hardcoded return.
"""

from __future__ import annotations

import pytest

from codequest.engine.evaluator import evaluate, values_match, verdict_from_guard
from codequest.engine.guard import GuardReport
from codequest.engine.runners.base import ExecutionResult
from codequest.models.mission import TestCase
from codequest.models.verdict import FailureReason
from helpers import make_mission


def ok(value) -> ExecutionResult:
    return ExecutionResult(returned=value, status="ok")


# ------------------------------------------------------------------- values_match


@pytest.mark.parametrize(
    ("expected", "actual", "match"),
    [
        (6, 6, True),
        (6, 7, False),
        (0, 0, True),
        ("abc", "abc", True),
        ([1, 2], [1, 2], True),
        ([1, 2], [2, 1], False),
        (None, None, True),
        (0, None, False),
    ],
)
def test_exact_comparison_by_default(expected, actual, match):
    assert values_match(expected, actual, None) is match


def test_true_does_not_satisfy_an_expected_one():
    """``True == 1`` in Python. A mission expecting 1 must not accept True."""
    assert values_match(1, True, None) is False
    assert values_match(True, 1, None) is False


def test_tolerance_allows_float_drift():
    assert values_match(0.3, 0.30000000000000004, 1e-9) is True
    assert values_match(0.3, 0.4, 1e-9) is False


def test_nan_equals_nan_when_both_sides_are_nan():
    """``nan != nan`` by IEEE rule, but a mission expecting nan and getting nan is right."""
    nan = float("nan")

    assert values_match(nan, nan, None) is True
    assert values_match(nan, nan, 0.1) is True


def test_tolerance_rejects_a_non_numeric_answer():
    assert values_match(1.0, "1.0", 0.1) is False


# ----------------------------------------------------------------- passing verdict


def test_all_cases_passing_awards_the_mission_xp():
    mission = make_mission()
    results = [ok(6), ok(0), ok(7)]

    verdict = evaluate(mission, mission.tests, results)

    assert verdict.passed
    assert verdict.reason is FailureReason.PASSED
    assert verdict.xp_awarded == mission.xp
    assert verdict.passed_count == 3


# ----------------------------------------------------------------- failing verdicts


def test_a_wrong_answer_on_a_visible_case_shows_expected_and_actual():
    mission = make_mission()
    results = [ok(99), ok(0), ok(7)]

    verdict = evaluate(mission, mission.tests, results)

    assert not verdict.passed
    assert verdict.reason is FailureReason.WRONG_ANSWER
    assert verdict.xp_awarded == 0
    assert "6" in verdict.summary and "99" in verdict.summary


def test_a_returned_none_gets_the_extra_nudge():
    """The single most common beginner bug deserves a sentence, not just a mismatch."""
    mission = make_mission()

    verdict = evaluate(mission, mission.tests, [ok(None), ok(0), ok(7)])

    assert "returned nothing" in verdict.summary


def test_a_hidden_failure_never_leaks_its_expected_value():
    """If the expected value leaked, hidden tests would become a lookup table."""
    mission = make_mission(
        tests=(TestCase(args=([],), expect=1234567, visible=False),),
    )

    verdict = evaluate(mission, mission.tests, [ok(0)])

    assert not verdict.passed
    assert "1234567" not in verdict.summary
    assert "1234567" not in verdict.outcomes[0].detail


def test_timeout_is_not_reported_as_a_wrong_answer():
    mission = make_mission()
    results = [ExecutionResult(status="timeout", timed_out=True), ok(0), ok(7)]

    verdict = evaluate(mission, mission.tests, results)

    assert verdict.reason is FailureReason.TIMEOUT
    assert "never finishes" in verdict.summary


def test_runtime_error_carries_the_exception_type():
    mission = make_mission()
    crash = ExecutionResult(
        status="error", exception_type="ZeroDivisionError", exception_message="division by zero"
    )

    verdict = evaluate(mission, mission.tests, [crash, ok(0), ok(7)])

    assert verdict.reason is FailureReason.RUNTIME_ERROR
    assert "ZeroDivisionError" in verdict.summary


def test_memory_exhaustion_has_its_own_reason():
    mission = make_mission()
    results = [ExecutionResult(status="memory"), ok(0), ok(7)]

    verdict = evaluate(mission, mission.tests, results)

    assert verdict.reason is FailureReason.MEMORY_EXCEEDED


def test_missing_entrypoint_has_its_own_reason():
    mission = make_mission()
    results = [
        ExecutionResult(status="missing_entrypoint", exception_message="no function named 'x'"),
        ok(0),
        ok(7),
    ]

    verdict = evaluate(mission, mission.tests, results)

    assert verdict.reason is FailureReason.MISSING_ENTRYPOINT


def test_an_unknown_runner_status_becomes_a_harness_error():
    """A new runner inventing a status must fail loudly as our bug, not as the player's."""
    mission = make_mission()

    verdict = evaluate(mission, mission.tests, [ExecutionResult(status="wat"), ok(0), ok(7)])

    assert verdict.reason is FailureReason.HARNESS_ERROR


def test_the_earliest_failure_sets_the_verdict_reason():
    """Reporting the first failure keeps the message aligned with the reading order."""
    mission = make_mission()
    results = [ok(99), ExecutionResult(status="timeout", timed_out=True), ok(7)]

    verdict = evaluate(mission, mission.tests, results)

    assert verdict.reason is FailureReason.WRONG_ANSWER


def test_a_case_result_mismatch_is_an_engine_bug_not_a_player_one():
    mission = make_mission()

    verdict = evaluate(mission, mission.tests, [ok(6)])

    assert verdict.reason is FailureReason.HARNESS_ERROR


def test_hardcoded_return_passes_visible_and_fails_hidden():
    """The reason hidden cases exist, proven end to end at the evaluator level."""
    mission = make_mission()
    results = [ok(6), ok(6), ok(6)]  # always returns 6

    verdict = evaluate(mission, mission.tests, results)

    assert not verdict.passed
    assert verdict.outcomes[0].passed
    assert not verdict.outcomes[1].passed


# -------------------------------------------------------------- guard short-circuit


def test_a_guard_rejection_becomes_a_verdict_without_running_anything():
    mission = make_mission()
    report = GuardReport(
        ok=False,
        reason=FailureReason.FORBIDDEN_CONSTRUCT,
        violations=("use of 'sum' is not allowed in this mission",),
        detail="use of 'sum' is not allowed in this mission",
    )

    verdict = verdict_from_guard(mission, report)

    assert not verdict.passed
    assert verdict.reason is FailureReason.FORBIDDEN_CONSTRUCT
    assert verdict.xp_awarded == 0
    assert "sum" in verdict.summary


def test_player_stdout_reaches_the_verdict():
    """Printing is how a beginner debugs. Their output must survive to the results panel."""
    mission = make_mission()
    results = [ExecutionResult(returned=6, status="ok", stdout="checking 1\n"), ok(0), ok(7)]

    verdict = evaluate(mission, mission.tests, results)

    assert "checking 1" in verdict.stdout


# --------------------------------------------------------------- cases that must raise


def raised(exception_type: str, message: str = "boom") -> ExecutionResult:
    return ExecutionResult(status="error", exception_type=exception_type, exception_message=message)


def raising_mission(**overrides):
    """A mission whose single case passes only by raising ValueError."""
    return make_mission(
        tests=(TestCase(args=(-1,), raises="ValueError", visible=True),), **overrides
    )


def test_raising_the_expected_exception_passes():
    mission = raising_mission()

    verdict = evaluate(mission, mission.tests, [raised("ValueError")])

    assert verdict.passed
    assert verdict.reason is FailureReason.PASSED


def test_returning_a_value_when_an_exception_was_required_fails():
    """The branch that stops a submission which never validates anything.

    Without it, a function that simply returns would pass every error case a mission
    was written to enforce.
    """
    mission = raising_mission()

    verdict = evaluate(mission, mission.tests, [ok(0)])

    assert not verdict.passed
    assert verdict.reason is FailureReason.WRONG_ANSWER
    assert "ValueError" in verdict.summary
    assert "returned" in verdict.summary


def test_raising_the_wrong_exception_type_fails_and_names_both():
    mission = raising_mission()

    verdict = evaluate(mission, mission.tests, [raised("TypeError", "bad operand")])

    assert not verdict.passed
    assert verdict.reason is FailureReason.WRONG_ANSWER
    assert "ValueError" in verdict.summary
    assert "TypeError" in verdict.summary


def test_exact_type_match_means_a_base_class_does_not_satisfy_a_subclass():
    """``raises: Exception`` must not be satisfied by a ValueError, and vice versa.

    Subclass matching would let an accidental crash pass as the intended answer, which
    is the opposite of what an error-handling mission is trying to teach.
    """
    mission = raising_mission()

    verdict = evaluate(mission, mission.tests, [raised("Exception")])

    assert not verdict.passed


def test_a_hidden_raising_case_names_the_type_but_not_the_input():
    """The one documented exception to the hidden-case rule, asserted rather than assumed.

    The exception type is already stated in the brief, so repeating it leaks nothing.
    The input must still be withheld.
    """
    mission = make_mission(
        tests=(TestCase(args=(-99,), raises="ValueError", visible=False),),
    )

    verdict = evaluate(mission, mission.tests, [ok(0)])

    assert "ValueError" in verdict.summary
    assert "-99" not in verdict.summary


def test_an_unexpected_exception_is_still_a_runtime_error():
    """The ordinary path must not regress: a case with no ``raises`` still fails on error."""
    mission = make_mission()

    verdict = evaluate(mission, mission.tests, [raised("ZeroDivisionError"), ok(0), ok(7)])

    assert not verdict.passed
    assert verdict.reason is FailureReason.RUNTIME_ERROR
