"""Find, filter and unlock rules for missions.

Owns the content catalogue in memory. Loading every mission once at startup rather than
per screen keeps the TUI responsive and means a broken mission file fails at launch,
where someone will see it, instead of when a player clicks on it.
"""

from __future__ import annotations

from pathlib import Path

from codequest.engine.loader import discover_missions, load_island, load_track
from codequest.models.curriculum import Island, Track
from codequest.models.mission import Mission


class MissionService:
    """The loaded catalogue for one track: its islands and their missions."""

    def __init__(self, content_dir: str | Path, track_id: str = "python") -> None:
        self.content_dir = Path(content_dir)
        self.track_id = track_id
        self.track: Track = load_track(self.content_dir / track_id / "track.yaml")
        self._islands: dict[str, Island] = {}
        self._missions: dict[str, Mission] = {}
        self._load()

    def _load(self) -> None:
        """Read every island and mission of the track into memory."""
        islands_root = self.content_dir / self.track_id / "islands"

        missions = discover_missions(self.content_dir, self.track_id)
        self._missions = {mission.id: mission for mission in missions}

        by_island: dict[str, list[Mission]] = {}
        for mission in missions:
            by_island.setdefault(mission.island, []).append(mission)

        for island_file in sorted(islands_root.glob("*/island.yaml")):
            island = load_island(island_file)
            owned = sorted(by_island.get(island.id, []), key=lambda m: m.order)
            self._islands[island.id] = Island(
                id=island.id,
                name=island.name,
                track=island.track,
                order=island.order,
                theme=island.theme,
                description=island.description,
                concepts=island.concepts,
                unlock_requires=island.unlock_requires,
                completion_reward_xp=island.completion_reward_xp,
                mission_ids=tuple(mission.id for mission in owned),
            )

    # ------------------------------------------------------------------- queries

    @property
    def islands(self) -> tuple[Island, ...]:
        """Islands of this track, in the order a player travels them."""
        return tuple(sorted(self._islands.values(), key=lambda i: i.order))

    @property
    def missions(self) -> tuple[Mission, ...]:
        """Every mission of this track, ordered by island then position."""
        return tuple(sorted(self._missions.values(), key=lambda m: (m.island, m.order)))

    def get_mission(self, mission_id: str) -> Mission | None:
        return self._missions.get(mission_id)

    def get_island(self, island_id: str) -> Island | None:
        return self._islands.get(island_id)

    def missions_in(self, island_id: str) -> tuple[Mission, ...]:
        island = self._islands.get(island_id)
        if island is None:
            return ()
        return tuple(
            mission
            for mission_id in island.mission_ids
            if (mission := self._missions.get(mission_id))
        )

    def next_mission_after(self, mission_id: str) -> Mission | None:
        """The mission that follows ``mission_id``, crossing into the next island if needed."""
        ordered = self.missions
        for index, mission in enumerate(ordered):
            if mission.id == mission_id:
                return ordered[index + 1] if index + 1 < len(ordered) else None
        return None

    def find_by_concept(self, concept: str) -> tuple[Mission, ...]:
        """Every mission that teaches ``concept``. Used by the mentor and by search."""
        return tuple(mission for mission in self.missions if concept in mission.concepts)

    def total_xp_available(self) -> int:
        """Sum of every mission's XP, for the progress bar on the map."""
        return sum(mission.xp for mission in self._missions.values())
