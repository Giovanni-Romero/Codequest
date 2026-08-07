"""ProfileRepository and ProgressRepository. Parameterized SQL only.

A repository owns the SQL for one table and returns domain objects. Nothing above this
layer writes a query, and nothing here decides a rule — "four saves maximum" is a
service rule, not a repository one, so the refusal can be a friendly sentence instead
of an ``IntegrityError``.

## The one rule with no exceptions

# [AI-ENG:sql-injection] Every value reaches SQL as a ``?`` placeholder. Never through
# an f-string, never through concatenation. The database then treats it as data that
# can never become syntax, which is a *structural* guarantee rather than a hope that
# the escaping was right.
#
# The same shape recurs everywhere in AI work: a retrieved document becoming part of a
# prompt, a tool argument becoming part of a shell command, model output becoming part
# of a query. Untrusted text that lands in a position where it can be read as
# instructions is the whole bug class. Parameterisation is the version of the fix that
# actually works, because it removes the possibility instead of filtering for it.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

from codequest.models.profile import MissionStatus, Profile, Progress
from codequest.models.verdict import Verdict


def _now() -> str:
    """Current UTC time as an ISO-8601 string.

    UTC and text on purpose: SQLite has no date type, and a naive local timestamp turns
    into a silent one-hour bug twice a year.
    """
    return datetime.now(UTC).isoformat()


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


class ProfileRepository:
    """Reads and writes career saves."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def _row_to_profile(self, row: sqlite3.Row) -> Profile:
        unlocked = self.connection.execute(
            "SELECT island_id FROM unlocked_island WHERE profile_id = ?", (row["id"],)
        ).fetchall()
        return Profile(
            id=row["id"],
            name=row["name"],
            track=row["track"],
            created_at=_parse_time(row["created_at"]),
            last_played_at=_parse_time(row["last_played_at"]),
            total_xp=row["total_xp"],
            unlocked_islands=frozenset(item["island_id"] for item in unlocked),
        )

    def create(self, name: str, track: str) -> Profile:
        """Create a save. The caller is responsible for the four-save rule."""
        now = _now()
        cursor = self.connection.execute(
            "INSERT INTO profile (name, track, created_at, last_played_at, total_xp)"
            " VALUES (?, ?, ?, ?, 0)",
            (name, track, now, now),
        )
        return Profile(
            id=cursor.lastrowid,
            name=name,
            track=track,
            created_at=_parse_time(now),
            last_played_at=_parse_time(now),
        )

    def get(self, profile_id: int) -> Profile | None:
        row = self.connection.execute(
            "SELECT * FROM profile WHERE id = ?", (profile_id,)
        ).fetchone()
        return self._row_to_profile(row) if row else None

    def get_by_name(self, name: str) -> Profile | None:
        row = self.connection.execute("SELECT * FROM profile WHERE name = ?", (name,)).fetchone()
        return self._row_to_profile(row) if row else None

    def list_all(self) -> list[Profile]:
        rows = self.connection.execute("SELECT * FROM profile ORDER BY id").fetchall()
        return [self._row_to_profile(row) for row in rows]

    def count(self) -> int:
        return self.connection.execute("SELECT COUNT(*) AS n FROM profile").fetchone()["n"]

    def add_xp(self, profile_id: int, amount: int) -> None:
        """Increment total XP.

        Written as ``total_xp = total_xp + ?`` rather than read-modify-write in Python:
        the addition happens inside the database, so two concurrent awards cannot both
        read the old value and one of them overwrite the other.
        """
        self.connection.execute(
            "UPDATE profile SET total_xp = total_xp + ?, last_played_at = ? WHERE id = ?",
            (amount, _now(), profile_id),
        )

    def touch(self, profile_id: int) -> None:
        """Record that this save was played just now."""
        self.connection.execute(
            "UPDATE profile SET last_played_at = ? WHERE id = ?", (_now(), profile_id)
        )

    def delete(self, profile_id: int) -> None:
        """Delete a save and, through ON DELETE CASCADE, everything it owns."""
        self.connection.execute("DELETE FROM profile WHERE id = ?", (profile_id,))


