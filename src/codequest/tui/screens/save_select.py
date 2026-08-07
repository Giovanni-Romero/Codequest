"""Save select: up to four career slots, create and delete.

The four-slot limit is a service rule, not a database constraint, which is why this
screen can show "you already have 4 saves" instead of an IntegrityError. See
``docs/architecture.md`` — the decision was made before the schema existed, so the
message could be a friendly one.
"""

from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import BindingType
from textual.containers import Center, Middle, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView, Static

from codequest.models.profile import MAX_PROFILES, Profile
from codequest.services.progress_service import (
    DuplicateProfileNameError,
    ProfileLimitReachedError,
)
from codequest.tui.screens.dialogs import ConfirmDialog
from codequest.tui.screens.island_map import IslandMapScreen
from codequest.tui.strings import t
from codequest.tui.symbols import AVAILABLE, CURRENT


class SaveSelectScreen(Screen):
    """Choose, create or delete a career."""

    BINDINGS: ClassVar[list[BindingType]] = [
        ("n", "new_save", "New save"),
        ("d", "delete_save", "Delete"),
        ("escape", "app.pop_screen", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Middle(), Center(), Vertical(id="menu-frame"):
            yield Static(t("save_select.title"), id="title")
            yield Static("", id="tagline")
            yield ListView(id="save-list")
            yield Input(placeholder=t("save_select.name_placeholder"), id="new-name")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#new-name", Input).display = False
        self.refresh_saves()

    # -------------------------------------------------------------------- data

    def refresh_saves(self) -> None:
        """Rebuild the list from storage. Called after anything that changes it."""
        profiles = self.app.context.progress.list_profiles()
        listing = self.query_one("#save-list", ListView)
        listing.clear()

        for profile in profiles:
            listing.append(ListItem(Label(self._describe(profile)), id=f"save-{profile.id}"))

        remaining = MAX_PROFILES - len(profiles)
        tagline = self.query_one("#tagline", Static)
        if remaining > 0:
            tagline.update(
                f"[$parchment-dim]"
                f"{t('save_select.slots_free', remaining=remaining, max=MAX_PROFILES)}"
                f"[/$parchment-dim]"
            )
        else:
            tagline.update(
                f"[$becalmed]{t('save_select.slots_full', max=MAX_PROFILES)}[/$becalmed]"
            )

        if profiles:
            # A rebuilt ListView has no highlighted row, and Enter on nothing does
            # nothing. Without this the list looks fine and simply refuses to open.
            listing.index = 0
            listing.focus()

    def _describe(self, profile: Profile) -> str:
        completed = self.app.context.progress.progress.completed_count(profile.id)
        total = len(self.app.context.missions.missions)
        mark = CURRENT if completed else AVAILABLE
        detail = t(
            "save_select.level_xp_missions",
            level=profile.level,
            xp=profile.total_xp,
            done=completed,
            total=total,
        )
        return f"{mark} {profile.name:<14} [$parchment-dim]{detail}[/$parchment-dim]"

    # ------------------------------------------------------------------ actions

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        profile_id = int((event.item.id or "save-0").removeprefix("save-"))
        profile = self.app.context.progress.profiles.get(profile_id)
        if profile is not None:
            self.app.set_profile(profile)
            self.app.push_screen(IslandMapScreen())

    def action_new_save(self) -> None:
        field = self.query_one("#new-name", Input)
        field.display = True
        field.value = ""
        field.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        name = event.value.strip()
        field = self.query_one("#new-name", Input)
        field.display = False

        if not name:
            return

        try:
            self.app.context.progress.create_profile(name, self.app.context.missions.track.id)
        except (ProfileLimitReachedError, DuplicateProfileNameError, ValueError) as exc:
            # The service raises a sentence written for a human. Show it verbatim rather
            # than inventing a second wording that will drift from the first.
            self.query_one("#tagline", Static).update(f"[$adrift]{exc}[/$adrift]")
            return

        self.refresh_saves()

    def action_delete_save(self) -> None:
        listing = self.query_one("#save-list", ListView)
        item = listing.highlighted_child
        if item is None:
            return

        profile_id = int((item.id or "save-0").removeprefix("save-"))
        profile = self.app.context.progress.profiles.get(profile_id)
        if profile is None:
            return

        def on_answer(confirmed: bool | None) -> None:
            if confirmed:
                self.app.context.progress.delete_profile(profile_id)
                self.refresh_saves()

        self.app.push_screen(
            ConfirmDialog(t("save_select.delete_confirm", name=profile.name, xp=profile.total_xp)),
            on_answer,
        )
