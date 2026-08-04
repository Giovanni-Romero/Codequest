"""Assembles the services a front end needs, so front ends never touch storage.

The layer rule says ``tui/`` may import ``services/`` and ``models/`` and nothing else,
which leaves a real question: somebody has to open the SQLite connection, and it cannot
be the UI.

This module is that seam. It is allowed to know about ``storage/`` because it lives in
``services/``, and it hands back an object the UI can hold without ever learning that a
database exists. The CLI uses the same function, so both front ends are wired identically.
"""

from __future__ import annotations

import contextlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from codequest.config import Settings, get_settings
from codequest.services.game_session import GameSession
from codequest.services.mission_service import MissionService
from codequest.services.progress_service import ProgressService
from codequest.storage.db import init_db


@dataclass(frozen=True, slots=True)
class GameContext:
    """Everything a front end needs, wired together and ready to use."""

    settings: Settings
    missions: MissionService
    progress: ProgressService
    session: GameSession
    connection: sqlite3.Connection

    def close(self) -> None:
        """Release the database. Safe to call more than once."""
        with contextlib.suppress(sqlite3.ProgrammingError):
            self.connection.close()


def create_context(
    settings: Settings | None = None,
    *,
    database: str | Path | None = None,
    track: str = "python",
) -> GameContext:
    """Open the database, load the catalogue, and wire the services together.

    Args:
        settings: Resolved configuration. Defaults to the process settings.
        database: Override for the save file. Tests pass a temp path; the CLI passes
            ``--db``. Taking it as a parameter is what keeps this testable without
            touching the real save.
        track: Which language track to load.
    """
    settings = settings or get_settings()
    connection = init_db(database or settings.database_path)
    progress = ProgressService(connection)

    return GameContext(
        settings=settings,
        missions=MissionService(settings.content_dir, track),
        progress=progress,
        session=GameSession(progress=progress),
        connection=connection,
    )
