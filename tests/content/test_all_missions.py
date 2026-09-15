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

import importlib.util
import tomllib

import pytest
import yaml

from codequest.engine.loader import iter_mission_paths, load_island, load_mission, load_track
from codequest.models.mission import XP_BY_DIFFICULTY
from codequest.services.game_session import GameSession
from helpers import CONTENT_ROOT, PROJECT_ROOT

TRACKS_ROOT = CONTENT_ROOT / "tracks"


def _catalogue(track_id, locale):
    return TRACKS_ROOT / track_id / "locales" / locale


#: Each pair is one curriculum in two locales. Both must independently pass every
#: content check while keeping their executable contracts identical.
TRACK_PAIRS = (
    (_catalogue("python", "en"), _catalogue("python", "pt-BR")),
    (_catalogue("ai-engineering", "en"), _catalogue("ai-engineering", "pt-BR")),
)
CATALOGUES = [catalogue for pair in TRACK_PAIRS for catalogue in pair]
AI_CATALOGUES = (_catalogue("ai-engineering", "en"), _catalogue("ai-engineering", "pt-BR"))
AI_EN_ROOT = AI_CATALOGUES[0]
AI_NEW_CONCEPT_ISLANDS = (
    "15-responsible-ai",
    "16-mlops-and-model-lifecycle",
    "17-langchain",
    "18-langgraph",
    "19-llamaindex",
    "20-pydanticai",
)
MISSION_PATHS = [path for catalogue in CATALOGUES for path in iter_mission_paths(catalogue)]
SOURCE_MISSION_PATHS = [
    path for source_catalogue, _ in TRACK_PAIRS for path in iter_mission_paths(source_catalogue)
]

MIRROR_LOCKED_FIELDS = (
    "id",
    "track",
    "island",
    "order",
    "difficulty",
    "xp",
    "concepts",
    "tags",
    "tests",
    "constraints",
    "solution",
)


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
def test_mission_hints_do_not_hide_unknown_yaml_keys(path):
    """Flow-mapping punctuation must not truncate text into silently ignored keys."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    for hint in raw["hints"]:
        assert set(hint) == {"level", "text"}, f"{path.name} has malformed hint keys {set(hint)}"


@pytest.mark.parametrize("path", SOURCE_MISSION_PATHS, ids=_ids(SOURCE_MISSION_PATHS))
def test_the_declared_solution_passes_its_own_tests(path):
    """Run canonical solutions; mirror parity below proves their copies are identical."""
    mission = load_mission(path)

    if "requires-ai-ml" in mission.tags and any(
        importlib.util.find_spec(package) is None for package in ("torch", "transformers")
    ):
        pytest.skip("install the ai-ml extra to execute this mission")
    if "requires-ai-orchestration" in mission.tags and any(
        importlib.util.find_spec(package) is None
        for package in ("langchain", "langgraph", "pydantic_ai")
    ):
        pytest.skip("install the ai-orchestration extra to execute this mission")
    if "requires-ai-rag" in mission.tags and importlib.util.find_spec("llama_index") is None:
        pytest.skip("install the ai-rag extra to execute this mission")

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


@pytest.mark.parametrize("catalogue", CATALOGUES)
def test_mission_ids_are_unique_within_a_content_tree(catalogue):
    """Duplicate ids inside one tree would make progress rows collide between lessons.

    Scoped per locale, not global: a translated catalogue is keyed identically on
    purpose, so switching language mid-game keeps the same progress row.
    """
    ids = [load_mission(path).id for path in iter_mission_paths(catalogue)]

    duplicates = {mission_id for mission_id in ids if ids.count(mission_id) > 1}
    assert not duplicates, f"duplicate mission ids in {catalogue}: {duplicates}"


@pytest.mark.parametrize(("source_catalogue", "mirror_catalogue"), TRACK_PAIRS)
def test_language_mirrors_declare_the_same_mission_ids(source_catalogue, mirror_catalogue):
    """The whole point of a mirror: identical id set, so a language switch never orphans
    or duplicates a save's progress."""
    source_ids = {load_mission(path).id for path in iter_mission_paths(source_catalogue)}
    mirror_ids = {load_mission(path).id for path in iter_mission_paths(mirror_catalogue)}

    assert source_ids, f"{source_catalogue} has no missions"
    assert mirror_ids == source_ids, (
        f"{mirror_catalogue} declares different ids than {source_catalogue}"
    )


