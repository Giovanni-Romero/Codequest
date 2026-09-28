# CLAUDE.md — CodeQuest

Operating rules for Claude Code in this repository. Read top to bottom before the first
action of every session. `AGENTS.md` is the long-form contract; this file is the part
that must be in context at all times.

---

## 0. Style override — read this first

**The global "caveman / cut all prose" style does NOT apply in this repository.**

This repo exists to teach Giovanni engineering. Clipped prose deletes the explanation,
which is the entire product. So here:

- **Chat in Portuguese (pt-BR). Write every file in English.** No exceptions.
- Explain with an everyday analogy first, then the formal definition.
- When several approaches exist, name the trade-offs: performance, readability,
  maintenance, scalability.
- Say explicitly when something is opinion or community convention. Never present a
  preference as a fact.
- Be direct. Say what is wrong and exactly why. Do not soften real problems.
- Treat Giovanni as a competent colleague. Do not oversimplify, but explain advanced
  jargon the first time it appears.

Brevity still applies to: status reports, tool-output summaries, commit messages, and
answers to questions that are genuinely one line long.

---

## 1. Prime directive

**Claude implements. Giovanni learns from the bookmarks, the HTML lessons, and by
playing the finished game.**

> **Contract change, 2026-08-03.** Until Phase 0 the rule was the opposite: Giovanni
> wrote every function body and Claude only taught. He weighed the estimate for Phases
> 1–2 under that rule (42–57 focused hours, 3–7 weeks of calendar) and chose delivery
> over hand-authorship. **`AGENTS.md` §0 is suspended and must not be applied.** Every
> other section of `AGENTS.md` still holds.

What this does *not* change:

- The teaching obligation moved, it did not disappear. It is now discharged through
  §9 — bookmarks in the code and one HTML lesson per phase. A phase is not done
  without them.
- Explanations in chat stay as described in §0. Shipping code is not a licence to stop
  explaining what was built and why.
- Architecture invariants (§3) and the definition of done (§7) are unchanged.

If Giovanni asks to go back to writing code himself for a given module, honour it for
that module without renegotiating the rest.

---

## 2. Commands

Python on this machine is 3.12.10 (`pyproject.toml` requires >=3.11).
Shell is PowerShell. Prefix with `rtk` where a filter exists.

```powershell
.venv\Scripts\Activate.ps1          # activate the venv first, every session
pip install -e ".[dev]"             # editable install + dev extras

rtk ruff check .                    # lint
rtk ruff format --check .           # format check (CI runs this too)
rtk pytest                          # all tests
rtk pytest tests/unit               # CI runs the three suites separately
python -m codequest                 # run the game
codequest                           # same, via [project.scripts]
```

CI (`.github/workflows/ci.yml`) runs `pytest tests/unit`, `pytest tests/content` and
`pytest tests/integration` as **separate steps**. A directory with zero collected tests
exits with code 5 and fails the build — every suite must always hold at least one test.

---

## 3. Architecture invariants

Check these on every review. They are the reason this project will not become spaghetti.

| Invariant | Consequence if broken |
|---|---|
| `tui/` must not import `storage/` or `engine/` — it goes through `services/` | Swapping the TUI for a web layer means rewriting logic |
| `engine/` must not import `tui/` | The engine stops being testable headless |
| `models/` has zero project imports and does no I/O — pure data | Models become untestable and circular |
| `content/` is YAML only, never executable Python | Non-coders can no longer contribute; content becomes a code-execution vector |
| `mentor/` is imported lazily behind a feature flag | Deleting the folder breaks the game; Ollama becomes mandatory |
| Every runner implements the `Runner` protocol in `engine/runners/base.py` | Adding Java means rewriting the evaluator instead of adding one file |

Build order in `engine/` — do not skip ahead:
`models → loader → guard → runner → evaluator → storage → services`

When Giovanni proposes something that breaks an invariant, explain the concrete
consequence ("if you do this, adding Java later means rewriting the evaluator"),
not just "no".

---

## 4. Skill routing

Load the matching skill from `.agents/skills/` **before** acting, not after.

| Working on | Skill |
|---|---|
| Module boundaries, refactors, new subsystems | `game-architect` |
| Syllabus, concept ordering, islands | `curriculum-designer` |
| A mission YAML file | `mission-author` |
| loader, guard, runners, evaluator, services, storage, models | `engine-developer` |
| Textual screens, widgets, keybindings, styling | `tui-developer` |
| Test strategy, fixtures, coverage, content validation | `test-engineer` |
| Sandbox escape, untrusted input, secrets | `security-auditor` |
| Ollama client, prompts, anti-spoiler policy | `ai-mentor-integrator` |
| README, docs/, docstrings, changelog | `docs-writer` |

---

## 5. Platform constraints — Windows is the dev machine

Giovanni develops on Windows 11. This is the project's largest technical risk and it
lands in Phase 1.4 (`engine/runners/python.py`).

- `resource.setrlimit` and `subprocess`'s `preexec_fn` **do not exist on Windows**.
- **Decision:** `PythonRunner` detects the platform.
  - POSIX → `resource.setrlimit` for CPU time and address space, applied in `preexec_fn`.
  - Windows → **timeout-only**: wall-clock `subprocess.run(timeout=...)`, plus killing
    the whole process tree (`CREATE_NEW_PROCESS_GROUP` + `Popen.kill()`, or `taskkill /T /F`).
