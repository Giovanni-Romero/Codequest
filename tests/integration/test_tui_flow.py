"""Pilot tests: drive the real app with keystrokes and inspect what happens.

These test *behaviour*, not appearance. A screen that renders beautifully and never
advances past the menu passes no test here, and that is the point — the snapshots next
door cover how it looks.

Every test builds the app against a temp database. Passing the context in rather than
letting the app reach for the configured save file is what keeps the suite from touching
the player's real progress.
"""

from __future__ import annotations

import pytest
from textual.color import Color
from textual.widgets import Input, Label, ListView, Static, TabbedContent

from codequest.services.bootstrap import create_context
from codequest.tui.app import CodeQuestApp
from codequest.tui.screens.dialogs import ConfirmDialog
from codequest.tui.screens.island_map import IslandMapScreen
from codequest.tui.screens.main_menu import MainMenuScreen
from codequest.tui.screens.mission import MissionScreen
from codequest.tui.screens.save_select import SaveSelectScreen
from codequest.tui.screens.settings import SettingsScreen
from codequest.tui.widgets.code_editor import CodeEditor
from codequest.tui.widgets.hint_panel import HintPanel

CORRECT_SUM_LIST = """
def sum_list(numbers):
    total = 0
    for n in numbers:
        total = total + n
    return total
"""


@pytest.fixture
def context(tmp_path):
    ctx = create_context(database=tmp_path / "save.db")
    yield ctx
    ctx.close()


@pytest.fixture
def app(context):
    return CodeQuestApp(context=context)


async def _create_save(pilot, name: str = "giovanni") -> None:
    """Walk the menu to a fresh save. Most tests need one before anything interesting."""
    await pilot.press("enter")  # Python -> save select
    await pilot.press("n")  # new save
    field = pilot.app.screen.query_one("#new-name", Input)
    field.value = name
    await pilot.press("enter")
    await pilot.pause()


async def _confirm(pilot) -> None:
    """Say yes to the dialog that is up.

    Cancel holds focus on mount, deliberately, so getting to the destructive button takes
    a tab. Driving it by keystroke rather than calling dismiss() is what keeps that
    ordering under test - a dialog that focused Confirm would still pass a dismiss(True).
    """
    await pilot.press("tab")
    await pilot.press("enter")
    await pilot.pause()


def _dialog_is_up(pilot) -> bool:
    return isinstance(pilot.app.screen, ConfirmDialog)


# ------------------------------------------------------------------ navigation


async def test_the_app_opens_on_the_main_menu(app):
    async with app.run_test() as pilot:
        assert isinstance(pilot.app.screen, MainMenuScreen)


async def test_choosing_python_reaches_the_save_screen(app):
    async with app.run_test() as pilot:
        await pilot.press("enter")
        assert isinstance(pilot.app.screen, SaveSelectScreen)


async def test_arrow_keys_highlight_ai_engineering_in_brass(app):
    async with app.run_test() as pilot:
        await pilot.press("down")

        selected = pilot.app.screen.query_one("#track-ai-engineering")
        assert selected.has_class("-highlight")
        assert selected.styles.color == Color.parse("#c9a227")


async def test_choosing_ai_engineering_loads_its_catalogue(app):
    async with app.run_test() as pilot:
        await pilot.press("down", "enter")

        assert isinstance(pilot.app.screen, SaveSelectScreen)
        assert pilot.app.context.missions.track.id == "ai-engineering"
        assert pilot.app.context.missions.get_mission("ai-documents-01") is not None


async def test_unbuilt_tracks_cannot_be_selected(app):
    """Java is visible so the player sees where the game is going, and disabled."""
    async with app.run_test() as pilot:
        java = pilot.app.screen.query_one("#track-java")
        assert java.disabled


async def test_settings_is_reachable_and_returns(app):
    async with app.run_test() as pilot:
        await pilot.press("s")
        assert isinstance(pilot.app.screen, SettingsScreen)
        await pilot.press("escape")
        assert isinstance(pilot.app.screen, MainMenuScreen)


# ----------------------------------------------------------------------- saves


