"""The Runner protocol and the shared subprocess machinery.

This is the single extension point for new languages. The evaluator, the services and
the TUI never learn which runner is active — they hold a ``Runner`` and call it.

The test of the abstraction, stated in ``docs/architecture.md``: adding ``JavaRunner``
in v1.1 must touch exactly one new file plus one registry entry. If it forces a change
in ``evaluator.py``, ``services/`` or ``tui/``, the protocol below is wrong.
"""

from __future__ import annotations

import platform
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from codequest.engine.exceptions import UnknownRunnerError
from codequest.models.mission import Constraints, Mission, TestCase
from codequest.models.verdict import FailureReason

#: True where ``resource.setrlimit`` exists. Windows has no equivalent, so memory caps
#: are silently unavailable there and the runner must say so rather than pretend.
SUPPORTS_RESOURCE_LIMITS = platform.system() != "Windows"


@dataclass(frozen=True, slots=True)
class PreparedCode:
    """Everything one submission needs on disk before any test case runs.

    ``error`` is the field that saves v1.1. Java compiles before it runs, and a compile
    failure happens *before* there is any test result to report. Letting ``prepare()``
    fail as data — rather than raising, or being assumed infallible — means the Java
    runner drops into this protocol without reshaping it. Python never sets it today;
    the field exists because the protocol is designed for the language after this one.
    """

    workdir: str
    entry_file: str
    entrypoint: str
    #: Data files the mission declared, carried here as ``(name, content)`` pairs so
    #: ``execute()`` can put them back before every case without needing the Mission
    #: again. Keeping them on the prepared code rather than widening ``execute``'s
    #: signature is what leaves the Runner protocol untouched for the next language.
    files: tuple[tuple[str, str], ...] = ()
    error: str | None = None
    reason: FailureReason = FailureReason.PASSED
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """Whether preparation succeeded and execution may proceed."""
        return self.error is None


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """The raw outcome of running one test case. Not yet a judgement.

    Deliberately dumb: it records what happened, not whether it was right. Deciding
    right from wrong is the evaluator's job, and keeping that split means a new runner
    cannot accidentally invent its own grading rules.
    """

    returned: Any = None
    status: str = "ok"
    exception_type: str = ""
    exception_message: str = ""
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration_ms: float = 0.0
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        """Whether the harness reported a clean call with a return value."""
        return self.status == "ok" and not self.timed_out


@runtime_checkable
class Runner(Protocol):
    """What every language backend must provide.

    # [AI-ENG:protocol-abstraction] A structural protocol lets the caller depend on a
    # shape rather than on a class. It is the same lever that keeps an LLM application
    # from being welded to one vendor: define what a completion provider must do, and
    # swapping Anthropic for a local Ollama becomes one new file, not a refactor.
    # Note that Runner is a Protocol, not a base class — implementations never import
    # it, so there is no inheritance chain to fight.
    """

    language: str
    file_extension: str

    def prepare(self, submission: str, mission: Mission) -> PreparedCode:
        """Write the submission to a scratch directory. Compile if the language needs it."""
        ...

    def execute(
        self, prepared: PreparedCode, case: TestCase, constraints: Constraints
    ) -> ExecutionResult:
        """Run one test case in an isolated subprocess. Must never raise on player error."""
        ...

    def cleanup(self, prepared: PreparedCode) -> None:
        """Remove the scratch directory. Must be safe to call twice."""
        ...


_REGISTRY: dict[str, Runner] = {}


def register_runner(runner: Runner) -> None:
    """Register a runner under its language name. Later registrations win."""
    _REGISTRY[runner.language] = runner


def get_runner(language: str) -> Runner:
    """Return the runner for ``language``.

    Raises:
        UnknownRunnerError: no runner is registered. This is a configuration bug — a
            track declared a runner that was never built — not a player mistake.
    """
    try:
        return _REGISTRY[language]
    except KeyError:
        known = ", ".join(sorted(_REGISTRY)) or "none"
        raise UnknownRunnerError(f"no runner registered for '{language}'. Known: {known}") from None


def available_languages() -> tuple[str, ...]:
    """Languages the engine can execute right now."""
    return tuple(sorted(_REGISTRY))
