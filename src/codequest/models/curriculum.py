"""Track and Island dataclasses.

A track is one language (Python, later Java, later TypeScript). An island is a themed
group of missions inside a track. Both are declared in YAML under ``content/`` and are
loaded into these objects before anything else touches them.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class UnlockRule:
    """What a player must have done before an island opens.

    Kept as data rather than as code in the island file, because ``content/`` is data
    only. The service layer interprets these numbers; the content never executes.
    """

    missions_completed: int = 0
    total_xp: int = 0
    requires_island: str | None = None
    requires_mission: str | None = None


@dataclass(frozen=True, slots=True)
class Island:
    """A themed group of missions inside a track."""

    id: str
    name: str
    track: str
    order: int
    theme: str = ""
    description: str = ""
    concepts: tuple[str, ...] = ()
    unlock_requires: UnlockRule = field(default_factory=UnlockRule)
    completion_reward_xp: int = 0
    mission_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Track:
    """One language taught by the game.

    ``runner`` names the Runner implementation that executes submissions for this
    track. That indirection is what lets v1.1 add Java by writing one runner file and
    one track file, with no change to the engine.
    """

    id: str
    name: str
    language: str
    runner: str
    file_extension: str
    version: str = ""
    description: str = ""
    island_ids: tuple[str, ...] = ()
