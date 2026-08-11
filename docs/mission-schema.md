# Mission Schema Reference

A mission is one YAML file. This document is the contract between the content and the
engine. If the loader and this document disagree, one of them is a bug.

**Location:** `content/<track>/islands/<NN>-<island>/missions/<NN>-<slug>.yaml`

**Working example:** `content/python/islands/01-foundations/missions/02-sum-list.yaml`

---

## Top-level fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Unique across the whole repo. Format `<track>-<island>-<NN>` |
| `title` | string | yes | Shown in the map and the mission header |
| `track` | string | yes | Must match a track id in `content/<track>/track.yaml` |
| `island` | string | yes | Must match an island id |
| `order` | int | yes | Position inside the island, starting at 1 |
| `difficulty` | enum | yes | `elementary`, `simple`, `moderate`, `challenging`, `expert` |
| `tags` | list[string] | no | Free-form, used for filtering and search |
| `xp` | int | yes | 10 elementary, 20 simple, 30 moderate, 45 challenging, 60 expert |
| `concepts` | list[string] | yes | Concept ids that must exist in the syllabus |
| `teaching` | object | yes | See below |
| `brief` | string | yes | What the player must build |
| `signature` | object | yes | See below |
| `constraints` | object | no | Defaults applied when absent |
| `files` | object | no | Data files planted in the sandbox. See below |
| `tests` | object | yes | See below |
| `hints` | list[object] | yes | At least one, normally three |
| `solution` | string | yes | Must pass every test. Never sent to the AI mentor |

---

## `teaching`

The lesson. Rendered in the teaching panel, in this order.

| Field | Type | Required | Notes |
|---|---|---|---|
| `analogy` | string | yes | A real-world situation with the same shape as the concept |
| `explanation` | string | yes | 3 to 6 short sentences. Plain words. Term defined after the intuition |
| `worked_example` | string | yes | 5 to 10 runnable lines, in a **different** domain from the task |
| `key_points` | list[string] | yes | 3 to 5 rules, each with the reason attached |

The worked example must not solve the mission. If the mission sums numbers, the example
joins strings.

---

## `signature`

| Field | Type | Required | Notes |
|---|---|---|---|
| `entrypoint` | string | yes | Function name the engine calls. Must match `stub` and `solution` |
| `stub` | string | yes | Pre-filled editor content |

### The entrypoint may be `async def`

Added for Island 11 (Async and Concurrency). The harness detects a coroutine and
resolves it before the value crosses the JSON boundary, so an async mission is an
ordinary mission everywhere downstream: `expect`, `raises` and `tolerance` all behave
identically, and an exception raised inside the coroutine arrives as a normal failure.

Three rules, all of them learned by writing the island rather than by guessing:

1. **The engine awaits the entrypoint.** The brief must say so. The player writes
   `async def` and returns a value; the engine does the rest.
2. **The solution must not call `asyncio.run` on itself.** `asyncio.run` owns its event
   loop from creation to close, and the harness has already opened one — a second raises
   `RuntimeError: asyncio.run() cannot be called from a running event loop`.
3. **A *synchronous* entrypoint may call `asyncio.run` freely.** Only the entrypoint
   itself is awaited for you. Missions 5 to 9 of Island 11 drive asyncio and threading
   themselves and hand back plain data.

A coroutine still cannot be *returned*, for the same reason an instance or a generator
cannot: `repr` carries a memory address that changes every run. Return the awaited
value, not the promise of it.

---

## `constraints`

All optional. Defaults shown.

| Field | Type | Default | Notes |
|---|---|---|---|
| `forbidden_builtins` | list[string] | `[]` | Rejected by the AST guard before execution |
| `forbidden_imports` | list[string] | `[]` | Rejected by the AST guard before execution |
| `max_runtime_ms` | int | `2000` | Wall-clock timeout per test case |
| `max_memory_mb` | int | `128` | POSIX only. Ignored on Windows with a warning |

Forbid the shortcut that skips the lesson. A mission about building a sum must forbid
`sum`, otherwise the mission teaches nothing.

---

## `files`

Optional. A mapping of filename to text content, written into the sandbox directory
before the mission runs. This is what lets a mission about reading files hand the player
something to open.

