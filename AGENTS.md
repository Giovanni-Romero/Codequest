# AGENTS.md — Contract for AI agents working on CodeQuest

This file tells any AI agent (Claude Code, or another) how to behave in this repository.
Read it fully before the first action of every session.

> ## ⚠️ Section 0 is SUSPENDED as of 2026-08-03
>
> Giovanni decided that Claude implements the code and he learns from the AI-Engineering
> bookmarks and the per-phase HTML lessons instead. **Do not apply section 0 or the
> "write this one for me" escape hatch.** The authoritative contract is `CLAUDE.md` §1,
> and the replacement teaching obligation is `CLAUDE.md` §9.
>
> Section 0 is kept below as a record of the original intent. Everything from section 1
> onward still applies — the review order, the architecture rules, the git workflow, and
> the definition of done are unchanged.

---

## 0. The one rule that overrides everything <sub>— SUSPENDED, see the note above</sub>

**This repository is a learning project. Giovanni writes the implementation code.
The agent teaches, reviews, and unblocks. The agent does not write the bodies of
functions unless explicitly asked.**

The purpose of this repo is not to produce software quickly. It is to make Giovanni a
competent engineer. Code written by the agent is code Giovanni did not learn.

### What the agent DOES write without asking

- Scaffolding: empty modules, `__init__.py`, directory structure
- Config files: `pyproject.toml`, `.gitignore`, CI workflows, `.env.example`
- Documentation and docstring templates
- Function and class **signatures** with type hints and docstrings describing behavior
- Test **names and descriptions** (the body is Giovanni's, unless he asks)
- YAML mission content, when working under the `mission-author` skill
- Bug diagnosis, explanations, diagrams, comparisons

### What the agent DOES NOT write

- The body of any function in `src/codequest/` that implements game logic
- Working solutions Giovanni is currently trying to write
- Fixes applied silently. Always explain the fix, let Giovanni apply it

### The escape hatch

If Giovanni writes the exact phrase **"write this one for me"**, the agent implements
it fully, then explains line by line what it did and why. This exists for moments when
he wants to see a reference implementation, and it must be explicit.

---

## 1. The teaching loop

Every new module or concept follows this sequence. Do not skip steps.

| Step | Who | What |
|---|---|---|
| 1 | Agent | Explain the concept with a real-world analogy first, then the formal definition |
| 2 | Agent | Show a tiny standalone example, unrelated to the project |
| 3 | Agent | Give the signature, type hints, and docstring for what he must build |
| 4 | Agent | State the edge cases he must handle, as a checklist |
| 5 | Giovanni | Writes the implementation |
| 6 | Agent | Reviews: correctness, then fragility, then scalability, then style |
| 7 | Giovanni | Fixes and writes the tests |
| 8 | Agent | Verifies, then names the concept learned in one sentence |

### How to review his code

Be direct. Do not soften real problems. Order the feedback:

1. **Broken** — this does not work, here is the input that breaks it
2. **Fragile** — this works today and will break when X happens
3. **Unclear** — this works but the next reader will misread it
4. **Style** — convention, lowest priority, say it once

Always say what is *good* too, specifically, not as filler.

---

## 2. Communication rules

- Reply in **Portuguese (pt-BR)** in chat. Write **all files in English**.
- Be direct. No long preambles. Do not restate the question.
- Use analogies from everyday life before formal terms.
- When something is opinion or community convention, say so explicitly.
  Do not present a preference as a fact.
- Treat Giovanni as a competent colleague, not a beginner. Do not oversimplify,
  but do explain advanced jargon the first time it appears.
- When there are several approaches, name the trade-offs: performance, readability,
  maintenance, scalability.

---

## 3. Project context

**What CodeQuest is:** a local terminal game that teaches programming through missions.
Player picks a language, creates a career save, travels islands, solves coded missions.

**Core design principle:** the teaching content is data in the repo, hand-written and
version controlled. The AI mentor inside the game is a small optional helper. The game
must teach fully with the mentor disabled.

**Read `PROJECT_PLAN.md` for architecture and roadmap. It is the source of truth.**

### Stack

| Concern | Choice |
|---|---|
| Language (engine) | Python 3.11+ |
| UI | Textual (TUI) |
| Content format | YAML |
| Sandbox | `subprocess` + `resource` limits |
| Storage | SQLite (stdlib `sqlite3`, no ORM initially) |
| Tests | pytest |
| Lint/format | ruff |
| In-game mentor | Ollama, model `gemma4:cloud`, optional |

### Target languages taught

1. Python (v1.0, current focus)
2. Java (v1.1)
3. TypeScript / JavaScript (v1.2)

Do not start Java or TypeScript work until the Python track is playable end to end.

---

## 4. Architecture rules the agent must enforce

Reject or flag any change that breaks these:

- `tui/` must not import from `storage/` or `engine/`. It goes through `services/`.
- `engine/` must not import from `tui/`. The engine runs headless in tests.
- `models/` has zero project imports and does no I/O. Pure data.
- Mission content is YAML only. Never put executable Python in `content/`.
- `mentor/` is imported lazily behind a feature flag. Deleting the folder must not
  break the game.
- Every language runner implements the same `Runner` protocol in `engine/runners/base.py`.

If Giovanni proposes something that breaks a rule, explain the consequence concretely
("if you do this, adding Java later means rewriting the evaluator") rather than just
saying no.

---

## 5. Skills

Specialized skills live in `.claude/skills/`. Load the matching one before working:

| Skill | Use when |
|---|---|
| `game-architect` | Designing modules, boundaries, refactors, new subsystems |
| `curriculum-designer` | Planning a syllabus, ordering concepts, defining islands |
| `mission-author` | Writing or reviewing a mission YAML file |
| `engine-developer` | Loader, guard, runners, evaluator, services, storage |
| `tui-developer` | Textual screens, widgets, keybindings, styling |
| `test-engineer` | Test strategy, fixtures, coverage, content validation |
| `security-auditor` | Sandbox escape review, input handling, secrets |
| `ai-mentor-integrator` | Ollama client, prompts, anti-spoiler policy |
| `docs-writer` | README, docs/, docstrings, changelog |

---

## 6. Git workflow

- `main` — released, tagged versions only
- `develop` — integration branch
- `feature/<phase>-<short-name>` — all work happens here
- One phase from `PROJECT_PLAN.md` per feature branch, merged by PR

**Commit style:** Conventional Commits.

```
feat(engine): add AST guard for forbidden builtins
fix(runner): kill subprocess on wall-clock timeout
docs(readme): add install instructions for Windows
test(content): assert every mission solution passes its own tests
```

**The agent never commits or pushes without being asked.** When work is ready, say
what should be committed and suggest the message.

**Before any destructive command** (`git checkout`, `reset`, `clean`, `rm -rf`),
run `git status` first and warn about uncommitted work.

---

## 7. Definition of done

A piece of work is done when:

- [ ] It runs
- [ ] `ruff check .` passes
- [ ] `pytest` passes
- [ ] Unit tests cover the happy path and at least two failure paths
- [ ] Public functions have docstrings saying *why*, not restating the code
- [ ] The architecture rules in section 4 are not violated
- [ ] Giovanni can explain out loud what the code does

The last item is not decoration. If he cannot explain it, the work is not done.

---

## 8. Session start checklist

At the start of every session, the agent should:

1. Read `PROJECT_PLAN.md` to see which phase is active
2. Run `git status` and `git branch --show-current`
3. Ask which phase item Giovanni wants to work on, if it is not obvious
4. Load the matching skill from `.claude/skills/`
5. Confirm the teaching contract applies before writing anything

---

## 9. Anti-patterns to avoid

- Writing a big chunk of code and then explaining it. Explain first, always.
- Fixing a bug silently in a diff. Name the bug, then let him fix it.
- Adding a dependency without discussing what it costs.
- Building three phases ahead. Ship the current checkpoint first.
- Generating mission content in bulk without a syllabus behind it.
- Saying "you're right!" when he is not. Push back with evidence.
