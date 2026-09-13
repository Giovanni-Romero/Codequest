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
    """The loaded catalogue for one track: its islands and their missions.

    ``track_id`` selects a curriculum and ``language`` selects its localized catalogue.
    Mission and island ids stay identical between locales, which lets a save's progress
    (keyed by those ids in SQLite) survive a language switch mid-game.
    """

    def __init__(
        self, content_dir: str | Path, track_id: str = "python", language: str = "en"
    ) -> None:
        self.content_dir = Path(content_dir)
        self.track_id = track_id
        self.language = language
        self.track: Track
        self._islands: dict[str, Island] = {}
        self._missions: dict[str, Mission] = {}
        self._load()

    @property
    def _track_root(self) -> Path:
        locale = "pt-BR" if self.language == "pt" else "en"
        return self.content_dir / "tracks" / self.track_id / "locales" / locale

    def set_language(self, language: str) -> None:
        """Switch which content tree is loaded, and reload the catalogue from it."""
        self.language = language
        self._load()

    def set_track(self, track_id: str) -> None:
        """Replace the active catalogue while keeping the player's chosen language."""
        self.track_id = track_id
        self._load()

    def _load(self) -> None:
        """Read every island and mission of the track into memory.

        Reassigns both dicts wholesale rather than mutating them in place - this runs
        again on every ``set_language`` call, and a stale entry left over from the
        previous language is a bug a reload should never be able to reintroduce.
        """
        track_root = self._track_root
        self.track = load_track(track_root / "track.yaml")
        islands_root = track_root / "islands"
        self._islands = {}

        missions = discover_missions(track_root)
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
        """Every mission of this track, in the order a player actually meets them.

        Sorted by the island's ``order``, not by its id. Those are not the same
        sequence and sorting by id was a real bug: island ids are words, so
        "collections" sorted before "foundations", which put Island 2 ahead of Island 1
        and made ``next_mission_after`` skip an entire island at every boundary. It was
        invisible while only one island existed.
        """

        def position(mission: Mission) -> tuple[int, int, str]:
            island = self._islands.get(mission.island)
            # An unknown island means content that failed to load. Sort it last rather
            # than crashing, and keep it deterministic with the id as a final tiebreak.
            island_order = island.order if island is not None else len(self._islands) + 1
            return (island_order, mission.order, mission.id)

        return tuple(sorted(self._missions.values(), key=position))

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
