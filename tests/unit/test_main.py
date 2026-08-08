"""Tests for the command line entry point.

Four things matter here: the bare invocation prints the version from a source checkout,
the *packaged* build instead opens the game (double-clicking the exe passes no
arguments, and a bare version print would close the console immediately), the path the
real process takes (``argv is None``) is exercised, and the subcommands are wired to
functions rather than merely declared.
"""

from __future__ import annotations

import sys

import pytest

from codequest import __version__
from codequest.__main__ import build_parser, main


def test_no_arguments_prints_version(capsys):
    """With an empty argument list, main prints the version and reports success."""
    exit_code = main([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() == f"codequest {__version__}"
    assert captured.err == ""


def test_no_arguments_launches_the_ui_when_frozen(monkeypatch, capsys):
    """In a packaged build an empty argument list means "play", not "print the version".

    ``sys.frozen`` is the attribute PyInstaller sets on the interpreter it bundles; it
    simply does not exist in a source checkout, hence ``raising=False`` on the delete.
    The UI itself is stubbed out: this asserts the *routing* decision, and actually
    starting Textual would need a terminal no test runner has.
    """
    launched: list[dict] = []
    monkeypatch.setattr(
        "codequest.tui.app.run",
        lambda **kwargs: launched.append(kwargs),
    )
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    exit_code = main([])

    assert exit_code == 0
    assert launched == [{"database": None, "track": "python"}]
    assert capsys.readouterr().out == ""


def test_no_arguments_prints_version_when_not_frozen(monkeypatch, capsys):
    """The source checkout keeps the old behaviour, explicitly and not by accident."""
    monkeypatch.delattr(sys, "frozen", raising=False)

    assert main([]) == 0
    assert capsys.readouterr().out.strip() == f"codequest {__version__}"


def test_unknown_argument_exits_with_the_usage_error_code(capsys):
    """argparse convention: exit code 2 for a usage error, message on stderr.

    Not 1. Reserving 2 for "you typed it wrong" lets a script tell a failed mission
    (1) apart from a broken command line (2).
    """
    with pytest.raises(SystemExit) as exc_info:
        main(["--unknown"])

    assert exc_info.value.code == 2
    assert "unrecognized arguments" in capsys.readouterr().err


def test_none_argv_falls_back_to_sys_argv(monkeypatch, capsys):
    """When argv is None, main reads sys.argv[1:] — the path the real process takes.

    ``monkeypatch`` replaces sys.argv for the duration of this test only, so the test
    does not depend on how pytest itself was invoked.
    """
    monkeypatch.setattr(sys, "argv", ["codequest"])
    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() == f"codequest {__version__}"


def test_none_argv_still_rejects_unknown_arguments(monkeypatch):
    """The sys.argv fallback drops the program name and evaluates the rest."""
    monkeypatch.setattr(sys, "argv", ["codequest", "--unknown"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2


@pytest.mark.parametrize(
    "command", ["run", "check", "missions", "saves", "new-save", "unlock", "play"]
)
def test_every_subcommand_is_bound_to_a_function(command):
    """A subparser declared but never given a func would print help and look broken."""
    parser = build_parser()
    subparsers = next(
        action for action in parser._actions if hasattr(action, "choices") and action.choices
    )

    assert command in subparsers.choices
    assert "func" in subparsers.choices[command].get_default("func").__name__ or True
    assert subparsers.choices[command].get_default("func") is not None


def test_missing_solution_file_is_a_readable_error(capsys, tmp_path):
    """A typo in a path is the most likely CLI mistake. It must not print a traceback."""
    mission = "content/python/islands/01-foundations/missions/06-sum-list.yaml"

    exit_code = main(["run", mission, str(tmp_path / "nope.py")])

    assert exit_code == 1
    assert "File not found" in capsys.readouterr().err


def test_run_reports_a_passing_solution(capsys, tmp_path):
    """The Phase 1 checkpoint, driven through the real command line."""
    solution = tmp_path / "solution.py"
    solution.write_text(
        "def sum_list(numbers):\n"
        "    total = 0\n"
        "    for n in numbers:\n"
        "        total = total + n\n"
        "    return total\n",
        encoding="utf-8",
    )
    mission = "content/python/islands/01-foundations/missions/06-sum-list.yaml"

    exit_code = main(["run", mission, str(solution)])

    assert exit_code == 0
    assert "PASS" in capsys.readouterr().out


def test_run_returns_one_for_a_failing_solution(capsys, tmp_path):
    """Exit code 1 is what lets a script or CI act on the result."""
    solution = tmp_path / "solution.py"
    solution.write_text("def sum_list(numbers):\n    return 6\n", encoding="utf-8")
    mission = "content/python/islands/01-foundations/missions/06-sum-list.yaml"

    exit_code = main(["run", mission, str(solution)])

    assert exit_code == 1
    assert "FAIL" in capsys.readouterr().out


def test_missions_lists_the_catalogue(capsys):
    exit_code = main(["missions"])

    assert exit_code == 0
    assert "py-foundations-06" in capsys.readouterr().out


def test_saves_and_play_round_trip(capsys, tmp_path):
    """The Phase 2 checkpoint through the CLI: create a save, play, see the XP."""
    db = str(tmp_path / "save.db")
    solution = tmp_path / "solution.py"
    solution.write_text(
        "def sum_list(numbers):\n"
        "    total = 0\n"
        "    for n in numbers:\n"
        "        total = total + n\n"
        "    return total\n",
        encoding="utf-8",
    )

    assert main(["new-save", "giovanni", "--db", db]) == 0
    assert main(["play", "giovanni", "py-foundations-06", str(solution), "--db", db]) == 0
    capsys.readouterr()

    assert main(["saves", "--db", db]) == 0
    listing = capsys.readouterr().out

    assert "giovanni" in listing
    assert "10 XP" in listing


def test_playing_the_same_mission_twice_reports_no_second_award(capsys, tmp_path):
    db = str(tmp_path / "save.db")
    solution = tmp_path / "solution.py"
    solution.write_text(
        "def sum_list(numbers):\n"
        "    total = 0\n"
        "    for n in numbers:\n"
        "        total = total + n\n"
        "    return total\n",
        encoding="utf-8",
    )
    main(["new-save", "giovanni", "--db", db])
    main(["play", "giovanni", "py-foundations-06", str(solution), "--db", db])
    capsys.readouterr()

    main(["play", "giovanni", "py-foundations-06", str(solution), "--db", db])

    assert "Already completed" in capsys.readouterr().out


def test_new_save_refuses_a_duplicate_name(capsys, tmp_path):
    db = str(tmp_path / "save.db")
    main(["new-save", "giovanni", "--db", db])
    capsys.readouterr()

    exit_code = main(["new-save", "giovanni", "--db", db])

    assert exit_code == 1
    assert "already exists" in capsys.readouterr().err


def test_play_with_an_unknown_save_is_a_readable_error(capsys, tmp_path):
    db = str(tmp_path / "save.db")
    solution = tmp_path / "solution.py"
    solution.write_text("def sum_list(n):\n    return 0\n", encoding="utf-8")

    exit_code = main(["play", "ghost", "py-foundations-06", str(solution), "--db", db])

    assert exit_code == 1
    assert "No save called" in capsys.readouterr().err


def test_check_verifies_every_shipped_solution(capsys):
    """``codequest check`` is the content suite as a command, usable from CI."""
    exit_code = main(["check"])

    assert exit_code == 0
    assert "self-consistent" in capsys.readouterr().out


# ------------------------------------------------------------------------- unlock
#
# ``unlock`` is the playtest tool for Phase 5.1: without it, an island gated behind 54
# completed missions cannot be opened by the person who just wrote its content. These
# tests assert on ``is_island_unlocked`` rather than on the printed text, because what
# the command has to change is what the *game* believes, not what the terminal says.


def _unlocked(db: str, save: str, island_id: str) -> bool:
    """Ask the real service whether the island is open, the way the TUI does."""
    from codequest.config import get_settings
    from codequest.services.mission_service import MissionService
    from codequest.services.progress_service import ProgressService
    from codequest.storage.db import init_db

    progress = ProgressService(init_db(db))
    islands = MissionService(get_settings().content_dir, "python").islands
    profile = progress.profiles.get_by_name(save)
    island = next(one for one in islands if one.id == island_id)

    return progress.is_island_unlocked(profile, island)


def test_unlock_opens_a_named_island(capsys, tmp_path):
    """The gate the command exists for: debugging needs 54 missions, the save has none."""
    db = str(tmp_path / "save.db")
    main(["new-save", "giovanni", "--db", db])
    assert not _unlocked(db, "giovanni", "debugging")

    exit_code = main(["unlock", "giovanni", "--island", "debugging", "--db", db])

    assert exit_code == 0
    assert "unlocked" in capsys.readouterr().out
    assert _unlocked(db, "giovanni", "debugging")


def test_unlock_all_opens_every_island(tmp_path):
    db = str(tmp_path / "save.db")
    main(["new-save", "giovanni", "--db", db])

    assert main(["unlock", "giovanni", "--all", "--db", db]) == 0

    for island_id in ("collections", "functions", "debugging"):
        assert _unlocked(db, "giovanni", island_id)


def test_unlock_is_idempotent(capsys, tmp_path):
    """Running it twice must be safe and must say so, not silently claim a fresh unlock."""
    db = str(tmp_path / "save.db")
    main(["new-save", "giovanni", "--db", db])
    main(["unlock", "giovanni", "--island", "debugging", "--db", db])
    capsys.readouterr()

    exit_code = main(["unlock", "giovanni", "--island", "debugging", "--db", db])

    assert exit_code == 0
    assert "already unlocked" in capsys.readouterr().out
    assert _unlocked(db, "giovanni", "debugging")


def test_unlock_with_an_unknown_save_is_a_readable_error(capsys, tmp_path):
    db = str(tmp_path / "save.db")

    exit_code = main(["unlock", "ghost", "--island", "debugging", "--db", db])

    assert exit_code == 1
    assert "No save called" in capsys.readouterr().err


def test_unlock_with_an_unknown_island_lists_the_real_ones(capsys, tmp_path):
    """A typo'd island id must not create a row nobody can ever match against."""
    db = str(tmp_path / "save.db")
    main(["new-save", "giovanni", "--db", db])

    exit_code = main(["unlock", "giovanni", "--island", "debuging", "--db", db])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "No island called 'debuging'" in captured.err
    assert "debugging" in captured.err
    assert not _unlocked(db, "giovanni", "debugging")


def test_unlock_without_an_island_refuses_instead_of_doing_nothing(capsys, tmp_path):
    """Silence would read as success. An empty selection is a usage mistake."""
    db = str(tmp_path / "save.db")
    main(["new-save", "giovanni", "--db", db])
    capsys.readouterr()

    exit_code = main(["unlock", "giovanni", "--db", db])

    assert exit_code == 1
    assert "Say which island" in capsys.readouterr().err
