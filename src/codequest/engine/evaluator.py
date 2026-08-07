"""Turns raw execution results into a Verdict with a readable failure reason.

The product of this module is the **sentence**, not the boolean.

    "Test 3 failed."

teaches nothing. Compare:

    "Expected 0 for an empty list, got None. Your function returns nothing when the
     loop never runs."

Same fact, and only one of them moves the player forward. Every branch below exists to
produce the second kind of message.

## Hidden cases

A hidden case that fails says *that* it failed and what shape of input it used — never
the expected value. Leaking it turns the hidden suite into a lookup table and the
mission stops catching the hardcoded answer it exists to catch.

One deliberate exception: a case with ``raises`` set names the expected exception type
even when hidden. That type is part of the contract the brief already states out loud
("raise ValueError when the amount is negative"), so repeating it reveals nothing the
player was not told, and withholding it would turn a wrong-exception failure into an
unsolvable riddle. The *input* stays hidden as always.
"""

from __future__ import annotations

import math
from typing import Any

from codequest.engine.guard import GuardReport
from codequest.engine.runners.base import ExecutionResult
from codequest.models.mission import Mission, TestCase
from codequest.models.verdict import CaseOutcome, FailureReason, Verdict

#: Maps the runner's raw status onto the taxonomy. Keeping the translation in one table
#: means a new runner cannot quietly invent a status nobody handles.
_STATUS_TO_REASON: dict[str, FailureReason] = {
    "ok": FailureReason.PASSED,
    "error": FailureReason.RUNTIME_ERROR,
    "timeout": FailureReason.TIMEOUT,
    "memory": FailureReason.MEMORY_EXCEEDED,
    "missing_entrypoint": FailureReason.MISSING_ENTRYPOINT,
    "crashed": FailureReason.RUNTIME_ERROR,
    "harness_error": FailureReason.HARNESS_ERROR,
    "skipped": FailureReason.NOT_RUN,
}


def _format_value(value: Any) -> str:
    """Render a value for a player-facing message, keeping it short."""
    text = repr(value)
    return text if len(text) <= 120 else text[:117] + "..."


def _describe_input(case: TestCase) -> str:
    """Describe the arguments of a case in a way a player recognises."""
    parts = [_format_value(arg) for arg in case.args]
    parts += [f"{name}={_format_value(value)}" for name, value in sorted(case.kwargs.items())]
    return ", ".join(parts) if parts else "no arguments"


def values_match(expected: Any, actual: Any, tolerance: float | None) -> bool:
    """Compare an expected value with what the submission returned.

    Exact equality by default. ``tolerance`` switches to approximate comparison, which
    a mission needs only when floating point makes exactness a lie.

    Two rules that a plain ``==`` gets wrong here:

    - ``True == 1`` in Python. A mission expecting ``1`` should not accept ``True``,
      so booleans are compared by type as well as by value.
    - ``float('nan') != float('nan')``. When both sides are NaN the answer is right.
    """
    if isinstance(expected, bool) != isinstance(actual, bool):
        return False

    if tolerance is not None and isinstance(expected, int | float):
        if not isinstance(actual, int | float):
            return False
        if math.isnan(expected) and math.isnan(actual):
            return True
        return abs(expected - actual) <= tolerance

    if (
        isinstance(expected, float)
        and isinstance(actual, float)
        and math.isnan(expected)
        and math.isnan(actual)
    ):
        return True

    return expected == actual


