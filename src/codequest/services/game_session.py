"""Orchestrates one full mission attempt: guard, run, evaluate, save.

This is the only place that knows the whole sequence. Everything it calls is
independently testable, and everything above it — the CLI today, the Textual UI in
Phase 4, a web layer that may never exist — calls this one method instead of
reimplementing the order.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from dataclasses import dataclass

from codequest.engine import guard
from codequest.engine.evaluator import evaluate, verdict_from_guard
from codequest.engine.runners.base import ExecutionResult, Runner, get_runner
from codequest.models.curriculum import Island
from codequest.models.mission import Mission, TestCase
from codequest.models.profile import Profile
from codequest.models.verdict import FailureReason, Verdict
from codequest.services.progress_service import AwardResult, ProgressService


@dataclass(frozen=True, slots=True)
class AttemptOutcome:
    """What one attempt produced: the judgement, and what it changed.

    ``award`` is ``None`` when the attempt was not persisted — the CLI checkpoint runs
    a mission without a save file, and that has to work.
    """

    verdict: Verdict
    award: AwardResult | None = None

    @property
    def passed(self) -> bool:
        return self.verdict.passed

    @property
    def xp_awarded(self) -> int:
        """XP gained *now*: zero on a replay, even when the verdict passed."""
        return self.award.xp_awarded if self.award else 0


class GameSession:
    """Runs mission attempts and, when given a progress service, records them."""

    def __init__(
        self,
        progress: ProgressService | None = None,
        runner: Runner | None = None,
        language: str = "python",
    ) -> None:
        self.progress = progress
        self.runner = runner or get_runner(language)

    def attempt(
        self,
        mission: Mission,
        code: str,
        profile: Profile | None = None,
        islands: tuple[Island, ...] = (),
        on_case: Callable[[int, int], None] | None = None,
    ) -> AttemptOutcome:
        """Judge one submission against one mission, and persist the result if possible.

        Args:
            on_case: Called as ``on_case(finished, total)`` after each test case. Optional
                so the CLI and every existing test keep working untouched. The UI uses it
                to show "case 3 of 8" instead of a spinner — the engine knows the total,
                so a spinner would be hiding information it already has.

        # [AI-ENG:orchestration-gates] The sequence is a chain of gates, and each one
        # can stop the chain with a *typed* reason: static check, preparation, execution,
        # judgement, persistence. Nothing downstream runs on input an earlier gate
        # rejected — forbidden code never reaches a subprocess.
        #
        # This is the shape of a guardrail chain around a model. Screen the input,
        # constrain the generation, validate the output, and only then let it touch
        # anything real. The value is not any single gate; it is that a rejection at any
        # stage produces a specific reason instead of a generic failure, so the caller
        # can respond differently to "forbidden" than to "timed out".
        """
        report = guard.check(code, mission.constraints, mission.signature.entrypoint)
        if not report.ok:
            return self._finish(
                mission, code, verdict_from_guard(mission, report), profile, islands
            )

        prepared = self.runner.prepare(code, mission)
        try:
            if not prepared.ok:
                # Reachable for compiled languages in v1.1, where preparation is a
                # compile step. Python never gets here, and the branch exists so Java
                # does not have to change this file.
                # ``or`` would be wrong here: FailureReason is a StrEnum and PASSED is a
                # non-empty string, so it is truthy and would win.
                reason = (
                    prepared.reason
                    if prepared.reason is not FailureReason.PASSED
                    else FailureReason.SYNTAX_ERROR
                )
                verdict = Verdict(
                    mission_id=mission.id,
                    passed=False,
                    reason=reason,
                    summary=prepared.error or "Your code could not be prepared to run.",
                )
                return self._finish(mission, code, verdict, profile, islands)

            results = self._run_cases(prepared, mission, on_case)
            verdict = evaluate(mission, mission.tests, results)
        finally:
            # In a finally block: a crash between preparation and judgement must not
            # leave a temp directory behind on the player's disk.
            self.runner.cleanup(prepared)

        return self._finish(mission, code, verdict, profile, islands)

    def _run_cases(
        self,
        prepared,
        mission: Mission,
        on_case: Callable[[int, int], None] | None = None,
    ) -> list[ExecutionResult]:
        """Run every case, stopping early once the outcome cannot change.

        A submission that times out on case one will time out on the rest, and making
        the player wait eight timeouts to learn that helps nobody. Remaining cases are
        filled in as not-run so the evaluator still receives one result per case.
        """
        results: list[ExecutionResult] = []
        halted = False
        total = len(mission.tests)

        for index, case in enumerate(mission.tests, start=1):
            if halted:
                results.append(ExecutionResult(status="skipped"))
                continue

            result = self.runner.execute(prepared, case, mission.constraints)
            results.append(result)

            if on_case is not None:
                # A misbehaving observer must not fail an attempt that actually ran. The
                # progress bar is decoration; the verdict is the product.
                with contextlib.suppress(Exception):
                    on_case(index, total)

            if result.status in {"timeout", "memory", "missing_entrypoint"}:
                halted = True

        return results

    def _finish(
        self,
        mission: Mission,
        code: str,
        verdict: Verdict,
        profile: Profile | None,
        islands: tuple[Island, ...],
    ) -> AttemptOutcome:
        """Persist the attempt when there is somewhere to persist it."""
        if self.progress is None or profile is None or profile.id is None:
            return AttemptOutcome(verdict=verdict)

        award = self.progress.record_attempt(profile, mission, code, verdict, islands)
        # The verdict carries the mission's XP value; the award carries what was
        # actually granted. Replacing one with the other keeps the UI honest on a replay.
        return AttemptOutcome(
            verdict=Verdict(
                mission_id=verdict.mission_id,
                passed=verdict.passed,
                reason=verdict.reason,
                summary=verdict.summary,
                outcomes=verdict.outcomes,
                xp_awarded=award.xp_awarded,
                stdout=verdict.stdout,
                diagnostics=verdict.diagnostics,
            ),
            award=award,
        )

    def check_solution(self, mission: Mission) -> AttemptOutcome:
        """Run a mission's own declared ``solution`` against its own tests.

        The engine half of the most valuable test in the repository: content that ships
        with a solution which does not pass is a lesson that cannot be completed.
        """
        return self.attempt(mission, mission.solution)


def cases_of(mission: Mission) -> tuple[TestCase, ...]:
    """All cases of a mission, visible first. Kept for callers that want the order."""
    return mission.tests
