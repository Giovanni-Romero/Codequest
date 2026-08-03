# CodeQuest — Project Plan

> A local, offline-first game that teaches programming from beginner to advanced.
> Inspired by CheckiO, but the teaching content lives inside the game, not in a cloud service.

**Owner:** Giovanni
**Status:** Phase 0 (not started)
**License:** MIT (suggested)

---

## 1. What we are building

CodeQuest is a terminal game. You pick a language, create a career save, and travel
through islands. Each island holds missions. A mission teaches one concept, then asks
you to write code. The game runs your code in a sandbox and tells you if it passed.

The important design decision is this: **the teaching is part of the game, not part of an AI.**
Every explanation, analogy, worked example, and hint is written by hand and stored in the
repository as YAML. The AI mentor is a small optional chat in the corner of the screen.
If Ollama is offline, the game still teaches perfectly well.

### Why this matters for the project

This is a portfolio project with two layers of learning happening at once:

1. **You learn by building the engine.** Sandboxing, data modeling, TUI architecture,
   testing, CI/CD, LLM integration. This is real software engineering.
2. **You learn by writing the content.** To write a good mission about decorators you
   have to actually understand decorators. Teaching forces depth.

---

## 2. Scope

### In scope for v1.0 (MVP)

- Python track only
- Textual TUI
- Up to 4 career saves
- Island map with progressive unlocking
- Missions defined in YAML
- Sandbox execution via subprocess with resource limits
- SQLite progress persistence
- Optional Ollama mentor chat

### Planned after v1.0

- Java track (v1.1)
- TypeScript track (v1.2)
- Architecture, Security, and AI Engineering tracks (v1.3)
- Community mission format so other people can contribute missions

### Explicitly out of scope

- Web server, accounts, cloud sync
- Multiplayer or leaderboards
- Anything that requires an internet connection to teach

---

## 3. Architecture

### 3.1 Layer overview

```
+-------------------------------------------------------------+
|  PRESENTATION            src/codequest/tui/                 |
|  Textual screens, widgets, keybindings, theme               |
+---------------------------+---------------------------------+
                            |  calls services, never touches SQL
+---------------------------v---------------------------------+
|  APPLICATION             src/codequest/services/            |
|  GameSession, MissionService, ProgressService               |
|  Orchestrates: load mission -> run code -> evaluate -> save |
+---------------------------+---------------------------------+
                            |
+---------------+-----------v-----------+---------------------+
|  DOMAIN       |  ENGINE               |  PERSISTENCE        |
|  models/      |  engine/              |  storage/           |
|  Mission      |  loader (YAML->obj)   |  SQLite repo        |
|  TestCase     |  runners/ (sandbox)   |  migrations         |
|  Profile      |  evaluator (verdict)  |                     |
|  Verdict      |  guard (AST checks)   |                     |
+---------------+-----------------------+---------------------+
                            |
+---------------------------v---------------------------------+
|  CONTENT (data, not code)     content/                      |
|  YAML missions, island definitions, curriculum tracks       |
+-------------------------------------------------------------+

   .........................................................
   :  OPTIONAL PLUGIN         src/codequest/mentor/        :
   :  Ollama client -> gemma4:cloud. Degrades to "offline". :
   :........................................................:
```

### 3.2 The rules that keep this clean

These are the constraints that stop the project turning into spaghetti. Every code
review should check them.

| Rule | Why |
|---|---|
| TUI never imports `storage/` or `engine/` directly | Lets you swap TUI for web later without touching logic |
| `engine/` never imports `tui/` | The engine must be testable with zero UI |
| Content is data, never Python code | Non-programmers can contribute missions; content is versioned separately |
| `mentor/` is imported behind a feature flag | Game must fully work with Ollama uninstalled |
| Every language runner implements the same `Runner` protocol | Adding Java = adding one file, not rewriting the engine |

### 3.3 The Runner protocol (key extension point)

This is the abstraction that makes multi-language possible later without a rewrite.