- **There is no memory cap on Windows.** Document this loudly in code and docs. Do not
  hide it behind a silent `try/except`.
- The wall-clock timeout is enforced by the parent. Never trust the child to stop itself.
- CI on Linux covers the full path. The `windows:` job in `ci.yml` **is enabled** and
  runs all three suites on `windows-latest` — it was gated with `if: false` until the
  fallback existed, because that fallback is exactly the code that breaks silently.
  Keep it enabled: a Windows-only regression is invisible on the Linux job by design.
- **No new dependencies for this.** Docker and WSL were considered and rejected; see
  `PROJECT_PLAN.md` §7.

Also honest, and worth repeating to Giovanni rather than pretending otherwise:
`subprocess` + `resource` is not a real security boundary, and an AST blocklist is
defeatable (`getattr(builtins, "s" + "um")`). The guard protects the lesson, not the host.
This is acceptable for a local single-player game and would not be acceptable on a server.

---

## 6. Git

- `main` — tagged releases only · `develop` — integration · `feature/<phase>-<name>` — all work
- Conventional Commits: `feat(engine): add AST guard for forbidden builtins`
- One concept per commit. The git history is part of the portfolio.
- **Never commit or push without being asked.** When work is ready, say what should be
  committed and propose the message.
- Before any destructive command (`checkout`, `reset`, `clean`, `rm -rf`), run
  `git status` first and warn about uncommitted work.

---

## 7. Definition of done

- [ ] It runs
- [ ] `ruff check .` and `ruff format --check .` pass
- [ ] `pytest` passes
- [ ] Tests cover the happy path and at least two failure paths
- [ ] Public functions have docstrings saying *why*, not restating the code
- [ ] No invariant from §3 is violated
- [ ] Every AI-Engineering-relevant decision carries an `[AI-ENG:...]` bookmark (§9)
- [ ] **At the end of a phase: the HTML lesson exists** (§9). No lesson, no phase.

---

## 8. Anti-patterns

- Adding a dependency without discussing what it costs.
- Building three phases ahead. Ship the current checkpoint first.
- Generating missions in bulk with no syllabus behind them.
- Saying "you're right!" when he is not. Push back with evidence.
- Shipping a phase without its bookmarks and its lesson. That is the whole point now.

---

## 9. Learning artifacts — mandatory

Since Claude writes the code (§1), these two artifacts are how Giovanni actually learns.
They are not documentation chores; they are the deliverable.

### 9.1 Bookmarks in the code

Any decision that transfers to AI Engineering gets a comment **on the exact line**:

```python
# [AI-ENG:sandboxing] Running untrusted code in a killable child process is the same
# problem as sandboxing an agent's tool calls or a code-interpreter session.
```

Rules:
- Slug is kebab-case and stable. Reuse an existing slug rather than inventing a synonym.
- The comment states **the bridge**, not what the line does. "Parses YAML" is worthless;
  "declarative data must be validated before use, exactly like LLM structured output" is
  the point.
- Keep them rare. One per genuine concept. A file peppered with bookmarks has none.

Index every bookmark in `docs/curriculum/ai-engineering/bookmarks.md` with `file:line` and the bridge.
A stale line number is worse than no index: it cites a specific wrong place. Line numbers
move whenever a bookmarked file gains an import, so this is a command, not a memory:

```bash
python scripts/refresh_bookmarks.py
```

It rewrites only the `file:line` targets and leaves the bridge text alone. A new bookmark
or a removed one is reported and needs a human — the bridge has to be written, and a
disappearance has to be intentional. `tests/unit/test_bookmarks.py` fails when the index
and the code disagree in either direction.

### 9.2 The HTML lesson, one per phase

At the end of **every** phase, write:

```
D:\Projetos\2026\_AI_Eng_Aulas\Fase<N>-<Tema>.html
```

and then **copy it into `docs/aulas/`**, so the lessons are readable from GitHub. The
external folder stays the source of truth — write there first, mirror second — and
`docs/aulas/README.md` indexes them.

- **Portuguese (pt-BR).** This is the one deliberate exception to §0's "every file in
  English" rule, and it is now an exception inside the repository rather than outside
  it. The reason is unchanged: these are Giovanni's study material, and translating them
  would cost exactly the clarity that justifies writing them. Everything else in
  `docs/` stays in English, `docs/aulas/README.md` included.
- **Fully self-contained.** Inline CSS, inline SVG diagrams. No CDN, no external font,
  no remote image. It must open offline by double-clicking.
- **Light and dark theme**, via `prefers-color-scheme`.
- Fixed structure:
  1. What was built in this phase, in one paragraph
  2. Everyday analogy for the core concept
  3. The theory, properly — the formal definition after the intuition
  4. The **real project code**, annotated. Never pseudocode.
  5. The bridge to AI Engineering, naming the `[AI-ENG:...]` slugs it covers
  6. A fixation exercise, with the answer collapsed behind a `<details>`

The lesson is written from the code that actually shipped, after the phase is green —
never from the plan.
