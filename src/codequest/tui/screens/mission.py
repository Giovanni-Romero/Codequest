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
from codequest.tui.strings import t
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
        Binding("f2", "toggle_mentor", "Mentor", priority=True),
        Binding("f3", "toggle_teaching", "Teaching", priority=True),
        Binding("f4", "reset_editor", "Reset", priority=True),
        Binding("f6", "next_mission", "Next", priority=True),
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
                    yield Static(t("mission.teaching_title"), classes="panel-title")
                    yield Static(self._teaching_text(), id="teaching-body")
                with Vertical(id="brief", classes="panel"):
                    yield Static(t("mission.brief_title"), classes="panel-title")
                    yield Static(self.mission.brief.rstrip(), id="brief-body")
            with Vertical(id="right-column"):
                with Vertical(id="editor-panel", classes="panel"):
                    yield Static(t("mission.your_code"), classes="panel-title")
                    yield CodeEditor(self.mission.signature.stub, id="editor")
                yield Static("", id="run-status")
                with TabbedContent(id="right-tabs"):
                    with TabPane(t("mission.tab_results"), id="tab-results"):
                        yield TestResults(id="results")
                    with TabPane(t("mission.tab_hints"), id="tab-hints"):
                        yield HintPanel(id="hints")
                yield from self._compose_mentor()
        yield Footer()

    def _compose_mentor(self):
        """Yield the mentor panel, but only if the package is present and enabled.

        Two conditions, and both are load-bearing. The flag is the player's choice; the
        ImportError branch is what makes deleting ``src/codequest/mentor/`` a supported
        operation rather than a crash. Neither is a fallback for the other.
        """
        if not self.app.context.settings.mentor_enabled:
            return

        try:
            from codequest.tui.widgets.mentor_chat import MentorChat
        except ImportError:
            return

        yield MentorChat(id="mentor-panel", classes="panel")

    def on_mount(self) -> None:
        self.sub_title = t("mission.subtitle", title=self.mission.title, xp=self.mission.xp)
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
            self.query_one("#reduced-notice", Static).update(t("mission.reduced_notice"))

    def _teaching_text(self) -> str:
        teaching = self.mission.teaching
        worked_example = t("mission.worked_example")
        parts = [
            teaching.analogy.rstrip(),
            "",
            teaching.explanation.rstrip(),
            "",
            f"[$brass]{worked_example}[/$brass]",
            teaching.worked_example.rstrip(),
        ]
        if teaching.key_points:
            key_points = t("mission.key_points")
            parts += ["", f"[$brass]{key_points}[/$brass]"]
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
        self.query_one("#run-status", Static).update(f"[$beacon]{t('mission.running')}[/$beacon]")
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
        progress = t("mission.case_progress", done=done, total=total)
        self.query_one("#run-status", Static).update(f"[$beacon]{progress}[/$beacon]")

    def _show_outcome(self, outcome: AttemptOutcome) -> None:
        self.running = False
        self.query_one("#results", TestResults).show_verdict(outcome.verdict, outcome.xp_awarded)
        self.app.refresh_profile()

        # Hand the mentor the failure, if it is here. Where they got stuck is usually
        # more informative than anything they will manage to type as a question.
        mentors = self.query("#mentor-panel")
        if mentors:
            mentors.first().set_verdict(outcome.verdict)

        status = self.query_one("#run-status", Static)
        if not outcome.passed:
            status.update("")
            return

        # Passing always earns the congratulations, whatever else happened. Unlock and
        # level-up are extra headlines layered on top, not alternatives to it - a
        # replay that unlocks nothing is still a mission solved.
        parts = [t("mission.congrats")]
        if outcome.award and outcome.award.newly_unlocked:
            unlocked = ", ".join(outcome.award.newly_unlocked)
            parts.append(t("mission.unlocked", islands=unlocked))
        elif outcome.award and outcome.award.leveled_up:
            parts.append(t("mission.level_up", level=outcome.award.profile.level))

        if self.app.context.missions.next_mission_after(self.mission.id) is not None:
            parts.append(t("mission.next_hint"))

        status.update(f"[$brass]{'  -  '.join(parts)}[/$brass]")

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

    def action_toggle_mentor(self) -> None:
        """Open or close the mentor panel. A no-op when the mentor is not there."""
        panels = self.query("#mentor-panel")
        if not panels:
            return

        panel = panels.first()
        panel.toggle_class("open")
        if panel.has_class("open"):
            panel.load(self.mission, self.query_one("#hints", HintPanel).revealed)
            panel.query_one("#mentor-input").focus()

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
                t("mission.reset_confirm"),
                confirm_label=t("mission.reset_label"),
            ),
            on_answer,
        )

    def action_next_mission(self) -> None:
        """Jump straight to the next mission in the island. A no-op past the last one.

        Silent rather than an error message: F6 is always listed in the footer, and
        pressing it on the final mission of a track is not a mistake worth interrupting
        the player for.
        """
        next_mission = self.app.context.missions.next_mission_after(self.mission.id)
        if next_mission is not None:
            self.app.switch_screen(MissionScreen(next_mission))
