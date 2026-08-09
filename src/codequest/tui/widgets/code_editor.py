"""The submission editor widget.

A thin wrapper over Textual's ``TextArea.code_editor``. Thin on purpose: the editor is
the single most complex piece of interaction in the game — cursor, selection, scrolling,
undo, copy and paste, syntax highlighting — and none of it is what this project set out
to teach. Writing one from scratch was the hidden cost that ruled out pixel graphics
(see ``PROJECT_PLAN.md`` section 7.1).

The highlighting depends on the ``textual[syntax]`` extra, which fails **silently** when
absent: you get a plain document, no error, no warning. ``tests/unit/
test_editor_highlighting.py`` asserts the capability rather than the import.
"""

from __future__ import annotations

from textual.widgets import TextArea


class CodeEditor(TextArea):
    """A Python editor pre-filled with a mission stub."""

    def __init__(self, stub: str = "", **kwargs) -> None:
        super().__init__(
            stub,
            language="python",
            show_line_numbers=True,
            soft_wrap=False,
            tab_behavior="indent",
            **kwargs,
        )
        self._stub = stub

    def reset_to_stub(self) -> None:
        """Throw away the player's work and start over from the mission's stub.

        Destructive, so the screen that calls this confirms first.
        """
        self.text = self._stub

    @property
    def is_modified(self) -> bool:
        """Whether anything has been typed since the stub was loaded.

        The editor is the only place a submission exists — nothing writes it to disk and
        the database stores verdicts, never source. So any screen that is about to unmount
        this widget has to ask this first, or the player's work is simply gone.
        """
        return self.text != self._stub

    @property
    def submission(self) -> str:
        """What the player wrote, ready to hand to the engine."""
        return self.text
