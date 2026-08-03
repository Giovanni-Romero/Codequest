"""Tests for the pure domain models.

There is no I/O here and no logic worth mocking, so these tests target the two things
that can actually break: the immutability guarantee the rest of the engine relies on,
and the derived properties that encode real rules (levels, visible/hidden split).
"""

import dataclasses

import pytest

from codequest.models.curriculum import Island, Track, UnlockRule
from codequest.models.mission import XP_BY_DIFFICULTY, Constraints, Difficulty
from codequest.models.profile import LEVEL_THRESHOLDS, MissionStatus, Profile, Progress
from codequest.models.verdict import CaseOutcome, FailureReason, Verdict
from conftest import make_mission as _mission

# --------------------------------------------------------------------------- mission


def test_mission_is_immutable():
    """A loaded Mission is shared across guard, runner and evaluator, so it must freeze.

    If any of them could mutate it, a bug in one layer would surface as a wrong verdict
    in another — the hardest class of bug to trace.
    """
    mission = _mission()
    with pytest.raises(dataclasses.FrozenInstanceError):
        mission.xp = 999


def test_visible_and_hidden_tests_partition_the_suite():
    mission = _mission()

    assert len(mission.visible_tests) == 1
    assert len(mission.hidden_tests) == 2
    assert len(mission.visible_tests) + len(mission.hidden_tests) == len(mission.tests)


def test_hint_at_returns_the_requested_rung():
    mission = _mission()

    assert mission.hint_at(2).text == "construct"
    assert mission.hint_at(9) is None


def test_constraints_defaults_match_the_documented_schema():
    """docs/mission-schema.md promises these defaults when the field is absent."""
    constraints = Constraints()

    assert constraints.max_runtime_ms == 2000
    assert constraints.max_memory_mb == 128
    assert constraints.forbidden_builtins == frozenset()
    assert constraints.forbidden_imports == frozenset()


def test_xp_table_covers_every_difficulty():
    """A new difficulty without an XP value would award zero and nobody would notice."""
    assert set(XP_BY_DIFFICULTY) == set(Difficulty)


def test_difficulty_round_trips_through_its_yaml_spelling():
    assert Difficulty("elementary") is Difficulty.ELEMENTARY
    assert str(Difficulty.EXPERT) == "expert"


# --------------------------------------------------------------------------- verdict


def test_verdict_reports_first_failure_and_counts():
    verdict = Verdict(
        mission_id="py-foundations-02",
        passed=False,
        reason=FailureReason.WRONG_ANSWER,
        summary="1 of 3 cases failed",
        outcomes=(
            CaseOutcome(0, True, True, FailureReason.PASSED),
            CaseOutcome(1, False, False, FailureReason.WRONG_ANSWER, "expected 0"),
            CaseOutcome(2, False, True, FailureReason.PASSED),
        ),
    )

    assert verdict.passed_count == 2
    assert len(verdict.failed_outcomes) == 1
    assert verdict.first_failure.index == 1


def test_verdict_with_no_failures_has_no_first_failure():
    verdict = Verdict("m", True, FailureReason.PASSED, "all good")

    assert verdict.first_failure is None
    assert verdict.failed_outcomes == ()


# --------------------------------------------------------------------------- profile


@pytest.mark.parametrize(
    ("total_xp", "expected_level"),
    [(0, 1), (99, 1), (100, 2), (249, 2), (250, 3), (5800, 10), (999_999, 10)],
)
def test_level_is_derived_from_xp(total_xp, expected_level):
    """Level is computed, never stored, so it cannot go stale when the table changes."""
    assert Profile(id=1, name="g", track="python", total_xp=total_xp).level == expected_level


def test_xp_to_next_level_is_none_at_the_cap():
    """Past the last threshold there is no next level, and 0 would be a lie."""
    capped = Profile(id=1, name="g", track="python", total_xp=LEVEL_THRESHOLDS[-1])

    assert capped.xp_to_next_level is None


def test_xp_to_next_level_counts_the_remaining_gap():
    profile = Profile(id=1, name="g", track="python", total_xp=60)

    assert profile.xp_to_next_level == 40


def test_progress_knows_whether_it_is_completed():
    done = Progress(1, "m", status=MissionStatus.COMPLETED, best_xp=10)
    tried = Progress(1, "m", status=MissionStatus.ATTEMPTED)

    assert done.is_completed
    assert not tried.is_completed


# ------------------------------------------------------------------------ curriculum


def test_island_defaults_to_no_unlock_requirement():
    """The first island of a track must be reachable by a brand new profile."""
    island = Island(id="foundations", name="Foundations", track="python", order=1)

    assert island.unlock_requires == UnlockRule()
    assert island.unlock_requires.missions_completed == 0


def test_track_is_immutable():
    track = Track(
        id="python", name="Python", language="python", runner="python", file_extension=".py"
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        track.runner = "java"
