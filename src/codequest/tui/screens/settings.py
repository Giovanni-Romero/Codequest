"""Settings screen.

Read-only on purpose, for now. Every value here comes from ``.env`` through
``config.py``, which is the one module allowed to read the environment. A settings screen
that wrote its own copy somewhere else would create a second source of truth, and the
game would start disagreeing with its own configuration file.

So this screen shows what is configured and where to change it. When there is a setting
that genuinely belongs to the player rather than to the installation — an editor
preference, say — it gets a row in the database and an edit control here.
"""

from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import BindingType
from textual.containers import Center, Middle, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from codequest.tui.symbols import FAIL, PASS


class SettingsScreen(Screen):
    """Shows the resolved configuration and where it comes from."""

    BINDINGS: ClassVar[list[BindingType]] = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Middle(), Center(), Vertical(id="menu-frame"):
            yield Static("Settings", id="title")
            yield Static(
                "[$parchment-dim]Configured in .env - copy .env.example to start[/$parchment-dim]",
                id="tagline",
            )
            yield Static("", id="settings-body")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#settings-body", Static).update(self._settings_text())

    def _settings_text(self) -> str:
        settings = self.app.context.settings
        mentor_mark = PASS if settings.mentor_enabled else FAIL
        mentor_style = "pass" if settings.mentor_enabled else "locked"

        rows = [
            ("[$brass]Mentor[/$brass]", ""),
            (
                "  enabled",
                f"[{mentor_style}]{mentor_mark}[/{mentor_style}] "
                f"CODEQUEST_MENTOR_ENABLED={str(settings.mentor_enabled).lower()}",
            ),
            ("  host", settings.ollama_host),
            ("  model", settings.ollama_model),
            ("  timeout", f"{settings.ollama_timeout_seconds}s"),
            ("", ""),
            ("[$brass]Sandbox[/$brass]", ""),
            ("  default timeout", f"{settings.default_timeout_ms} ms"),
            ("  default memory", f"{settings.default_memory_mb} MB"),
            ("", ""),
            ("[$brass]Paths[/$brass]", ""),
            ("  content", str(settings.content_dir)),
            ("  saves", str(settings.database_path)),
        ]

        lines = [f"{label:<20}{value}" if label else "" for label, value in rows]
        lines.append("")
        lines.append(
            "[$parchment-dim]The game is fully playable with the mentor off. "
            "It teaches from the hand-written content, not from a model.[/$parchment-dim]"
        )
        return "\n".join(lines)
