---
name: ai-mentor-integrator
description: Build and tune the optional in-game AI mentor — Ollama client, prompt design, context assembly, anti-spoiler policy, and graceful degradation. Use when working under src/codequest/mentor or on the mentor chat widget.
---

# AI Mentor Integrator

## What the mentor is, and is not

**Is:** a small chat panel in the corner. The player asks a question, it answers.
Think of a study partner sitting next to you, not the teacher.

**Is not:** the teaching system. All lessons, hints, analogies, and progression live
in the YAML content, hand written. The mentor adds nothing the game depends on.

**Hard requirement: the game must be fully playable and fully educational with Ollama
uninstalled.** If deleting `src/codequest/mentor/` breaks anything outside that folder,
the integration is wrong.

## Setup

```
Model:    gemma4:cloud
Host:     http://localhost:11434  (configurable via OLLAMA_HOST)
Endpoint: POST /api/chat
Transport: httpx, streaming responses
```

Config in `.env`, read by `config.py`. Never hardcode the host.

## Context to send

Assemble deliberately. More context is not better, it is slower and noisier.

```
System prompt      - role and the anti-spoiler policy
Mission brief      - what the player must build
Concepts           - ids and names of what this mission teaches
Player's code      - current editor content
Last verdict       - failure reason and the failing test, if any
Hints already used - so the mentor does not repeat them
Player question    - the actual message
```

Do **not** send: the mission `solution`, the hidden tests, or other missions.
Sending the solution into the context is how a spoiler leaks even with a good prompt.
Filter at the source, not in the prompt.

## The anti-spoiler policy (`mentor/policy.py`)

The system prompt states it, and code enforces what it can:

1. Never output a complete working solution to the current mission
2. Prefer a question that makes the player find the gap themselves
3. Point at the concept by name, and at where in the game it was taught
4. Illustrative code must use a different problem and different names
5. If the player insists on the answer, offer the next hint level instead

Post-filter as a second layer: if the response contains a function whose name matches
`signature.entrypoint`, replace it with a nudge. Prompt instructions are guidance, not
enforcement. Teach that distinction, it applies to every LLM feature.

## Graceful degradation

Failure is normal, not exceptional. Ollama may be off, the model may not be pulled,
the machine may be slow.

- Connection error, model missing, timeout -> panel shows a clear offline state
- Never block the game loop. Streaming, in a worker, cancellable
- No retry storms. One retry, then stop
- The game never waits on the mentor to do anything

## What Giovanni learns here

This is the bridge to the AI Engineer track. Concepts, in order:

1. Chat API shape: messages, roles, streaming versus blocking
2. Context assembly and why the window is a budget you spend
3. Prompt engineering, and its limits as a control mechanism
4. Guardrails: filter the input, filter the output, do not trust the instruction alone
5. Local models: quantization, memory cost, latency, why local is a real trade-off
6. Failure design: what a feature does when the model is unavailable

Later, when the AI Engineering track is built (v1.3), this same module becomes the
teaching example for RAG, evals, and MCP.

## Review checklist

- [ ] Nothing outside `mentor/` imports it at module scope
- [ ] Deleting the folder leaves the game working
- [ ] `solution` and hidden tests never enter the context
- [ ] Output filtered for the entrypoint name before display
- [ ] Every network failure has a defined user-visible state
- [ ] Requests are cancellable, and cancelled when the screen changes
- [ ] The client is mocked in tests, no test touches the network
