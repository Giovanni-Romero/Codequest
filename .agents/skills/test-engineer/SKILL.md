---
name: test-engineer
description: Test strategy and quality assurance — unit tests, integration tests, fixtures, content validation, and CI. Use when planning what to test, writing test suites, debugging flaky behavior, or setting up the CI pipeline.
---

# Test Engineer

Teaching contract applies with one adjustment: the agent may write test *names and
descriptions* so Giovanni has a checklist. The bodies are his.

## The test pyramid for this project

```
        /\        content tests   - every mission YAML is valid and its
       /  \                         own solution passes its own tests
      /----\      integration     - full attempt: load -> guard -> run -> evaluate -> save
     /      \     unit            - one module, no I/O, fast
    /--------\
```

## The single most valuable test in the repo

`tests/content/test_all_missions.py`

For every YAML file under `content/`:

1. it loads without error
2. required fields are present
3. `signature.entrypoint` matches the function name in `stub` and in `solution`
4. the `solution` passes every visible test
5. the `solution` passes every hidden test
6. concept ids referenced exist in the syllabus

This catches broken content before a player ever hits it. Parametrize it so each
mission is a separate test case with the filename in the id, otherwise a failure tells
you nothing about which file broke.

## What to unit test, per module

**loader** — valid file; missing required field; malformed YAML; unknown difficulty;
entrypoint mismatch between stub and solution

**guard** — clean code passes; forbidden import rejected; forbidden builtin rejected;
syntax error handled without crashing; code that is empty

**runner** — normal return; player raises an exception; infinite loop hits the timeout;
memory hog is capped (skip on Windows); player prints to stdout and it does not corrupt
the result; submission that never defines the entrypoint

**evaluator** — all pass; one wrong answer; exception; timeout; float comparison
tolerance; expected `None` vs missing return

**storage** — create profile; four profile limit enforced; progress survives reconnect;
transaction rolls back on error; parameterized query resists an injection string

**services** — XP awarded once, not twice, for the same mission; island unlocks at the
right threshold; a failed attempt is recorded but awards nothing

## Fixtures worth building early

- `tmp_mission` — writes a minimal valid mission YAML to a temp dir
- `tmp_db` — fresh SQLite database per test, torn down after
- `sample_profile` — a profile with known progress
- `runner` — a configured PythonRunner with short timeouts so tests stay fast

Teach the concept: a fixture is the setup you would otherwise copy into every test.
Copying setup is how test suites rot.

## Rules

- A test that needs the network is not a unit test. Mock the Ollama client.
- Tests must not depend on execution order or share mutable state.
- Every bug fixed gets a regression test that fails before the fix and passes after.
  Write the failing test first, then fix.
- Slow tests get marked and excluded from the fast local run, but still run in CI.
- Aim for meaningful coverage on `engine/` and `services/`. Do not chase a number on
  `tui/`; test its logic through services instead.

## CI pipeline (.github/workflows/ci.yml)

```
ruff check .
ruff format --check .
pytest tests/unit -q
pytest tests/content -q
pytest tests/integration -q
```

Run on push and pull request. Matrix on Python 3.11 and 3.12. Add Windows to the
matrix once the platform fallback in the runner exists, because that is exactly the
code path that breaks silently.