```python
class Runner(Protocol):
    language: str

    def prepare(self, submission: str, mission: Mission) -> PreparedCode:
        """Write files to a temp dir. Compile if the language needs it."""

    def execute(self, prepared: PreparedCode, case: TestCase) -> ExecutionResult:
        """Run one test case in an isolated subprocess. Never raise on user error."""
```

- `PythonRunner` — writes a `.py` file, runs a harness in a subprocess
- `JavaRunner` (v1.1) — writes `.java`, calls `javac`, then `java`
- `TypeScriptRunner` (v1.2) — writes `.ts`, runs via `tsx` or compiles with `tsc`

The evaluator and the TUI do not know or care which runner is active.

---

## 4. Folder structure

```
codequest/
├── AGENTS.md                    # contract for the AI agent working on this repo
├── README.md                    # game manual (how to install and play)
├── PROJECT_PLAN.md              # this file
├── FINAL_PLAN.md                # bootstrap prompt for Claude Code
├── pyproject.toml
├── .gitignore
├── .env.example
│
├── .claude/
│   └── skills/                  # specialized skills that feed the agent
│       ├── curriculum-designer/SKILL.md
│       ├── mission-author/SKILL.md
│       ├── game-architect/SKILL.md
│       ├── engine-developer/SKILL.md
│       ├── tui-developer/SKILL.md
│       ├── test-engineer/SKILL.md
│       ├── security-auditor/SKILL.md
│       ├── ai-mentor-integrator/SKILL.md
│       └── docs-writer/SKILL.md
│
├── src/codequest/
│   ├── __init__.py
│   ├── __main__.py              # entry point: python -m codequest
│   ├── config.py                # paths, feature flags, settings
│   │
│   ├── models/                  # pure dataclasses, no I/O, no dependencies
│   │   ├── mission.py           # Mission, TestCase, Hint, Constraints
│   │   ├── curriculum.py        # Track, Island
│   │   ├── profile.py           # Profile, Progress
│   │   └── verdict.py           # Verdict, FailureReason
│   │
│   ├── engine/
│   │   ├── loader.py            # YAML -> Mission, with schema validation
│   │   ├── guard.py             # AST checks: forbidden imports/builtins
│   │   ├── evaluator.py         # compares output vs expected -> Verdict
│   │   ├── harness.py           # code injected around user code at runtime
│   │   ├── exceptions.py
│   │   └── runners/
│   │       ├── base.py          # Runner protocol + shared subprocess logic
│   │       ├── python.py
│   │       ├── java.py          # v1.1
│   │       └── typescript.py    # v1.2
│   │
│   ├── storage/
│   │   ├── db.py                # connection, schema creation
│   │   ├── migrations/
│   │   └── repositories.py      # ProfileRepository, ProgressRepository
│   │
│   ├── services/
│   │   ├── game_session.py      # orchestrates a full mission attempt
│   │   ├── mission_service.py   # find, filter, unlock rules
│   │   └── progress_service.py  # XP, level, island unlocking
│   │
│   ├── tui/
│   │   ├── app.py               # CodeQuestApp(App)
│   │   ├── screens/
│   │   │   ├── main_menu.py     # language selection
│   │   │   ├── save_select.py   # up to 4 careers
│   │   │   ├── island_map.py
│   │   │   ├── mission.py       # brief + teaching + editor + results
│   │   │   └── settings.py
│   │   ├── widgets/
│   │   │   ├── code_editor.py
│   │   │   ├── test_results.py
│   │   │   ├── hint_panel.py
│   │   │   └── mentor_chat.py   # the "bird in the corner"
│   │   └── styles.tcss
│   │
│   └── mentor/                  # optional plugin
│       ├── client.py            # Ollama HTTP client
│       ├── prompts.py
│       └── policy.py            # anti-spoiler rules
│
├── content/
│   ├── python/
│   │   ├── track.yaml
│   │   └── islands/
│   │       ├── 01-foundations/
│   │       │   ├── island.yaml
│   │       │   └── missions/
│   │       │       ├── 01-hello-value.yaml
│   │       │       └── 02-sum-list.yaml
│   │       ├── 02-collections/
│   │       └── 03-functions/
│   ├── java/                    # v1.1
│   ├── typescript/              # v1.2
│   └── crosscutting/            # v1.3
│       ├── architecture/
│       ├── security/
│       └── ai-engineering/
│
├── tests/
│   ├── unit/                    # per module, fast, no I/O
│   ├── integration/             # full mission attempt end to end
│   └── content/
│       └── test_all_missions.py # every YAML validates AND its solution passes
│
├── docs/
│   ├── architecture.md
│   ├── mission-schema.md
│   └── curriculum/
│       └── python-syllabus.md
│
└── .github/workflows/ci.yml
```

