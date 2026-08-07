"""YAML to Mission, with schema validation and loud author-facing errors.

This is the only module that knows the mission file format. Everything downstream
works on the dataclasses in ``models/``, which is what makes the content format
replaceable without touching the engine.

Two rules shape the design:

1. **Parse, then validate.** Never validate while parsing. Mixing the two produces
   error messages that describe the parser's position rather than the author's mistake.
2. **Report every problem at once.** A validator that stops at the first error turns a
   file with five typos into five edit-run cycles.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

import yaml

from codequest.engine.exceptions import ContentError, MissionValidationError
from codequest.models.curriculum import Island, Track, UnlockRule
from codequest.models.mission import (
    XP_BY_DIFFICULTY,
    Constraints,
    Difficulty,
    Hint,
    Mission,
    Signature,
    Teaching,
    TestCase,
)

_REQUIRED_MISSION_FIELDS = (
    "id",
    "title",
    "track",
    "island",
    "order",
    "difficulty",
    "xp",
    "concepts",
    "teaching",
    "brief",
    "signature",
    "tests",
    "hints",
    "solution",
)

_REQUIRED_TEACHING_FIELDS = ("analogy", "explanation", "worked_example", "key_points")


def _read_yaml(path: Path) -> Any:
    """Parse a YAML file, or raise ContentError naming the file.

    # [AI-ENG:untrusted-parsing] ``safe_load`` refuses to construct arbitrary Python
    # objects; ``load`` will happily instantiate a class named in the document. The
    # same reflex applies to anything a model emits — never hand model output to a
    # deserializer that can build objects or call code.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContentError(f"cannot read {path}: {exc}") from exc

    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ContentError(f"{path} is not valid YAML: {exc}") from exc


def _defines_function(source: str, name: str) -> bool:
    """Whether ``source`` contains a ``def name(`` at any indentation level."""
    pattern = rf"^\s*def\s+{re.escape(name)}\s*\("
    return re.search(pattern, source, re.MULTILINE) is not None


def _as_tuple(value: Any) -> tuple[Any, ...]:
    """Coerce a YAML scalar or sequence into a tuple, treating a bare string as one item."""
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, Iterable):
        return (value,)
    return tuple(value)