async def test_creating_a_save_lists_it(app):
    async with app.run_test() as pilot:
        await _create_save(pilot)

        listing = pilot.app.screen.query_one("#save-list", ListView)
        assert len(listing.children) == 1
        assert pilot.app.context.progress.profiles.get_by_name("giovanni") is not None


async def test_each_track_lists_only_its_saves_without_changing_existing_progress(app, context):
    python_profile = context.progress.create_profile("python-career", "python")
    context.progress.profiles.add_xp(python_profile.id, 125)
    context.progress.progress.record_attempt(
        python_profile.id, "py-foundations-01", passed=True, xp=10
    )

    async with app.run_test() as pilot:
        await pilot.press("enter")
        assert len(pilot.app.screen.query_one("#save-list", ListView).children) == 1

        await pilot.press("escape", "down", "enter")
        assert len(pilot.app.screen.query_one("#save-list", ListView).children) == 0

        await pilot.press("n")
        pilot.app.screen.query_one("#new-name", Input).value = "ai-career"
        await pilot.press("enter")

        ai_profile = context.progress.profiles.get_by_name("ai-career")
        assert ai_profile is not None
        assert ai_profile.track == "ai-engineering"

        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(pilot.app.screen, IslandMapScreen)
        assert pilot.app.context.missions.get_mission("ai-documents-01") is not None

        await pilot.press("escape", "escape", "up", "enter")
        await pilot.pause()
        assert pilot.app.context.missions.track.id == "python"
        python_saves = pilot.app.screen.query_one("#save-list", ListView)
        assert len(python_saves.children) == 1
        assert "python-career" in str(python_saves.children[0].query_one(Label).render())

        reloaded = context.progress.profiles.get(python_profile.id)
        assert reloaded is not None
        assert reloaded.track == "python"
        assert reloaded.total_xp == 125
        assert context.progress.progress.get(python_profile.id, "py-foundations-01").is_completed


async def test_selecting_a_save_opens_the_map(app):
    async with app.run_test() as pilot:
        await _create_save(pilot)
        pilot.app.screen.query_one("#save-list", ListView).focus()
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, IslandMapScreen)
        assert pilot.app.profile is not None


async def test_a_duplicate_name_is_refused_with_the_services_own_message(app, context):
    context.progress.create_profile("giovanni", "python")

    async with app.run_test() as pilot:
        await _create_save(pilot, "giovanni")

        tagline = pilot.app.screen.query_one("#tagline")
        assert "already exists" in str(tagline.render())


# ------------------------------------------------------------------- the map


async def test_the_map_shows_the_ten_foundations_missions(app):
    async with app.run_test() as pilot:
        await _create_save(pilot)
        pilot.app.screen.query_one("#save-list", ListView).focus()
        await pilot.press("enter")
        await pilot.pause()

        entries = pilot.app.screen.query_one("#entries", ListView)
        mission_rows = [c for c in entries.children if (c.id or "").startswith("mission-")]
        assert len(mission_rows) == 10


async def test_opening_a_mission_loads_its_stub_into_the_editor(app):
    async with app.run_test() as pilot:
        await _create_save(pilot)
        pilot.app.screen.query_one("#save-list", ListView).focus()
        await pilot.press("enter")
        await pilot.pause()

        entries = pilot.app.screen.query_one("#entries", ListView)
        first = next(c for c in entries.children if (c.id or "").startswith("mission-"))
        entries.index = entries.children.index(first)
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, MissionScreen)
        assert "def supplies_after_trip" in pilot.app.screen.query_one("#editor", CodeEditor).text


# ---------------------------------------------------------------- the mission


async def _open_mission(pilot, mission_id: str = "py-foundations-06") -> None:
    await _create_save(pilot)
    pilot.app.screen.query_one("#save-list", ListView).focus()
    await pilot.press("enter")
    await pilot.pause()

    mission = pilot.app.context.missions.get_mission(mission_id)
    pilot.app.push_screen(MissionScreen(mission))
    await pilot.pause()


