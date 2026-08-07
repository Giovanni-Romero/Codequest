"""Layered hints, revealed one at a time.

Three rungs, each one costing XP, and the cost is the reason the panel reveals them one
at a time instead of showing all three: a player who can see rung 3 has no reason to try
rung 1, and rung 1 is the one that teaches.

The widget only displays. Recording the reveal — and therefore charging for it — is
``ProgressService.record_hint``. The panel does not know the price, and that is correct:
the discount table lives in ``config.HINT_XP_MULTIPLIERS`` where it can be argued with.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from codequest.models.mission import Mission
from codequest.tui.strings import t

#: What each rung gives, from docs/mission-schema.md. Shown to the player before they
#: spend anything, because an informed choice is the point of a graduated cost. Values
#: are strings.py keys, translated at render time.
RUNG_LABELS = {
    1: "hints.rung_1",
    2: "hints.rung_2",
    3: "hints.rung_3",
}


class HintPanel(VerticalScroll):
    """Reveals a mission's hints in order, never out of it."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.mission: Mission | None = None
        self.revealed = 0

    def compose(self) -> ComposeResult:
        yield Static("", id="hints-body")

    def load(self, mission: Mission, already_revealed: int = 0) -> None:
        """Attach a mission and restore how many hints this save already paid for.

        Restoring matters: a player who bought two hints yesterday should not be charged
        again to see them today.
        """
        self.mission = mission
        self.revealed = min(already_revealed, len(mission.hints))
        self._refresh_body()

    def reveal_next(self) -> int | None:
        """Reveal one more rung and return its level, or ``None`` when none are left."""
        if self.mission is None or self.revealed >= len(self.mission.hints):
            return None
        self.revealed += 1
        self._refresh_body()
        return self.revealed

    @property
    def exhausted(self) -> bool:
        return self.mission is not None and self.revealed >= len(self.mission.hints)

    # ------------------------------------------------------------------ rendering

    def _refresh_body(self) -> None:
        body = self.query_one("#hints-body", Static)
        if self.mission is None:
            body.update("")
            return

        lines: list[str] = []
        total = len(self.mission.hints)

        for level in range(1, total + 1):
            hint = self.mission.hint_at(level)
            if hint is None:
                continue
            if level <= self.revealed:
                lines.append(f"[$brass]{t('hints.hint_n', n=level)}[/$brass]")
                lines.append(hint.text.rstrip())
            else:
                label = t(RUNG_LABELS.get(level, "hints.rung_other"))
                locked_hint = t("hints.locked_hint", n=level, label=label)
                lines.append(f"[$becalmed]{locked_hint}[/$becalmed]")
            lines.append("")

        if self.revealed == 0:
            lines.append(f"[$parchment-dim]{t('hints.none_revealed')}[/$parchment-dim]")
        elif self.exhausted:
            lines.append(f"[$parchment-dim]{t('hints.exhausted')}[/$parchment-dim]")

        body.update("\n".join(lines))
