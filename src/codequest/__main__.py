"""Entry point for ``python -m codequest`` and for the ``codequest`` console script.

Phase 0 target: print the version and exit cleanly. The TUI is wired in later, in Phase 4.
"""

import sys

from codequest import __version__


def main(argv: list[str] | None = None) -> int:
    """Run the CodeQuest command line entry point.

    Args:
        argv: Command line arguments **without** the program name. When ``None``,
            ``sys.argv[1:]`` is used. Taking this as a parameter is what makes the
            function testable without touching the real process arguments.

    Returns:
        The process exit code. ``0`` means success; any non-zero value means failure.

    Phase 0 behaviour: print ``codequest <version>`` and return ``0``.
    """
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print(f"codequest {__version__}")
        return 0

    print(f"Unknown arguments: {argv}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
