"""XP awards, level thresholds and island unlocking.

Rules live here, SQL lives in ``storage/``. The split matters because the four-save
limit, the XP-once rule and the unlock thresholds are *game design*, and game design
changes far more often than a schema does.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from codequest.models.curriculum import Island
from codequest.models.mission import Mission
from codequest.models.profile import MAX_PROFILES, MissionStatus, Profile, Progress
from codequest.models.verdict import Verdict
from codequest.storage.db import transaction
from codequest.storage.repositories import (
    AttemptRepository,
    IslandRepository,
    ProfileRepository,
    ProgressRepository,
)


class ProfileLimitReachedError(Exception):
    """Raised when a fifth career save is requested.

    A plain exception rather than a database constraint, exactly as
    ``docs/architecture.md`` specifies, so the UI can show "you already have four
    saves — delete one first" instead of an IntegrityError.
    """


class DuplicateProfileNameError(Exception):
    """Raised when a save name is already taken."""


@dataclass(frozen=True, slots=True)
class AwardResult:
    """What actually changed after an attempt was recorded.

    ``xp_awarded`` is what the player *gained now*, which is zero on a replay even
    though the verdict says the mission passed. The UI needs the difference: showing
    "+10 XP" on a mission that granted nothing is a lie the player will notice.
    """

    profile: Profile
    progress: Progress
    xp_awarded: int
    leveled_up: bool
    newly_unlocked: tuple[str, ...] = ()
    already_completed: bool = False


class ProgressService:
    """Owns progression: XP, levels, unlocking, and the save limit."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.profiles = ProfileRepository(connection)
        self.progress = ProgressRepository(connection)
        self.attempts = AttemptRepository(connection)
        self.islands = IslandRepository(connection)

    # ------------------------------------------------------------------- profiles

    def create_profile(self, name: str, track: str) -> Profile:
        """Create a career save, enforcing the limit and the unique name.

        Raises:
            ProfileLimitReachedError: four saves already exist.
            DuplicateProfileNameError: the name is taken.
        """
        name = name.strip()
        if not name:
            raise ValueError("a save needs a name")
        if self.profiles.count() >= MAX_PROFILES:
            raise ProfileLimitReachedError(
                f"you already have {MAX_PROFILES} saves. Delete one before creating another."
            )
        if self.profiles.get_by_name(name):
            raise DuplicateProfileNameError(f"a save called '{name}' already exists")

        with transaction(self.connection):
            return self.profiles.create(name, track)

    def list_profiles(self) -> list[Profile]:
        return self.profiles.list_all()

    def delete_profile(self, profile_id: int) -> None:
        with transaction(self.connection):
            self.profiles.delete(profile_id)

    # ------------------------------------------------------------------ attempts

    def record_attempt(
        self,
        profile: Profile,
        mission: Mission,
        code: str,
        verdict: Verdict,
        islands: tuple[Island, ...] = (),
    ) -> AwardResult:
        """Persist one attempt and award whatever it earned.

        # [AI-ENG:idempotency] The rule that makes this correct is that XP is awarded
        # for a mission *once*, decided by state already in the database rather than by
        # trusting the caller not to call twice. Replay the same winning submission and
        # the attempt is recorded, the verdict still says passed, and the XP granted is
        # zero.
        #
        # This is the same discipline an agent pipeline needs. A retried step must not
        # charge the card twice, send the email twice, or write the row twice, and "we
        # will be careful not to retry" is not a design. Make the effect depend on
        # persisted state and repetition stops being dangerous.
        """
        if profile.id is None:
            raise ValueError("cannot record an attempt for an unsaved profile")

        with transaction(self.connection):
            existing = self.progress.get(profile.id, mission.id)
            already_completed = existing is not None and existing.is_completed

            # The decision, in one line: pay only the first time.
            xp_to_award = mission.xp if (verdict.passed and not already_completed) else 0

            self.attempts.record(profile.id, mission.id, code, verdict)
            progress = self.progress.record_attempt(
                profile.id, mission.id, passed=verdict.passed, xp=xp_to_award
            )

            level_before = profile.level
            if xp_to_award:
                self.profiles.add_xp(profile.id, xp_to_award)
            else:
                self.profiles.touch(profile.id)

            updated = self.profiles.get(profile.id)
            assert updated is not None  # written inside this transaction

            newly_unlocked = self._unlock_eligible_islands(updated, islands)

        return AwardResult(
            profile=updated,
            progress=progress,
            xp_awarded=xp_to_award,
            leveled_up=updated.level > level_before,
            newly_unlocked=newly_unlocked,
            already_completed=already_completed,
        )

    def record_hint(self, profile: Profile, mission: Mission) -> None:
        """Record that a hint was revealed. Never blocks, never costs XP today."""
        if profile.id is None:
            raise ValueError("cannot record a hint for an unsaved profile")
        with transaction(self.connection):
            self.progress.record_hint(profile.id, mission.id)

    # ------------------------------------------------------------------ unlocking

    def is_island_unlocked(self, profile: Profile, island: Island) -> bool:
        """Whether ``island`` is open for this profile right now."""
        if profile.id is None:
            return island.unlock_requires == type(island.unlock_requires)()
        if self.islands.is_unlocked(profile.id, island.id):
            return True
        return self._meets_requirements(profile, island)

    def _meets_requirements(self, profile: Profile, island: Island) -> bool:
        rule = island.unlock_requires
        if profile.id is None:
            return False
        if profile.total_xp < rule.total_xp:
            return False
        if self.progress.completed_count(profile.id) < rule.missions_completed:
            return False
        return not (
            rule.requires_island and not self.islands.is_unlocked(profile.id, rule.requires_island)
        )

    def _unlock_eligible_islands(
        self, profile: Profile, islands: tuple[Island, ...]
    ) -> tuple[str, ...]:
        """Unlock every island whose requirements the profile now meets.

        Evaluated in ``order`` so a chain of islands can open in one go: finishing a
        mission that unlocks island 2 may immediately satisfy island 3's dependency
        on island 2.
        """
        if profile.id is None:
            return ()

        unlocked: list[str] = []
        for island in sorted(islands, key=lambda i: i.order):
            if self.islands.is_unlocked(profile.id, island.id):
                continue
            if self._meets_requirements(profile, island) and self.islands.unlock(
                profile.id, island.id
            ):
                unlocked.append(island.id)
        return tuple(unlocked)

    # -------------------------------------------------------------------- queries

    def mission_status(self, profile: Profile, mission: Mission) -> MissionStatus:
        """The status to paint next to a mission on the island map."""
        if profile.id is None:
            return MissionStatus.AVAILABLE
        progress = self.progress.get(profile.id, mission.id)
        return progress.status if progress else MissionStatus.AVAILABLE

    def progress_for(self, profile: Profile) -> dict[str, Progress]:
        """Every mission this profile has touched, keyed by mission id."""
        if profile.id is None:
            return {}
        return {item.mission_id: item for item in self.progress.list_for_profile(profile.id)}
