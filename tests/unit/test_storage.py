"""Tests for the SQLite layer.

These use a real database on disk rather than a mock. The behaviours worth guarding —
foreign key cascade, transaction rollback, an upsert that never regresses — are
behaviours of SQLite itself, and a mock would only assert that we called the methods we
wrote, which proves nothing.
"""

from __future__ import annotations

import sqlite3

import pytest

from codequest.models.profile import MissionStatus
from codequest.models.verdict import FailureReason, Verdict
from codequest.storage.db import MIGRATIONS, current_version, init_db, migrate, transaction
from codequest.storage.repositories import (
    AttemptRepository,
    IslandRepository,
    ProfileRepository,
    ProgressRepository,
)

PASSED = Verdict("m1", True, FailureReason.PASSED, "all good", xp_awarded=10)
FAILED = Verdict("m1", False, FailureReason.WRONG_ANSWER, "nope")


@pytest.fixture
def db(tmp_path):
    connection = init_db(tmp_path / "save.db")
    yield connection
    connection.close()


@pytest.fixture
def profiles(db) -> ProfileRepository:
    return ProfileRepository(db)


@pytest.fixture
def progress(db) -> ProgressRepository:
    return ProgressRepository(db)


# ------------------------------------------------------------------------ schema


def test_migrations_bring_a_fresh_database_up_to_date(tmp_path):
    connection = init_db(tmp_path / "fresh.db")

    assert current_version(connection) == MIGRATIONS[-1][0]
    connection.close()


def test_migrating_twice_is_a_no_op(tmp_path):
    """A player's save must survive an update instead of being recreated."""
    connection = init_db(tmp_path / "again.db")
    ProfileRepository(connection).create("giovanni", "python")

    migrate(connection)

    assert ProfileRepository(connection).count() == 1
    connection.close()


def test_foreign_keys_are_enforced(db):
    """SQLite ships with foreign keys OFF. Without the pragma, REFERENCES is decorative."""
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO progress (profile_id, mission_id, status) VALUES (?, ?, ?)",
            (999, "m1", "available"),
        )


def test_deleting_a_profile_cascades(db, profiles, progress):
    profile = profiles.create("giovanni", "python")
    progress.record_attempt(profile.id, "m1", passed=True, xp=10)

    profiles.delete(profile.id)

    assert progress.get(profile.id, "m1") is None


def test_transaction_rolls_back_on_failure(db, profiles):
    """A crash mid-write must leave nothing behind, not half a save."""
    with pytest.raises(RuntimeError), transaction(db):
        profiles.create("doomed", "python")
        raise RuntimeError("something exploded")

    assert profiles.get_by_name("doomed") is None


def test_transaction_commits_on_success(db, profiles):
    with transaction(db):
        profiles.create("kept", "python")

    assert profiles.get_by_name("kept") is not None


# ---------------------------------------------------------------------- profiles


def test_create_and_read_a_profile(profiles):
    created = profiles.create("giovanni", "python")

    fetched = profiles.get(created.id)

    assert fetched.name == "giovanni"
    assert fetched.total_xp == 0
    assert fetched.created_at is not None


def test_profile_names_are_unique(profiles):
    profiles.create("giovanni", "python")

    with pytest.raises(sqlite3.IntegrityError):
        profiles.create("giovanni", "python")


def test_add_xp_accumulates(profiles):
    profile = profiles.create("giovanni", "python")

    profiles.add_xp(profile.id, 10)
    profiles.add_xp(profile.id, 25)

    assert profiles.get(profile.id).total_xp == 35


def test_unknown_profile_is_none_not_an_error(profiles):
    assert profiles.get(4242) is None


# ------------------------------------------------------------- injection defence


def test_a_profile_name_that_looks_like_sql_is_stored_as_text(db, profiles):
    """The classic. With a parameterised query this is a silly name, not a dropped table.

    If the repository built SQL with an f-string, this input would end the INSERT and
    start a DROP. Because the value travels as a bound parameter, the database can only
    ever read it as data.
    """
    hostile = "Robert'); DROP TABLE profile;--"

    profiles.create(hostile, "python")

    assert profiles.get_by_name(hostile).name == hostile
    assert db.execute("SELECT COUNT(*) AS n FROM profile").fetchone()["n"] == 1


