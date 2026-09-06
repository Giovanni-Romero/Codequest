"""Main menu: language selection.

Java and TypeScript are listed and visibly disabled rather than hidden. A player should
be able to see where the game is going; a menu with one entry that silently grows later
says nothing about the shape of the thing they are learning.
"""

from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import BindingType
from textual.containers import Center, Middle, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static

from codequest.tui.screens.save_select import SaveSelectScreen
from codequest.tui.strings import t
from codequest.tui.symbols import LOCKED, ROUTE

#: Tracks the game knows about. Only those with content and a runner are playable.
#: The note is a strings.py key, not text - translated at render time, not at import.
TRACKS = [
    ("python", "Python", True, "track.python.note"),
    ("ai-engineering", "AI Engineering", True, "track.ai_engineering.note"),
    ("java", "Java", False, "track.java.note"),
    ("typescript", "TypeScript", False, "track.typescript.note"),
]


class MainMenuScreen(Screen):
    """Pick a language."""

    BINDINGS: ClassVar[list[BindingType]] = [
        ("s", "settings", "Settings"),
        ("q", "app.quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Middle(), Center(), Vertical(id="menu-frame"):
            yield Static(t("main_menu.title"), id="title")
            yield Static(f"{ROUTE * 3} {t('main_menu.tagline')} {ROUTE * 3}", id="tagline")
            yield ListView(*self._track_items(), id="track-list")
        yield Footer()

    def _track_items(self) -> list[ListItem]:
        items: list[ListItem] = []
        for track_id, name, playable, note_key in TRACKS:
            note = t(note_key)
            if playable:
                label = f"  {name:<16} [$parchment-dim]{note}[/$parchment-dim]"
                items.append(ListItem(Label(label), id=f"track-{track_id}"))
            else:
                label = f"{LOCKED} {name:<16} [$becalmed]{note}[/$becalmed]"
                item = ListItem(Label(label), id=f"track-{track_id}")
                item.disabled = True
                items.append(item)
        return items

    def on_mount(self) -> None:
        self.query_one("#track-list", ListView).focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        # Disabled items cannot be selected, so anything arriving here is playable.
        track_id = (event.item.id or "").removeprefix("track-")
        self.app.set_track(track_id)
        self.app.push_screen(SaveSelectScreen())

    def action_settings(self) -> None:
        from codequest.tui.screens.settings import SettingsScreen

        self.app.push_screen(SettingsScreen())
