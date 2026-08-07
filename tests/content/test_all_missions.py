"""The most valuable test in the repository.

For every mission file that ships, this proves the lesson is completable: the file
validates, the entrypoint lines up across stub and solution, and the declared solution
actually passes the mission's own visible *and* hidden tests.

Content that ships with a solution which does not pass is a mission a player cannot
finish, and no amount of unit testing on the engine catches it.

Each mission is a separate parametrised case with the file name in the id, so a failure
names the file instead of saying "content is broken".
"""

from __future__ import annotations

import pytest

from codequest.engine.loader import iter_mission_paths, load_mission, load_track
from codequest.models.mission import XP_BY_DIFFICULTY
from codequest.services.game_session import GameSession
from conftest import CONTENT_ROOT

#: "python-pt" is a content *directory*, not a second track id - the Portuguese mirror
#: of the Python track lives in its own tree (see mission-author SKILL.md) so it can be
#: validated the same way as the English one without the engine ever learning about
#: languages. Both must independently pass every check in this file.
TRACKS = ["python", "python-pt"]
MISSION_PATHS = [path for track in TRACKS for path in iter_mission_paths(CONTENT_ROOT, track)]


def _ids(paths):
    return [f"{path.parent.parent.name}/{path.name}" for path in paths]


def test_there_is_content_to_validate():
    """Guards against a vacuous suite: an empty glob would make every test below pass."""
    assert MISSION_PATHS, "no mission files found under content/"


@pytest.mark.parametrize("path", MISSION_PATHS, ids=_ids(MISSION_PATHS))
def test_mission_file_is_valid(path):
    """The loader accepts it: required fields, types, difficulty, entrypoint agreement."""
    mission = load_mission(path)

    assert mission.id
    assert mission.visible_tests, "a mission with no visible cases teaches nothing"
    assert mission.hidden_tests, "without hidden cases a hardcoded return passes"


@pytest.mark.parametrize("path", MISSION_PATHS, ids=_ids(MISSION_PATHS))
def test_mission_xp_matches_its_difficulty(path):
    mission = load_mission(path)

    assert mission.xp == XP_BY_DIFFICULTY[mission.difficulty]


@pytest.mark.parametrize("path", MISSION_PATHS, ids=_ids(MISSION_PATHS))
def test_mission_has_a_full_hint_ladder(path):
    """Three rungs: a question, the name of the construct, the pattern on another problem."""
    mission = load_mission(path)

    levels = sorted(hint.level for hint in mission.hints)
    assert levels == [1, 2, 3], f"{path.name} has hint levels {levels}"


@pytest.mark.parametrize("path", MISSION_PATHS, ids=_ids(MISSION_PATHS))
def test_the_declared_solution_passes_its_own_tests(path):
    """The heart of it. Runs the shipped solution through the real sandbox."""
    mission = load_mission(path)

    outcome = GameSession().check_solution(mission)

    assert outcome.passed, f"{path.name}: {outcome.verdict.summary}"


#: Missions whose stub is deliberately complete and wrong - the Debugging island's
#: shape, where the task is to find and fix a bug rather than fill in a skeleton.
BUG_FIX_PATHS = [path for path in MISSION_PATHS if "bug-fix" in load_mission(path).tags]


def test_there_are_bug_fix_missions_to_validate():
    """Guards against a vacuous check: if the tag is ever renamed, the test below would
    silently stop covering anything."""
    assert BUG_FIX_PATHS, "no mission is tagged 'bug-fix'"


@pytest.mark.parametrize("path", BUG_FIX_PATHS, ids=_ids(BUG_FIX_PATHS))
def test_a_bug_fix_missions_stub_actually_fails(path):
    """The one guarantee this mission shape needs, and the only test that can give it.

    A skeleton mission is obviously incomplete, so nothing has to verify that. A bug-fix
    mission ships a stub that *looks* finished, and if a typo in the planted bug happens
    to make it correct, the mission still validates perfectly - the solution passes, the
    schema is fine - while asking the player to fix code that already works.
    """
    mission = load_mission(path)

    outcome = GameSession().attempt(mission, mission.signature.stub)

    assert not outcome.passed, (
        f"{path.name}: the stub passes its own tests, so there is no bug to find"
    )


@pytest.mark.parametrize("path", MISSION_PATHS, ids=_ids(MISSION_PATHS))
def test_the_solution_obeys_the_missions_own_constraints(path):
    """A solution using a builtin the mission forbids would teach the opposite lesson."""
    from codequest.engine.guard import check

    mission = load_mission(path)

    report = check(mission.solution, mission.constraints, mission.signature.entrypoint)

    assert report.ok, f"{path.name}: {report.violations}"


@pytest.mark.parametrize("track", TRACKS)
def test_mission_ids_are_unique_within_a_content_tree(track):
    """Duplicate ids inside one tree would make progress rows collide between lessons.

    Scoped per tree, not global: the same id appearing in both ``python/`` and
    ``python-pt/`` is not a collision, it is the point - a language mirror is keyed
    identically on purpose, so switching language mid-game keeps the same progress row.
    """
    ids = [load_mission(path).id for path in iter_mission_paths(CONTENT_ROOT, track)]

    duplicates = {mission_id for mission_id in ids if ids.count(mission_id) > 1}
    assert not duplicates, f"duplicate mission ids in {track}: {duplicates}"


def test_language_mirrors_declare_the_same_mission_ids():
    """The whole point of a mirror: identical id set, so a language switch never orphans
    or duplicates a save's progress."""
    by_track = {
        track: {load_mission(path).id for path in iter_mission_paths(CONTENT_ROOT, track)}
        for track in TRACKS
    }
    reference = by_track[TRACKS[0]]

    for track, ids in by_track.items():
        assert ids == reference, f"{track} declares a different id set than {TRACKS[0]}"


@pytest.mark.parametrize("track_id", TRACKS)
def test_every_island_declared_by_a_track_exists_on_disk(track_id):
    track = load_track(CONTENT_ROOT / track_id / "track.yaml")
    islands_dir = CONTENT_ROOT / track_id / "islands"

    missing = [
        island_id
        for island_id in track.island_ids
        if (islands_dir / island_id).is_dir()
        and not (islands_dir / island_id / "island.yaml").is_file()
    ]
    assert not missing, f"islands without an island.yaml: {missing}"


@pytest.mark.parametrize("path", MISSION_PATHS, ids=_ids(MISSION_PATHS))
def test_mission_concepts_are_declared_by_its_island(path):
    """A mission teaching a concept its island never lists means the syllabus drifted."""
    from codequest.engine.loader import load_island

    mission = load_mission(path)
    island = load_island(path.parent.parent / "island.yaml")

    unknown = set(mission.concepts) - set(island.concepts)
    assert not unknown, f"{path.name} teaches {unknown}, not listed in island '{island.id}'"
