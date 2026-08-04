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
from textual.widgets import Input, ListView

from codequest.services.bootstrap import create_context
from codequest.tui.app import CodeQuestApp
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


# ------------------------------------------------------------------ navigation


async def test_the_app_opens_on_the_main_menu(app):
    async with app.run_test() as pilot:
        assert isinstance(pilot.app.screen, MainMenuScreen)


async def test_choosing_python_reaches_the_save_screen(app):
    async with app.run_test() as pilot:
        await pilot.press("enter")
        assert isinstance(pilot.app.screen, SaveSelectScreen)


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


async def test_running_a_correct_solution_awards_xp(app):
    """The whole loop, driven by keystrokes: type, F5, see the verdict, see the XP."""
    async with app.run_test() as pilot:
        await _open_mission(pilot)

        pilot.app.screen.query_one("#editor", CodeEditor).text = CORRECT_SUM_LIST
        await pilot.press("f5")
        await pilot.pause(delay=6)

        profile = pilot.app.context.progress.profiles.get_by_name("giovanni")
        assert profile.total_xp == 10


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

        assert isinstance(pilot.app.screen, IslandMapScreen)


async def test_reset_asks_before_discarding_work(app):
    """Destructive actions confirm. The editor holds whatever the player just typed."""
    async with app.run_test() as pilot:
        await _open_mission(pilot)
        editor = pilot.app.screen.query_one("#editor", CodeEditor)
        editor.text = "my work in progress"

        await pilot.press("ctrl+r")
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
