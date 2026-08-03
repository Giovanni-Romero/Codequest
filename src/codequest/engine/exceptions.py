"""Engine-level exceptions. Player errors are Verdicts, not exceptions.

The split that matters: a broken mission file is an **author** bug and should stop the
program loudly, because shipping it would show a player a broken lesson. A broken
submission is a **player** bug and is a normal outcome — it becomes a Verdict and never
raises. Every exception in this module belongs to the first category.
"""


class CodeQuestError(Exception):
    """Base class for everything this project raises deliberately.

    Having one root lets a caller write ``except CodeQuestError`` to separate our
    failures from a genuine bug in the interpreter or the standard library.
    """


class ContentError(CodeQuestError):
    """The content tree is wrong: a missing file, an unreadable directory, bad YAML."""


class MissionValidationError(ContentError):
    """A mission file parsed but does not satisfy the schema.

    Carries every problem found in the file rather than only the first. Fixing content
    one error per run is how a ten-field typo becomes a ten-round game of whack-a-mole.
    """

    def __init__(self, path: str, problems: list[str]) -> None:
        self.path = path
        self.problems = problems
        bullets = "\n".join(f"  - {problem}" for problem in problems)
        super().__init__(f"{path} is not a valid mission:\n{bullets}")


class RunnerError(CodeQuestError):
    """The execution machinery itself failed — not the player's code.

    Raised when the temp directory cannot be created, the interpreter is missing, or
    the harness could not be written. Never raised because a submission misbehaved.
    """


class HarnessError(CodeQuestError):
    """The harness ran but produced something the engine cannot read.

    Usually means the result file is missing or is not valid JSON, which points at a
    bug in the harness or at a player who managed to kill the process mid-write.
    """


class UnknownRunnerError(CodeQuestError):
    """No runner is registered for the requested language."""
