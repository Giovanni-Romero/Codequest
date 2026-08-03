"""Tests for the command line entry point.

Three paths matter here: the happy path, the unknown-argument path, and the path the
real process actually takes (``argv is None``), which reads ``sys.argv`` and is the
easiest one to leave untested.
"""

import sys

from codequest import __version__
from codequest.__main__ import main


def test_no_arguments_prints_version(capsys):
    """With an empty argument list, main prints the version and reports success."""
    exit_code = main([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() == f"codequest {__version__}"
    assert captured.err == ""


def test_unknown_argument_fails(capsys):
    """An unrecognised argument goes to stderr and reports a non-zero exit code."""
    exit_code = main(["--unknown"])
    captured = capsys.readouterr()

    assert isinstance(exit_code, int)
    assert exit_code != 0
    assert "Unknown arguments" in captured.err
    assert captured.out == ""


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


def test_none_argv_still_rejects_unknown_arguments(monkeypatch, capsys):
    """The sys.argv fallback drops the program name and evaluates the rest."""
    monkeypatch.setattr(sys, "argv", ["codequest", "--unknown"])
    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "--unknown" in captured.err