---

## 5. Mission schema

A mission is one YAML file. This is the contract between content and engine.
Full reference lives in `docs/mission-schema.md`.

See `content/python/islands/01-foundations/missions/02-sum-list.yaml` for a working example.

### Why hidden tests exist

Visible tests teach. Hidden tests catch shortcuts. If a player hardcodes `return 6`
the visible test passes and the hidden ones fail. Edge cases like empty lists and
negative numbers belong in hidden.

---

## 6. Development roadmap

Each phase ends with something you can run. No phase is "just refactoring".

### Phase 0 — Repository and environment

**Goal:** `python -m codequest` prints a version and exits cleanly.

1. Create repo, `main` and `develop` branches
2. `pyproject.toml` with `textual`, `pyyaml`, `pytest`, `ruff`
3. Virtual environment, `.gitignore`, `.env.example`
4. Package skeleton with empty modules
5. `.github/workflows/ci.yml` running ruff + pytest
6. First commit on `develop`

**You learn:** project layout, packaging, gitflow, CI basics.

---

### Phase 1 — Engine core

This is the heart. Build it in this order, each step tested before the next.

**1.1 Models** (`models/mission.py`)
Dataclasses for Mission, TestCase, Hint, Constraints. No logic, no I/O.
*Learn: dataclasses, type hints, immutability.*

**1.2 Loader** (`engine/loader.py`)
Read YAML, validate required fields, produce a `Mission`. Fail loudly with a
clear message naming the file and the missing field.
*Learn: YAML parsing, validation, error message design.*

**1.3 Guard** (`engine/guard.py`)
Parse the submission with `ast`, walk the tree, reject forbidden imports and
builtins before execution.
*Learn: AST, static analysis, why blocklists are weaker than allowlists.*

**1.4 Runner** (`engine/runners/python.py`)
Write submission to a temp dir. Run in `subprocess` with `resource` limits
(CPU time, address space) and a wall-clock timeout. Capture stdout, stderr,
exit code. Never let a player crash or hang the game.
*Learn: subprocess, process isolation, resource limits, timeouts.*

**1.5 Evaluator** (`engine/evaluator.py`)
Run each test case, compare results, build a `Verdict` with a readable failure
reason. Distinguish: wrong answer, exception, timeout, forbidden construct.
*Learn: test design, error taxonomy, useful feedback.*

**Checkpoint:** a CLI script that takes a mission file and a solution file and prints pass/fail.

---

### Phase 2 — Persistence and progression

**2.1 Schema** — tables: `profile`, `progress`, `attempt`, `unlocked_island`
**2.2 Repositories** — plain SQL, no ORM at first, so you see what SQL does
**2.3 ProgressService** — XP awards, level thresholds, island unlock rules

**Checkpoint:** create a save, solve a mission from the CLI, quit, reopen, progress persisted.

*Learn: relational modeling, SQL, migrations, separation of repo vs service.*

---

### Phase 3 — Content, first Python island

Write the Python syllabus first (`docs/curriculum/python-syllabus.md`), then the
missions. Do not write missions randomly. Every mission maps to a concept in the syllabus.

