"""End-to-end tests: YAML on disk to XP in the database.

Unit tests prove each module is right in isolation. These prove the *wiring* is right,
which is a different failure mode: every part can be correct while the sequence that
joins them is wrong.

Both phase checkpoints from PROJECT_PLAN.md live here.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from codequest.engine.loader import load_mission
from codequest.models.verdict import FailureReason
from codequest.services.game_session import GameSession
from codequest.services.mission_service import MissionService
from codequest.services.progress_service import ProgressService
from codequest.storage.db import init_db
from helpers import CONTENT_ROOT

SUM_LIST = (
    CONTENT_ROOT
    / "tracks"
    / "python"
    / "locales"
    / "en"
    / "islands"
    / "01-foundations"
    / "missions"
    / "06-sum-list.yaml"
)

CORRECT = """
def sum_list(numbers):
    total = 0
    for n in numbers:
        total = total + n
    return total
"""

USES_FORBIDDEN_BUILTIN = """
def sum_list(numbers):
    return sum(numbers)
"""

HANGS = """
def sum_list(numbers):
    while True:
        pass
"""

HARDCODED = """
def sum_list(numbers):
    return 6
"""

CRASHES = """
def sum_list(numbers):
    return numbers[0] / 0
"""

FORGETS_TO_RETURN = """
def sum_list(numbers):
    total = 0
    for n in numbers:
        total = total + n
"""


@pytest.fixture
def mission():
    return load_mission(SUM_LIST)


@pytest.fixture
def session():
    return GameSession()


# ---------------------------------------------------- Phase 1 checkpoint: the engine


def test_a_correct_solution_passes_every_case(session, mission):
    outcome = session.attempt(mission, CORRECT)

    assert outcome.passed
    assert outcome.verdict.reason is FailureReason.PASSED
    assert outcome.verdict.passed_count == len(mission.tests)


def test_a_forbidden_builtin_is_rejected_before_anything_runs(session, mission):
    """The mission teaches building a sum, so sum() must not be a way through it."""
    outcome = session.attempt(mission, USES_FORBIDDEN_BUILTIN)

    assert not outcome.passed
    assert outcome.verdict.reason is FailureReason.FORBIDDEN_CONSTRUCT
    assert outcome.verdict.outcomes == ()  # nothing executed


def test_an_infinite_loop_is_stopped(session, mission):
    outcome = session.attempt(mission, HANGS)

    assert not outcome.passed
    assert outcome.verdict.reason is FailureReason.TIMEOUT


def test_a_hardcoded_answer_passes_visible_and_fails_hidden(session, mission):
    """Exactly why hidden cases exist, proven against the real shipped mission."""
    outcome = session.attempt(mission, HARDCODED)

    visible = [o for o in outcome.verdict.outcomes if o.visible]
    hidden = [o for o in outcome.verdict.outcomes if not o.visible]

    assert not outcome.passed
    assert visible[0].passed
    assert any(not o.passed for o in hidden)


def test_a_hidden_failure_does_not_disclose_the_expected_value(session, mission):
    outcome = session.attempt(mission, HARDCODED)

    hidden_details = " ".join(o.detail for o in outcome.verdict.outcomes if not o.visible)

    assert "expected" not in hidden_details.lower()


def test_a_crash_is_reported_as_a_runtime_error(session, mission):
    outcome = session.attempt(mission, CRASHES)

    assert outcome.verdict.reason is FailureReason.RUNTIME_ERROR
    assert "ZeroDivisionError" in outcome.verdict.summary


def test_a_missing_return_gets_the_helpful_sentence(session, mission):
    """The most common beginner bug in this exact mission."""
    outcome = session.attempt(mission, FORGETS_TO_RETURN)

    assert not outcome.passed
    assert "returned nothing" in outcome.verdict.summary


def test_a_syntax_error_never_escapes_as_an_exception(session, mission):
    outcome = session.attempt(mission, "def sum_list(:\n")

    assert outcome.verdict.reason is FailureReason.SYNTAX_ERROR


def test_the_wrong_function_name_is_caught_by_the_guard(session, mission):
    outcome = session.attempt(mission, "def add_them(numbers):\n    return 0\n")

    assert outcome.verdict.reason is FailureReason.MISSING_ENTRYPOINT


def test_progress_is_reported_once_per_case(session, mission):
    """The UI needs a determinate bar, so the engine has to say how far along it is."""
    seen: list[tuple[int, int]] = []

    session.attempt(mission, CORRECT, on_case=lambda done, total: seen.append((done, total)))

    assert len(seen) == len(mission.tests)
    assert seen[0] == (1, len(mission.tests))
    assert seen[-1] == (len(mission.tests), len(mission.tests))


def test_skipped_cases_do_not_report_progress(session, mission):
    """A timeout halts the run, so the bar stops where it stopped. It must not lie."""
    seen: list[tuple[int, int]] = []

    session.attempt(mission, HANGS, on_case=lambda done, total: seen.append((done, total)))

    assert len(seen) == 1


def test_a_broken_progress_callback_does_not_fail_the_attempt(session, mission):
    """The bar is decoration; the verdict is the product. An observer must not break it."""

    def explode(done: int, total: int) -> None:
        raise RuntimeError("the widget was disposed mid-run")

    outcome = session.attempt(mission, CORRECT, on_case=explode)

    assert outcome.passed


def test_no_temp_directories_are_left_behind(session, mission, tmp_path):
    """Cleanup runs in a finally block; a crash must not litter the player's disk."""
    import tempfile

    before = set(Path(tempfile.gettempdir()).glob("codequest-*"))
    session.attempt(mission, CRASHES)
    after = set(Path(tempfile.gettempdir()).glob("codequest-*"))

    assert after <= before


