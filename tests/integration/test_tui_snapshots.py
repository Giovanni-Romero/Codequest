"""Snapshot tests: catch visual regressions the pilot tests cannot see.

The pilot suite next door proves the game *works*. These prove it still *looks* the way
it was designed to, which is a different failure: a stylesheet edit that silently drops a
border, a palette change that makes locked and available islands indistinguishable, a
layout band that stops reflowing.

Each test renders a screen to SVG and compares it against a stored image. Regenerate
after an intentional visual change:

    pytest tests/integration/test_tui_snapshots.py --snapshot-update

and then **look at the diff** before committing it. A snapshot updated without being read
is a test that has been switched off.

Terminal size is pinned on every snapshot. Without it the images depend on whatever
terminal the runner happened to have, and the Windows CI job would disagree with Linux
for no real reason.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from codequest.config import Settings
from codequest.services.bootstrap import create_context
from codequest.tui.app import CodeQuestApp
from codequest.tui.screens.mission import MissionScreen

WIDE = (110, 34)
NARROW = (90, 30)
TINY = (70, 26)
#: A short-but-wide terminal, matching a VS Code integrated terminal panel. Rows are
#: the scarce resource here, not columns - this is what exposed the editor being
#: squeezed to nothing by an unsized #right-tabs (TabbedContent has no height rule
#: of its own, so it grows to fit its content instead of sharing the column's fr).
SHORT = (110, 22)


@pytest.fixture
def context(tmp_path):
    settings = Settings(content_dir=Path("content"), save_dir=Path("saves"))
    ctx = create_context(settings=settings, database=tmp_path / "save.db")
    yield ctx
    ctx.close()


# --------------------------------------------------------------------- screens


def test_main_menu(snap_compare, context):
    """Python starts brass-selected while unavailable tracks keep their lock glyph."""
    assert snap_compare(CodeQuestApp(context=context), terminal_size=WIDE)


def test_main_menu_with_ai_engineering_selected(snap_compare, context):
    """Moving down transfers the brass selection instead of leaving two highlighted rows."""

    async def run(pilot):
        await pilot.press("down")

    assert snap_compare(CodeQuestApp(context=context), terminal_size=WIDE, run_before=run)


def test_save_select_empty(snap_compare, context):
    async def run(pilot):
        await pilot.press("enter")

    assert snap_compare(CodeQuestApp(context=context), terminal_size=WIDE, run_before=run)


def test_save_select_with_a_save(snap_compare, context):
    context.progress.create_profile("giovanni", "python")

    async def run(pilot):
        await pilot.press("enter")

    assert snap_compare(CodeQuestApp(context=context), terminal_size=WIDE, run_before=run)


def test_island_map(snap_compare, context):
    """Progress bars, mission states, and a locked island showing its requirement."""
    profile = context.progress.create_profile("giovanni", "python")

    async def run(pilot):
        pilot.app.set_profile(profile)
        from codequest.tui.screens.island_map import IslandMapScreen

        pilot.app.push_screen(IslandMapScreen())
        await pilot.pause()

    assert snap_compare(CodeQuestApp(context=context), terminal_size=WIDE, run_before=run)


def test_island_map_selection_and_completion(snap_compare, context):
    """The three row states side by side: selected, completed, and neither.

    ``test_island_map`` above cannot show any of it. Its highlight lands on the first row,
    which is an island header whose text is entirely inline markup, and no mission is
    completed there - so it renders identically whether the mission-row colours exist or
    not. A snapshot that cannot fail on a change is not covering that change.

    Here row 1 is completed *and* selected, which is the case worth pinning: the selection
    has to win over the state, and the green check has to survive it winning.
    """
    profile = context.progress.create_profile("giovanni", "python")
    for mission_id in ("py-foundations-01", "py-foundations-02"):
        mission = context.missions.get_mission(mission_id)
        context.session.attempt(mission, mission.solution, profile, context.missions.islands)

    async def run(pilot):
        pilot.app.set_profile(profile)
        from codequest.tui.screens.island_map import IslandMapScreen

        pilot.app.push_screen(IslandMapScreen())
        await pilot.pause()
        # Off the island header and onto the first mission row.
        await pilot.press("down")
        await pilot.pause()

    assert snap_compare(CodeQuestApp(context=context), terminal_size=WIDE, run_before=run)


def test_settings(snap_compare, context):
    async def run(pilot):
        await pilot.press("s")

    assert snap_compare(CodeQuestApp(context=context), terminal_size=WIDE, run_before=run)


def test_editor_stays_visible_with_many_failing_cases(snap_compare, context):
    """A results pane full of failures must not starve the editor's row budget.

    Regression test for the bug where #right-tabs had no height rule: a long list of
    failing cases grew it to fit its own content, and #editor-panel's 2fr lost the fr
    split down to a sliver on a short terminal.
    """

    async def run(pilot):
        await _open_mission(pilot)
        from codequest.tui.widgets.code_editor import CodeEditor

        pilot.app.screen.query_one(
            "#editor", CodeEditor
        ).text = "def sum_list(numbers):\n    return 6\n"
        await pilot.press("f5")
        await _wait_for_run(pilot)

    assert snap_compare(CodeQuestApp(context=context), terminal_size=SHORT, run_before=run)


# ------------------------------------------------------- the three layout bands


async def _open_mission(pilot) -> None:
    profile = pilot.app.context.progress.create_profile("giovanni", "python")
    pilot.app.set_profile(profile)
    mission = pilot.app.context.missions.get_mission("py-foundations-06")
    pilot.app.push_screen(MissionScreen(mission))
    await pilot.pause()

    # The editor's cursor blinks, which makes the rendered SVG depend on what phase of
    # the blink the snapshot lands in. A visible cursor is one more distinct colour, so
    # Rich emits an extra `.terminal-rN` class and renumbers every class after it -- the
    # whole stylesheet shifts by one and the comparison fails on a diff that has nothing
    # to do with layout. It caught four runs in forty before this line existed.
    #
    # Blinking is right in the real game and meaningless in a still image.
    from codequest.tui.widgets.code_editor import CodeEditor

    for editor in pilot.app.screen.query(CodeEditor):
        editor.cursor_blink = False


async def _wait_for_run(pilot, limit: float = 20.0) -> None:
    """Wait until the attempt is finished, rather than for a fixed number of seconds.

    A run spawns one subprocess per test case on a worker thread, so how long it takes
    depends on the machine and on what else it is doing. A fixed ``pause(delay=...)`` is
    therefore a coin flip in both directions: too short and the snapshot catches the
    results panel mid-render, too long and every run pays for the worst case. Both of
    these tests used to sleep eight seconds and failed roughly two runs in three.

    ``MissionScreen.running`` is the screen's own answer to "am I done" — set in
    ``action_run`` and cleared in ``_show_outcome`` — so the condition was already
    there to be waited on.

    The ceiling exists so that a run which never finishes fails as a wrong snapshot
    instead of hanging the suite forever.

    Three waits, because "the run finished" and "the screen is done redrawing" are not
    the same moment. The flag clears first, the worker thread joins second, and the
    widgets settle last — the editor's syntax highlighting was still splitting ``def``
    across two spans one run in ten with only the flag waited on. ``_wait_for_screen``
    is what Textual's own ``App.run_test`` uses for exactly this.
    """
    waited = 0.0
    while getattr(pilot.app.screen, "running", False) and waited < limit:
        await pilot.pause(delay=0.1)
        waited += 0.1

    await pilot.app.workers.wait_for_complete()
    await pilot._wait_for_screen()
    await pilot.pause()


def test_mission_wide(snap_compare, context):
    """At 110 columns all four panels sit side by side."""
    assert snap_compare(CodeQuestApp(context=context), terminal_size=WIDE, run_before=_open_mission)


def test_mission_narrow(snap_compare, context):
    """At 90 columns teaching and brief give way to the tabs."""
    assert snap_compare(
        CodeQuestApp(context=context), terminal_size=NARROW, run_before=_open_mission
    )


def test_mission_tiny(snap_compare, context):
    """At 70 columns the view is reduced and says so. It never refuses to run."""
    assert snap_compare(CodeQuestApp(context=context), terminal_size=TINY, run_before=_open_mission)


# ------------------------------------------------------------------- the panels


def test_mission_with_hints_revealed(snap_compare, context):
    async def run(pilot):
        await _open_mission(pilot)
        await pilot.press("f1")
        await pilot.press("f1")
        await pilot.pause()

    assert snap_compare(CodeQuestApp(context=context), terminal_size=WIDE, run_before=run)


def test_results_after_a_failing_run(snap_compare, context):
    """Pass, fail and not-run each carry a symbol, so the panel survives no colour."""

    async def run(pilot):
        await _open_mission(pilot)
        from codequest.tui.widgets.code_editor import CodeEditor

        pilot.app.screen.query_one(
            "#editor", CodeEditor
        ).text = "def sum_list(numbers):\n    return 6\n"
        await pilot.press("f5")
        await _wait_for_run(pilot)

    assert snap_compare(CodeQuestApp(context=context), terminal_size=WIDE, run_before=run)


def test_output_after_a_printing_run(snap_compare, context):
    """Each case keeps its own literal stdout in the third lower-right tab."""

    async def run(pilot):
        await _open_mission(pilot)
        from codequest.tui.widgets.code_editor import CodeEditor

        pilot.app.screen.query_one("#editor", CodeEditor).text = """
def sum_list(numbers):
    print(f"[red]{numbers}[/red]")
    total = 0
    for number in numbers:
        total += number
    return total
"""
        await pilot.press("f5")
        await _wait_for_run(pilot)
        await pilot.press("f7")

    assert snap_compare(CodeQuestApp(context=context), terminal_size=WIDE, run_before=run)
