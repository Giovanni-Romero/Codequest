"""Database connection and schema creation.

Plain ``sqlite3``, no ORM. The schema is small enough that an ORM would hide the SQL
without removing the need to understand it, and the SQL here is the part worth seeing.

## Migrations

Every schema change is a numbered migration in ``MIGRATIONS``, applied in order and
recorded in ``schema_version``. Running them is idempotent: a database already at
version 3 skips 1 through 3 and applies only what is new. That property is what lets a
player's save survive an update instead of being recreated.
"""

from __future__ import annotations

import contextlib
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

#: Ordered schema migrations. Append only — never edit a shipped one, because a database
#: that already applied version 2 will never see the edit, and the two installs silently
#: diverge.
MIGRATIONS: tuple[tuple[int, str], ...] = (
    (
        1,
        """
        CREATE TABLE profile (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT    NOT NULL UNIQUE,
            track          TEXT    NOT NULL,
            created_at     TEXT    NOT NULL,
            last_played_at TEXT    NOT NULL,
            total_xp       INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE progress (
            profile_id   INTEGER NOT NULL REFERENCES profile(id) ON DELETE CASCADE,
            mission_id   TEXT    NOT NULL,
            status       TEXT    NOT NULL,
            best_xp      INTEGER NOT NULL DEFAULT 0,
            attempts     INTEGER NOT NULL DEFAULT 0,
            hints_used   INTEGER NOT NULL DEFAULT 0,
            completed_at TEXT,
            PRIMARY KEY (profile_id, mission_id)
        );

        CREATE TABLE attempt (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL REFERENCES profile(id) ON DELETE CASCADE,
            mission_id TEXT    NOT NULL,
            code       TEXT    NOT NULL,
            verdict    TEXT    NOT NULL,
            passed     INTEGER NOT NULL,
            created_at TEXT    NOT NULL
        );

        CREATE TABLE unlocked_island (
            profile_id  INTEGER NOT NULL REFERENCES profile(id) ON DELETE CASCADE,
            island_id   TEXT    NOT NULL,
            unlocked_at TEXT    NOT NULL,
            PRIMARY KEY (profile_id, island_id)
        );

        CREATE INDEX idx_attempt_profile_mission ON attempt(profile_id, mission_id);
        """,
    ),
)


def connect(path: str | Path) -> sqlite3.Connection:
    """Open a connection with the settings this project depends on.

    Three pragmas are not optional here:

    ``foreign_keys = ON``
        SQLite ships with foreign key enforcement **off**, per connection, for backwards
        compatibility. Every ``REFERENCES`` clause above is decorative until this runs.
        Deleting a profile would silently orphan its progress rows.

    ``journal_mode = WAL``
        Lets a reader and a writer coexist. The Phase 4 UI reads progress on one thread
        while a save is written on another; without WAL that is a "database is locked".

    ``row_factory``
        Rows come back accessible by column name. Positional access breaks the moment
        someone adds a column in the middle of a SELECT.
    """
    path = Path(path)
    if path.parent != Path():
        path.parent.mkdir(parents=True, exist_ok=True)

    # check_same_thread=False because the UI runs an attempt on a worker thread and that
    # attempt persists its result. Python's default guard assumes one connection per
    # thread; the underlying library here reports threadsafety 3 (serialized), so sharing
    # a connection is supported. What is *not* automatic is transaction interleaving, so
    # ProgressService serialises its writers with a lock. Dropping the guard without
    # adding that lock would trade a loud error for a rare corrupted save.
    connection = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def current_version(connection: sqlite3.Connection) -> int:
    """Return the highest migration applied, or 0 for an untouched database."""
    connection.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)")
    row = connection.execute("SELECT MAX(version) AS version FROM schema_version").fetchone()
    return row["version"] or 0


def migrate(connection: sqlite3.Connection) -> int:
    """Apply every pending migration and return the resulting version.

    Each migration runs inside a transaction, so a failure halfway leaves the database
    at the previous version rather than in a state that is neither.
    """
    version = current_version(connection)

    for number, script in MIGRATIONS:
        if number <= version:
            continue

        # The transaction has to live *inside* the script. ``executescript`` commits any
        # pending transaction before it runs, so a BEGIN issued around the call is gone
        # by the time the script starts.
        #
        # The version number is formatted into the SQL rather than bound, because
        # ``executescript`` takes no parameters. It is safe here for a structural reason,
        # not a hopeful one: it is an ``int`` from a module-level constant in this file,
        # and ``int()`` makes anything else a TypeError before it reaches the database.
        # This is the only interpolation in the project, and it is spelled out so it is
        # never read as permission for the next one.
        statements = f"BEGIN;\n{script}\nINSERT INTO schema_version (version) VALUES ({int(number)});\nCOMMIT;"
        try:
            connection.executescript(statements)
        except sqlite3.Error:
            with contextlib.suppress(sqlite3.Error):
                connection.execute("ROLLBACK")
            raise
        version = number

    return version


def init_db(path: str | Path) -> sqlite3.Connection:
    """Open a connection and bring the schema up to date. The normal entry point."""
    connection = connect(path)
    migrate(connection)
    return connection


@contextmanager
def transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Run a block as one all-or-nothing unit.

    Awarding XP touches ``progress``, ``profile`` and possibly ``unlocked_island``. A
    crash between those writes would leave a player who completed a mission with no XP,
    or with XP for a mission not marked complete. Either is worse than the whole thing
    failing cleanly.
    """
    connection.execute("BEGIN")
    try:
        yield connection
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    else:
        connection.execute("COMMIT")
