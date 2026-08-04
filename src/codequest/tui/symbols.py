"""The character vocabulary, in one place.

``docs/art-direction.md`` fixes these so two screens built a month apart do not disagree.
Keeping them as named constants rather than literals scattered through the widgets is
what makes that enforceable — and what makes a single edit change every screen at once.

The rule that governs all of them: **colour never carries meaning alone.** Every state
symbol below is paired with a colour class in ``styles.tcss``, never replaced by one.
That covers colour blindness and a monochrome terminal.
"""

from __future__ import annotations

from codequest.models.profile import MissionStatus

# --------------------------------------------------------------------- state

PASS = "✔"  # heavy check
FAIL = "✘"  # heavy ballot X
NOT_RUN = "·"  # middle dot
CURRENT = "▸"  # small right-pointing triangle
AVAILABLE = "◇"  # white diamond
#: A small square rather than a padlock emoji: emoji width is inconsistent across
#: terminal fonts, and a double-width glyph breaks column alignment.
LOCKED = "▪"

# ---------------------------------------------------------------------- map

SEA = "≈"
ISLAND = "▲"
ISLAND_CURRENT = "◆"
ROUTE = "┈"

# ----------------------------------------------------------------- progress

#: Eighth-blocks give a bar eight times the resolution of a cell, so a 10-cell bar has
#: 80 steps and progress never looks stuck.
EIGHTHS = ("", "▏", "▎", "▍", "▌", "▋", "▊", "▉")
FULL_BLOCK = "█"
EMPTY_CELL = "·"

STATUS_SYMBOL: dict[MissionStatus, str] = {
    MissionStatus.COMPLETED: PASS,
    MissionStatus.ATTEMPTED: CURRENT,
    MissionStatus.AVAILABLE: AVAILABLE,
    MissionStatus.LOCKED: LOCKED,
}

STATUS_CLASS: dict[MissionStatus, str] = {
    MissionStatus.COMPLETED: "pass",
    MissionStatus.ATTEMPTED: "accent",
    MissionStatus.AVAILABLE: "muted",
    MissionStatus.LOCKED: "locked",
}


def progress_bar(done: int, total: int, width: int = 12) -> str:
    """Render a proportional bar using eighth-blocks.

    Args:
        done: How many units are complete.
        total: How many there are. Zero yields an empty bar rather than dividing by it.
        width: Bar width in cells.

    Returns:
        A string exactly ``width`` cells wide.
    """
    if total <= 0 or width <= 0:
        return EMPTY_CELL * max(width, 0)

    filled_eighths = round(min(done / total, 1.0) * width * 8)
    whole, remainder = divmod(filled_eighths, 8)

    bar = FULL_BLOCK * whole
    if remainder and whole < width:
        bar += EIGHTHS[remainder]
    return bar.ljust(width, EMPTY_CELL)[:width]
