# CodeQuest — Project Plan

> A local, offline-first game that teaches programming from beginner to advanced.
> Inspired by CheckiO, but the teaching content lives inside the game, not in a cloud service.

**Owner:** Giovanni
**Status:** Phase 5.1 complete; Phase 6 awaits the final Python playtest. Phase 7's
AI Engineering track is complete with 22 bilingual islands and 176 missions.
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
│   └── tracks/
│       ├── python/
│       │   └── locales/
│       │       ├── en/
│       │       │   ├── track.yaml
│       │       │   └── islands/
│       │       └── pt-BR/
│       │           ├── track.yaml
│       │           └── islands/
│       └── ai-engineering/
│           └── locales/
│               ├── en/
│               └── pt-BR/
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
│       ├── python/
│       │   └── syllabus.md
│       └── ai-engineering/
│           ├── syllabus.md
│           └── bookmarks.md
│
└── .github/workflows/ci.yml
```

---

## 5. Mission schema

A mission is one YAML file. This is the contract between content and engine.
Full reference lives in `docs/mission-schema.md`.

See `content/tracks/python/locales/en/islands/01-foundations/missions/02-sum-list.yaml` for a working example.

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

Write the Python syllabus first (`docs/curriculum/python/syllabus.md`), then the
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

#### F8 — ask the mentor to teach, not only to nudge

Added 2026-08-10, from playtesting. Giovanni's report: the missions are enjoyable but the
teaching panels are too shallow for a concept the player has never met. The panel is
roughly a quarter of the screen (`tui/styles.tcss`), and `mission-author` caps
`explanation` at three to six sentences, so depth has nowhere to go.

The decision was **not** to change the teaching schema or the layout. Instead, a second
keybinding asks the mentor for a longer explanation of the current concept:

- `mentor/prompts.py` gains `build_explain_messages(...)`, taking the track language, the
  island theme, the mission and the concept ids.
- The system prompt is the current one **relaxed**: today it says "You are not the
  teacher: the lesson, the analogy and the hints are already written"
  (`mentor/policy.py:44`). The explain profile lifts that sentence and lifts the 120-word
  cap, because a lecture is what is being asked for.
- `policy.defines_entrypoint` still runs and still redacts. Relaxing the *guidance* while
  keeping the *filter* is the whole point of the two-layer design already documented in
  that module.

Two costs to keep visible rather than discover later:

1. Ollama is optional and not bundled (§7). A player who never installs it gets the shallow
   version, which means the fix does not reach everyone the complaint came from.
2. The written teaching is reviewed; model output is not. A small local model explaining
   `dunder-methods` can be confidently wrong, and confidently wrong is worse than short and
   right for someone meeting a concept for the first time.

Sequenced after the game is complete, by Giovanni's decision. Retrofitting the shipped
islands' teaching panels is a separate, later pass, island by island.

---

### Phase 5.1 — Complete the Python curriculum, island by island

Added 2026-08-05, after Foundations shipped and Giovanni played it. The track has 11
islands now, not 10 — a **Debugging** island was inserted as island 6, right after
Errors and Edge Cases, because reading a traceback usefully depends on already knowing
what an exception is.

**Islands 1 to 7 were designed one at a time; 8 to 11 were designed together on
2026-08-10.** The original rule was that designing every remaining island now would freeze
decisions that playing the earlier ones should change. It was relaxed for the last four
because three of them share a single constraint — what can cross the JSON boundary between
the sandbox and the game — and finding that constraint four separate times would have been
the same decision paid for four times. See the note at the end of
`docs/curriculum/python/syllabus.md`.

**Island 11 had engine work that shipped before its first mission was authored**, in the
same way `raises:` preceded Island 5 and `files:` preceded Island 7. Both landed on
2026-08-10 and both were the size the design predicted: `engine/harness.py` now detects a
coroutine with `inspect.iscoroutine` and resolves it with `asyncio.run` inside the existing
error handling (`[AI-ENG:deferred-results]`), and `engine/loader.py:107` accepts
`async def`. Mission 2's own solution passed on the first run, which is what building the
engine first buys.

**Status, 2026-08-10: all eleven islands have shipped.** 117 missions per language, 234
mission files, both trees at `codequest check` 117/117. What remains in this phase is the
playtesting, not authoring.

**The HTML lesson shipped 2026-08-11** as `Fase7-Curriculo-como-Eval-Design.html`, which
closes the phase under `CLAUDE.md` §7. It was written alongside an audit of the whole
repository — see **`docs/project-audit.md`** for what that audit found, what it fixed,
and what is deferred on purpose. The two findings worth carrying forward: the teaching
retrofit of Islands 1 to 7 now has a number attached to it (117 lines of mission against
265), and two snapshot tests that had been dismissed as flaky for two islands turned out
to have two real, stacked causes.

The authoring cycle is unchanged and still runs one island at a time:

1. **Design** one island (`curriculum-designer`): concept graph, prerequisites,
   misconceptions, an 8-to-12-mission map, sawtooth difficulty curve.
2. **Author** that island's missions (`mission-author`) — in `content/tracks/python/locales/en/` **and**
   its `content/tracks/python/locales/pt-BR/` mirror, ids and tests identical, only text translated.
3. **Validate**: `codequest check` on both language trees, `tests/content` covering the
   new island.
4. **Playtest**: Giovanni plays the whole island in the TUI and approves it before the
   next island is designed.

Order: Collections -> Functions -> Strings and Text -> Errors and Edge Cases ->
**Debugging** -> Files and Data -> Objects -> Pythonic Patterns -> Algorithms -> Async
and Concurrency.

**Checkpoint:** each island, playable and bilingual, before the next one starts. The
phase as a whole closes when Island 11 (Async) ships, at which point it gets its HTML
lesson — curriculum design as iterative eval design, the strongest AI-Eng bridge in the
project, plus `[AI-ENG:debugging-methodology]` from the Debugging island.

*Learn: syllabus design under real feedback instead of upfront, translation as a content
pipeline problem, what "one concept per mission" costs at scale.*

---

### Phase 5.2 — Portable build (pendrive, no install)

Added 2026-08-05, independent of Phase 5.1's content work — this is packaging, not
curriculum, and could ship with however much of the track exists at the time.

- **PyInstaller, `--onedir` mode**, not `--onefile`. `--onefile` re-extracts to a fresh
  temp folder on every launch, which would silently reset save progress every time the
  game opens on a different machine. `--onedir` is a stable folder that can live on a
  pendrive and keep its saves between sessions.
- `src/codequest/config.py`'s `PROJECT_ROOT` has to become frozen-aware
  (`getattr(sys, "frozen", False)` -> resolve from `Path(sys.executable).parent`
  instead of `Path(__file__).resolve().parents[2]`), or `content/`/`saves/` resolve
  into the wrong place once the game is no longer running from the source tree.
- `pyinstaller` is a **build-only** dependency (a new `[project.optional-dependencies].
  build` extra), never a runtime cost for someone who only plays.
- The mentor is not bundled — Ollama plus its models is multiple gigabytes, out of
  scope for a pendrive. The game already degrades to "mentor offline" without it
  (Phase 5), so the portable build needs no new code for this, only a verification
  pass that it actually behaves that way with no Ollama on the host.
- Windows only, matching every machine in Giovanni's stated use case (his own,
  the office, travel).

**Checkpoint:** the built folder, copied to a location with no Python installed and no
copy of the source repo, launches, plays a mission, and keeps that save open across two
separate launches.

*Learn: what "no dependencies" actually requires under the hood, why extraction
strategy is a correctness question and not just a packaging preference.*

---

### Phase 6 — Java track

Add `engine/runners/java.py`. The rest of the engine should need zero changes.
If it does need changes, the abstraction in Phase 1 was wrong, and that lesson is
itself worth the exercise.

Then add `content/tracks/java/locales/en/` with its own syllabus. Add other locales only
when their translated content exists.

---

### Phase 7 — Cross-cutting tracks

Architecture, Security, and AI Engineering missions. These reuse the same engine but
the missions are different in shape: refactor this code, find the vulnerability,
build a retrieval function. Same YAML schema, harder briefs.

#### AI Engineering track — 22-island roadmap

Added 2026-09-05 and expanded 2026-09-06 after comparing the plan with curricula from
Carnegie Mellon, MIT, Stanford, and Georgia Tech. The authoritative concept graph is
`docs/curriculum/ai-engineering/syllabus.md`.

The approved sequence is:

1. **Reliable AI systems:** Documents into Context, Prompt Contracts, Retrieval, RAG,
   Structured Outputs, Evals, Tools and Agents, Production AI.
2. **Academic and engineering foundations:** Mathematical and Statistical Foundations,
   Machine Learning Foundations, Reasoning and Decision Making, Data Engineering for AI,
   PyTorch and Deep Learning, NLP and Transformers, Responsible AI, MLOps and Model Lifecycle.
3. **Mandatory framework specializations:** LangChain, LangGraph, LlamaIndex, PydanticAI,
   and DSPy. Packages remain separately installed extras, but all five islands are required
   for track completion.
4. **Synthesis:** AI Engineering Capstone.

Mathematics, statistics, reasoning, governance, and other non-framework topics still use
Python: code calculates, simulates, validates assumptions, and produces auditable results.
The graded artifact remains deterministic and offline; written interpretation appears in
the brief and expected return structure rather than requiring subjective grading.

**Status, 2026-09-21: all 22 islands have shipped.** Each has eight bilingual missions.
Island 1 covers bounded traceable context, Island 2 prompt contracts and trust boundaries,
and Island 3 sparse retrieval, cosine similarity, stable top-k ranking, thresholds, and a
closing retrieval pipeline. Island 4 adds deterministic RAG assembly, citation provenance,
and abstention. Islands unlock only after the final mission of the previous island is
completed. Island 6 adds deterministic eval datasets, capability metrics, adversarial cases, and held-out leakage checks. Island 7 adds explicit tool contracts, least-authority routing, ordered orchestration gates, and idempotent effect plans. Island 8 adds deterministic guardrails, safe traces, bounded latency and cost plans, and graceful provider fallbacks. Island 9 adds vector operations, descriptive statistics, finite probability distributions, and explicit optimization steps. Island 10 adds reproducible dataset splits, supervised learning contracts, honest baselines, generalization diagnostics, and deterministic unsupervised grouping. Island 11 adds explicit state-space search, heuristic comparisons, constrained action planning, and temporal-difference updates. Island 12 adds executable data contracts, multidimensional quality reports, immutable lineage, and reproducible transformations. Islands 13 and 14 add tiny offline PyTorch training and Transformers inference through the separately installed `ai-ml` extra; they download no model weights. Island 15 adds group fairness metrics, privacy boundaries, explainability records, and human oversight. Island 16 adds experiment tracking, model versioning, deployment strategies, and drift monitoring. Island 17 adds runnable composition, prompt templates, deterministic retrieval, and bounded tool agents with LangChain. Islands 18 to 20 add durable stateful workflows with LangGraph, data ingestion and query workflows with LlamaIndex, and typed provider-independent agents with PydanticAI. Island 21 adds LM programs declared as signatures, composed as modules, measured by metrics, and optimized without leakage with DSPy. Island 22 closes the track by turning requirements into acceptance gates, selecting the smallest justified architecture, testing failure budgets, and certifying operational readiness.

Framework missions use deterministic local fixtures, tiny CPU workloads, and fake providers.
Model-backed exercises may be optional labs, but do not replace the mandatory graded missions.
The eighth HTML lesson, `docs/aulas/Fase8-Engenharia-de-IA-de-Ponta-a-Ponta.html`, closes
Phase 7 under `CLAUDE.md` §9.2.

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

### 7.1 Art direction and game scope

Decided 2026-08-04, after Phases 0 to 2 were already merged. Full visual contract in
`docs/art-direction.md`.

| Concern | Decision | Why |
|---|---|---|
| Presentation | Textual TUI, no pixel graphics | See the rejected alternatives below |
| Aesthetic | Nautical chart | The game is already about islands, sailing and a career. The metaphor was in the README before the interface existed |
| Palette | Night chart, dark ground | A light panel inside a dark terminal reads as a window pasted on top. Sessions are long |
| Characters | Unicode box-drawing, no ASCII fallback | Windows Terminal and the VS Code terminal render it. The thin rules are the aesthetic; a fallback would need two versions of every visual element |
| Game mechanics | Island map, XP, levels, unlocking, layered hints — nothing more | Already built and tested. No timer, no lives, no narrative arc |
| Audio | None | Most people who program are already listening to something. A game soundtrack is the first thing they mute |
| Minimum size | 100x30 comfortable, reflows to 80x24 | Below 100 columns the four panels stack into tabs. Never a hard refusal |

**Hint cost.** Revealing a hint reduces that mission's XP: 100 / 90 / 70 / 40 percent for
zero to three hints. Floored at 40 because a hint is a tool, not a punishment — zeroing the
reward teaches players to stay stuck in silence, which is the worst outcome available.

#### Rejected alternatives, and what they would have cost

**pygame with real 8-bit pixel art.** Sprites, tiles, chiptune, a far more eye-catching
portfolio screenshot. Rejected on a hidden cost: the game's core interaction is *typing
code*, and pygame has no text editor. Building one — cursor, selection, scrolling, undo,
copy and paste, syntax highlighting — is more work than Phases 1 and 2 combined, and none
of it teaches anything this project set out to teach. Textual's `TextArea` supplies all of
it, with tree-sitter highlighting, for free.

**pygame with an external editor.** Pixel art plus watching a file the player edits in
VS Code. Sidesteps the editor problem, but the player alt-tabs on every attempt and the
game stops being one place.

**Web frontend.** Contradicts section 2: no server, no network, offline-first.

The engine survives any of these. `engine/` never imports `tui/`, and
`tests/integration/test_architecture.py` enforces it, so a second frontend later is an
addition rather than a rewrite. That is what makes "TUI now, reconsider at v2" a real
option rather than a hope.

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