def test_a_mission_id_that_looks_like_sql_is_harmless(progress, profiles):
    profile = profiles.create("giovanni", "python")
    hostile = "m1'; DELETE FROM progress WHERE '1'='1"

    progress.record_attempt(profile.id, hostile, passed=True, xp=10)
    progress.record_attempt(profile.id, "m2", passed=True, xp=10)

    assert len(progress.list_for_profile(profile.id)) == 2


# ---------------------------------------------------------------------- progress


def test_first_attempt_creates_the_row(progress, profiles):
    profile = profiles.create("giovanni", "python")

    result = progress.record_attempt(profile.id, "m1", passed=False, xp=0)

    assert result.attempts == 1
    assert result.status is MissionStatus.ATTEMPTED


def test_attempts_accumulate_on_the_same_mission(progress, profiles):
    profile = profiles.create("giovanni", "python")

    progress.record_attempt(profile.id, "m1", passed=False, xp=0)
    progress.record_attempt(profile.id, "m1", passed=False, xp=0)
    result = progress.record_attempt(profile.id, "m1", passed=True, xp=10)

    assert result.attempts == 3
    assert result.status is MissionStatus.COMPLETED


def test_completed_status_never_regresses(progress, profiles):
    """Failing a mission you already solved must not take the completion away."""
    profile = profiles.create("giovanni", "python")
    progress.record_attempt(profile.id, "m1", passed=True, xp=10)

    result = progress.record_attempt(profile.id, "m1", passed=False, xp=0)

    assert result.status is MissionStatus.COMPLETED
    assert result.best_xp == 10


def test_best_xp_never_decreases(progress, profiles):
    profile = profiles.create("giovanni", "python")
    progress.record_attempt(profile.id, "m1", passed=True, xp=30)

    result = progress.record_attempt(profile.id, "m1", passed=True, xp=0)

    assert result.best_xp == 30


def test_completed_count_only_counts_solved_missions(progress, profiles):
    profile = profiles.create("giovanni", "python")
    progress.record_attempt(profile.id, "m1", passed=True, xp=10)
    progress.record_attempt(profile.id, "m2", passed=False, xp=0)

    assert progress.completed_count(profile.id) == 1


def test_recording_a_hint_creates_the_row_when_absent(progress, profiles):
    profile = profiles.create("giovanni", "python")

    progress.record_hint(profile.id, "m1")
    progress.record_hint(profile.id, "m1")

    assert progress.get(profile.id, "m1").hints_used == 2


# ----------------------------------------------------------------------- attempts


def test_attempt_history_is_newest_first(db, profiles):
    attempts = AttemptRepository(db)
    profile = profiles.create("giovanni", "python")

    attempts.record(profile.id, "m1", "first version", FAILED)
    attempts.record(profile.id, "m1", "second version", PASSED)

    history = attempts.history(profile.id, "m1")

    assert history[0]["code"] == "second version"
    assert attempts.count_for_profile(profile.id) == 2


# ------------------------------------------------------------------------ islands


def test_unlocking_is_idempotent(db, profiles):
    islands = IslandRepository(db)
    profile = profiles.create("giovanni", "python")

    first = islands.unlock(profile.id, "foundations")
    second = islands.unlock(profile.id, "foundations")

    assert first is True
    assert second is False
    assert islands.list_for_profile(profile.id) == ["foundations"]


def test_unlocked_islands_come_back_on_the_profile(db, profiles):
    IslandRepository(db).unlock(profiles.create("giovanni", "python").id, "foundations")

    assert "foundations" in profiles.get_by_name("giovanni").unlocked_islands


def test_progress_survives_a_reconnect(tmp_path):
    """The Phase 2 checkpoint in miniature: quit the process, reopen, still there."""
    path = tmp_path / "persistent.db"

    first = init_db(path)
    profile = ProfileRepository(first).create("giovanni", "python")
    ProgressRepository(first).record_attempt(profile.id, "m1", passed=True, xp=10)
    ProfileRepository(first).add_xp(profile.id, 10)
    first.close()

    second = init_db(path)
    reloaded = ProfileRepository(second).get_by_name("giovanni")
    try:
        assert reloaded.total_xp == 10
        assert ProgressRepository(second).get(reloaded.id, "m1").is_completed
    finally:
        second.close()
