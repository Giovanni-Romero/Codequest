"""Language runners. Each one implements the Runner protocol in ``base``.

Importing this package registers every built-in runner, so ``get_runner("python")``
works without the caller knowing which module defines it. When ``java.py`` arrives in
v1.1 it adds exactly one line here — the registry entry promised in
``docs/architecture.md``.
"""

from codequest.engine.runners import python as _python  # noqa: F401 - import registers it
from codequest.engine.runners.base import (
    ExecutionResult,
    PreparedCode,
    Runner,
    available_languages,
    get_runner,
    register_runner,
)

__all__ = [
    "ExecutionResult",
    "PreparedCode",
    "Runner",
    "available_languages",
    "get_runner",
    "register_runner",
]
