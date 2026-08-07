"""Renders a Verdict as a readable test report.

The widget renders; it never judges. Every sentence shown here was written by
``engine/evaluator.py``, which is the module that owns the failure taxonomy and the
wording that goes with it. If a message needs improving, it gets improved there — putting
a second opinion in the UI is how two parts of a program start disagreeing about what
happened.

The one rule this widget must not break: a hidden case never displays its expected value.
The evaluator already withholds it, and nothing here reaches around that.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from codequest.models.verdict import FailureReason, Verdict
from codequest.tui.strings import t
from codequest.tui.symbols import FAIL, NOT_RUN, PASS


class TestResults(VerticalScroll):
    """The results panel of the mission screen."""

    def compose(self) -> ComposeResult:
        yield Static(t("results.press_f5"), classes="muted", id="results-body")

    def clear(self) -> None:
        self.query_one("#results-body", Static).update("")

    def show_waiting(self, done: int, total: int) -> None:
        """Determinate progress: the engine knows the total, so never a spinner."""
        self.query_one("#results-body", Static).update(
            t("results.running_case", done=done, total=total)
        )

    def show_verdict(self, verdict: Verdict, xp_awarded: int = 0) -> None:
        """Render a finished attempt."""
        self.query_one("#results-body", Static).update(self._format_verdict(verdict, xp_awarded))

    # ------------------------------------------------------------------ rendering

    def _format_verdict(self, verdict: Verdict, xp_awarded: int) -> str:
        lines: list[str] = []

        headline = t("results.passed") if verdict.passed else t("results.failed")
        style = "pass" if verdict.passed else "fail"
        lines.append(f"[{style}]{headline}[/{style}]  {verdict.summary}")
        lines.append("")

        # A rejection before execution has no cases to list, so show why and stop.
        if not verdict.outcomes:
            if verdict.reason is not FailureReason.PASSED:
                reason = t("results.reason", reason=verdict.reason.value)
                lines.append(f"[$becalmed]{reason}[/$becalmed]")
            return "\n".join(lines)

        for outcome in verdict.outcomes:
            if outcome.passed:
                mark, mark_style = PASS, "pass"
            elif outcome.reason is FailureReason.NOT_RUN:
                mark, mark_style = NOT_RUN, "locked"
            else:
                mark, mark_style = FAIL, "fail"

            kind = t("results.visible") if outcome.visible else t("results.hidden")
            case = t("results.case", n=outcome.index + 1, kind=kind)
            lines.append(f"[{mark_style}]{mark}[/{mark_style}] {case}")
            if outcome.detail and not outcome.passed:
                lines.append(f"    [$parchment-dim]{outcome.detail}[/$parchment-dim]")

        if verdict.stdout:
            lines.append("")
            lines.append(f"[$brass]{t('results.your_output')}[/$brass]")
            for line in verdict.stdout.rstrip().splitlines():
                lines.append(f"    {line}")

        if xp_awarded:
            lines.append("")
            lines.append(f"[$beacon]{t('results.xp_gained', xp=xp_awarded)}[/$beacon]")
        elif verdict.passed:
            lines.append("")
            lines.append(f"[$parchment-dim]{t('results.already_completed')}[/$parchment-dim]")

        return "\n".join(lines)
