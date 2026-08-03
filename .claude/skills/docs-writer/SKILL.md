---
name: docs-writer
description: Write and maintain project documentation — README, docs/ pages, docstrings, changelog, and the mission schema reference. Use when documenting a new subsystem, updating the game manual, or preparing the repo to be read by someone else.
---

# Docs Writer

This repository is a portfolio piece. A recruiter or a hiring engineer will read the
README before reading any code. Documentation quality is part of the deliverable.

## Document map

| File | Audience | Answers |
|---|---|---|
| `README.md` | Player and visitor | What is it, how do I install it, how do I play |
| `PROJECT_PLAN.md` | Giovanni and the agent | Architecture, roadmap, decisions |
| `AGENTS.md` | AI agents | How to behave in this repo |
| `FINAL_PLAN.md` | Giovanni | Bootstrap prompt and first sessions |
| `docs/architecture.md` | Contributor | How the layers fit, why |
| `docs/mission-schema.md` | Mission author | Every field, with examples |
| `docs/curriculum/*.md` | Curriculum designer | Concept order and objectives |

Do not duplicate content across these. Link instead. Duplicated docs drift, and drifted
docs are worse than missing ones.

## README structure for a game

1. One-sentence description, then a screenshot or a terminal recording
2. What makes it different (offline, content-as-data, multi-language)
3. Install, exactly, copy-pasteable, per platform
4. How to play: first run, saves, islands, missions, hints, mentor
5. Keybindings table
6. Project status and roadmap
7. Contributing (how to add a mission)
8. Honest limitations, including the sandbox one
9. License

## Docstring rule

Document **why**, not what. The code already says what.

```python
def kill_process_tree(pid: int) -> None:
    """Kill the child and everything it spawned.

    A submission can fork. Killing only the direct child leaves orphans
    holding CPU, which shows up later as a mysteriously slow game.
    """
```

Not this:

```python
def kill_process_tree(pid: int) -> None:
    """Kills the process tree for the given pid."""
```

## Writing rules

- Short sentences. Simple words.
- Second person for instructions: "run this", not "the user should run".
- Every command copy-pasteable and actually tested.
- State limitations openly. Honest docs read as competent, not as weak.
- Prefer a table to a paragraph when comparing things.
- Keep a changelog from the first release, Keep a Changelog format.

## Before a release

- [ ] README install steps tested on a clean machine
- [ ] Every keybinding in the docs matches the code
- [ ] Mission schema doc matches the loader's actual validation
- [ ] Screenshots current
- [ ] Roadmap reflects what actually shipped
- [ ] Links resolve