async def _wait_for_attempt(pilot, limit: float = 20.0) -> None:
    waited = 0.0
    while getattr(pilot.app.screen, "running", False) and waited < limit:
        await pilot.pause(delay=0.1)
        waited += 0.1

    await pilot.app.workers.wait_for_complete()
    await pilot.pause()


async def test_output_tab_shows_literal_prints_from_every_case(app):
    """Dropping any CaseOutcome.stdout, including hidden cases, must fail this test."""
    async with app.run_test() as pilot:
        await _open_mission(pilot)
        pilot.app.screen.query_one("#editor", CodeEditor).text = """
def sum_list(numbers):
    print(f"[red]{numbers}[/red]")
    total = 0
    for number in numbers:
        total += number
    return total
"""

        await pilot.press("f5")
        await _wait_for_attempt(pilot)
        await pilot.press("f7")

        tabs = pilot.app.screen.query_one("#right-tabs", TabbedContent)
        rendered = str(pilot.app.screen.query_one("#output-body", Static).render())
        assert tabs.active == "tab-output"
        assert rendered.count("[red]") == 8
        assert "case 1 (visible)" in rendered
        assert "case 8 (hidden)" in rendered


async def test_a_new_attempt_replaces_the_previous_output(app):
    """The console represents one attempt, not an accidental unbounded history."""
    async with app.run_test() as pilot:
        await _open_mission(pilot)
        editor = pilot.app.screen.query_one("#editor", CodeEditor)
        editor.text = CORRECT_SUM_LIST.replace("total = 0", 'print("old output")\n    total = 0')

        await pilot.press("f5")
        await _wait_for_attempt(pilot)

        editor.text = CORRECT_SUM_LIST
        await pilot.press("f5")
        await _wait_for_attempt(pilot)
        await pilot.press("f7")

        rendered = str(pilot.app.screen.query_one("#output-body", Static).render())
        assert "old output" not in rendered
        assert rendered.count("No output") == 8


async def test_output_marks_cases_skipped_after_execution_stops(app):
    """A halted attempt must not describe untouched cases as executed with empty stdout."""
    async with app.run_test() as pilot:
        await _open_mission(pilot)
        pilot.app.screen.query_one("#editor", CodeEditor).text = """
def sum_list(numbers):
    while True:
        pass
"""

        await pilot.press("f5")
        await _wait_for_attempt(pilot)
        await pilot.press("f7")

        rendered = str(pilot.app.screen.query_one("#output-body", Static).render())
        assert rendered.count("Not executed") == 7


async def test_running_a_correct_solution_awards_xp(app):
    """The whole loop, driven by keystrokes: type, F5, see the verdict, see the XP."""
    async with app.run_test() as pilot:
        await _open_mission(pilot)

        pilot.app.screen.query_one("#editor", CodeEditor).text = CORRECT_SUM_LIST
        await pilot.press("f5")
        await pilot.pause(delay=6)

        profile = pilot.app.context.progress.profiles.get_by_name("giovanni")
        assert profile.total_xp == 10


async def test_the_map_shows_completion_after_returning_from_a_solved_mission(app):
    """Regression: popping back from a mission never remounts the map screen, so it
    only ever reflected progress from before the player solved anything unless the
    map explicitly refreshes on resume."""
    async with app.run_test() as pilot:
        await _open_mission(pilot)

        pilot.app.screen.query_one("#editor", CodeEditor).text = CORRECT_SUM_LIST
        await pilot.press("f5")
        await pilot.pause(delay=6)

        await pilot.press("escape")
        await pilot.pause()

        assert isinstance(pilot.app.screen, IslandMapScreen)
        heading = str(pilot.app.screen.query_one("#map-heading").render())
        total_missions = len(pilot.app.context.missions.missions)
        assert f"1/{total_missions}" in heading

        row = pilot.app.screen.query_one("#mission-py-foundations-06")
        assert "10 XP" in str(row.query_one(Label).render())