@pytest.mark.parametrize(("source_catalogue", "mirror_catalogue"), TRACK_PAIRS)
def test_language_mirrors_keep_structural_fields_identical(source_catalogue, mirror_catalogue):
    """Translated prose may differ; executable contracts and progress keys may not."""
    source_paths = {load_mission(path).id: path for path in iter_mission_paths(source_catalogue)}
    mirror_paths = {load_mission(path).id: path for path in iter_mission_paths(mirror_catalogue)}

    assert mirror_paths.keys() == source_paths.keys()
    for mission_id, source_path in source_paths.items():
        source = yaml.safe_load(source_path.read_text(encoding="utf-8"))
        mirror = yaml.safe_load(mirror_paths[mission_id].read_text(encoding="utf-8"))

        for field in MIRROR_LOCKED_FIELDS:
            assert mirror.get(field) == source.get(field), (
                f"{mission_id}: translated field '{field}'"
            )
        assert mirror["signature"]["entrypoint"] == source["signature"]["entrypoint"]


@pytest.mark.parametrize("catalogue", CATALOGUES)
def test_every_island_declared_by_a_track_exists_on_disk(catalogue):
    track = load_track(catalogue / "track.yaml")
    islands_dir = catalogue / "islands"

    missing = [
        island_id
        for island_id in track.island_ids
        if not (islands_dir / island_id / "island.yaml").is_file()
    ]
    assert not missing, f"islands without an island.yaml: {missing}"


@pytest.mark.parametrize("locale", ("en", "pt-BR"))
def test_ai_engineering_ships_complete_islands_in_order(locale):
    from codequest.services.mission_service import MissionService

    service = MissionService(CONTENT_ROOT, "ai-engineering", "pt" if locale == "pt-BR" else "en")
    islands_dir = _catalogue("ai-engineering", locale) / "islands"
    disk_folders = tuple(path.name for path in sorted(islands_dir.iterdir()) if path.is_dir())

    assert service.track.island_ids == disk_folders
    assert [island.order for island in service.islands] == list(range(1, len(service.islands) + 1))
    assert all(
        [mission.order for mission in service.missions_in(island.id)] == list(range(1, 9))
        for island in service.islands
    )
    expected_unlocks = [None] + [
        service.missions_in(island.id)[-1].id for island in service.islands[:-1]
    ]
    assert [
        island.unlock_requires.requires_mission for island in service.islands
    ] == expected_unlocks
    assert service.missions_in(service.islands[-1].id)[-1].id == "ai-pydanticai-08"


def test_ai_orchestration_extra_pins_the_shipped_frameworks():
    project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["optional-dependencies"]["ai-orchestration"] == [
        "langchain>=1.4,<1.5",
        "langgraph>=1.2,<1.3",
        "pydantic-ai-slim>=2.43,<2.44",
    ]


def test_ai_rag_extra_pins_llamaindex():
    project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["optional-dependencies"]["ai-rag"] == [
        "llama-index>=0.14,<0.15",
    ]


@pytest.mark.parametrize("locale", ("en", "pt-BR"))
def test_ai_pytorch_capstone_integrates_every_island_concept(locale):
    island_path = _catalogue("ai-engineering", locale) / "islands" / "13-pytorch-and-deep-learning"
    island = load_island(island_path / "island.yaml")
    capstone = load_mission(island_path / "missions" / "08-audit-a-tiny-training-pipeline.yaml")

    assert set(capstone.concepts) == set(island.concepts)


@pytest.mark.parametrize("locale", ("en", "pt-BR"))
def test_ai_nlp_concepts_are_introduced_before_reinforcement(locale):
    island_path = _catalogue("ai-engineering", locale) / "islands" / "14-nlp-and-transformers"
    expected = (
        "tokenizer-boundaries",
        "model-config-and-weights",
        "inference-pipelines",
        "fine-tuning-boundaries",
    )
    missions = [
        load_mission(path)
        for path in iter_mission_paths(_catalogue("ai-engineering", locale))
        if path.parent.parent == island_path
    ]
    seen = set()
    for mission, concept in zip(missions[:4], expected, strict=True):
        introduced = set(mission.concepts) - seen
        assert introduced == {concept}, f"{mission.id} introduces {introduced}"
        seen.update(mission.concepts)
    for mission in missions[4:7]:
        assert set(mission.concepts) <= seen, f"{mission.id} introduces a late concept"


@pytest.mark.parametrize("locale", ("en", "pt-BR"))
@pytest.mark.parametrize("island_id", AI_NEW_CONCEPT_ISLANDS)
def test_ai_new_concepts_are_introduced_before_reinforcement(locale, island_id):
    island_path = _catalogue("ai-engineering", locale) / "islands" / island_id
    island = load_island(island_path / "island.yaml")
    missions = [load_mission(path) for path in sorted((island_path / "missions").glob("*.yaml"))]

    assert len(island.concepts) == 4
    assert len(missions) == 8
    seen = set()
    for mission, concept in zip(missions[:4], island.concepts, strict=True):
        introduced = set(mission.concepts) - seen
        assert introduced == {concept}, f"{mission.id} introduces {introduced}"
        seen.update(mission.concepts)
    for mission in missions[4:7]:
        assert set(mission.concepts) <= seen, f"{mission.id} introduces a late concept"
    assert set(missions[7].concepts) == set(island.concepts)


