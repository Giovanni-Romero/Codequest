"""Static AST checks run before execution: forbidden imports and builtins.

An AST is the code as a tree, before it runs. Walking that tree sees structure a regex
cannot: ``sum`` inside a string, inside a comment, or as part of ``summary`` are all
different nodes, and only one of them is a call to the builtin.

## What this is honestly for

Read this before trusting the guard with anything:

    The guard exists to keep the *lesson* intact, not to stop an attacker.

A blocklist is defeatable and this one is no exception. ``getattr(__builtins__, "s" +
"um")`` builds the name at runtime, so no static pass can see it. ``eval`` and
``exec`` open the same hole. Someone determined to cheat a single-player game they
installed themselves will win, and that is fine — there is no privilege boundary here
between the player and themselves.

The real security control is the sandbox in ``runners/python.py``: process isolation,
a wall-clock timeout and resource limits. This module is a teaching aid.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field

from codequest.models.mission import Constraints
from codequest.models.verdict import FailureReason


@dataclass(frozen=True, slots=True)
class GuardReport:
    """The outcome of the static pass over a submission.

    Never an exception. A submission that does not parse is an ordinary player mistake
    and must arrive at the evaluator as data, exactly like a wrong answer does.
    """

    ok: bool
    reason: FailureReason = FailureReason.PASSED
    violations: tuple[str, ...] = ()
    detail: str = ""
    defined_functions: frozenset[str] = field(default_factory=frozenset)


class _BindingCollector(ast.NodeVisitor):
    """Collects every name the submission binds anywhere: assignments, params, defs.

    Needed because ``sum = 0`` followed by ``return sum`` is a *local variable*, not a
    call to the builtin. Without this pass the guard rejects a perfectly correct
    accumulator solution that happened to pick an unlucky variable name.

    The pass is deliberately scope-blind: a name bound in one function exempts it
    everywhere. That is a false negative — shadow the name in one place, use the
    builtin in another, and the guard misses it. The trade is chosen on purpose. A
    false positive blocks a correct answer and teaches the player that the game is
    broken; a false negative lets someone cheat a single-player game they installed
    themselves. Only one of those costs anything.
    """

    # [AI-ENG:blocklist-vs-allowlist] This class is a blocklist widening itself, and
    # every widening costs coverage. That is the structural weakness of enumerating what
    # is forbidden: the attacker picks from an infinite set, you enumerate a finite one.
    # An allowlist inverts the asymmetry — say what is permitted and everything unnamed
    # is refused by default.
    #
    # The lesson transfers straight to prompt injection. Filtering for known bad phrases
    # loses to a rephrasing; constraining the model to a fixed set of permitted actions
    # with validated arguments does not, because the unnamed action was never reachable.
    # When a blocklist is the only option, as here, say what it does not cover.

    def __init__(self) -> None:
        self.bound: set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store | ast.Del):
            self.bound.add(node.id)
        self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> None:
        self.bound.add(node.arg)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.bound.add(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.bound.add(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.bound.add(node.name)
        self.generic_visit(node)


class _SubmissionVisitor(ast.NodeVisitor):
    """Walks a parsed submission collecting forbidden constructs and defined names.

    # [AI-ENG:static-analysis] Inspecting code as a tree *before* executing it is the
    # same move as validating a model's proposed tool call before dispatching it: you
    # decide on structure you can see, not on a string you hope is safe. The reason it
    # beats pattern matching is identical in both cases — structure survives
    # reformatting, whitespace and clever spelling; a regex does not.
    """

    def __init__(self, constraints: Constraints, bound_names: set[str]) -> None:
        self.constraints = constraints
        self.bound_names = bound_names
        self.violations: list[str] = []
        self.defined_functions: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = alias.name.split(".")[0]
            if root in self.constraints.forbidden_imports:
                self.violations.append(f"import of '{alias.name}' is not allowed here")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            root = node.module.split(".")[0]
            if root in self.constraints.forbidden_imports:
                self.violations.append(f"import from '{node.module}' is not allowed here")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        # A *load* of a forbidden name is only a use of the builtin when the player has
        # not bound that name themselves. ``sum = 0`` makes every later ``sum`` their
        # own variable, and rejecting it would fail a correct accumulator solution.
        if (
            isinstance(node.ctx, ast.Load)
            and node.id in self.constraints.forbidden_builtins
            and node.id not in self.bound_names
        ):
            self.violations.append(f"use of '{node.id}' is not allowed in this mission")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # Catches builtins.sum and __builtins__.sum, the two obvious ways around a
        # bare-name check. Not the string-built form; see the module docstring.
        if node.attr in self.constraints.forbidden_builtins:
            self.violations.append(f"use of '{node.attr}' is not allowed in this mission")
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.defined_functions.add(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.defined_functions.add(node.name)
        self.generic_visit(node)


def check(source: str, constraints: Constraints, entrypoint: str | None = None) -> GuardReport:
    """Statically inspect a submission before it is allowed to run.

    Args:
        source: The player's code, exactly as typed.
        constraints: Forbidden builtins and imports for this mission.
        entrypoint: Function the engine will call. When given, its absence is reported
            here rather than surfacing later as a confusing NameError inside the harness.

    Returns:
        A GuardReport. This function never raises for player input — a syntax error is
        a normal outcome and comes back as ``FailureReason.SYNTAX_ERROR``.
    """
    if not source.strip():
        return GuardReport(
            ok=False,
            reason=FailureReason.SYNTAX_ERROR,
            violations=("the editor is empty",),
            detail="Write your solution before running it.",
        )

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        line = exc.lineno or 0
        return GuardReport(
            ok=False,
            reason=FailureReason.SYNTAX_ERROR,
            violations=(f"line {line}: {exc.msg}",),
            detail=f"Python cannot read your code yet. Line {line}: {exc.msg}.",
        )

    bindings = _BindingCollector()
    bindings.visit(tree)

    visitor = _SubmissionVisitor(constraints, bindings.bound)
    visitor.visit(tree)

    if visitor.violations:
        return GuardReport(
            ok=False,
            reason=FailureReason.FORBIDDEN_CONSTRUCT,
            violations=tuple(visitor.violations),
            detail=visitor.violations[0],
            defined_functions=frozenset(visitor.defined_functions),
        )

    if entrypoint and entrypoint not in visitor.defined_functions:
        return GuardReport(
            ok=False,
            reason=FailureReason.MISSING_ENTRYPOINT,
            violations=(f"no function named '{entrypoint}' was defined",),
            detail=(
                f"This mission runs a function called '{entrypoint}'. "
                f"Your code does not define one with that exact name."
            ),
            defined_functions=frozenset(visitor.defined_functions),
        )

    return GuardReport(ok=True, defined_functions=frozenset(visitor.defined_functions))
