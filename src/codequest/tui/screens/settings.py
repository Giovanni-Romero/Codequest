"""Settings screen.

Mostly read-only. Every value shown here except the language comes from ``.env``
through ``config.py``, which is the one module allowed to read the environment. A
settings screen that wrote its own copy somewhere else would create a second source of
truth, and the game would start disagreeing with its own configuration file.

Language is the one setting that genuinely belongs to the player rather than to the
installation, so it is the first row in this screen with a real edit control: a value
in the ``preference`` table (see ``storage/repositories.PreferenceRepository``), not
``.env``. The next player-owned setting that shows up follows the same pattern.
"""

from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Center, Middle, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from codequest.tui import strings
from codequest.tui.strings import t
from codequest.tui.symbols import FAIL, PASS


class SettingsScreen(Screen):
    """Shows the resolved configuration, the one player-owned setting, and where the rest comes from."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
        Binding("l", "toggle_language", "Language", priority=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Middle(), Center(), Vertical(id="menu-frame"):
            yield Static(t("settings.title"), id="title")
            yield Static("", id="tagline")
            yield Static("", id="settings-body")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh()

    def action_toggle_language(self) -> None:
        new_language = "pt" if strings.get_language() == "en" else "en"
        self.app.set_language(new_language)
        self._refresh()

    def _refresh(self) -> None:
        self.query_one("#tagline", Static).update(
            f"[$parchment-dim]{t('settings.tagline')}[/$parchment-dim]"
        )
        self.query_one("#settings-body", Static).update(self._settings_text())

    def _settings_text(self) -> str:
        settings = self.app.context.settings
        language = strings.get_language()
        mentor_mark = PASS if settings.mentor_enabled else FAIL
        mentor_style = "pass" if settings.mentor_enabled else "locked"

        rows = [
            (f"[$brass]{t('settings.language_label')}[/$brass]", ""),
            (
                "  L",
                f"[accent]{t(f'settings.language_name.{language}')}[/accent]  "
                f"[$parchment-dim]{t('settings.language_hint')}[/$parchment-dim]",
            ),
            ("", ""),
            (f"[$brass]{t('settings.mentor')}[/$brass]", ""),
            (
                f"  {t('settings.mentor_enabled')}",
                f"[{mentor_style}]{mentor_mark}[/{mentor_style}] "
                f"CODEQUEST_MENTOR_ENABLED={str(settings.mentor_enabled).lower()}",
            ),
            (f"  {t('settings.mentor_host')}", settings.ollama_host),
            (f"  {t('settings.mentor_model')}", settings.ollama_model),
            (f"  {t('settings.mentor_timeout')}", f"{settings.ollama_timeout_seconds}s"),
            ("", ""),
            (f"[$brass]{t('settings.sandbox')}[/$brass]", ""),
            (f"  {t('settings.sandbox_timeout')}", f"{settings.default_timeout_ms} ms"),
            (f"  {t('settings.sandbox_memory')}", f"{settings.default_memory_mb} MB"),
            ("", ""),
            (f"[$brass]{t('settings.paths')}[/$brass]", ""),
            (f"  {t('settings.paths_content')}", str(settings.content_dir)),
            (f"  {t('settings.paths_saves')}", settings.database_path.as_posix()),
        ]

        lines = [f"{label:<24}{value}" if label else "" for label, value in rows]
        lines.append("")
        lines.append(f"[$parchment-dim]{t('settings.footer_note')}[/$parchment-dim]")
        return "\n".join(lines)