async def test_a_solved_mission_row_carries_the_completed_class(app):
    """The row's colour comes from CSS, not from markup inside the label.

    That is the load-bearing part: inline markup would beat the stylesheet, so the
    selection highlight would silently stop working on exactly the rows the player has
    already finished. The check glyph still marks completion on its own, so nothing here
    depends on the colour being seen.
    """
    async with app.run_test() as pilot:
        await _open_mission(pilot)

        pilot.app.screen.query_one("#editor", CodeEditor).text = CORRECT_SUM_LIST
        await pilot.press("f5")
        await pilot.pause(delay=6)

        await pilot.press("escape")
        await pilot.pause()

        solved = pilot.app.screen.query_one("#mission-py-foundations-06")
        untouched = pilot.app.screen.query_one("#mission-py-foundations-07")
        assert solved.has_class("completed")
        assert not untouched.has_class("completed")


async def test_f6_advances_straight_after_solving(app):
    """The happy path asks nothing.

    Solve, then take the "F6 for the next mission" the status line just offered. The
    editor holds the solution rather than the stub, so a naive dirty check would stop
    here - and a confirmation on the most common path in the game is one people learn to
    dismiss without reading, which is how the F4 dialog would lose its meaning too.
    """
    async with app.run_test() as pilot:
        await _open_mission(pilot)

        pilot.app.screen.query_one("#editor", CodeEditor).text = CORRECT_SUM_LIST
        await pilot.press("f5")
        await pilot.pause(delay=6)

        await pilot.press("f6")
        await pilot.pause()

        assert isinstance(pilot.app.screen, MissionScreen)
        assert pilot.app.screen.mission.id == "py-foundations-07"


async def test_f6_asks_before_leaving_an_unsolved_mission(app):
    """The accident this dialog exists for: reaching for F5 and hitting F6."""
    async with app.run_test() as pilot:
        await _open_mission(pilot)
        pilot.app.screen.query_one("#editor", CodeEditor).text = "my work in progress"

        await pilot.press("f6")
        await pilot.pause()

        assert _dialog_is_up(pilot)


async def test_cancelling_f6_keeps_the_mission_and_the_code(app):
    async with app.run_test() as pilot:
        await _open_mission(pilot)
        pilot.app.screen.query_one("#editor", CodeEditor).text = "my work in progress"

        await pilot.press("f6")
        await pilot.pause()
        await pilot.press("escape")  # cancel the dialog
        await pilot.pause()

        assert isinstance(pilot.app.screen, MissionScreen)
        assert pilot.app.screen.mission.id == "py-foundations-06"
        assert pilot.app.screen.query_one("#editor", CodeEditor).text == "my work in progress"


async def test_f6_asks_again_once_solved_code_is_edited(app):
    """Passing makes leaving free. Typing after it makes leaving cost again."""
    async with app.run_test() as pilot:
        await _open_mission(pilot)

        pilot.app.screen.query_one("#editor", CodeEditor).text = CORRECT_SUM_LIST
        await pilot.press("f5")
        await pilot.pause(delay=6)

        pilot.app.screen.query_one("#editor", CodeEditor).text = CORRECT_SUM_LIST + "\n# more"
        await pilot.press("f6")
        await pilot.pause()

        assert _dialog_is_up(pilot)


async def test_f6_crosses_into_the_next_island(app):
    """The last mission of an island leads into the first of the next one.

    Regression: this used to jump to whichever island sorted first alphabetically,
    skipping a whole island at every boundary.
    """
    async with app.run_test() as pilot:
        await _open_mission(pilot, mission_id="py-foundations-10")

        await pilot.press("f6")
        await pilot.pause()
        await _confirm(pilot)

        assert pilot.app.screen.mission.id == "py-collections-01"


async def test_f6_does_nothing_after_the_last_mission_of_the_track(app):
    """And asks nothing either.

    The lookup runs before the question on purpose. Asking "are you sure?" and then doing
    nothing would be worse than the silence this has always had.
    """
    async with app.run_test() as pilot:
        # Whichever mission is genuinely last, rather than a hardcoded id that goes
        # stale the moment another island ships.
        last = pilot.app.context.missions.missions[-1]
        await _open_mission(pilot, mission_id=last.id)
        pilot.app.screen.query_one("#editor", CodeEditor).text = "my work in progress"

        await pilot.press("f6")
        await pilot.pause()

        assert not _dialog_is_up(pilot)
        assert isinstance(pilot.app.screen, MissionScreen)
        assert pilot.app.screen.mission.id == last.id