def _validate_mission(raw: Any) -> list[str]:
    """Return every schema problem found in ``raw``. An empty list means valid.

    # [AI-ENG:schema-validation] Declarative data from outside the program is exactly
    # the shape of an LLM's structured output: it *looks* like the contract and
    # silently is not. Validating the whole document and reporting all violations at
    # once is what turns a vague "the model returned garbage" into a fixable list.
    """
    problems: list[str] = []

    if not isinstance(raw, dict):
        return [f"top level must be a mapping, got {type(raw).__name__}"]

    for field_name in _REQUIRED_MISSION_FIELDS:
        if field_name not in raw or raw[field_name] is None:
            problems.append(f"missing required field '{field_name}'")

    difficulty: Difficulty | None = None
    if "difficulty" in raw:
        try:
            difficulty = Difficulty(raw["difficulty"])
        except ValueError:
            valid = ", ".join(d.value for d in Difficulty)
            problems.append(f"difficulty '{raw['difficulty']}' is not one of: {valid}")

    if difficulty is not None and isinstance(raw.get("xp"), int):
        expected_xp = XP_BY_DIFFICULTY[difficulty]
        if raw["xp"] != expected_xp:
            problems.append(
                f"xp is {raw['xp']} but difficulty '{difficulty.value}' awards {expected_xp}"
            )

    teaching = raw.get("teaching")
    if isinstance(teaching, dict):
        for field_name in _REQUIRED_TEACHING_FIELDS:
            if not teaching.get(field_name):
                problems.append(f"teaching.{field_name} is missing or empty")
    elif "teaching" in raw:
        problems.append("teaching must be a mapping")

    signature = raw.get("signature")
    entrypoint = None
    if isinstance(signature, dict):
        entrypoint = signature.get("entrypoint")
        if not entrypoint:
            problems.append("signature.entrypoint is missing")
        if not signature.get("stub"):
            problems.append("signature.stub is missing")
    elif "signature" in raw:
        problems.append("signature must be a mapping")

    # The entrypoint has to exist in both places or the engine calls a function that
    # is not there, and the player sees a confusing NameError instead of a lesson.
    if entrypoint:
        stub = (signature or {}).get("stub", "")
        if stub and not _defines_function(stub, entrypoint):
            problems.append(f"signature.stub does not define 'def {entrypoint}('")
        solution = raw.get("solution", "")
        if solution and not _defines_function(solution, entrypoint):
            problems.append(f"solution does not define 'def {entrypoint}('")

    tests = raw.get("tests")
    if isinstance(tests, dict):
        for group in ("visible", "hidden"):
            cases = tests.get(group)
            if not cases:
                problems.append(f"tests.{group} must hold at least one case")
                continue
            if not isinstance(cases, list):
                problems.append(f"tests.{group} must be a list")
                continue
            for index, case in enumerate(cases):
                if not isinstance(case, dict):
                    problems.append(f"tests.{group}[{index}] must be a mapping")
                    continue
                if "args" not in case:
                    problems.append(f"tests.{group}[{index}] is missing 'args'")

                # A case passes either by returning a value or by raising. Demanding
                # exactly one of the two is what stops a silently ambiguous case: with
                # both, the author cannot say which outcome they meant, and with
                # neither there is nothing to check at all.
                has_expect = "expect" in case
                has_raises = "raises" in case
                if has_expect and has_raises:
                    problems.append(
                        f"tests.{group}[{index}] sets both 'expect' and 'raises' - "
                        "a case either returns a value or raises, never both"
                    )
                elif not has_expect and not has_raises:
                    problems.append(f"tests.{group}[{index}] needs either 'expect' or 'raises'")
                elif has_raises and not isinstance(case["raises"], str):
                    problems.append(
                        f"tests.{group}[{index}].raises must be an exception type name, "
                        "written as a string"
                    )
    elif "tests" in raw:
        problems.append("tests must be a mapping with 'visible' and 'hidden'")

    hints = raw.get("hints")
    if isinstance(hints, list):
        if not hints:
            problems.append("hints must hold at least one entry")
        for index, hint in enumerate(hints):
            if not isinstance(hint, dict):
                problems.append(f"hints[{index}] must be a mapping")
            elif not isinstance(hint.get("level"), int):
                problems.append(f"hints[{index}].level must be an integer")
            elif not hint.get("text"):
                problems.append(f"hints[{index}].text is missing or empty")
    elif "hints" in raw:
        problems.append("hints must be a list")

    if not isinstance(raw.get("order", 0), int):
        problems.append("order must be an integer")

    return problems


def _build_cases(tests: dict[str, Any]) -> tuple[TestCase, ...]:
    """Flatten the visible/hidden groups into one ordered tuple of cases.

    Visible cases come first so their indices match what the player sees on screen.
    """
    cases: list[TestCase] = []
    for group, visible in (("visible", True), ("hidden", False)):
        for raw_case in tests.get(group) or []:
            cases.append(
                TestCase(
                    args=tuple(raw_case.get("args") or ()),
                    kwargs=dict(raw_case.get("kwargs") or {}),
                    expect=raw_case.get("expect"),
                    raises=raw_case.get("raises"),
                    tolerance=raw_case.get("tolerance"),
                    visible=visible,
                )
            )
    return tuple(cases)


def _build_constraints(raw: Any) -> Constraints:
    """Build Constraints from the optional block, falling back to documented defaults."""
    if not isinstance(raw, dict):
        return Constraints()
    defaults = Constraints()
    return Constraints(
        forbidden_builtins=frozenset(raw.get("forbidden_builtins") or ()),
        forbidden_imports=frozenset(raw.get("forbidden_imports") or ()),
        max_runtime_ms=int(raw.get("max_runtime_ms") or defaults.max_runtime_ms),
        max_memory_mb=int(raw.get("max_memory_mb") or defaults.max_memory_mb),
    )


