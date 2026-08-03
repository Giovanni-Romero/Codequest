"""Tests for the AST guard.

The guard's contract has two halves. It must reject what the mission forbids, and it
must **never raise** on player input — a submission that does not even parse is an
everyday event, not an exception.
"""

from __future__ import annotations

from codequest.engine.guard import check
from codequest.models.mission import Constraints
from codequest.models.verdict import FailureReason

NO_LIMITS = Constraints()
NO_SUM = Constraints(forbidden_builtins=frozenset({"sum"}))
NO_MATH = Constraints(forbidden_imports=frozenset({"math", "numpy"}))


def test_clean_code_passes():
    report = check("def total(xs):\n    return 0\n", NO_LIMITS)

    assert report.ok
    assert report.reason is FailureReason.PASSED


def test_forbidden_builtin_is_rejected():
    report = check("def total(xs):\n    return sum(xs)\n", NO_SUM)

    assert not report.ok
    assert report.reason is FailureReason.FORBIDDEN_CONSTRUCT
    assert "sum" in report.violations[0]


def test_forbidden_builtin_reached_through_an_attribute_is_rejected():
    """``builtins.sum`` is the first thing anyone tries after a bare-name check."""
    report = check("import builtins\n\ndef t(xs):\n    return builtins.sum(xs)\n", NO_SUM)

    assert not report.ok
    assert report.reason is FailureReason.FORBIDDEN_CONSTRUCT


def test_shadowing_a_forbidden_name_is_allowed():
    """``sum = 0`` is a store, not a call. Forbidding it would ban a normal variable."""
    report = check("def total(xs):\n    sum = 0\n    return sum\n", NO_SUM)

    assert report.ok


def test_binding_the_name_anywhere_exempts_it_everywhere():
    """The documented false negative of the scope-blind binding pass.

    Binding ``sum`` in one function exempts the load in another. Closing this would need
    real scope analysis, and the cost of getting it slightly wrong is rejecting a
    correct solution — a far worse outcome than letting someone cheat their own game.
    """
    source = "def helper():\n    sum = 0\n    return sum\n\ndef total(xs):\n    return sum(xs)\n"

    report = check(source, NO_SUM)

    assert report.ok


def test_a_word_containing_the_forbidden_name_is_not_a_match():
    """A regex would flag 'summary'. The AST sees a different identifier entirely."""
    report = check("def total(xs):\n    summary = 0\n    return summary\n", NO_SUM)

    assert report.ok


def test_the_forbidden_name_inside_a_string_is_not_a_match():
    report = check("def total(xs):\n    return 'use sum() later'\n", NO_SUM)

    assert report.ok


def test_forbidden_import_is_rejected():
    report = check("import math\n\ndef t():\n    return 1\n", NO_MATH)

    assert not report.ok
    assert "math" in report.violations[0]


def test_forbidden_import_from_is_rejected():
    report = check("from math import sqrt\n\ndef t():\n    return 1\n", NO_MATH)

    assert not report.ok
    assert report.reason is FailureReason.FORBIDDEN_CONSTRUCT


def test_forbidden_submodule_import_is_rejected():
    """``import numpy.linalg`` must not slip past a check on the root package."""
    report = check("import numpy.linalg\n\ndef t():\n    return 1\n", NO_MATH)

    assert not report.ok


def test_allowed_import_passes():
    report = check("import json\n\ndef t():\n    return 1\n", NO_MATH)

    assert report.ok


def test_syntax_error_is_a_report_not_an_exception():
    """The whole point: broken code is data, never a crash inside the game."""
    report = check("def broken(:\n", NO_LIMITS)

    assert not report.ok
    assert report.reason is FailureReason.SYNTAX_ERROR
    assert "line 1" in report.violations[0]


def test_empty_submission_is_reported_kindly():
    report = check("   \n  \n", NO_LIMITS)

    assert not report.ok
    assert report.reason is FailureReason.SYNTAX_ERROR


def test_missing_entrypoint_is_caught_before_execution():
    """Catching it here beats a NameError from inside the harness, which reads as noise."""
    report = check("def other(n):\n    return n\n", NO_LIMITS, entrypoint="double")

    assert not report.ok
    assert report.reason is FailureReason.MISSING_ENTRYPOINT
    assert "double" in report.detail


def test_entrypoint_present_passes():
    report = check("def double(n):\n    return n * 2\n", NO_LIMITS, entrypoint="double")

    assert report.ok
    assert "double" in report.defined_functions


def test_async_entrypoint_counts_as_defined():
    report = check("async def double(n):\n    return n\n", NO_LIMITS, entrypoint="double")

    assert report.ok


def test_nested_function_is_seen():
    source = "def outer():\n    def double(n):\n        return n\n    return double\n"

    report = check(source, NO_LIMITS, entrypoint="double")

    assert report.ok


def test_violations_are_reported_together():
    constraints = Constraints(
        forbidden_builtins=frozenset({"sum", "max"}), forbidden_imports=frozenset({"math"})
    )
    source = "import math\n\ndef t(xs):\n    return sum(xs) + max(xs)\n"

    report = check(source, constraints)

    assert len(report.violations) == 3


def test_the_guard_is_documented_as_defeatable():
    """A blocklist loses to a name built at runtime. This proves the limit is real.

    Not a bug report: it is the documented boundary. The guard keeps the lesson intact,
    the sandbox in runners/python.py is what actually contains the process.
    """
    source = "def total(xs):\n    f = getattr(__builtins__, 's' + 'um')\n    return f(xs)\n"

    report = check(source, NO_SUM)

    assert report.ok
