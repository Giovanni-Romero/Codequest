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

TRACKS = ["python"]
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


@pytest.mark.parametrize("path", MISSION_PATHS, ids=_ids(MISSION_PATHS))
def test_the_solution_obeys_the_missions_own_constraints(path):
    """A solution using a builtin the mission forbids would teach the opposite lesson."""
    from codequest.engine.guard import check

    mission = load_mission(path)

    report = check(mission.solution, mission.constraints, mission.signature.entrypoint)

    assert report.ok, f"{path.name}: {report.violations}"


def test_mission_ids_are_unique_across_the_repository():
    """Duplicate ids would make progress rows collide between two different lessons."""
    ids = [load_mission(path).id for path in MISSION_PATHS]

    duplicates = {mission_id for mission_id in ids if ids.count(mission_id) > 1}
    assert not duplicates, f"duplicate mission ids: {duplicates}"


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
