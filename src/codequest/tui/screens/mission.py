"""Mission screen: brief, teaching panel, editor and results.

The screen where the game actually happens. Three things here are worth reading before
changing anything.

**Nothing is judged here.** F5 hands the editor's contents to ``GameSession.attempt`` and
renders whatever comes back. No XP arithmetic, no unlock decision, no comparison of
expected against actual. If any of that appears in this file it is in the wrong layer.

**The run happens off the UI thread.** An attempt spawns one subprocess per test case and
takes seconds. On the main thread that is a frozen window, which reads as a crash.

**The layout reflows, it never refuses.** Three bands, from ``docs/art-direction.md``
section 5.
"""

from __future__ import annotations

from typing import ClassVar

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static, TabbedContent, TabPane

from codequest.models.mission import Mission
from codequest.services.game_session import AttemptOutcome
from codequest.tui.screens.dialogs import ConfirmDialog
from codequest.tui.widgets.code_editor import CodeEditor
from codequest.tui.widgets.hint_panel import HintPanel
from codequest.tui.widgets.test_results import TestResults

#: Column counts that separate the three layout bands. Named here rather than left as
#: numbers inside on_resize, so the rule stays comparable with the art direction.
WIDE_MIN_COLUMNS = 100
NARROW_MIN_COLUMNS = 80


class MissionScreen(Screen):
    """Teaching, brief, editor and results for one mission."""

    # priority=True on every one of these: the editor has focus almost all the time and
    # a focused TextArea swallows plain keys. Without priority the game's own controls
    # stop working the moment the player clicks into their code, which is always.
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("f5", "run", "Run", priority=True),
        Binding("f1", "hint", "Hint", priority=True),
        Binding("f3", "toggle_teaching", "Teaching", priority=True),
        Binding("ctrl+r", "reset_editor", "Reset", priority=True),
        Binding("escape", "app.pop_screen", "Map", priority=True),
    ]

    def __init__(self, mission: Mission) -> None:
        super().__init__()
        self.mission = mission
        self.running = False

    # ------------------------------------------------------------------ layout

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("", id="reduced-notice")
        with Horizontal(id="mission-body"):
            with Vertical(id="left-column"):
                with Vertical(id="teaching", classes="panel"):
                    yield Static("Teaching", classes="panel-title")
                    yield Static(self._teaching_text(), id="teaching-body")
                with Vertical(id="brief", classes="panel"):
                    yield Static("Brief", classes="panel-title")
                    yield Static(self.mission.brief.rstrip(), id="brief-body")
            with Vertical(id="right-column"):
                with Vertical(id="editor-panel", classes="panel"):
                    yield Static("Your code", classes="panel-title")
                    yield CodeEditor(self.mission.signature.stub, id="editor")
                yield Static("", id="run-status")
                with TabbedContent(id="right-tabs"):
                    with TabPane("Results", id="tab-results"):
                        yield TestResults(id="results")
                    with TabPane("Hints", id="tab-hints"):
                        yield HintPanel(id="hints")
        yield Footer()

    def on_mount(self) -> None:
        self.sub_title = f"{self.mission.title}  -  {self.mission.xp} XP"
        self.query_one("#hints", HintPanel).load(self.mission, self._hints_already_used())
        self.query_one("#editor", CodeEditor).focus()
        self._apply_band(self.size.width)

    def on_resize(self) -> None:
        self._apply_band(self.size.width)

    def _apply_band(self, width: int) -> None:
        """Pick a layout band. Never a refusal to run, only a reflow."""
        self.set_class(NARROW_MIN_COLUMNS <= width < WIDE_MIN_COLUMNS, "narrow")
        self.set_class(width < NARROW_MIN_COLUMNS, "tiny")

        if width < NARROW_MIN_COLUMNS:
            self.query_one("#reduced-notice", Static).update(
                "  Narrow terminal: teaching and brief are in the tabs. Widen to see all panels."
            )

    def _teaching_text(self) -> str:
        teaching = self.mission.teaching
        parts = [
            teaching.analogy.rstrip(),
            "",
            teaching.explanation.rstrip(),
            "",
            "[$brass]Worked example[/$brass]",
            teaching.worked_example.rstrip(),
        ]
        if teaching.key_points:
            parts += ["", "[$brass]Key points[/$brass]"]
            parts += [f"  - {point}" for point in teaching.key_points]
        return "\n".join(parts)

    def _hints_already_used(self) -> int:
        profile = self.app.profile
        if profile is None:
            return 0
        record = self.app.context.progress.progress_for(profile).get(self.mission.id)
        return record.hints_used if record else 0

    # ------------------------------------------------------------------ running

    def action_run(self) -> None:
        """Judge the current editor contents. Ignored while a run is already going."""
        if self.running:
            return
        self.running = True
        self.query_one("#right-tabs", TabbedContent).active = "tab-results"
        self.query_one("#run-status", Static).update("[$beacon]running...[/$beacon]")
        self._run_attempt(self.query_one("#editor", CodeEditor).submission)

    @work(thread=True, exclusive=True)
    def _run_attempt(self, code: str) -> None:
        """Run the attempt on a worker thread.

        One subprocess per test case takes seconds. On the UI thread that is a frozen
        window, and a frozen window reads as a crash rather than as work in progress.
        """
        context = self.app.context
        total = len(self.mission.tests)

        def report(done: int, _total: int) -> None:
            # Widgets may only be touched from the UI thread, so hop back for each update.
            self.app.call_from_thread(self._show_progress, done, total)

        outcome = context.session.attempt(
            self.mission,
            code,
            self.app.profile,
            context.missions.islands,
            on_case=report,
        )
        self.app.call_from_thread(self._show_outcome, outcome)

    def _show_progress(self, done: int, total: int) -> None:
        self.query_one("#results", TestResults).show_waiting(done, total)
        self.query_one("#run-status", Static).update(f"[$beacon]case {done} of {total}[/$beacon]")

    def _show_outcome(self, outcome: AttemptOutcome) -> None:
        self.running = False
        self.query_one("#results", TestResults).show_verdict(outcome.verdict, outcome.xp_awarded)
        self.app.refresh_profile()

        status = self.query_one("#run-status", Static)
        if outcome.award and outcome.award.newly_unlocked:
            unlocked = ", ".join(outcome.award.newly_unlocked)
            status.update(f"[$brass]Unlocked: {unlocked}[/$brass]")
        elif outcome.award and outcome.award.leveled_up:
            status.update(f"[$brass]Level {outcome.award.profile.level}![/$brass]")
        else:
            status.update("")

    # ------------------------------------------------------------------ hints

    def action_hint(self) -> None:
        """Reveal the next rung, and record it so the XP cost is charged."""
        panel = self.query_one("#hints", HintPanel)
        self.query_one("#right-tabs", TabbedContent).active = "tab-hints"

        level = panel.reveal_next()
        if level is None:
            return

        profile = self.app.profile
        if profile is not None:
            self.app.context.progress.record_hint(profile, self.mission)

    def action_toggle_teaching(self) -> None:
        panel = self.query_one("#teaching", Vertical)
        panel.display = not panel.display

    def action_reset_editor(self) -> None:
        """Throw away the player's work. Destructive, so it asks first."""

        def on_answer(confirmed: bool | None) -> None:
            if confirmed:
                self.query_one("#editor", CodeEditor).reset_to_stub()

        self.app.push_screen(
            ConfirmDialog(
                "Reset the editor to the original stub?\n\n"
                "[$parchment-dim]Everything you have typed is discarded.[/$parchment-dim]",
                confirm_label="Reset",
            ),
            on_answer,
        )
