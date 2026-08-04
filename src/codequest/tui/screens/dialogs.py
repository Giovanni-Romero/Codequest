"""Modal dialogs.

One dialog, used wherever an action cannot be undone. Deleting a save destroys weeks of
work and resetting the editor throws away whatever the player just typed, so both ask
first — the rule is in the ``tui-developer`` skill under accessibility and feel.
"""

from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import BindingType
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmDialog(ModalScreen[bool]):
    """Asks a yes/no question and returns the answer.

    Escape cancels, which is the safe direction: a player who reaches for the exit key
    while a destructive prompt is up meant to back out, not to confirm.
    """

    BINDINGS: ClassVar[list[BindingType]] = [("escape", "dismiss_false", "Cancel")]

    def __init__(self, question: str, confirm_label: str = "Delete") -> None:
        super().__init__()
        self.question = question
        self.confirm_label = confirm_label

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog-frame"):
            yield Static(self.question, id="dialog-question")
            with Horizontal(id="dialog-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button(self.confirm_label, id="confirm", variant="error")

    def on_mount(self) -> None:
        # Focus lands on Cancel, not on the destructive button. Someone tapping Enter
        # out of habit should not lose a save.
        self.query_one("#cancel", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm")

    def action_dismiss_false(self) -> None:
        self.dismiss(False)
