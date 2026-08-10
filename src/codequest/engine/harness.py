"""Code injected around the player's submission at runtime.

This module is unusual: it is part of the package, but it is *executed* as a standalone
script inside the sandbox subprocess. It must therefore import nothing from
``codequest`` — the child runs with a bare interpreter in a temp directory and the
package may not even be importable from there.

Invocation::

    python harness.py <submission.py> <request.json> <result.json>

The request carries the entrypoint, the arguments, and the resource limits. The result
is written to ``result.json``.

## Why the result does not go to stdout

The player owns stdout. A mission that asks them to debug with ``print()`` is a good
mission, and the moment their output shares a channel with ours, a stray ``print`` can
forge or corrupt a result. So results go to a file whose path only the parent knows.

A file rather than an inherited file descriptor because descriptor inheritance behaves
differently on Windows, and this is the one place where a platform difference would be
invisible until it silently broke.
"""

from __future__ import annotations

import contextlib
import importlib.util
import json
import sys
import traceback
import types
from typing import Any


def _apply_resource_limits(limits: dict[str, Any]) -> None:
    """Cap CPU seconds and address space for this process, where the OS supports it.

    # [AI-ENG:resource-limits] The child limits *itself* rather than being limited by
    # the parent through ``preexec_fn``. ``preexec_fn`` runs between fork and exec and
    # is documented as unsafe in a process with threads — and the Textual UI in Phase 4
    # runs its work in a worker thread. Self-limiting is both thread-safe and portable
    # in shape: the Windows branch simply has nothing to apply.
    #
    # The generalisation for agent work: a budget the executor sets on itself before
    # doing anything is enforceable; a budget the caller merely hopes for is not.
    """
    try:
        import resource
    except ImportError:  # Windows: no rlimits. Wall-clock timeout is the only guard.
        return

    cpu_seconds = limits.get("cpu_seconds")
    if cpu_seconds:
        # Hard limit one second above the soft one so the process receives SIGXCPU and
        # can die reporting the reason, instead of being killed with no explanation.
        resource.setrlimit(resource.RLIMIT_CPU, (int(cpu_seconds), int(cpu_seconds) + 1))

    memory_bytes = limits.get("memory_bytes")
    if memory_bytes:
        # Some platforms refuse RLIMIT_AS. Losing the memory cap is survivable;
        # failing to run the mission because of it is not.
        with contextlib.suppress(ValueError, OSError):
            resource.setrlimit(resource.RLIMIT_AS, (int(memory_bytes), int(memory_bytes)))


def _load_submission(path: str) -> Any:
    """Import the player's file as a module, without putting it on sys.path."""
    spec = importlib.util.spec_from_file_location("player_submission", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load submission from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["player_submission"] = module
    spec.loader.exec_module(module)
    return module


def _jsonable(value: Any) -> tuple[Any, bool]:
    """Return ``(value, True)`` when JSON can carry it, else ``(repr, False)``.

    A player may legitimately return a set, a generator or their own class. That is not
    an error — it is simply a value the evaluator must compare by representation rather
    than by structure, and it needs to know which it got.
    """
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        return repr(value), False
    return value, True


def run(request: dict[str, Any]) -> dict[str, Any]:
    """Execute one test case and describe the outcome as plain data.

    Every failure mode is caught and returned. The harness raising would leave the
    parent with an empty result file and no idea why.
    """
    _apply_resource_limits(request.get("limits") or {})

    try:
        module = _load_submission(request["submission"])
    except MemoryError:
        return {"status": "memory", "type": "MemoryError", "message": "out of memory on import"}
    except BaseException as exc:  # import-time code is the player's; nothing may escape
        return {
            "status": "error",
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(limit=3),
            "phase": "import",
        }

    entrypoint = request["entrypoint"]
    function = getattr(module, entrypoint, None)
    if function is None:
        return {
            "status": "missing_entrypoint",
            "type": "NameError",
            "message": f"no function named '{entrypoint}' was defined",
        }
    if not callable(function):
        return {
            "status": "missing_entrypoint",
            "type": "TypeError",
            "message": f"'{entrypoint}' exists but is not a function",
        }

    args = list(request.get("args") or [])
    kwargs = dict(request.get("kwargs") or {})

    try:
        returned = function(*args, **kwargs)
        if isinstance(returned, types.CoroutineType):
            # [AI-ENG:deferred-results] What the callable handed back is not the answer:
            # it is a promise to produce one. Serializing it now would ship
            # ``<coroutine object ... at 0x7f...>`` — a fresh address every run, and a
            # value that looks like data. Resolving the promise *before* the boundary,
            # inside the same error handling that covers the ordinary call, is the same
            # discipline an agent's tool executor needs: await first, then serialize,
            # then report. The order is the whole point.
            #
            # ``asyncio.run`` owns its event loop from creation to close, so it must be
            # the outermost call. A mission whose async entrypoint ran its own would be
            # nesting loops; every async brief says the engine awaits for them.
            #
            # Imported here rather than at the top, and detected with ``types`` rather
            # than ``inspect``: this module is re-executed by a fresh interpreter for
            # every test case of every mission, and ``import asyncio`` costs about 75 ms
            # against a 5 ms baseline. Paying that on all 117 missions to serve the four
            # that are async pushed a TUI snapshot test past its deadline — a cost
            # measured after the test went red, not guessed at beforehand.
            import asyncio

            returned = asyncio.run(returned)
    except MemoryError:
        return {"status": "memory", "type": "MemoryError", "message": "out of memory"}
    except RecursionError as exc:
        return {"status": "error", "type": "RecursionError", "message": str(exc)}
    except BaseException as exc:  # any player exception is a normal outcome, not a crash
        return {
            "status": "error",
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(limit=3),
            "phase": "call",
        }

    value, exact = _jsonable(returned)
    return {"status": "ok", "returned": value, "exact": exact, "type": type(returned).__name__}


def main(argv: list[str] | None = None) -> int:
    """Read the request, run it, write the result. Always exits 0 on a written result."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 3:
        print("usage: harness.py <submission> <request.json> <result.json>", file=sys.stderr)
        return 2

    submission_path, request_path, result_path = argv

    try:
        with open(request_path, encoding="utf-8") as handle:
            request = json.load(handle)
    except (OSError, ValueError) as exc:
        print(f"harness could not read its request: {exc}", file=sys.stderr)
        return 3

    request["submission"] = submission_path
    result = run(request)

    try:
        with open(result_path, "w", encoding="utf-8") as handle:
            json.dump(result, handle)
    except (OSError, ValueError) as exc:
        print(f"harness could not write its result: {exc}", file=sys.stderr)
        return 4

    return 0


if __name__ == "__main__":
    sys.exit(main())
