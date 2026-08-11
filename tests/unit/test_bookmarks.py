"""Keeps docs/ai-eng-bookmarks.md honest.

An index with a stale line number is worse than no index: it sends the reader somewhere
specific and wrong, with the confidence of a citation. These tests fail the build the
moment the document and the code disagree.
"""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = PROJECT_ROOT / "src" / "codequest"
CONTENT_ROOT = PROJECT_ROOT / "content"
INDEX = PROJECT_ROOT / "docs" / "ai-eng-bookmarks.md"

BOOKMARK = re.compile(r"\[AI-ENG:([a-z-]+)\]")
#: Rows look like: | `slug` | [src/codequest/x.py:42](src/codequest/x.py#L42) | ... |
INDEX_ROW = re.compile(r"^\|\s*`([a-z-]+)`\s*\|\s*\[([^\]:]+):(\d+)\]", re.MULTILINE)


def _bookmarked_files() -> list[Path]:
    """Source files first, then mission YAML, skipping translated trees.

    Some bridges belong to a mission rather than to a line of engine code, and they get
    checked here for the same reason the code ones do: a citation nobody verifies goes
    stale silently. The ``-pt`` mirrors carry the identical comment, so indexing them
    too would only make the target flip between languages.

    Kept in step with ``scripts/refresh_bookmarks.py``, which walks the same set.
    """
    paths = sorted(PACKAGE_ROOT.rglob("*.py"))
    if CONTENT_ROOT.is_dir():
        paths += sorted(
            path
            for path in CONTENT_ROOT.rglob("*.yaml")
            if not any(part.endswith("-pt") for part in path.parts)
        )
    return paths


def bookmarks_in_source() -> dict[str, tuple[str, int]]:
    """Every bookmark in the repo, mapped to the file and line where it first appears."""
    found: dict[str, tuple[str, int]] = {}
    for path in _bookmarked_files():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = BOOKMARK.search(line)
            if match and match.group(1) not in found:
                found[match.group(1)] = (path.relative_to(PROJECT_ROOT).as_posix(), number)
    return found


def bookmarks_in_index() -> dict[str, tuple[str, int]]:
    text = INDEX.read_text(encoding="utf-8")
    return {slug: (path, int(line)) for slug, path, line in INDEX_ROW.findall(text)}


def test_the_index_exists_and_has_rows():
    """Guards against a vacuous suite: an empty index would satisfy every check below."""
    assert bookmarks_in_index(), "docs/ai-eng-bookmarks.md lists no bookmarks"


def test_every_indexed_bookmark_points_at_a_real_line():
    """Follow each file:line in the index and confirm the marker is actually there."""
    wrong: list[str] = []

    for slug, (rel_path, line_number) in bookmarks_in_index().items():
        path = PROJECT_ROOT / rel_path
        if not path.is_file():
            wrong.append(f"{slug}: {rel_path} does not exist")
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        if line_number > len(lines) or f"[AI-ENG:{slug}]" not in lines[line_number - 1]:
            wrong.append(f"{slug}: {rel_path}:{line_number} is not that bookmark")

    assert not wrong, (
        "stale index entries:\n"
        + "\n".join(wrong)
        + "\n\nFix with: python scripts/refresh_bookmarks.py"
    )


def test_no_bookmark_in_the_code_is_missing_from_the_index():
    """A concept marked in the code but never indexed is a lesson nobody finds."""
    missing = set(bookmarks_in_source()) - set(bookmarks_in_index())

    assert not missing, f"bookmarks absent from the index: {sorted(missing)}"


def test_the_index_lists_nothing_that_no_longer_exists():
    orphaned = set(bookmarks_in_index()) - set(bookmarks_in_source())

    assert not orphaned, f"index rows with no bookmark in the code: {sorted(orphaned)}"


def test_slugs_are_kebab_case():
    """A stable spelling is what lets an HTML lesson reference a slug and stay correct."""
    bad = [slug for slug in bookmarks_in_source() if not re.fullmatch(r"[a-z]+(-[a-z]+)*", slug)]

    assert not bad, f"slugs that are not kebab-case: {bad}"
