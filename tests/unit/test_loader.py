"""Tests for the mission loader.

The loader is the boundary between hand-written content and the engine, so the tests
that matter are the ones about *bad* input. A loader that accepts a broken mission ships
a broken lesson to a player.
"""

from __future__ import annotations

import pytest

from codequest.engine.exceptions import ContentError, MissionValidationError
from codequest.engine.loader import (
    discover_missions,
    iter_mission_paths,
    load_island,
    load_mission,
    load_track,
)
from codequest.models.mission import Difficulty

CONTENT_DIR = "content"


# ------------------------------------------------------------------ the happy path


def test_loads_a_valid_mission(tmp_mission):
    mission = load_mission(tmp_mission)

    assert mission.id == "py-test-01"
    assert mission.difficulty is Difficulty.ELEMENTARY
    assert mission.signature.entrypoint == "double"
    assert mission.source_path == str(tmp_mission)


def test_visible_cases_come_first_and_keep_their_flag(tmp_mission):
    """Case order is what the player sees numbered on screen, so it must be stable."""
    mission = load_mission(tmp_mission)

    assert [case.visible for case in mission.tests] == [True, False, False]
    assert len(mission.visible_tests) == 1
    assert len(mission.hidden_tests) == 2


def test_constraints_are_read_from_the_file(tmp_mission):
    constraints = load_mission(tmp_mission).constraints

    assert constraints.forbidden_builtins == frozenset({"pow"})
    assert constraints.forbidden_imports == frozenset({"math"})
    assert constraints.max_runtime_ms == 1000
    assert constraints.max_memory_mb == 64


def test_absent_constraints_fall_back_to_documented_defaults(mission_factory):
    """docs/mission-schema.md says the whole block is optional."""
    path = mission_factory(remove=["constraints"])

    constraints = load_mission(path).constraints

    assert constraints.max_runtime_ms == 2000
    assert constraints.max_memory_mb == 128
    assert constraints.forbidden_builtins == frozenset()


# ------------------------------------------------------------------ failure paths


def test_missing_required_field_is_reported_by_name(mission_factory):
    path = mission_factory(remove=["solution"])

    with pytest.raises(MissionValidationError) as exc_info:
        load_mission(path)

    assert "missing required field 'solution'" in str(exc_info.value)


def test_every_problem_is_reported_at_once(mission_factory):
    """One run must surface all the errors, or fixing content becomes whack-a-mole."""
    path = mission_factory(remove=["brief", "hints", "concepts"])

    with pytest.raises(MissionValidationError) as exc_info:
        load_mission(path)

    assert len(exc_info.value.problems) >= 3
    message = str(exc_info.value)
    for field_name in ("brief", "hints", "concepts"):
        assert field_name in message


def test_unknown_difficulty_lists_the_valid_values(mission_factory):
    path = mission_factory(difficulty="impossible")

    with pytest.raises(MissionValidationError) as exc_info:
        load_mission(path)

    message = str(exc_info.value)
    assert "impossible" in message
    assert "elementary" in message


def test_xp_must_match_the_difficulty_table(mission_factory):
    """Content that pays the wrong XP unbalances progression silently."""
    path = mission_factory(xp=999)

    with pytest.raises(MissionValidationError) as exc_info:
        load_mission(path)

    assert "999" in str(exc_info.value)


def test_entrypoint_missing_from_the_stub_is_rejected(mission_factory):
    path = mission_factory(signature={"entrypoint": "double", "stub": "def other(n):\n    pass\n"})

    with pytest.raises(MissionValidationError) as exc_info:
        load_mission(path)

    assert "stub does not define 'def double('" in str(exc_info.value)


def test_entrypoint_missing_from_the_solution_is_rejected(mission_factory):
    """The most valuable check here: an unrunnable solution breaks the content suite."""
    path = mission_factory(solution="def other(n):\n    return n\n")

    with pytest.raises(MissionValidationError) as exc_info:
        load_mission(path)

    assert "solution does not define 'def double('" in str(exc_info.value)


def test_empty_hidden_test_group_is_rejected(mission_factory):
    """Without hidden cases, returning a constant passes the mission."""
    path = mission_factory(tests={"visible": [{"args": [2], "expect": 4}], "hidden": []})

    with pytest.raises(MissionValidationError) as exc_info:
        load_mission(path)

    assert "tests.hidden" in str(exc_info.value)


def test_case_without_expect_is_rejected(mission_factory):
    path = mission_factory(
        tests={"visible": [{"args": [2]}], "hidden": [{"args": [0], "expect": 0}]}
    )

    with pytest.raises(MissionValidationError) as exc_info:
        load_mission(path)

    assert "missing 'expect'" in str(exc_info.value)


def test_malformed_yaml_names_the_file(tmp_path):
    broken = tmp_path / "broken.yaml"
    broken.write_text("id: [unclosed\n", encoding="utf-8")

    with pytest.raises(ContentError) as exc_info:
        load_mission(broken)

    assert "broken.yaml" in str(exc_info.value)


def test_missing_file_raises_content_error(tmp_path):
    with pytest.raises(ContentError):
        load_mission(tmp_path / "does-not-exist.yaml")


def test_yaml_that_is_not_a_mapping_is_rejected(tmp_path):
    path = tmp_path / "list.yaml"
    path.write_text("- one\n- two\n", encoding="utf-8")

    with pytest.raises(MissionValidationError) as exc_info:
        load_mission(path)

    assert "mapping" in str(exc_info.value)


# ------------------------------------------------------------------ real content


def test_loads_the_shipped_example_mission():
    """The example in content/ is the reference every new mission is copied from."""
    path = "content/python/islands/01-foundations/missions/06-sum-list.yaml"

    mission = load_mission(path)

    assert mission.id == "py-foundations-06"
    assert mission.signature.entrypoint == "sum_list"
    assert "sum" in mission.constraints.forbidden_builtins
    assert len(mission.visible_tests) == 2
    assert len(mission.hidden_tests) == 6


def test_loads_the_python_track():
    track = load_track("content/python/track.yaml")

    assert track.id == "python"
    assert track.runner == "python"
    assert track.island_ids[0] == "01-foundations"


def test_loads_the_foundations_island():
    island = load_island("content/python/islands/01-foundations/island.yaml")

    assert island.id == "foundations"
    assert island.order == 1
    assert island.unlock_requires.missions_completed == 0


def test_discovery_finds_the_shipped_missions():
    missions = discover_missions(CONTENT_DIR, "python")

    assert any(mission.id == "py-foundations-06" for mission in missions)


def test_discovery_is_sorted_so_runs_are_reproducible():
    """Unsorted glob makes test ids depend on filesystem order, which differs per OS."""
    paths = list(iter_mission_paths(CONTENT_DIR, "python"))

    assert paths == sorted(paths)


def test_discovery_of_an_unknown_track_is_empty_not_an_error():
    """Java content does not exist yet; asking for it is a normal, empty answer."""
    assert discover_missions(CONTENT_DIR, "klingon") == []
