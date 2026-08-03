"""Tests for the progression rules.

The one that matters most is idempotency: XP is paid once per mission, decided by state
in the database rather than by trusting the caller not to submit twice.
"""

from __future__ import annotations

import pytest

from codequest.models.curriculum import Island, UnlockRule
from codequest.models.verdict import FailureReason, Verdict
from codequest.services.progress_service import (
    DuplicateProfileNameError,
    ProfileLimitReachedError,
    ProgressService,
)
from codequest.storage.db import init_db
from conftest import make_mission

MISSION = make_mission(id="m1", xp=10)
PASSED = Verdict("m1", True, FailureReason.PASSED, "all good")
FAILED = Verdict("m1", False, FailureReason.WRONG_ANSWER, "nope")


@pytest.fixture
def service(tmp_path):
    connection = init_db(tmp_path / "save.db")
    yield ProgressService(connection)
    connection.close()


def island(island_id: str, order: int, **rule) -> Island:
    return Island(
        id=island_id,
        name=island_id,
        track="python",
        order=order,
        unlock_requires=UnlockRule(**rule),
    )


# ------------------------------------------------------------------- save limit


def test_creating_a_profile_works(service):
    profile = service.create_profile("giovanni", "python")

    assert profile.id is not None
    assert profile.level == 1


def test_the_fifth_save_is_refused_with_a_readable_message(service):
    """A service rule, not a database constraint, so the message can be friendly."""
    for index in range(4):
        service.create_profile(f"save-{index}", "python")

    with pytest.raises(ProfileLimitReachedError) as exc_info:
        service.create_profile("one-too-many", "python")

    assert "4 saves" in str(exc_info.value)


def test_deleting_a_save_frees_a_slot(service):
    for index in range(4):
        service.create_profile(f"save-{index}", "python")
    victim = service.list_profiles()[0]

    service.delete_profile(victim.id)
    service.create_profile("replacement", "python")

    assert len(service.list_profiles()) == 4


def test_duplicate_names_are_refused(service):
    service.create_profile("giovanni", "python")

    with pytest.raises(DuplicateProfileNameError):
        service.create_profile("giovanni", "python")


def test_a_blank_name_is_refused(service):
    with pytest.raises(ValueError, match="name"):
        service.create_profile("   ", "python")


# ------------------------------------------------------------------ idempotency


def test_passing_a_mission_awards_its_xp(service):
    profile = service.create_profile("giovanni", "python")

    result = service.record_attempt(profile, MISSION, "code", PASSED)

    assert result.xp_awarded == 10
    assert result.profile.total_xp == 10
    assert result.progress.is_completed


def test_solving_the_same_mission_twice_pays_once(service):
    """The rule this whole service exists to get right."""
    profile = service.create_profile("giovanni", "python")

    first = service.record_attempt(profile, MISSION, "code", PASSED)
    second = service.record_attempt(first.profile, MISSION, "code", PASSED)

    assert first.xp_awarded == 10
    assert second.xp_awarded == 0
    assert second.already_completed
    assert second.profile.total_xp == 10


def test_replaying_ten_times_still_pays_once(service):
    """Repetition must be boring, not expensive. This is the retry-safety property."""
    profile = service.create_profile("giovanni", "python")

    for _ in range(10):
        profile = service.record_attempt(profile, MISSION, "code", PASSED).profile

    assert profile.total_xp == 10


def test_a_failed_attempt_is_recorded_but_pays_nothing(service):
    profile = service.create_profile("giovanni", "python")

    result = service.record_attempt(profile, MISSION, "broken", FAILED)

    assert result.xp_awarded == 0
    assert result.profile.total_xp == 0
    assert result.progress.attempts == 1


def test_failing_after_completing_keeps_the_xp(service):
    profile = service.create_profile("giovanni", "python")
    first = service.record_attempt(profile, MISSION, "good", PASSED)

    second = service.record_attempt(first.profile, MISSION, "broken", FAILED)

    assert second.profile.total_xp == 10
    assert second.progress.is_completed


