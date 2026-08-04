"""CodeQuestApp: the Textual application root.

The app owns three things and nothing else: the shared ``GameContext``, the currently
selected profile, and the screen stack. Every decision about XP, unlocking or judging
code happens in ``services/`` — a screen that computes any of that is in the wrong place.

That separation is not tidiness. It is what makes this whole layer replaceable: the game
was fully playable through the CLI before a single widget existed, and it still is.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from textual.app import App
from textual.binding import Binding, BindingType

from codequest.models.profile import Profile
from codequest.services.bootstrap import GameContext, create_context
from codequest.tui.screens.main_menu import MainMenuScreen


class CodeQuestApp(App):
    """The terminal game."""

    CSS_PATH = "styles.tcss"
    TITLE = "CodeQuest"
    SUB_TITLE = "learn to program by sailing"

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
    ]

    def __init__(
        self,
        context: GameContext | None = None,
        *,
        database: str | Path | None = None,
        track: str = "python",
    ) -> None:
        """Build the app.

        Args:
            context: Pre-wired services. Tests pass one built against a temp database;
                passing it in rather than reaching for a global is what makes the pilot
                tests independent of the player's real save file.
            database: Save file override, used when ``context`` is not supplied.
            track: Which language track to load.
        """
        super().__init__()
        self._owns_context = context is None
        self.context = context or create_context(database=database, track=track)
        self.profile: Profile | None = None

    def on_mount(self) -> None:
        self.push_screen(MainMenuScreen())

    def on_unmount(self) -> None:
        """Close the database, but only the one this app opened.

        A context handed in by a test belongs to the test, and closing it here would
        break the assertions that run after the app exits.
        """
        if self._owns_context:
            self.context.close()

    # ------------------------------------------------------------------ helpers

    def set_profile(self, profile: Profile) -> None:
        """Remember which career save is in play, and refresh it from storage."""
        self.profile = profile

    def refresh_profile(self) -> None:
        """Re-read the active profile so XP and unlocks shown on screen are current."""
        if self.profile is not None and self.profile.id is not None:
            reloaded = self.context.progress.profiles.get(self.profile.id)
            if reloaded is not None:
                self.profile = reloaded


def run(database: str | Path | None = None, track: str = "python") -> None:
    """Launch the game. Called by ``codequest play``."""
    CodeQuestApp(database=database, track=track).run()