@pytest.mark.parametrize("path", MISSION_PATHS, ids=_ids(MISSION_PATHS))
def test_mission_concepts_are_declared_by_its_island(path):
    """A mission teaching a concept its island never lists means the syllabus drifted."""
    from codequest.engine.loader import load_island

    mission = load_mission(path)
    island = load_island(path.parent.parent / "island.yaml")

    unknown = set(mission.concepts) - set(island.concepts)
    assert not unknown, f"{path.name} teaches {unknown}, not listed in island '{island.id}'"


@pytest.mark.parametrize("catalogue", AI_CATALOGUES)
def test_ai_math_capstone_integrates_every_island_concept(catalogue):
    """Island 9 closes by combining math, statistics, probability, and optimization."""
    from codequest.engine.loader import load_island

    island_path = catalogue / "islands" / "09-mathematical-statistical-foundations"
    island = load_island(island_path / "island.yaml")
    capstone = load_mission(island_path / "missions" / "08-take-one-gradient-step.yaml")

    assert set(capstone.concepts) == set(island.concepts), (
        f"capstone covers {capstone.concepts}, expected {island.concepts}"
    )


@pytest.mark.parametrize("catalogue", AI_CATALOGUES)
def test_ai_machine_learning_capstone_integrates_every_island_concept(catalogue):
    """Island 10 closes with one auditable experiment spanning all ML concepts."""
    from codequest.engine.loader import load_island

    island_path = catalogue / "islands" / "10-machine-learning-foundations"
    island = load_island(island_path / "island.yaml")
    capstone = load_mission(island_path / "missions" / "08-audit-a-learning-experiment.yaml")

    assert set(capstone.concepts) == set(island.concepts), (
        f"capstone covers {capstone.concepts}, expected {island.concepts}"
    )


@pytest.mark.parametrize("catalogue", AI_CATALOGUES)
def test_ai_reasoning_capstone_integrates_every_island_concept(catalogue):
    """Island 11 closes with one audit spanning search, planning, and learning."""
    from codequest.engine.loader import load_island

    island_path = catalogue / "islands" / "11-reasoning-and-decision-making"
    island = load_island(island_path / "island.yaml")
    capstone = load_mission(island_path / "missions" / "08-audit-a-decision-process.yaml")

    assert set(capstone.concepts) == set(island.concepts), (
        f"capstone covers {capstone.concepts}, expected {island.concepts}"
    )


@pytest.mark.parametrize("catalogue", AI_CATALOGUES)
def test_ai_data_engineering_capstone_integrates_every_island_concept(catalogue):
    """Island 12 closes with one reproducible audit spanning every data concept."""
    from codequest.engine.loader import load_island

    island_path = catalogue / "islands" / "12-data-engineering-for-ai"
    island = load_island(island_path / "island.yaml")
    capstone = load_mission(island_path / "missions" / "08-audit-a-data-pipeline.yaml")

    assert set(capstone.concepts) == set(island.concepts), (
        f"capstone covers {capstone.concepts}, expected {island.concepts}"
    )


@pytest.mark.parametrize(
    ("mission_name", "args"),
    (
        ("05-fingerprint-a-dataset.yaml", ([{1: "x"}],)),
        ("05-fingerprint-a-dataset.yaml", ([{"value": (1, 2)}],)),
        (
            "06-record-dataset-lineage.yaml",
            ([{"value": (1, 2)}], {"raw": "a" * 64}, "v1"),
        ),
        (
            "07-run-a-reproducible-pipeline.yaml",
            ([{"id": 1, "value": (1, 2)}], ["id", "value"], "id", "v1"),
        ),
        (
            "08-audit-a-data-pipeline.yaml",
            (
                [{"id": 1, "value": (1, 2)}],
                {
                    "id": {
                        "type": "integer",
                        "nullable": False,
                        "min": None,
                        "max": None,
                        "allowed": None,
                    },
                    "value": {
                        "type": "string",
                        "nullable": False,
                        "min": None,
                        "max": None,
                        "allowed": None,
                    },
                },
                "id",
                "v1",
            ),
        ),
    ),
)
def test_ai_data_hashing_rejects_values_outside_json(mission_name, args):
    mission_path = AI_EN_ROOT / "islands" / "12-data-engineering-for-ai" / "missions" / mission_name
    mission = load_mission(mission_path)
    namespace = {}
    exec(mission.solution, namespace)

    with pytest.raises(ValueError):
        namespace[mission.signature.entrypoint](*args)


def test_ai_data_fingerprint_translates_unicode_encoding_errors():
    mission_path = (
        AI_EN_ROOT
        / "islands"
        / "12-data-engineering-for-ai"
        / "missions"
        / "05-fingerprint-a-dataset.yaml"
    )
    mission = load_mission(mission_path)
    namespace = {}
    exec(mission.solution, namespace)

    with pytest.raises(ValueError):
        namespace[mission.signature.entrypoint]([{"text": "\ud800"}])
