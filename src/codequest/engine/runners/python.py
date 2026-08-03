"""Python runner: temp dir, subprocess, resource limits, wall-clock timeout.

## Why a subprocess and not ``exec``

``exec`` runs the player's code inside the game's own interpreter. It shares our memory,
our globals and our lifetime. An infinite loop there freezes the game with no way back,
and there is no ``exec`` equivalent of "kill it". A separate OS process can be killed,
limited, and cannot corrupt the parent — the isolation is provided by the kernel rather
than by our good intentions.

## Platform reality

``resource.setrlimit`` and the ``preexec_fn`` hook are POSIX-only. On Windows this
runner degrades to **timeout-only**: no memory ceiling. That limitation is real, it is
reported through ``limits_enforced`` on every result, and it is never silently swallowed.

On POSIX the limits are applied by the *child itself* (see ``engine/harness.py``)
instead of through ``preexec_fn``, which is unsafe in a process that has threads — and
the Phase 4 Textual UI runs its work in a worker thread.
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from codequest.engine import harness as harness_module
from codequest.engine.exceptions import RunnerError
from codequest.engine.runners.base import (
    SUPPORTS_RESOURCE_LIMITS,
    ExecutionResult,
    PreparedCode,
    register_runner,
)
from codequest.models.mission import Constraints, Mission, TestCase

#: Grace added to the wall-clock timeout before the parent gives up, covering interpreter
#: start-up. Without it a mission with a 100 ms budget would time out on process launch
#: alone and blame the player for the runtime's cost.
_STARTUP_GRACE_SECONDS = 2.0

#: Captured output is truncated before it reaches a Verdict. A player printing inside a
#: loop can produce megabytes, and nothing good happens when that lands in a terminal
#: widget or a database row.
_MAX_CAPTURED_CHARS = 8_000


def _truncate(text: str) -> str:
    if len(text) <= _MAX_CAPTURED_CHARS:
        return text
    return text[:_MAX_CAPTURED_CHARS] + f"\n... [truncated, {len(text)} chars total]"


def _kill_process_tree(process: subprocess.Popen) -> None:
    """Kill the child *and everything it spawned*.

    # [AI-ENG:sandboxing] Killing only the direct child is the classic mistake. A
    # player whose code calls ``subprocess`` or ``multiprocessing`` leaves orphans that
    # keep burning CPU after the timeout "worked". The same failure shows up in agent
    # infrastructure: cancelling a task that already fanned out leaves the fan-out
    # running. Terminate the group, not the process you happen to hold a handle to.
    """
    if process.poll() is not None:
        return

    if os.name == "nt":
        # Windows has no process groups in the POSIX sense; taskkill /T walks the tree.
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(process.pid)],
            capture_output=True,
            check=False,
        )
    else:
        import signal

        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)

    with contextlib.suppress(ProcessLookupError, OSError):
        process.kill()


def _spawn_kwargs() -> dict[str, object]:
    """Platform flags that put the child in its own killable group."""
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    # Python 3.11+: thread-safe replacement for ``preexec_fn=os.setsid``.
    return {"process_group": 0}


class PythonRunner:
    """Runs Python submissions, one subprocess per test case.

    One process per case rather than one per submission: state cannot leak from an
    earlier case into a later one, and a case that hangs takes only itself down. The
    cost is interpreter start-up per case, which is milliseconds and buys determinism.
    """

    language = "python"
    file_extension = ".py"

    def __init__(self, interpreter: str | None = None) -> None:
        #: Defaults to the interpreter running the game, so a venv install stays inside
        #: that venv instead of finding some other python on PATH.
        self.interpreter = interpreter or sys.executable

    # ------------------------------------------------------------------ preparation

    def prepare(self, submission: str, mission: Mission) -> PreparedCode:
        """Write the submission and a copy of the harness into a fresh temp directory."""
        try:
            workdir = tempfile.mkdtemp(prefix="codequest-")
        except OSError as exc:
            raise RunnerError(f"cannot create a sandbox directory: {exc}") from exc

        try:
            entry_file = Path(workdir) / "submission.py"
            entry_file.write_text(submission, encoding="utf-8")
            shutil.copyfile(harness_module.__file__, Path(workdir) / "harness.py")
        except OSError as exc:
            shutil.rmtree(workdir, ignore_errors=True)
            raise RunnerError(f"cannot write the sandbox files: {exc}") from exc

        return PreparedCode(
            workdir=workdir,
            entry_file=str(entry_file),
            entrypoint=mission.signature.entrypoint,
            metadata={"limits_enforced": "cpu,memory" if SUPPORTS_RESOURCE_LIMITS else "timeout"},
        )

    # ------------------------------------------------------------------- execution

    def execute(
        self, prepared: PreparedCode, case: TestCase, constraints: Constraints
    ) -> ExecutionResult:
        """Run one test case. Never raises because of anything the player wrote."""
        workdir = Path(prepared.workdir)
        request_path = workdir / "request.json"
        result_path = workdir / "result.json"
        result_path.unlink(missing_ok=True)

        timeout_seconds = constraints.max_runtime_ms / 1000
        request = {
            "entrypoint": prepared.entrypoint,
            "args": list(case.args),
            "kwargs": dict(case.kwargs),
            "limits": {
                # One CPU second above the wall clock: a process that is merely slow to
                # start should die on the wall clock with a clear TIMEOUT, not on a CPU
                # limit that would read as something else entirely.
                "cpu_seconds": max(1, int(timeout_seconds) + 1),
                "memory_bytes": constraints.max_memory_mb * 1024 * 1024,
            },
        }
        request_path.write_text(json.dumps(request), encoding="utf-8")

        command = [
            self.interpreter,
            "-I",  # isolated: ignore PYTHON* env vars and the user site directory
            str(workdir / "harness.py"),
            prepared.entry_file,
            str(request_path),
            str(result_path),
        ]

        started = time.perf_counter()
        try:
            process = subprocess.Popen(
                command,
                cwd=workdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                **_spawn_kwargs(),
            )
        except OSError as exc:
            raise RunnerError(f"cannot start the sandbox process: {exc}") from exc

        timed_out = False
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds + _STARTUP_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            # The wall clock is measured here, in the parent. A child asked to stop
            # itself is a child trusted not to hang, which is the thing being guarded.
            timed_out = True
            _kill_process_tree(process)
            stdout, stderr = process.communicate()

        duration_ms = (time.perf_counter() - started) * 1000

        if timed_out:
            return ExecutionResult(
                status="timeout",
                stdout=_truncate(stdout or ""),
                stderr=_truncate(stderr or ""),
                exit_code=process.returncode or -1,
                duration_ms=duration_ms,
                timed_out=True,
            )

        return self._read_result(result_path, stdout, stderr, process.returncode, duration_ms)

    def _read_result(
        self,
        result_path: Path,
        stdout: str,
        stderr: str,
        exit_code: int,
        duration_ms: float,
    ) -> ExecutionResult:
        """Turn the harness's result file into an ExecutionResult.

        # [AI-ENG:channel-separation] The answer is read from a file the player cannot
        # name; their ``print`` output arrives separately on stdout. Mixing the two is
        # the bug that makes a sandbox forgeable — and it is the same bug as parsing a
        # model's JSON out of a reply that also contains prose. Give the payload its own
        # channel and the parsing problem disappears instead of being papered over.
        """
        stdout = _truncate(stdout or "")
        stderr = _truncate(stderr or "")

        if not result_path.exists():
            # No result file: the process died before writing. On POSIX a SIGKILL from
            # the memory limit shows up exactly like this.
            killed_by_signal = exit_code < 0
            memory_hint = "MemoryError" in stderr or "Cannot allocate" in stderr
            status = "memory" if (killed_by_signal or memory_hint) else "crashed"
            return ExecutionResult(
                status=status,
                exception_type="MemoryError" if status == "memory" else "",
                exception_message=stderr.strip().splitlines()[-1] if stderr.strip() else "",
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                duration_ms=duration_ms,
            )

        try:
            payload = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return ExecutionResult(
                status="harness_error",
                exception_type=type(exc).__name__,
                exception_message=str(exc),
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                duration_ms=duration_ms,
            )

        return ExecutionResult(
            returned=payload.get("returned"),
            status=payload.get("status", "harness_error"),
            exception_type=payload.get("type", ""),
            exception_message=payload.get("message", ""),
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            duration_ms=duration_ms,
        )

    # --------------------------------------------------------------------- cleanup

    def cleanup(self, prepared: PreparedCode) -> None:
        """Remove the sandbox directory. Safe to call more than once."""
        shutil.rmtree(prepared.workdir, ignore_errors=True)


register_runner(PythonRunner())
