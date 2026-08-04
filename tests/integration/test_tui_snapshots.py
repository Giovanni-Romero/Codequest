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

import pytest

from codequest.services.bootstrap import create_context
from codequest.tui.app import CodeQuestApp
from codequest.tui.screens.mission import MissionScreen

WIDE = (110, 34)
NARROW = (90, 30)
TINY = (70, 26)


@pytest.fixture
def context(tmp_path):
    ctx = create_context(database=tmp_path / "save.db")
    yield ctx
    ctx.close()


# --------------------------------------------------------------------- screens


def test_main_menu(snap_compare, context):
    """Java and TypeScript must read as unavailable without relying on colour alone."""
    assert snap_compare(CodeQuestApp(context=context), terminal_size=WIDE)


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


def test_settings(snap_compare, context):
    async def run(pilot):
        await pilot.press("s")

    assert snap_compare(CodeQuestApp(context=context), terminal_size=WIDE, run_before=run)


# ------------------------------------------------------- the three layout bands


async def _open_mission(pilot) -> None:
    profile = pilot.app.context.progress.create_profile("giovanni", "python")
    pilot.app.set_profile(profile)
    mission = pilot.app.context.missions.get_mission("py-foundations-06")
    pilot.app.push_screen(MissionScreen(mission))
    await pilot.pause()


def test_mission_wide(snap_compare, context):
    """At 110 columns all four panels sit side by side."""
    assert snap_compare(
        CodeQuestApp(context=context), terminal_size=WIDE, run_before=_open_mission
    )


def test_mission_narrow(snap_compare, context):
    """At 90 columns teaching and brief give way to the tabs."""
    assert snap_compare(
        CodeQuestApp(context=context), terminal_size=NARROW, run_before=_open_mission
    )


def test_mission_tiny(snap_compare, context):
    """At 70 columns the view is reduced and says so. It never refuses to run."""
    assert snap_compare(
        CodeQuestApp(context=context), terminal_size=TINY, run_before=_open_mission
    )


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

        pilot.app.screen.query_one("#editor", CodeEditor).text = (
            "def sum_list(numbers):\n    return 6\n"
        )
        await pilot.press("f5")
        await pilot.pause(delay=8)

    assert snap_compare(CodeQuestApp(context=context), terminal_size=WIDE, run_before=run)
