"""Refresh the file:line targets in the AI Engineering bookmark index.

Line numbers move every time a bookmarked file gains an import, and a stale index is
worse than no index: it sends the reader somewhere specific and wrong, with the
confidence of a citation.

``CLAUDE.md`` section 9 says to regenerate the index whenever bookmarks move. This exists
so that instruction is a command rather than something to remember:

    python scripts/refresh_bookmarks.py

Only the ``file:line`` targets are rewritten. The hand-written bridge text in each row is
left alone, because that is the part with the value in it.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "src"
CONTENT_ROOT = PROJECT_ROOT / "content"
INDEX = PROJECT_ROOT / "docs" / "curriculum" / "ai-engineering" / "bookmarks.md"

BOOKMARK = re.compile(r"\[AI-ENG:([a-z-]+)\]")
ROW = re.compile(r"\| `([a-z-]+)` \| \[[^\]]+\]\([^)]+\) \|")


def _bookmarked_files() -> list[Path]:
    """Every file that may carry a bookmark, in the order the index should prefer.

    Source first, then mission YAML. A few bridges belong to a *mission* rather than to
    a line of engine code -- ``concurrency-cost`` is the argument a mission makes, not
    something ``harness.py`` does -- and those deserve the same stale-line checking as
    the rest, because an index nobody verifies is an index nobody can trust.

    Translated mission trees are skipped. The mirror carries the same comment, and
    indexing whichever one happened to sort first would make the target flip between
    languages for no reason.
    """
    paths = sorted(PACKAGE_ROOT.rglob("*.py"))
    if CONTENT_ROOT.is_dir():
        paths += sorted(path for path in CONTENT_ROOT.rglob("*.yaml") if "pt-BR" not in path.parts)
    return paths


def bookmarks_in_source() -> dict[str, tuple[str, int]]:
    """Map each slug to the file and line where it first appears."""
    found: dict[str, tuple[str, int]] = {}
    for path in _bookmarked_files():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = BOOKMARK.search(line)
            if match and match.group(1) not in found:
                found[match.group(1)] = (path.relative_to(PROJECT_ROOT).as_posix(), number)
    return found


def main() -> int:
    current = bookmarks_in_source()
    text = INDEX.read_text(encoding="utf-8")

    def replace(match: re.Match[str]) -> str:
        slug = match.group(1)
        if slug not in current:
            return match.group(0)
        path, line = current[slug]
        return f"| `{slug}` | [{path}:{line}]({path}#L{line}) |"

    new_text, rows = ROW.subn(replace, text)

    indexed = set(ROW.findall(text))
    missing = sorted(set(current) - indexed)
    orphaned = sorted(indexed - set(current))

    if new_text != text:
        INDEX.write_text(new_text, encoding="utf-8")
        print(f"refreshed {rows} rows in {INDEX.relative_to(PROJECT_ROOT)}")
    else:
        print("index already up to date")

    # These two need a human: a new bookmark needs its bridge written, and a removed one
    # needs someone to decide whether the concept left the codebase on purpose.
    if missing:
        print(f"\nbookmarks in the code with no row in the index: {missing}", file=sys.stderr)
        print("add a row for each, with the bridge to AI Engineering.", file=sys.stderr)
    if orphaned:
        print(f"\nrows in the index with no bookmark in the code: {orphaned}", file=sys.stderr)

    return 1 if (missing or orphaned) else 0


if __name__ == "__main__":
    sys.exit(main())
