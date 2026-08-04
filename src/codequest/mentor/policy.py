"""Anti-spoiler policy: the mentor asks questions, it never hands over code.

Two layers, and the reason there are two is the whole lesson of this module.

**Layer one, at the source.** The mission's ``solution`` and its hidden test cases are
never put into the context. Not filtered out later, not discouraged in the prompt —
simply never assembled. A model cannot leak what it was not given.

**Layer two, on the output.** Whatever comes back is inspected for a definition of the
mission's entrypoint, and replaced if it appears.

# [AI-ENG:guardrails] Layer one is a *control*. Layer two is a *control*. The sentence in
# the system prompt asking the model not to give the answer is neither — it is guidance,
# and it works most of the time, which is the dangerous kind of working.
#
# This is the distinction to carry into every LLM feature: a prompt shifts probability, a
# filter decides. Anything you must guarantee needs code on one side of the model or the
# other. Anything you merely prefer can live in the prompt.
"""

from __future__ import annotations

import re

#: What the player sees instead of a leaked solution. Written as a nudge rather than a
#: refusal: the player asked a fair question and deserves a route forward, just not this
#: one.
REDACTION = (
    "I nearly wrote the answer out for you, which would take the mission away from you.\n\n"
    "Look at the hint panel instead - the next rung is written for exactly this moment. "
    "And tell me in your own words what your function should return for the smallest "
    "possible input; that is usually where the gap is."
)


def build_system_prompt(entrypoint: str) -> str:
    """The mentor's standing instructions.

    Guidance, not enforcement. It reduces how often the model reaches for the answer; the
    filter below is what makes the guarantee.
    """
    return (
        "You are a study partner sitting next to a beginner programmer inside a game "
        "called CodeQuest. You are not the teacher: the lesson, the analogy and the "
        "hints are already written and the player has them.\n\n"
        "How you help:\n"
        "- Ask the question that makes them notice the gap themselves.\n"
        "- Name the concept, and say it was covered in the teaching panel.\n"
        "- If you show code, use a different problem and different names.\n"
        f"- Never write a function called '{entrypoint}'. That is the mission.\n"
        "- If they ask outright for the answer, say no once, kindly, and point at the "
        "next hint.\n\n"
        "Keep replies under 120 words. You are a nudge, not a lecture."
    )


def defines_entrypoint(text: str, entrypoint: str) -> bool:
    """Whether ``text`` contains a definition of the mission's entrypoint.

    Matches ``def name(`` at any indentation, in any code fence, which is the shape a
    leaked solution actually takes. Deliberately narrow: a mentor that says the words
    "sum_list" while asking a question is being helpful, and only a *definition* hands
    over the work.
    """
    pattern = rf"^\s*(?:async\s+)?def\s+{re.escape(entrypoint)}\s*\("
    return re.search(pattern, text, re.MULTILINE) is not None


def filter_reply(text: str, entrypoint: str) -> tuple[str, bool]:
    """Screen a reply before it reaches the player.

    Returns:
        The text to display and whether it was redacted. The caller wants the flag: a
        redaction is worth logging, because a policy that fires constantly is a prompt
        that needs fixing.
    """
    if defines_entrypoint(text, entrypoint):
        return REDACTION, True
    return text, False


def is_safe_context(payload: str, mission_solution: str, hidden_values: list[str]) -> bool:
    """Assert that nothing forbidden made it into the assembled context.

    Belt and braces over the filtering that already happened at assembly time. Cheap, and
    the failure it guards against — a refactor quietly widening what gets sent — is
    exactly the kind that survives code review.
    """
    if mission_solution.strip() and mission_solution.strip() in payload:
        return False
    return all(not (value and value in payload) for value in hidden_values)