class ProgressRepository:
    """Reads and writes a profile's standing on each mission."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    @staticmethod
    def _row_to_progress(row: sqlite3.Row) -> Progress:
        return Progress(
            profile_id=row["profile_id"],
            mission_id=row["mission_id"],
            status=MissionStatus(row["status"]),
            best_xp=row["best_xp"],
            attempts=row["attempts"],
            hints_used=row["hints_used"],
            completed_at=_parse_time(row["completed_at"]),
        )

    def get(self, profile_id: int, mission_id: str) -> Progress | None:
        row = self.connection.execute(
            "SELECT * FROM progress WHERE profile_id = ? AND mission_id = ?",
            (profile_id, mission_id),
        ).fetchone()
        return self._row_to_progress(row) if row else None

    def list_for_profile(self, profile_id: int) -> list[Progress]:
        rows = self.connection.execute(
            "SELECT * FROM progress WHERE profile_id = ? ORDER BY mission_id", (profile_id,)
        ).fetchall()
        return [self._row_to_progress(row) for row in rows]

    def completed_count(self, profile_id: int) -> int:
        return self.connection.execute(
            "SELECT COUNT(*) AS n FROM progress WHERE profile_id = ? AND status = ?",
            (profile_id, MissionStatus.COMPLETED.value),
        ).fetchone()["n"]

    def record_attempt(
        self, profile_id: int, mission_id: str, *, passed: bool, xp: int
    ) -> Progress:
        """Upsert the row for one mission attempt and return the new standing.

        ``best_xp = MAX(best_xp, ?)`` and ``status`` never regressing from COMPLETED are
        what make replaying a solved mission harmless: the write happens, and nothing
        the player already earned moves backwards.
        """
        status = MissionStatus.COMPLETED if passed else MissionStatus.ATTEMPTED
        completed_at = _now() if passed else None

        self.connection.execute(
            """
            INSERT INTO progress
                (profile_id, mission_id, status, best_xp, attempts, hints_used, completed_at)
            VALUES (?, ?, ?, ?, 1, 0, ?)
            ON CONFLICT (profile_id, mission_id) DO UPDATE SET
                attempts     = attempts + 1,
                best_xp      = MAX(best_xp, excluded.best_xp),
                status       = CASE
                                   WHEN progress.status = 'completed' THEN 'completed'
                                   ELSE excluded.status
                               END,
                completed_at = COALESCE(progress.completed_at, excluded.completed_at)
            """,
            (profile_id, mission_id, status.value, xp, completed_at),
        )
        result = self.get(profile_id, mission_id)
        assert result is not None  # just written in this transaction
        return result

    def record_hint(self, profile_id: int, mission_id: str) -> None:
        """Count a revealed hint, creating the row if the mission was never attempted."""
        self.connection.execute(
            """
            INSERT INTO progress
                (profile_id, mission_id, status, best_xp, attempts, hints_used, completed_at)
            VALUES (?, ?, ?, 0, 0, 1, NULL)
            ON CONFLICT (profile_id, mission_id) DO UPDATE SET hints_used = hints_used + 1
            """,
            (profile_id, mission_id, MissionStatus.AVAILABLE.value),
        )


class AttemptRepository:
    """Append-only history of submitted code.

    ``progress`` holds the current best; this holds the journey. Keeping both means a
    player can read code they wrote weeks ago and see how they got better.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def record(self, profile_id: int, mission_id: str, code: str, verdict: Verdict) -> int:
        cursor = self.connection.execute(
            "INSERT INTO attempt (profile_id, mission_id, code, verdict, passed, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                profile_id,
                mission_id,
                code,
                json.dumps({"reason": verdict.reason.value, "summary": verdict.summary}),
                int(verdict.passed),
                _now(),
            ),
        )
        return int(cursor.lastrowid or 0)

    def history(self, profile_id: int, mission_id: str, limit: int = 20) -> list[sqlite3.Row]:
        """Most recent attempts first."""
        return self.connection.execute(
            "SELECT * FROM attempt WHERE profile_id = ? AND mission_id = ?"
            " ORDER BY id DESC LIMIT ?",
            (profile_id, mission_id, limit),
        ).fetchall()

    def count_for_profile(self, profile_id: int) -> int:
        return self.connection.execute(
            "SELECT COUNT(*) AS n FROM attempt WHERE profile_id = ?", (profile_id,)
        ).fetchone()["n"]


class PreferenceRepository:
    """Reads and writes app-wide settings that belong to the player, not a save.

    Deliberately not scoped to a profile: the game's language has to be readable from
    the main menu, before any save is chosen, so it cannot live on the ``profile`` row.
    A generic key/value table keeps this repository from needing a schema change the
    next time a preference like this shows up.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def get(self, key: str, default: str | None = None) -> str | None:
        row = self.connection.execute(
            "SELECT value FROM preference WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def set(self, key: str, value: str) -> None:
        self.connection.execute(
            "INSERT INTO preference (key, value) VALUES (?, ?)"
            " ON CONFLICT (key) DO UPDATE SET value = excluded.value",
            (key, value),
        )

    def get_language(self) -> str:
        return self.get("language", "en") or "en"

    def set_language(self, language: str) -> None:
        self.set("language", language)


class IslandRepository:
    """Which islands a profile has unlocked."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def unlock(self, profile_id: int, island_id: str) -> bool:
        """Unlock an island. Returns False when it was already unlocked.

        ``INSERT OR IGNORE`` against the composite primary key makes a repeated unlock a
        no-op instead of an error, so the caller does not have to check first — and the
        check-then-write race disappears with it.
        """
        cursor = self.connection.execute(
            "INSERT OR IGNORE INTO unlocked_island (profile_id, island_id, unlocked_at)"
            " VALUES (?, ?, ?)",
            (profile_id, island_id, _now()),
        )
        return cursor.rowcount > 0

    def list_for_profile(self, profile_id: int) -> list[str]:
        rows = self.connection.execute(
            "SELECT island_id FROM unlocked_island WHERE profile_id = ? ORDER BY island_id",
            (profile_id,),
        ).fetchall()
        return [row["island_id"] for row in rows]

    def is_unlocked(self, profile_id: int, island_id: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM unlocked_island WHERE profile_id = ? AND island_id = ?",
            (profile_id, island_id),
        ).fetchone()
        return row is not None