def load_mission(path: str | Path) -> Mission:
    """Read one mission YAML file and return a validated Mission.

    Raises:
        ContentError: the file is unreadable or is not valid YAML.
        MissionValidationError: the file parsed but violates the schema. The exception
            lists every problem found, not just the first.
    """
    path = Path(path)
    raw = _read_yaml(path)

    problems = _validate_mission(raw)
    if problems:
        raise MissionValidationError(str(path), problems)

    teaching_raw = raw["teaching"]
    signature_raw = raw["signature"]

    return Mission(
        id=raw["id"],
        title=raw["title"],
        track=raw["track"],
        island=raw["island"],
        order=raw["order"],
        difficulty=Difficulty(raw["difficulty"]),
        xp=raw["xp"],
        concepts=_as_tuple(raw["concepts"]),
        teaching=Teaching(
            analogy=teaching_raw["analogy"],
            explanation=teaching_raw["explanation"],
            worked_example=teaching_raw["worked_example"],
            key_points=_as_tuple(teaching_raw["key_points"]),
        ),
        brief=raw["brief"],
        signature=Signature(
            entrypoint=signature_raw["entrypoint"],
            stub=signature_raw["stub"],
        ),
        tests=_build_cases(raw["tests"]),
        hints=tuple(Hint(level=h["level"], text=h["text"]) for h in raw["hints"]),
        solution=raw["solution"],
        constraints=_build_constraints(raw.get("constraints")),
        tags=_as_tuple(raw.get("tags")),
        source_path=str(path),
    )


def load_track(path: str | Path) -> Track:
    """Read a ``track.yaml`` and return a Track."""
    path = Path(path)
    raw = _read_yaml(path)
    if not isinstance(raw, dict):
        raise ContentError(f"{path}: track file must be a mapping")

    missing = [f for f in ("id", "name", "language", "runner") if not raw.get(f)]
    if missing:
        raise ContentError(f"{path}: track is missing {', '.join(missing)}")

    return Track(
        id=raw["id"],
        name=raw["name"],
        language=raw["language"],
        runner=raw["runner"],
        file_extension=raw.get("file_extension", ".txt"),
        version=str(raw.get("version", "")),
        description=raw.get("description", ""),
        island_ids=_as_tuple(raw.get("islands")),
    )


def load_island(path: str | Path) -> Island:
    """Read an ``island.yaml`` and return an Island."""
    path = Path(path)
    raw = _read_yaml(path)
    if not isinstance(raw, dict):
        raise ContentError(f"{path}: island file must be a mapping")

    missing = [f for f in ("id", "name", "track", "order") if raw.get(f) is None]
    if missing:
        raise ContentError(f"{path}: island is missing {', '.join(missing)}")

    unlock_raw = raw.get("unlock_requires") or {}
    return Island(
        id=raw["id"],
        name=raw["name"],
        track=raw["track"],
        order=raw["order"],
        theme=raw.get("theme", ""),
        description=raw.get("description", ""),
        concepts=_as_tuple(raw.get("concepts")),
        unlock_requires=UnlockRule(
            missions_completed=int(unlock_raw.get("missions_completed", 0)),
            total_xp=int(unlock_raw.get("total_xp", 0)),
            requires_island=unlock_raw.get("requires_island"),
        ),
        completion_reward_xp=int(raw.get("completion_reward_xp", 0)),
        mission_ids=(),
    )


def iter_mission_paths(content_dir: str | Path, track: str) -> Iterator[Path]:
    """Yield every mission file of a track, sorted, so runs are reproducible.

    Sorting matters more than it looks: an unsorted ``glob`` makes test ids and error
    output depend on filesystem order, which differs between Windows and Linux CI.
    """
    root = Path(content_dir) / track / "islands"
    if not root.is_dir():
        return
    yield from sorted(root.glob("*/missions/*.yaml"))


def discover_missions(content_dir: str | Path, track: str) -> list[Mission]:
    """Load every mission of a track, ordered by island then by ``order``.

    Raises the first validation failure it hits. Callers that want to survey all broken
    content should iterate ``iter_mission_paths`` and call ``load_mission`` themselves.
    """
    missions = [load_mission(path) for path in iter_mission_paths(content_dir, track)]
    return sorted(missions, key=lambda m: (m.island, m.order))
