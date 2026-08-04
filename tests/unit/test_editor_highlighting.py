"""Guards the syntax highlighting capability, not the import.

``from textual.widgets import TextArea`` succeeds whether or not the ``[syntax]`` extra
is installed. So does ``TextArea.code_editor(language="python")`` — it just quietly hands
back a plain Document with no highlighting, raises nothing, and warns about nothing.

That failure was live in this repository until Phase 4: ``pyproject.toml`` asked for bare
``textual``, and the editor everyone assumed was highlighted was not. These tests assert
the *capability*, which is the only version of the check that would have caught it.
"""

from __future__ import annotations

from textual.document._syntax_aware_document import SyntaxAwareDocument
from textual.widgets import TextArea


def test_the_code_editor_really_parses_python():
    """The document must be syntax-aware, not merely constructed without error."""
    editor = TextArea.code_editor("def f(x):\n    return x + 1\n", language="python")

    assert isinstance(editor.document, SyntaxAwareDocument), (
        "TextArea fell back to a plain Document. The textual[syntax] extra is missing: "
        "reinstall with pip install -e '.[dev]'"
    )


def test_the_editor_produces_highlight_spans():
    """A syntax-aware document that highlights nothing would pass the check above.

    This asserts the parse actually produced spans, which is what the player sees.
    """
    editor = TextArea.code_editor("def f(x):\n    return x + 1\n", language="python")

    assert editor._highlights, "the parser produced no highlight spans for valid Python"


def test_broken_python_does_not_crash_the_editor():
    """A player's code is broken most of the time they are looking at it.

    tree-sitter is an error-tolerant parser and this is the property being relied on: the
    editor keeps rendering while the code is halfway typed.
    """
    editor = TextArea.code_editor("def f(:\n    ret", language="python")

    assert isinstance(editor.document, SyntaxAwareDocument)
    assert editor.text.startswith("def f(:")