```yaml
files:
  cargo.csv: |
    port,weight
    lisbon,10
    porto,4
```

The player's code runs with the sandbox as its working directory, so `open("cargo.csv")`
finds it with no path involved.

### Filename rules

A key must be a **plain filename**: one segment, nothing else. The loader rejects the
file — with the mission — when a name

- contains `/` or `\`, on any platform
- contains `:`
- starts with `.` (which also rules out `.` and `..`)
- is one of `submission.py`, `harness.py`, `request.json`, `result.json`, which the
  runner owns

This is not fussiness. `content/` is the one part of the repository a non-programmer is
invited to edit, and a name that becomes a write path turns that invitation into an
arbitrary file-write primitive. The rule is to **reject** the name, never to clean it up.

### Three things a mission may not assume

1. **The sandbox directory is not empty, and its contents vary.** It always holds
   `submission.py`, `request.json` and `result.json`, plus `harness.py` outside a
   packaged build. No mission may list the directory or count what is in it.
2. **An open file handle cannot cross back to the game.** Results travel as JSON; a
   handle degrades to its `repr`. An entrypoint may neither take nor return one. Read or
   write inside the function and return a value.
3. **There is no stdin.** The sandbox process never gets one. A mission that needs input
   takes arguments.

### Every test case starts from the declared content

Test cases share one sandbox directory, but the files are re-planted before each case.
A submission that appends to a file in case 1 does not hand its leftovers to case 2 — so
a mission may safely teach writing, and the author never has to think about the reuse.

---

## `tests`

| Field | Type | Required | Notes |
|---|---|---|---|
| `visible` | list[case] | yes | 2 or 3. Shown to the player. These teach the shape |
| `hidden` | list[case] | yes | 4 or more. Not shown. These verify |

### Test case

| Field | Type | Required | Notes |
|---|---|---|---|
| `args` | list | yes | Positional arguments, in order |
| `kwargs` | object | no | Keyword arguments |
| `expect` | any | see below | Expected return value |
| `raises` | string | see below | Exception type name the call must raise |
| `tolerance` | float | no | For float comparison. Absent means exact equality |

**Exactly one of `expect` or `raises` is required.** A case either ends by returning a
value or by raising — never both, and never neither. Setting both is a validation error,
because the author has not said which outcome they meant.

### `raises`

For missions that teach error handling: the case passes when the call raises an
exception whose type name matches exactly.

```yaml
hidden:
  - args: [-1]
    raises: ValueError
```

Three rules worth knowing before using it:

- **Exact type name, not subclass.** `raises: Exception` does *not* match a `ValueError`.
  In a teaching game "expected ValueError, got TypeError" is the message that helps;
  accepting any subclass would let an accidental crash pass as the intended answer.
- **Returning normally fails the case.** A submission that never validates anything does
  not quietly pass its error cases — it is told it returned a value where an exception
  was required.
- **Hidden cases still name the expected type.** This is the one documented exception to
  "hidden cases never reveal the expected value": the exception type is already stated
  in the brief, so repeating it leaks nothing. The input stays hidden.

### Hidden set must cover

- empty or degenerate input
- a single element
- boundary values: zero, negative, maximum
- the case that catches a hardcoded return
- type variations the brief allows

**Rule:** if returning a constant passes all visible tests, add hidden tests until it
does not.

---

## `hints`

| Field | Type | Required | Notes |
|---|---|---|---|
| `level` | int | yes | 1, 2, or 3. Unlocked in order |
| `text` | string | yes | See the rules below |

| Level | Gives | Never gives |
|---|---|---|
| 1 | A question pointing at the missing idea | Any code |
| 2 | The name of the construct or approach | Code for this problem |
| 3 | The pattern as code, different problem, different names | The assembled answer |

If pasting hint 3 solves the mission, rewrite hint 3.

---

## Validation

`tests/content/test_all_missions.py` enforces, for every file:

1. YAML parses with `safe_load`
2. All required fields present, types correct
3. `difficulty` is a valid enum value
4. `concepts` reference ids that exist in the syllabus
5. `signature.entrypoint` appears as a `def` — or an `async def` — in both `stub` and
   `solution`
6. `solution` passes every visible test
7. `solution` passes every hidden test
8. `id` is unique across the repository

A content pull request that fails any of these does not merge.
