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
5. `signature.entrypoint` appears as a `def` in both `stub` and `solution`
6. `solution` passes every visible test
7. `solution` passes every hidden test
8. `id` is unique across the repository

A content pull request that fails any of these does not merge.
