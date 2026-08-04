"""Tests for the optional mentor.

Nothing here touches the network. Every client test drives a mocked transport, which is
the rule from the ``test-engineer`` skill and also the only way these run in CI at all.

The tests that matter most are not about the happy path. They are about the two things
the mentor must never do: leak the solution, and take the game down with it.
"""

from __future__ import annotations

import httpx
import pytest

from codequest.mentor.client import MentorState, OllamaClient
from codequest.mentor.policy import (
    REDACTION,
    build_system_prompt,
    defines_entrypoint,
    filter_reply,
    is_safe_context,
)
from codequest.mentor.prompts import MentorContext, build_messages, forbidden_strings
from codequest.models.mission import Signature, TestCase
from codequest.models.verdict import CaseOutcome, FailureReason, Verdict
from conftest import make_mission

MISSION = make_mission(
    signature=Signature("sum_list", "def sum_list(numbers):\n    pass\n"),
    solution="def sum_list(numbers):\n    total = 0\n    for n in numbers:\n        total += n\n    return total\n",
    tests=(
        TestCase(args=([1, 2, 3],), expect=6, visible=True),
        TestCase(args=([],), expect=987654, visible=False),
    ),
)


def _client_with(handler) -> OllamaClient:
    """An OllamaClient whose HTTP calls are answered by ``handler``.

    Patched at the httpx level rather than at our own method, so the test exercises the
    real status-code and JSON handling instead of a stub of it.
    """
    client = OllamaClient(host="http://testhost:11434", model="test-model")
    transport = httpx.MockTransport(handler)

    def post(url, **kwargs):
        with httpx.Client(transport=transport) as inner:
            return inner.post(url, **kwargs)

    client._post = post  # type: ignore[attr-defined]
    return client


# ----------------------------------------------------------------- the policy


def test_a_reply_defining_the_entrypoint_is_replaced():
    """The guarantee. A prompt asking nicely is not one; this is."""
    reply = "Here you go:\n\n```python\ndef sum_list(numbers):\n    return sum(numbers)\n```"

    text, redacted = filter_reply(reply, "sum_list")

    assert redacted
    assert text == REDACTION
    assert "def sum_list" not in text


def test_an_indented_definition_is_still_caught():
    reply = "```python\n    def sum_list(xs):\n        return 0\n```"

    _, redacted = filter_reply(reply, "sum_list")

    assert redacted


def test_an_async_definition_is_still_caught():
    _, redacted = filter_reply("async def sum_list(xs):\n    return 0", "sum_list")

    assert redacted


def test_merely_naming_the_function_is_allowed():
    """A mentor that cannot say the function's name cannot ask a useful question."""
    reply = "What should sum_list return when the list is empty?"

    text, redacted = filter_reply(reply, "sum_list")

    assert not redacted
    assert text == reply


def test_a_different_function_is_allowed():
    """Rung 3 of a hint shows the pattern on another problem. So may the mentor."""
    reply = (
        "The shape is:\n\n```python\ndef count_letters(word):\n    total = 0\n    return total\n```"
    )

    _, redacted = filter_reply(reply, "sum_list")

    assert not redacted


def test_the_system_prompt_names_the_forbidden_function():
    """Guidance, not enforcement — but guidance that is specific works better."""
    prompt = build_system_prompt("sum_list")

    assert "sum_list" in prompt
    assert "study partner" in prompt


@pytest.mark.parametrize("entrypoint", ["sum_list", "f", "count_vowels"])
def test_defines_entrypoint_needs_a_definition_not_a_mention(entrypoint):
    assert not defines_entrypoint(f"think about {entrypoint} carefully", entrypoint)
    assert defines_entrypoint(f"def {entrypoint}(x):\n    pass", entrypoint)


# ---------------------------------------------------------- context assembly


def test_the_solution_never_enters_the_context():
    """Filtered at the source. A model cannot leak what it was never given."""
    messages = build_messages(MentorContext(mission=MISSION, code="def sum_list(n): pass"), "help")

    payload = " ".join(message["content"] for message in messages)

    assert "total = 0" not in payload
    assert is_safe_context(payload, MISSION.solution, forbidden_strings(MISSION))


def test_hidden_expectations_never_enter_the_context():
    """A leaked expected value turns the hidden suite into a lookup table."""
    messages = build_messages(MentorContext(mission=MISSION, code=""), "help")

    payload = " ".join(message["content"] for message in messages)

    assert "987654" not in payload


