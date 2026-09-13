"""Sentinel tests for every shipped content track.

The full suite in ``test_all_missions.py`` proves each mission's solution. These cheaper
checks keep track discovery and the data-only content boundary explicit.
"""

from pathlib import Path

import pytest
import yaml

CONTENT_ROOT = Path(__file__).resolve().parents[2] / "content"
TRACKS_ROOT = CONTENT_ROOT / "tracks"
CATALOGUES = (
    ("python", "en"),
    ("python", "pt-BR"),
    ("ai-engineering", "en"),
    ("ai-engineering", "pt-BR"),
)


@pytest.mark.parametrize(("track_id", "locale"), CATALOGUES)
def test_track_is_valid_yaml(track_id: str, locale: str) -> None:
    """track.yaml parses with safe_load and declares the fields the loader will need."""
    track_file = TRACKS_ROOT / track_id / "locales" / locale / "track.yaml"
    track = yaml.safe_load(track_file.read_text(encoding="utf-8"))

    assert isinstance(track, dict)
    for field in ("id", "name", "language", "runner", "islands"):
        assert field in track, f"track.yaml is missing the '{field}' field"


def test_declared_islands_are_only_yaml() -> None:
    """The content tree holds data, never executable Python (CLAUDE.md section 3)."""
    stray = list(CONTENT_ROOT.rglob("*.py"))
    assert not stray, f"Executable Python found under content/: {stray}"


@pytest.mark.parametrize(("track_id", "locale"), CATALOGUES)
def test_first_island_directory_exists(track_id: str, locale: str) -> None:
    """The first island declared in the track is present on disk.

    Island directories are added over time, so only the first is required here — the
    full cross-check between the track and the filesystem lands with the loader.
    """
    catalogue = TRACKS_ROOT / track_id / "locales" / locale
    track = yaml.safe_load((catalogue / "track.yaml").read_text(encoding="utf-8"))
    first = track["islands"][0]
    assert (catalogue / "islands" / first / "island.yaml").is_file()


def test_content_root_contains_only_the_track_collection() -> None:
    """Locales belong below a track instead of masquerading as sibling tracks."""
    assert {path.name for path in CONTENT_ROOT.iterdir()} == {"tracks"}
