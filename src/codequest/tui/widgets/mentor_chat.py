"""The bird in the corner: optional mentor chat.

Collapsed by default, and everything about this widget assumes the mentor may not exist.
The import of ``codequest.mentor`` happens **inside** a method, never at module scope, so
that deleting ``src/codequest/mentor/`` leaves a working game. That rule is enforced by
``tests/integration/test_architecture.py``, not by remembering it.
"""

from __future__ import annotations

from typing import ClassVar

from textual import work
from textual.app import ComposeResult
from textual.binding import BindingType
from textual.containers import Vertical
from textual.widgets import Input, RichLog, Static

from codequest.models.mission import Mission
from codequest.models.verdict import Verdict


class MentorChat(Vertical):
    """A small chat panel. Absent, offline or working — all three are normal."""

    BINDINGS: ClassVar[list[BindingType]] = []

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.mission: Mission | None = None
        self.verdict: Verdict | None = None
        self.hints_used = 0
        self.busy = False

    def compose(self) -> ComposeResult:
        yield Static("Mentor", classes="panel-title")
        yield RichLog(id="mentor-log", wrap=True, markup=True)
        yield Input(placeholder="ask the mentor...", id="mentor-input")

    def on_mount(self) -> None:
        self._say(
            "[$parchment-dim]Ask a question. I will not hand you the answer - "
            "that is what the hint panel is for.[/$parchment-dim]"
        )

    # ------------------------------------------------------------------ context

    def load(self, mission: Mission, hints_used: int = 0) -> None:
        self.mission = mission
        self.hints_used = hints_used

    def set_verdict(self, verdict: Verdict | None) -> None:
        """Tell the mentor where the player just got stuck. Usually the whole answer."""
        self.verdict = verdict

    # --------------------------------------------------------------------- chat

    def on_input_submitted(self, event: Input.Submitted) -> None:
        question = event.value.strip()
        event.input.value = ""
        if not question or self.mission is None or self.busy:
            return

        self._say(f"[$beacon]you[/$beacon]  {question}")
        self.busy = True
        self._say("[$parchment-dim]thinking...[/$parchment-dim]")
        self._ask(question)

    @work(thread=True, exclusive=True)
    def _ask(self, question: str) -> None:
        """Talk to the model off the UI thread.

        The import lives here rather than at the top of the file: the mentor package is
        optional, and a module-scope import would make deleting it a crash on startup.
        """
        from codequest.mentor.client import MentorState, OllamaClient
        from codequest.mentor.policy import filter_reply
        from codequest.mentor.prompts import MentorContext, build_messages

        settings = self.app.context.settings
        client = OllamaClient(
            host=settings.ollama_host,
            model=settings.ollama_model,
            timeout_seconds=settings.ollama_timeout_seconds,
        )

        context = MentorContext(
            mission=self.mission,
            code=self._current_code(),
            verdict=self.verdict,
            hints_used=self.hints_used,
        )
        reply = client.chat(build_messages(context, question))

        if reply.state is MentorState.READY:
            text, redacted = filter_reply(reply.text, self.mission.signature.entrypoint)
            rendered = f"[$brass]mentor[/$brass]  {text}"
            if redacted:
                rendered += "\n[$becalmed](answer withheld by the anti-spoiler rule)[/$becalmed]"
        else:
            rendered = f"[$becalmed]{reply.text}[/$becalmed]"

        self.app.call_from_thread(self._finish, rendered)

    def _finish(self, rendered: str) -> None:
        self.busy = False
        self._say(rendered)

    def _current_code(self) -> str:
        """Read the editor if there is one. The panel works without it."""
        from codequest.tui.widgets.code_editor import CodeEditor

        editors = self.screen.query(CodeEditor)
        return editors.first().text if editors else ""

    def _say(self, markup: str) -> None:
        self.query_one("#mentor-log", RichLog).write(markup)