# --------------------------------------------- Phase 2 checkpoint: it is remembered


@pytest.fixture
def game(tmp_path):
    connection = init_db(tmp_path / "save.db")
    progress = ProgressService(connection)
    yield progress, GameSession(progress=progress), MissionService(CONTENT_ROOT, "python")
    connection.close()


def test_solving_a_mission_awards_xp_to_the_save(game, mission):
    progress, session, missions = game
    profile = progress.create_profile("giovanni", "python")

    outcome = session.attempt(mission, CORRECT, profile, missions.islands)

    assert outcome.passed
    assert outcome.xp_awarded == mission.xp
    assert outcome.award.profile.total_xp == mission.xp


def test_a_failed_attempt_is_recorded_and_pays_nothing(game, mission):
    progress, session, missions = game
    profile = progress.create_profile("giovanni", "python")

    outcome = session.attempt(mission, HARDCODED, profile, missions.islands)

    assert not outcome.passed
    assert outcome.xp_awarded == 0
    assert outcome.award.progress.attempts == 1


def test_solving_twice_pays_once(game, mission):
    progress, session, missions = game
    profile = progress.create_profile("giovanni", "python")

    first = session.attempt(mission, CORRECT, profile, missions.islands)
    second = session.attempt(mission, CORRECT, first.award.profile, missions.islands)

    assert first.xp_awarded == mission.xp
    assert second.passed
    assert second.xp_awarded == 0
    assert second.award.profile.total_xp == mission.xp


def test_progress_survives_closing_and_reopening_the_database(tmp_path, mission):
    """The Phase 2 checkpoint verbatim: play, quit, reopen, it is still there."""
    db_path = tmp_path / "persistent.db"

    first_connection = init_db(db_path)
    first_progress = ProgressService(first_connection)
    profile = first_progress.create_profile("giovanni", "python")
    GameSession(progress=first_progress).attempt(mission, CORRECT, profile)
    first_connection.close()

    second_connection = init_db(db_path)
    try:
        reopened = ProgressService(second_connection)
        reloaded = reopened.profiles.get_by_name("giovanni")

        assert reloaded.total_xp == mission.xp
        assert reopened.progress_for(reloaded)[mission.id].is_completed
    finally:
        second_connection.close()


def test_attempt_history_keeps_every_submission(game, mission):
    """progress holds the current best; attempt holds the journey."""
    progress, session, _ = game
    profile = progress.create_profile("giovanni", "python")

    session.attempt(mission, HARDCODED, profile)
    session.attempt(mission, CORRECT, profile)

    history = progress.attempts.history(profile.id, mission.id)

    assert len(history) == 2
    assert "total = 0" in history[0]["code"]


# ----------------------------------------------------------------- catalogue wiring


def test_the_mission_service_loads_the_shipped_catalogue():
    service = MissionService(CONTENT_ROOT, "python")

    assert service.track.id == "python"
    assert service.get_mission("py-foundations-06") is not None
    assert service.islands[0].id == "foundations"


def test_the_mission_service_can_switch_to_ai_engineering_and_back():
    service = MissionService(CONTENT_ROOT, "python")

    service.set_track("ai-engineering")

    assert service.track.id == "ai-engineering"
    assert service.get_mission("ai-documents-01") is not None
    assert service.get_mission("py-foundations-06") is None

    service.set_track("python")

    assert service.track.id == "python"
    assert service.get_mission("py-foundations-06") is not None
    assert service.get_mission("ai-documents-01") is None


def test_islands_know_which_missions_they_own():
    service = MissionService(CONTENT_ROOT, "python")

    assert "py-foundations-06" in service.get_island("foundations").mission_ids
    assert service.missions_in("foundations")[0].island == "foundations"


def test_missions_are_ordered_by_island_order_not_island_id():
    """Regression: sorting by island *id* is alphabetical, not curricular.

    "collections" sorts before "foundations", so the whole catalogue came out with
    Island 2 ahead of Island 1 - which made ``next_mission_after`` skip an island at
    every boundary. Invisible while only one island existed.
    """
    service = MissionService(CONTENT_ROOT, "python")

    island_sequence = []
    for mission in service.missions:
        if mission.island not in island_sequence:
            island_sequence.append(mission.island)

    expected = [island.id for island in service.islands if service.missions_in(island.id)]
    assert island_sequence == expected


def test_next_mission_crosses_from_one_island_into_the_next():
    service = MissionService(CONTENT_ROOT, "python")

    last_of_first = service.missions_in(service.islands[0].id)[-1]
    first_of_second = service.missions_in(service.islands[1].id)[0]

    assert service.next_mission_after(last_of_first.id) == first_of_second


def test_the_last_mission_of_the_track_has_no_successor():
    service = MissionService(CONTENT_ROOT, "python")

    assert service.next_mission_after(service.missions[-1].id) is None