def test_visible_cases_do_enter_the_context():
    """They are already on the player's screen, so withholding them helps nobody."""
    messages = build_messages(MentorContext(mission=MISSION, code=""), "help")

    payload = " ".join(message["content"] for message in messages)

    assert "[1, 2, 3]" in payload


def test_the_context_carries_where_the_player_got_stuck():
    verdict = Verdict(
        mission_id=MISSION.id,
        passed=False,
        reason=FailureReason.WRONG_ANSWER,
        summary="1 of 2 cases passed.",
        outcomes=(
            CaseOutcome(0, True, False, FailureReason.WRONG_ANSWER, "Expected 6, got None."),
        ),
    )

    messages = build_messages(MentorContext(mission=MISSION, code="", verdict=verdict), "why?")

    assert "Expected 6, got None." in messages[-1]["content"]


def test_a_hidden_failure_reaches_the_mentor_without_its_value():
    verdict = Verdict(
        mission_id=MISSION.id,
        passed=False,
        reason=FailureReason.WRONG_ANSWER,
        summary="failed",
        outcomes=(
            CaseOutcome(1, False, False, FailureReason.WRONG_ANSWER, "A hidden case failed."),
        ),
    )

    messages = build_messages(MentorContext(mission=MISSION, code="", verdict=verdict), "why?")
    payload = messages[-1]["content"]

    assert "hidden test" in payload
    assert "987654" not in payload


def test_hints_already_used_are_reported_so_they_are_not_repeated():
    messages = build_messages(MentorContext(mission=MISSION, code="", hints_used=2), "help")

    assert "Hints already revealed: 2" in messages[-1]["content"]


def test_enormous_pasted_code_is_truncated():
    """A runaway paste would blow the context window for nothing."""
    messages = build_messages(MentorContext(mission=MISSION, code="x = 1\n" * 5000), "help")

    assert "middle omitted" in messages[-1]["content"]


# --------------------------------------------------------------- the client


def test_a_successful_reply_comes_back_ready(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {"content": "  What ends your loop?  "}})

    monkeypatch.setattr(
        httpx,
        "post",
        lambda url, **kw: httpx.MockTransport(handler).handle_request(httpx.Request("POST", url)),
    )
    client = OllamaClient(host="http://testhost:11434", model="test-model")

    reply = client.chat([{"role": "user", "content": "hi"}])

    assert reply.ok
    assert reply.text == "What ends your loop?"


def test_a_refused_connection_becomes_offline_not_an_exception(monkeypatch):
    """The mentor is optional. A feature that can crash the game is not optional."""

    def explode(url, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "post", explode)
    client = OllamaClient(host="http://testhost:11434")

    reply = client.chat([])

    assert reply.state is MentorState.OFFLINE
    assert "ollama serve" in reply.text
    assert "testhost" in reply.text


def test_a_timeout_has_its_own_state(monkeypatch):
    def slow(url, **kwargs):
        raise httpx.ReadTimeout("too slow")

    monkeypatch.setattr(httpx, "post", slow)

    reply = OllamaClient().chat([])

    assert reply.state is MentorState.TIMED_OUT


def test_a_missing_model_is_told_apart_from_a_missing_server(monkeypatch):
    """Different problems deserve different sentences. 404 means pull the model."""
    monkeypatch.setattr(
        httpx, "post", lambda url, **kw: httpx.Response(404, request=httpx.Request("POST", url))
    )

    reply = OllamaClient(model="gemma4:cloud").chat([])

    assert reply.state is MentorState.MODEL_MISSING
    assert "ollama pull gemma4:cloud" in reply.text


def test_malformed_json_is_an_error_state_not_a_crash(monkeypatch):
    monkeypatch.setattr(
        httpx,
        "post",
        lambda url, **kw: httpx.Response(200, text="not json", request=httpx.Request("POST", url)),
    )

    reply = OllamaClient().chat([])

    assert reply.state is MentorState.ERROR


def test_availability_probe_answers_false_when_nothing_is_listening(monkeypatch):
    def explode(url, **kwargs):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(httpx, "get", explode)

    assert OllamaClient().is_available() is False


def test_every_failure_state_has_a_message():
    """A state with no sentence would reach the player as an empty panel."""
    from codequest.mentor.client import STATE_MESSAGES

    failures = set(MentorState) - {MentorState.READY, MentorState.THINKING}

    assert failures <= set(STATE_MESSAGES)