async def test_running_a_wrong_solution_awards_nothing(app):
    async with app.run_test() as pilot:
        await _open_mission(pilot)

        pilot.app.screen.query_one(
            "#editor", CodeEditor
        ).text = "def sum_list(numbers):\n    return 6\n"
        await pilot.press("f5")
        await pilot.pause(delay=6)

        profile = pilot.app.context.progress.profiles.get_by_name("giovanni")
        assert profile.total_xp == 0


async def test_a_hint_is_revealed_and_recorded(app):
    """F1 reveals one rung and charges for it. Revealing is what costs, not solving."""
    async with app.run_test() as pilot:
        await _open_mission(pilot)

        await pilot.press("f1")
        await pilot.pause()

        panel = pilot.app.screen.query_one("#hints", HintPanel)
        assert panel.revealed == 1

        profile = pilot.app.context.progress.profiles.get_by_name("giovanni")
        record = pilot.app.context.progress.progress_for(profile)["py-foundations-06"]
        assert record.hints_used == 1


async def test_hints_run_out_and_the_panel_says_so(app):
    async with app.run_test() as pilot:
        await _open_mission(pilot)

        for _ in range(5):
            await pilot.press("f1")
        await pilot.pause()

        panel = pilot.app.screen.query_one("#hints", HintPanel)
        assert panel.revealed == 3
        assert panel.exhausted


async def test_two_hints_then_solving_pays_the_discounted_xp(app):
    """The Phase 3 rule, reaching the player through the interface for the first time."""
    async with app.run_test() as pilot:
        await _open_mission(pilot)

        await pilot.press("f1")
        await pilot.press("f1")
        await pilot.pause()

        pilot.app.screen.query_one("#editor", CodeEditor).text = CORRECT_SUM_LIST
        await pilot.press("f5")
        await pilot.pause(delay=6)

        profile = pilot.app.context.progress.profiles.get_by_name("giovanni")
        assert profile.total_xp == 7


async def test_escape_returns_to_the_map(app):
    async with app.run_test() as pilot:
        await _open_mission(pilot)
        await pilot.press("escape")
        await pilot.pause()
        await _confirm(pilot)

        assert isinstance(pilot.app.screen, IslandMapScreen)


async def test_escape_asks_before_discarding_work(app):
    """Escape is the same accident as F6 with a key that sits nearer the typing hand."""
    async with app.run_test() as pilot:
        await _open_mission(pilot)
        pilot.app.screen.query_one("#editor", CodeEditor).text = "my work in progress"

        await pilot.press("escape")
        await pilot.pause()

        assert _dialog_is_up(pilot)

        await pilot.press("escape")  # cancel the dialog
        await pilot.pause()

        assert isinstance(pilot.app.screen, MissionScreen)
        assert pilot.app.screen.query_one("#editor", CodeEditor).text == "my work in progress"


async def test_reset_asks_before_discarding_work(app):
    """Destructive actions confirm. The editor holds whatever the player just typed."""
    async with app.run_test() as pilot:
        await _open_mission(pilot)
        editor = pilot.app.screen.query_one("#editor", CodeEditor)
        editor.text = "my work in progress"

        await pilot.press("f4")
        await pilot.pause()
        await pilot.press("escape")  # cancel the dialog
        await pilot.pause()

        assert pilot.app.screen.query_one("#editor", CodeEditor).text == "my work in progress"


# ------------------------------------------------------------------ responsive


@pytest.mark.parametrize(
    ("width", "expected"),
    [(120, set()), (90, {"narrow"}), (70, {"tiny"})],
)
async def test_the_layout_reflows_and_never_refuses(context, width, expected):
    """Three bands from docs/art-direction.md section 5. None of them is a wall."""
    app = CodeQuestApp(context=context)
    async with app.run_test(size=(width, 30)) as pilot:
        await _open_mission(pilot)
        await pilot.pause()

        screen = pilot.app.screen
        applied = {name for name in ("narrow", "tiny") if screen.has_class(name)}
        assert applied == expected
