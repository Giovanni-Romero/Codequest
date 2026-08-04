"""Paths, feature flags and settings loaded from the environment.

The whole configuration surface of the game is this one file. Nothing else reads
``os.environ`` — a rule from ``docs/architecture.md`` that exists so a test can hand the
game a different Settings object instead of mutating the real process environment and
hoping to put it back.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

#: Fraction of a mission's XP kept after revealing N hints, indexed by hint count.
#: Beyond the last entry the last value holds, which is the floor.
#:
#: The floor is deliberate and it is 40%, not 0%. A hint is a tool, not a punishment: a
#: player who asks for help and then solves the mission has learned it. Zeroing the reward
#: teaches them to stay stuck in silence instead, which is the worst outcome this game can
#: produce. Design rule, not arithmetic — it lives here so it can be argued with.
HINT_XP_MULTIPLIERS: tuple[float, ...] = (1.0, 0.9, 0.7, 0.4)


def xp_after_hints(base_xp: int, hints_used: int) -> int:
    """Return the XP a mission awards after ``hints_used`` hints were revealed.

    Rounds to the nearest integer but never below 1 for a mission worth anything, so the
    smallest missions do not silently become worthless. A 10 XP mission with three hints
    pays 4; without the floor a hypothetical 1 XP mission would pay 0 and read as a bug.
    """
    if base_xp <= 0:
        return 0
    index = min(max(hints_used, 0), len(HINT_XP_MULTIPLIERS) - 1)
    return max(1, round(base_xp * HINT_XP_MULTIPLIERS[index]))


def _env_bool(name: str, default: bool) -> bool:
    """Read a boolean from the environment, accepting the spellings people actually type."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    """Read an int, falling back to the default rather than crashing on a typo.

    A malformed ``CODEQUEST_DEFAULT_TIMEOUT_MS=2 000`` should not stop someone playing.
    Config that refuses to start is only correct when the value is security-relevant.
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True, slots=True)
class Settings:
    """Everything the game reads from the outside world, resolved once."""

    content_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "content")
    save_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "saves")
    database_name: str = "codequest.db"

    default_timeout_ms: int = 2000
    default_memory_mb: int = 128

    mentor_enabled: bool = False
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "gemma4:cloud"
    ollama_timeout_seconds: int = 30

    debug: bool = False

    @property
    def database_path(self) -> Path:
        """Where the save database lives."""
        return self.save_dir / self.database_name


def load_settings(env_file: str | Path | None = None) -> Settings:
    """Build Settings from ``.env`` and the process environment.

    Real environment variables win over the ``.env`` file, which is what makes
    ``CODEQUEST_DEBUG=1 python -m codequest`` work for a one-off run.
    """
    load_dotenv(env_file or PROJECT_ROOT / ".env", override=False)

    content = os.getenv("CODEQUEST_CONTENT_DIR")
    saves = os.getenv("CODEQUEST_SAVE_DIR")

    return Settings(
        content_dir=Path(content) if content else PROJECT_ROOT / "content",
        save_dir=Path(saves) if saves else PROJECT_ROOT / "saves",
        default_timeout_ms=_env_int("CODEQUEST_DEFAULT_TIMEOUT_MS", 2000),
        default_memory_mb=_env_int("CODEQUEST_DEFAULT_MEMORY_MB", 128),
        mentor_enabled=_env_bool("CODEQUEST_MENTOR_ENABLED", False),
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "gemma4:cloud"),
        ollama_timeout_seconds=_env_int("OLLAMA_TIMEOUT_SECONDS", 30),
        debug=_env_bool("CODEQUEST_DEBUG", False),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """The process-wide settings, resolved on first use.

    Cached so the ``.env`` file is read once. Tests that need different values build a
    ``Settings`` directly and pass it in, rather than clearing this cache — a function
    that takes its configuration is easier to test than one that reaches for a global.
    """
    return load_settings()