Island 1 "Foundations": 8 to 10 missions covering variables, conditionals, loops,
the accumulator pattern, and simple string work.

**Checkpoint:** `tests/content/test_all_missions.py` proves every mission's own
`solution` passes its own tests. This is the most valuable test in the repo.

---

### Phase 4 — TUI

Build screens in this order, because each depends on the last:

1. Main menu (language select)
2. Save select (4 slots, create/delete)
3. Island map
4. Mission screen (teaching panel, brief, editor, run button, results panel)
5. Hint panel

*Learn: Textual, event-driven UI, reactive state, CSS-like styling in terminal.*

**Checkpoint:** full loop playable with keyboard only.

---

### Phase 5 — Ollama mentor

Small, isolated, optional.

- `mentor/client.py` talks to `http://localhost:11434` (or the configured host)
- Model: `gemma4:cloud`
- Context sent: mission brief, concepts, the player's current code, the last verdict
- `mentor/policy.py` enforces the anti-spoiler rule: the mentor asks questions and
  points at concepts, it does not hand over working code
- If the client cannot connect, the widget shows "Mentor offline" and the game continues

*Learn: LLM API integration, prompt design, context windows, graceful degradation.*

---

### Phase 6 — Java track

Add `engine/runners/java.py`. The rest of the engine should need zero changes.
If it does need changes, the abstraction in Phase 1 was wrong, and that lesson is
itself worth the exercise.

Then write `content/java/` with its own syllabus.

---

### Phase 7 — Cross-cutting tracks

Architecture, Security, and AI Engineering missions. These reuse the same engine but
the missions are different in shape: refactor this code, find the vulnerability,
build a retrieval function. Same YAML schema, harder briefs.

---

## 7. Technical decisions and trade-offs

| Decision | Chosen | Alternative | Why |
|---|---|---|---|
| Mission format | YAML | Python modules | Content stays data. Non-coders can contribute. Diffs are readable. Cost: needs a validation layer. |
| Sandbox | subprocess + `resource` | Docker | No external dependency, teaches OS-level isolation. Cost: weaker isolation than a container. Acceptable because the player runs their own code. |
| Persistence | SQLite | JSON files | Real queries, real schema, transferable skill. Cost: slightly more setup. |
| UI | Textual TUI | Web (FastAPI) | Rich enough to feel like a game, no frontend stack to learn yet. Cost: no graphics. |
| Repo | Monorepo | Split engine/content | Simpler solo workflow, one strong README for portfolio. Cost: content and engine version together. |
| Mentor | Ollama, optional | Cloud API, required | Free, local, private, and the game works without it. |

### Known limitations, stated honestly

- `subprocess` + `resource` is not a real security boundary. A determined player can
  escape it. This is fine for a single-player local game, and it is **not** fine if
  this ever becomes a web service. Document this loudly.
- `resource.setrlimit` is not available on Windows. Plan a fallback path
  (timeout only, no memory cap) and detect the platform at startup.
- AST blocklists can be bypassed (for example `getattr(builtins, "s" + "um")`). Treat
  the guard as a teaching aid, not a security control.

---

## 8. Definition of done, per phase

A phase is done when all of these are true:

- [ ] Code runs without errors
- [ ] Unit tests cover the happy path and at least two failure paths
- [ ] `ruff check` passes
- [ ] Public functions have docstrings explaining *why*, not *what*
- [ ] The checkpoint demo works
- [ ] Merged to `develop` via a PR with a description of what you learned

---

## 9. How the learning loop works

For every module, the sequence is fixed:

1. **Agent explains** the concept with an analogy and a small example
2. **Agent shows** the signature and describes the expected behavior, not the body
3. **Giovanni writes** the implementation
4. **Agent reviews**: what is wrong, what is fragile, what would break at scale
5. **Giovanni fixes**, then writes the tests
6. **Agent verifies** and names the concept that was just learned

The agent does not write implementation code unless explicitly asked with the words
"write this one for me". This rule is enforced in `AGENTS.md`.
