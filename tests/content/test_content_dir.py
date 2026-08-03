"""Sentinel tests for the content tree.

The real content suite arrives in Phase 3 (``test_all_missions.py``, which proves every
mission's own solution passes its own tests). Until then these guard the one thing that
is already true: the Python track file exists, parses, and names islands that exist on disk.
"""

from pathlib import Path

import yaml

CONTENT_ROOT = Path(__file__).resolve().parents[2] / "content"
PYTHON_TRACK = CONTENT_ROOT / "python" / "track.yaml"


def test_python_track_is_valid_yaml() -> None:
    """track.yaml parses with safe_load and declares the fields the loader will need."""
    track = yaml.safe_load(PYTHON_TRACK.read_text(encoding="utf-8"))

    assert isinstance(track, dict)
    for field in ("id", "name", "language", "runner", "islands"):
        assert field in track, f"track.yaml is missing the '{field}' field"


def test_declared_islands_are_only_yaml() -> None:
    """The content tree holds data, never executable Python (CLAUDE.md section 3)."""
    stray = list(CONTENT_ROOT.rglob("*.py"))
    assert not stray, f"Executable Python found under content/: {stray}"


def test_first_island_directory_exists() -> None:
    """The first island declared in the track is present on disk.

    Island directories are added over time, so only the first is required here — the
    full cross-check between the track and the filesystem lands with the loader.
    """
    track = yaml.safe_load(PYTHON_TRACK.read_text(encoding="utf-8"))
    first = track["islands"][0]
    assert (CONTENT_ROOT / "python" / "islands" / first / "island.yaml").is_file()
