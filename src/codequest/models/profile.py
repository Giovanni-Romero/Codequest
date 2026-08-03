"""Profile and Progress dataclasses.

A profile is one career save. Progress is that profile's standing on one mission.
Both are plain data: the rules about XP, levels and unlocking live in
``services/progress_service.py``, never here.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

#: XP required to reach each level, index 0 being level 1. Kept next to the model
#: because it is a property of progression, not of the UI or the database.
LEVEL_THRESHOLDS: tuple[int, ...] = (0, 100, 250, 500, 900, 1400, 2100, 3000, 4200, 5800)

#: The game allows four career saves. Enforced by ProgressService, deliberately not by
#: a database constraint, so the refusal can be a friendly sentence instead of an
#: IntegrityError (see docs/architecture.md).
MAX_PROFILES = 4


class MissionStatus(StrEnum):
    """Where a profile stands on a single mission."""

    LOCKED = "locked"
    AVAILABLE = "available"
    ATTEMPTED = "attempted"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class Progress:
    """One profile's standing on one mission.

    ``best_xp`` records what was actually awarded, which is what makes XP idempotent:
    replaying a completed mission compares against this and awards nothing.
    """

    profile_id: int
    mission_id: str
    status: MissionStatus = MissionStatus.AVAILABLE
    best_xp: int = 0
    attempts: int = 0
    hints_used: int = 0
    completed_at: datetime | None = None

    @property
    def is_completed(self) -> bool:
        """Whether this mission has ever been solved by this profile."""
        return self.status is MissionStatus.COMPLETED


@dataclass(frozen=True, slots=True)
class Profile:
    """One career save."""

    id: int | None
    name: str
    track: str
    created_at: datetime | None = None
    last_played_at: datetime | None = None
    total_xp: int = 0
    unlocked_islands: frozenset[str] = frozenset()
    diagnostics: dict[str, str] = field(default_factory=dict)

    @property
    def level(self) -> int:
        """The level this profile's XP buys, starting at 1.

        Derived rather than stored: a stored level is a second source of truth that
        silently goes stale the day the threshold table changes.
        """
        level = 1
        for threshold in LEVEL_THRESHOLDS[1:]:
            if self.total_xp >= threshold:
                level += 1
            else:
                break
        return level

    @property
    def xp_to_next_level(self) -> int | None:
        """XP still needed for the next level, or ``None`` at the maximum level."""
        next_index = self.level
        if next_index >= len(LEVEL_THRESHOLDS):
            return None
        return LEVEL_THRESHOLDS[next_index] - self.total_xp