def test_different_missions_each_pay_their_own_xp(service):
    profile = service.create_profile("giovanni", "python")
    other = make_mission(id="m2", xp=10)

    first = service.record_attempt(profile, MISSION, "code", PASSED)
    second = service.record_attempt(
        first.profile, other, "code", Verdict("m2", True, FailureReason.PASSED, "ok")
    )

    assert second.profile.total_xp == 20


# ----------------------------------------------------------------------- levels


def test_crossing_a_threshold_reports_a_level_up(service):
    profile = service.create_profile("giovanni", "python")
    big = make_mission(id="big", xp=60)

    result = service.record_attempt(
        profile, big, "code", Verdict("big", True, FailureReason.PASSED, "ok")
    )
    second = service.record_attempt(
        result.profile,
        make_mission(id="big2", xp=60),
        "code",
        Verdict("big2", True, FailureReason.PASSED, "ok"),
    )

    assert second.profile.total_xp == 120
    assert second.profile.level == 2
    assert second.leveled_up


def test_no_level_up_reported_when_the_threshold_is_not_crossed(service):
    profile = service.create_profile("giovanni", "python")

    result = service.record_attempt(profile, MISSION, "code", PASSED)

    assert not result.leveled_up


# -------------------------------------------------------------------- unlocking


def test_an_island_with_no_requirements_is_open_immediately(service):
    profile = service.create_profile("giovanni", "python")

    assert service.is_island_unlocked(profile, island("foundations", 1))


def test_an_island_unlocks_when_its_mission_count_is_met(service):
    profile = service.create_profile("giovanni", "python")
    second = island("collections", 2, missions_completed=1)

    result = service.record_attempt(profile, MISSION, "code", PASSED, islands=(second,))

    assert "collections" in result.newly_unlocked
    assert service.is_island_unlocked(result.profile, second)


def test_an_island_stays_locked_below_the_threshold(service):
    profile = service.create_profile("giovanni", "python")
    far = island("algorithms", 9, missions_completed=50)

    result = service.record_attempt(profile, MISSION, "code", PASSED, islands=(far,))

    assert result.newly_unlocked == ()
    assert not service.is_island_unlocked(result.profile, far)


def test_an_island_gated_on_xp_unlocks_at_the_right_total(service):
    profile = service.create_profile("giovanni", "python")
    gated = island("gated", 2, total_xp=10)

    result = service.record_attempt(profile, MISSION, "code", PASSED, islands=(gated,))

    assert "gated" in result.newly_unlocked


def test_a_chain_of_islands_can_open_in_one_go(service):
    """Island 3 depends on island 2, and both become eligible on the same attempt."""
    profile = service.create_profile("giovanni", "python")
    second = island("collections", 2, missions_completed=1)
    third = island("functions", 3, missions_completed=1, requires_island="collections")

    result = service.record_attempt(profile, MISSION, "code", PASSED, islands=(third, second))

    assert set(result.newly_unlocked) == {"collections", "functions"}


def test_an_island_is_not_reported_as_newly_unlocked_twice(service):
    profile = service.create_profile("giovanni", "python")
    second = island("collections", 2, missions_completed=1)

    first = service.record_attempt(profile, MISSION, "code", PASSED, islands=(second,))
    again = service.record_attempt(first.profile, MISSION, "code", PASSED, islands=(second,))

    assert first.newly_unlocked == ("collections",)
    assert again.newly_unlocked == ()


# ------------------------------------------------------------------- bookkeeping


def test_hints_are_counted(service):
    profile = service.create_profile("giovanni", "python")

    service.record_hint(profile, MISSION)
    service.record_hint(profile, MISSION)

    assert service.progress_for(profile)["m1"].hints_used == 2


def test_progress_for_returns_every_touched_mission(service):
    profile = service.create_profile("giovanni", "python")
    service.record_attempt(profile, MISSION, "code", PASSED)
    service.record_attempt(profile, make_mission(id="m2"), "code", FAILED)

    assert set(service.progress_for(profile)) == {"m1", "m2"}


def test_recording_for_an_unsaved_profile_is_refused(service):
    from codequest.models.profile import Profile

    with pytest.raises(ValueError, match="unsaved"):
        service.record_attempt(Profile(id=None, name="x", track="python"), MISSION, "c", PASSED)
