# Architecture

Detailed view of how the layers fit. The summary lives in `PROJECT_PLAN.md` section 3.
The enforcement rules live in `AGENTS.md` section 4.

---

## Import rules

```
tui/       -> services/, models/
services/  -> engine/, storage/, models/
engine/    -> models/
storage/   -> models/
models/    -> (nothing from this project)
mentor/    -> models/   (imported lazily, behind a feature flag)
content/   -> data only, no code
```

Any arrow not in this list is a bug. The reason each one exists:

- **tui does not touch engine or storage** so the game logic can be driven by a CLI, a
  test, or a future web layer without touching the UI.
- **engine does not import tui** so the whole engine runs headless in CI.
- **models imports nothing** so it can be imported from anywhere without a cycle.
- **mentor is lazy** so deleting the folder leaves a working game.

---

## Flow of one mission attempt

```
Player presses F5
        |
        v
tui/screens/mission.py          collects editor content
        |
        v
services/game_session.py        orchestrates, owns the sequence
        |
        +--> engine/guard.py            AST check. Forbidden construct? stop here
        |
        +--> engine/runners/python.py   subprocess per test case, limits applied
        |
        +--> engine/evaluator.py        raw results -> Verdict
        |
        +--> services/progress_service  award XP, check unlocks
        |         |
        |         v
        |    storage/repositories.py    persist attempt and progress
        v
      Verdict returned to the screen, rendered in the results panel
```

`game_session` is the only place that knows this whole sequence. Everything it calls is
independently testable.

---

## The Runner protocol

The single extension point for new languages.

```python
class Runner(Protocol):
    language: str
    file_extension: str

    def prepare(self, submission: str, mission: Mission) -> PreparedCode: ...
    def execute(self, prepared: PreparedCode, case: TestCase) -> ExecutionResult: ...
    def cleanup(self, prepared: PreparedCode) -> None: ...
```

| Runner | Version | Notes |
|---|---|---|
| `PythonRunner` | v1.0 | Writes `.py`, runs a JSON harness in a subprocess |
| `JavaRunner` | v1.1 | Writes `.java`, `javac` then `java`. Compile errors are their own verdict |
| `TypeScriptRunner` | v1.2 | Writes `.ts`, runs via `tsx` |

**The test of a good abstraction:** adding `JavaRunner` should touch exactly one new
file plus one registry entry. If it forces a change in `evaluator.py`, `services/`, or
`tui/`, the protocol is wrong and must be fixed before the Java content is written.

Java adds one thing Python does not have: a compile step that can fail before any test
runs. Decide during Phase 1 whether `prepare()` may return a failure, so the protocol
does not need reshaping in v1.1.

---

## The harness

The engine cannot simply import the player's file. It needs to call one function, pass
arguments, capture the return value, and survive anything the player wrote.

The harness is a small wrapper written next to the submission at runtime. It:

1. imports the submission
2. reads the test case arguments as JSON
3. calls `signature.entrypoint`
4. writes the return value back as JSON on a dedicated channel
5. catches every exception and reports it as structured data, never as a crash

**Player `print()` must not corrupt the result.** Use a separate file descriptor or a
temp file for results, not stdout. This is the detail that breaks naive implementations.

---

## Storage schema

```sql
profile          id, name, track, created_at, last_played_at, level, total_xp
progress         profile_id, mission_id, status, best_xp, hints_used, completed_at
attempt          id, profile_id, mission_id, code, verdict, created_at
unlocked_island  profile_id, island_id, unlocked_at
```

- `profile` is capped at four rows. The limit is a service rule, not a database
  constraint, so the error message can be a friendly one.
- `attempt` keeps history, so a player can read code they wrote weeks ago.
- `progress` holds the current best, `attempt` holds the journey.

---

## Configuration

`config.py` reads `.env` once at startup and exposes a frozen settings object.
Nothing else in the codebase reads `os.environ` directly. That way the whole
configuration surface is one file, and tests can substitute it.
