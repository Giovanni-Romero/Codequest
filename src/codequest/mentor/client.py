"""Ollama HTTP client. Degrades to offline instead of raising.

# [AI-ENG:graceful-degradation] Every method here returns a state; none of them raise for
# a network condition. That is a design decision, not defensive habit: the mentor is
# optional, and a feature that can take the game down with it is no longer optional.
#
# The generalisation is that for an LLM feature, **failure is a normal branch, not an
# exception**. The model being down, the model being slow, the model not being pulled,
# the machine being out of memory — all are Tuesday. Deciding up front what the user sees
# in each of those states is part of designing the feature, not something to bolt on after
# the first outage.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum

import httpx


class MentorState(StrEnum):
    """What the mentor panel should be showing."""

    READY = "ready"
    THINKING = "thinking"
    OFFLINE = "offline"
    MODEL_MISSING = "model_missing"
    TIMED_OUT = "timed_out"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class MentorReply:
    """One answer, or one explanation of why there is no answer."""

    text: str
    state: MentorState

    @property
    def ok(self) -> bool:
        return self.state is MentorState.READY


#: What the player reads in each failure state. Written as information rather than
#: apology: "mentor offline" plus how to fix it beats "something went wrong".
STATE_MESSAGES = {
    MentorState.OFFLINE: (
        "Mentor offline. Ollama is not answering on {host}.\n"
        "Start it with `ollama serve`, or keep playing - the game teaches without it."
    ),
    MentorState.MODEL_MISSING: (
        "Mentor offline. Ollama is running but the model `{model}` is not installed.\n"
        "Install it with `ollama pull {model}`."
    ),
    MentorState.TIMED_OUT: (
        "The mentor took too long and was cancelled. A smaller model answers faster."
    ),
    MentorState.ERROR: "The mentor hit an error and has been switched off for this run.",
}


class OllamaClient:
    """A small, cancellable client for Ollama's chat endpoint."""

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "gemma4:cloud",
        timeout_seconds: int = 30,
    ) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    # --------------------------------------------------------------------- probe

    def is_available(self) -> bool:
        """Whether Ollama answers at all. Short timeout: this runs on a screen open."""
        try:
            response = httpx.get(f"{self.host}/api/tags", timeout=2.0)
        except httpx.HTTPError:
            return False
        return response.status_code == 200

    # ---------------------------------------------------------------------- chat

    def chat(self, messages: list[dict[str, str]]) -> MentorReply:
        """Ask once and wait for the whole answer.

        Never raises for a network condition. One attempt, no retry: a mentor that
        hammers a machine already struggling to serve a local model makes things worse,
        and the player is one keystroke from asking again themselves.
        """
        payload = {"model": self.model, "messages": messages, "stream": False}

        try:
            response = httpx.post(
                f"{self.host}/api/chat", json=payload, timeout=self.timeout_seconds
            )
        except httpx.TimeoutException:
            return self._failure(MentorState.TIMED_OUT)
        except httpx.HTTPError:
            return self._failure(MentorState.OFFLINE)

        if response.status_code == 404:
            # Ollama answers 404 for an unknown model, which is a different problem from
            # being down and deserves a different sentence.
            return self._failure(MentorState.MODEL_MISSING)
        if response.status_code >= 400:
            return self._failure(MentorState.ERROR)

        try:
            content = response.json()["message"]["content"]
        except (ValueError, KeyError):
            return self._failure(MentorState.ERROR)

        return MentorReply(text=content.strip(), state=MentorState.READY)

    def stream(self, messages: list[dict[str, str]]) -> Iterator[str]:
        """Yield the answer in pieces, so the panel fills instead of hanging.

        Yields nothing at all on failure. The caller checks ``is_available`` first and
        renders the state; a generator is the wrong place to report an error.
        """
        payload = {"model": self.model, "messages": messages, "stream": True}
        try:
            with httpx.stream(
                "POST", f"{self.host}/api/chat", json=payload, timeout=self.timeout_seconds
            ) as response:
                if response.status_code >= 400:
                    return
                for line in response.iter_lines():
                    if not line:
                        continue
                    chunk = self._parse_chunk(line)
                    if chunk:
                        yield chunk
        except httpx.HTTPError:
            return

    @staticmethod
    def _parse_chunk(line: str) -> str:
        import json

        try:
            data = json.loads(line)
        except ValueError:
            return ""
        return data.get("message", {}).get("content", "")

    def _failure(self, state: MentorState) -> MentorReply:
        template = STATE_MESSAGES[state]
        return MentorReply(
            text=template.format(host=self.host, model=self.model),
            state=state,
        )
