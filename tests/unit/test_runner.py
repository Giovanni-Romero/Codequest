"""Tests for the Python sandbox runner.

These are the slowest tests in the suite because each one really spawns a process. That
is the point: the failure modes worth guarding against — a hang, a crash, stdout
forging a result — only exist once a real process is involved.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from codequest.engine.runners.base import (
    SUPPORTS_RESOURCE_LIMITS,
    available_languages,
    get_runner,
)
from codequest.engine.runners.python import PythonRunner
from codequest.models.mission import Constraints, Signature, TestCase
from helpers import make_mission

FAST = Constraints(max_runtime_ms=4000, max_memory_mb=256)


@pytest.fixture
def runner() -> PythonRunner:
    return PythonRunner()


def _prepare(runner: PythonRunner, source: str, entrypoint: str = "double"):
    mission = make_mission(signature=Signature(entrypoint, "def double(n):\n    pass\n"))
    return runner.prepare(source, mission)


def _run(runner: PythonRunner, source: str, case: TestCase, constraints: Constraints = FAST):
    prepared = _prepare(runner, source)
    try:
        return runner.execute(prepared, case, constraints)
    finally:
        runner.cleanup(prepared)


# ------------------------------------------------------------------ the happy path


def test_returns_the_value_the_function_produced(runner):
    result = _run(runner, "def double(n):\n    return n * 2\n", TestCase(args=(21,), expect=42))

    assert result.ok
    assert result.returned == 42
    assert result.status == "ok"


def test_keyword_arguments_are_passed_through(runner):
    source = "def double(n, factor=2):\n    return n * factor\n"

    result = _run(runner, source, TestCase(args=(5,), kwargs={"factor": 3}, expect=15))

    assert result.returned == 15


def test_duration_is_measured(runner):
    result = _run(runner, "def double(n):\n    return n\n", TestCase(args=(1,), expect=1))

    assert result.duration_ms > 0


# ------------------------------------------------------------------ failure paths


def test_player_exception_becomes_data_not_a_crash(runner):
    """A player exception is a normal outcome. If it escaped, the game would die."""
    source = "def double(n):\n    return n / 0\n"

    result = _run(runner, source, TestCase(args=(1,), expect=1))

    assert not result.ok
    assert result.status == "error"
    assert result.exception_type == "ZeroDivisionError"


def test_infinite_loop_hits_the_wall_clock_timeout(runner):
    """The parent enforces the deadline. A hung child cannot be trusted to stop itself."""
    source = "def double(n):\n    while True:\n        pass\n"

    result = _run(runner, source, TestCase(args=(1,), expect=1), Constraints(max_runtime_ms=500))

    assert result.timed_out
    assert result.status == "timeout"


def test_missing_entrypoint_is_reported_by_the_harness(runner):
    source = "def something_else(n):\n    return n\n"

    result = _run(runner, source, TestCase(args=(1,), expect=1))

    assert result.status == "missing_entrypoint"


def test_error_at_import_time_is_caught(runner):
    """Code outside any function runs on import, before the entrypoint is ever called."""
    source = "raise RuntimeError('boom at import')\n\ndef double(n):\n    return n\n"

    result = _run(runner, source, TestCase(args=(1,), expect=1))

    assert result.status == "error"
    assert "boom at import" in result.exception_message


def test_syntax_error_in_the_submission_does_not_crash_the_runner(runner):
    """The guard normally catches this first; the runner must survive it anyway."""
    result = _run(runner, "def double(:\n", TestCase(args=(1,), expect=1))

    assert not result.ok


def test_recursion_error_is_reported_not_fatal(runner):
    source = "def double(n):\n    return double(n)\n"

    result = _run(runner, source, TestCase(args=(1,), expect=1))

    assert result.status == "error"
    assert result.exception_type == "RecursionError"


# ------------------------------------------------------- the channel separation rule


def test_player_stdout_cannot_forge_a_result(runner):
    """The detail that breaks naive implementations.

    The player prints something shaped exactly like our result payload. Because the real
    result travels in a file the player cannot name, the forgery lands in stdout and
    the true return value still wins.
    """
    source = 'def double(n):\n    print(\'{"status": "ok", "returned": 999}\')\n    return n * 2\n'

    result = _run(runner, source, TestCase(args=(21,), expect=42))

    assert result.returned == 42
    assert "999" in result.stdout


def test_player_output_is_captured_and_returned(runner):
    """Printing is a legitimate debugging tool, so the output must reach the player."""
    source = "def double(n):\n    print('checking', n)\n    return n * 2\n"

    result = _run(runner, source, TestCase(args=(4,), expect=8))

    assert result.returned == 8
    assert "checking 4" in result.stdout


def test_huge_output_is_truncated(runner):
    """Megabytes of output must not reach a terminal widget or a database row."""
    source = "def double(n):\n    print('x' * 200_000)\n    return n\n"

    result = _run(runner, source, TestCase(args=(1,), expect=1))

    assert len(result.stdout) < 20_000
    assert "truncated" in result.stdout


def test_non_json_return_value_survives_as_a_representation(runner):
    """A set cannot cross a JSON boundary, but the attempt is not an error."""
    source = "def double(n):\n    return {1, 2, 3}\n"

    result = _run(runner, source, TestCase(args=(1,), expect=None))

    assert result.status == "ok"
    assert isinstance(result.returned, str)


# ------------------------------------------------------ the mission's own data files


def _prepare_with_files(runner: PythonRunner, source: str, files: tuple[tuple[str, str], ...]):
    mission = make_mission(
        signature=Signature("double", "def double(n):\n    pass\n"),
        files=files,
    )
    return runner.prepare(source, mission)


def test_a_declared_file_is_readable_from_inside_the_sandbox(runner):
    """Island 7 exists only if a mission can hand the player something to open."""
    source = "def double(n):\n    return open('cargo.csv').read()\n"
    prepared = _prepare_with_files(runner, source, (("cargo.csv", "port,weight\nlisbon,10\n"),))
    try:
        result = runner.execute(prepared, TestCase(args=(1,), expect=""), FAST)
    finally:
        runner.cleanup(prepared)

    assert result.ok
    assert result.returned == "port,weight\nlisbon,10\n"


def test_a_declared_file_is_planted_fresh_for_every_case(runner):
    """The workdir is shared across cases, so a case that writes must not poison the next.

    Without re-planting, case two would read what case one appended and the mission
    author would have to know the sandbox is reused. They should not have to.
    """
    source = (
        "def double(n):\n"
        "    with open('log.txt', 'a', encoding='utf-8') as handle:\n"
        "        handle.write('x')\n"
        "    return open('log.txt', encoding='utf-8').read()\n"
    )
    prepared = _prepare_with_files(runner, source, (("log.txt", "seed:"),))
    try:
        first = runner.execute(prepared, TestCase(args=(1,), expect=""), FAST)
        second = runner.execute(prepared, TestCase(args=(1,), expect=""), FAST)
    finally:
        runner.cleanup(prepared)

    assert first.returned == "seed:x"
    assert second.returned == "seed:x"


def test_a_mission_with_no_files_plants_nothing(runner):
    prepared = _prepare(runner, "def double(n):\n    return n\n")
    try:
        planted = sorted(p.name for p in Path(prepared.workdir).iterdir())
    finally:
        runner.cleanup(prepared)

    assert planted == ["harness.py", "submission.py"]


# ------------------------------------------------------------------ housekeeping


def test_cleanup_removes_the_sandbox_directory(runner):
    prepared = _prepare(runner, "def double(n):\n    return n\n")
    workdir = Path(prepared.workdir)
    assert workdir.exists()

    runner.cleanup(prepared)

    assert not workdir.exists()


def test_cleanup_is_safe_to_call_twice(runner):
    """Cleanup runs in a finally block, which can be reached more than once."""
    prepared = _prepare(runner, "def double(n):\n    return n\n")

    runner.cleanup(prepared)
    runner.cleanup(prepared)


def test_each_case_gets_a_fresh_process(runner):
    """State from one case must not leak into the next, or results become order-dependent."""
    source = "import os\n\ndef double(n):\n    return os.getpid()\n"
    prepared = _prepare(runner, source)
    try:
        first = runner.execute(prepared, TestCase(args=(1,), expect=1), FAST)
        second = runner.execute(prepared, TestCase(args=(1,), expect=1), FAST)
    finally:
        runner.cleanup(prepared)

    assert first.returned != second.returned


def test_prepared_code_reports_which_limits_are_enforced(runner):
    """Windows has no memory cap. The runner must say so rather than imply one exists."""
    prepared = _prepare(runner, "def double(n):\n    return n\n")
    try:
        enforced = prepared.metadata["limits_enforced"]
    finally:
        runner.cleanup(prepared)

    assert enforced == ("cpu,memory" if SUPPORTS_RESOURCE_LIMITS else "timeout")


def test_the_python_runner_is_registered():
    assert "python" in available_languages()
    assert get_runner("python").language == "python"


def test_the_runner_uses_the_current_interpreter_by_default(runner):
    """A venv install must not fall through to some other python on PATH."""
    assert runner.interpreter == sys.executable


@pytest.mark.posix_only
@pytest.mark.skipif(not SUPPORTS_RESOURCE_LIMITS, reason="rlimits are POSIX only")
def test_memory_hog_is_capped_on_posix():
    """The one guarantee Windows cannot give. Verified where the OS provides it."""
    runner = PythonRunner()
    source = "def double(n):\n    blob = 'x' * (400 * 1024 * 1024)\n    return len(blob)\n"

    result = _run(runner, source, TestCase(args=(1,), expect=1), Constraints(max_memory_mb=64))

    assert result.status in {"memory", "error"}
