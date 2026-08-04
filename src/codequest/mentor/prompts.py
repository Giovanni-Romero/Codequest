"""Prompt templates for the mentor.

Context assembly, and the thing worth internalising here is that assembly is *editing*,
not collecting.

# [AI-ENG:context-assembly] More context is not better context. Every token spent on
# something the model does not need is a token of attention taken from something it does,
# plus latency and money. The discipline is to decide what earns its place, per field,
# and to be able to say why.
#
# The second half is what is deliberately left out. The mission's solution and its hidden
# tests are excluded *here*, at assembly, not filtered later — filtering at the source is
# the only version that cannot be undone by a careless edit downstream.
"""

from __future__ import annotations

from dataclasses import dataclass

from codequest.mentor.policy import build_system_prompt
from codequest.models.mission import Mission
from codequest.models.verdict import FailureReason, Verdict

#: The player's code is sent whole up to this size, then truncated from the middle. A
#: beginner solution is never near this; a runaway paste is, and it would blow the window
#: for nothing.
MAX_CODE_CHARS = 4_000


@dataclass(frozen=True, slots=True)
class MentorContext:
    """Everything the mentor is allowed to know about the current moment."""

    mission: Mission
    code: str
    verdict: Verdict | None = None
    hints_used: int = 0


def _truncate(text: str, limit: int = MAX_CODE_CHARS) -> str:
    if len(text) <= limit:
        return text
    head = text[: limit // 2]
    tail = text[-limit // 2 :]
    return f"{head}\n\n... [middle omitted] ...\n\n{tail}"


def _describe_verdict(verdict: Verdict | None) -> str:
    """Summarise the last attempt without disclosing a hidden case's expected value.

    The evaluator already withholds it, and this reads only from the failure it produced,
    so the restriction holds by construction rather than by remembering to be careful.
    """
    if verdict is None:
        return "They have not run their code yet."

    if verdict.passed:
        return "Their last run passed every test."

    failure = verdict.first_failure
    if failure is None:
        return f"Their last run failed: {verdict.reason.value}."

    if verdict.reason is FailureReason.FORBIDDEN_CONSTRUCT:
        return f"Their code was rejected before running: {verdict.summary}"

    where = "a visible test" if failure.visible else "a hidden test"
    return f"Their last run failed on {where}. {failure.detail}"


def build_messages(context: MentorContext, question: str) -> list[dict[str, str]]:
    """Assemble the chat messages for one question.

    What goes in, and why each field earns its place:

    - **system** — the role and the standing policy
    - **brief** — without it the mentor cannot tell right from wrong
    - **concepts** — lets it name what was taught instead of inventing vocabulary
    - **player code** — the actual subject of nearly every question
    - **last verdict** — where they are stuck, which is usually the whole answer
    - **hints used** — so it does not repeat a rung they already paid for

    What stays out, on purpose: ``mission.solution`` and the hidden test cases.
    """
    mission = context.mission
    concepts = ", ".join(mission.concepts) or "none listed"

    visible_cases = "\n".join(f"  {case.args} -> {case.expect!r}" for case in mission.visible_tests)

    user_content = (
        f"Mission: {mission.title}\n"
        f"Concepts it teaches: {concepts}\n\n"
        f"Brief:\n{mission.brief.strip()}\n\n"
        f"Example cases the player can see:\n{visible_cases}\n\n"
        f"Their current code:\n```python\n{_truncate(context.code).strip()}\n```\n\n"
        f"{_describe_verdict(context.verdict)}\n"
        f"Hints already revealed: {context.hints_used} of {len(mission.hints)}.\n\n"
        f"Their question: {question}"
    )

    return [
        {"role": "system", "content": build_system_prompt(mission.signature.entrypoint)},
        {"role": "user", "content": user_content},
    ]


def forbidden_strings(mission: Mission) -> list[str]:
    """Values that must never appear in an assembled context.

    Used by ``policy.is_safe_context`` and by the tests. Hidden expectations are the
    interesting half: a leaked expected value turns the hidden suite into a lookup table.
    """
    values = [repr(case.expect) for case in mission.hidden_tests]
    return [value for value in values if len(value) > 2]