def _evaluate_case(index: int, case: TestCase, result: ExecutionResult) -> CaseOutcome:
    """Judge one executed case and write the sentence the player will read."""
    reason = _STATUS_TO_REASON.get(result.status, FailureReason.HARNESS_ERROR)
    shown_input = _describe_input(case) if case.visible else "a hidden input"

    if reason is FailureReason.TIMEOUT:
        detail = (
            f"Case {index + 1} ran out of time with {shown_input}. "
            "Something in your code never finishes. Check the condition that ends your loop."
        )
        return CaseOutcome(index, case.visible, False, reason, detail, result.stdout)

    if reason is FailureReason.MEMORY_EXCEEDED:
        detail = (
            f"Case {index + 1} used more memory than the mission allows, with {shown_input}. "
            "A list that grows on every pass of a loop is the usual cause."
        )
        return CaseOutcome(index, case.visible, False, reason, detail, result.stdout)

    if reason is FailureReason.NOT_RUN:
        detail = f"Case {index + 1} was not run: an earlier case already settled the outcome."
        return CaseOutcome(index, case.visible, False, reason, detail, result.stdout)

    if reason is FailureReason.MISSING_ENTRYPOINT:
        return CaseOutcome(
            index, case.visible, False, reason, result.exception_message, result.stdout
        )

    if reason is FailureReason.RUNTIME_ERROR:
        # An exception is normally a failure, but a case with ``raises`` set is asking
        # for one. Matched on the exact type name: see TestCase.raises for why subclass
        # matching would be the wrong kindness here.
        if case.expects_error:
            if result.exception_type == case.raises:
                return CaseOutcome(
                    index, case.visible, True, FailureReason.PASSED, "", result.stdout
                )
            detail = (
                f"Case {index + 1} was supposed to raise {case.raises}, "
                f"but raised {result.exception_type} instead: {result.exception_message} "
                f"(input: {shown_input})."
            )
            return CaseOutcome(
                index, case.visible, False, FailureReason.WRONG_ANSWER, detail, result.stdout
            )

        detail = (
            f"Case {index + 1} raised {result.exception_type}: {result.exception_message} "
            f"(input: {shown_input})."
        )
        return CaseOutcome(index, case.visible, False, reason, detail, result.stdout)

    if reason is FailureReason.HARNESS_ERROR:
        detail = "The game could not read the result of this run. This is a bug in CodeQuest."
        return CaseOutcome(index, case.visible, False, reason, detail, result.stdout)

    # Reaching here with ``raises`` set means the call returned normally when it was
    # supposed to fail. Without this branch a submission that never validates anything
    # would quietly pass every error case it was written to catch.
    if case.expects_error:
        detail = (
            f"Case {index + 1} was supposed to raise {case.raises}, but returned "
            f"{_format_value(result.returned)} instead (input: {shown_input})."
        )
        return CaseOutcome(
            index, case.visible, False, FailureReason.WRONG_ANSWER, detail, result.stdout
        )

    if values_match(case.expect, result.returned, case.tolerance):
        return CaseOutcome(index, case.visible, True, FailureReason.PASSED, "", result.stdout)

    if case.visible:
        detail = (
            f"Expected {_format_value(case.expect)} for {shown_input}, "
            f"got {_format_value(result.returned)}."
        )
        if result.returned is None:
            detail += " Your function returned nothing. Check that every path ends in a return."
    else:
        # No expected value here, on purpose. See the module docstring.
        detail = f"A hidden case failed with {len(case.args)} argument(s). Check your edge cases."

    return CaseOutcome(
        index, case.visible, False, FailureReason.WRONG_ANSWER, detail, result.stdout
    )


def verdict_from_guard(mission: Mission, report: GuardReport) -> Verdict:
    """Build the Verdict for a submission that never got to run."""
    return Verdict(
        mission_id=mission.id,
        passed=False,
        reason=report.reason,
        summary=report.detail or "Your code was rejected before it ran.",
        diagnostics={"violations": "; ".join(report.violations)},
    )


def evaluate(
    mission: Mission,
    cases: tuple[TestCase, ...],
    results: list[ExecutionResult],
) -> Verdict:
    """Turn per-case execution results into one Verdict.

    Args:
        mission: The mission being attempted, used for its id and XP value.
        cases: The cases that were run, in the same order as ``results``.
        results: One raw result per case.

    Returns:
        A Verdict whose ``reason`` is the *first* thing that went wrong. Reporting the
        earliest failure rather than the most severe keeps the message aligned with the
        order the player reads their tests in.
    """
    if len(cases) != len(results):
        return Verdict(
            mission_id=mission.id,
            passed=False,
            reason=FailureReason.HARNESS_ERROR,
            summary="The engine ran a different number of cases than it was given.",
        )

    outcomes = tuple(
        _evaluate_case(index, case, result)
        for index, (case, result) in enumerate(zip(cases, results, strict=True))
    )
    failures = [outcome for outcome in outcomes if not outcome.passed]
    stdout = next((outcome.stdout for outcome in outcomes if outcome.stdout), "")

    if not failures:
        return Verdict(
            mission_id=mission.id,
            passed=True,
            reason=FailureReason.PASSED,
            summary=f"All {len(outcomes)} cases passed.",
            outcomes=outcomes,
            xp_awarded=mission.xp,
            stdout=stdout,
        )

    first = failures[0]
    passed_count = len(outcomes) - len(failures)
    return Verdict(
        mission_id=mission.id,
        passed=False,
        reason=first.reason,
        summary=f"{passed_count} of {len(outcomes)} cases passed. {first.detail}",
        outcomes=outcomes,
        xp_awarded=0,
        stdout=stdout,
    )
