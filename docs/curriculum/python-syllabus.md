# Python Syllabus

The concept map for the Python track. **Missions are written from this document, never
the other way around.**

Read `.claude/skills/curriculum-designer/SKILL.md` for the design rules.

---

## Concept record format

Every concept below follows this shape:

```
id            stable slug used in mission files
name          human name
prereqs       concept ids that must come first
objective     what the player can DO after, as a verb
misconceptions what beginners get wrong, specifically
mastery       the observable proof they got it
```

---

## Island 1 — Foundations

**Theme:** values, decisions, repetition
**Band:** elementary
**Missions:** 10

### Mission map

Each mission introduces **at most one** new concept. Everything else it touches has been
mastered already. The reinforce column is what keeps a concept from being introduced,
used once and forgotten.

The curve is a sawtooth, not a ramp: missions 3 and 9 are relief points that reuse the
previous concept in a friendlier shape. The feeling to design for is "that was hard, and
now I can do it again easily."

| # | Slug | Introduces | Reinforces | Note |
|---|---|---|---|---|
| 1 | `hello-value` | `variables` | — | The first mission anyone plays. Nothing to combine yet |
| 2 | `type-detective` | `basic-types` | `variables` | Uses no branching: `isinstance` joined with `and`/`not`. Conditionals arrive in 4 |
| 3 | `crate-label` | — | `basic-types`, `variables` | **Relief.** `str()` conversion, no branching either |
| 4 | `grade-or-fail` | `conditionals` | `basic-types` | Boundary values are the lesson |
| 5 | `count-the-vowels` | `for-loop` | `conditionals` | Loop plus a decision inside it |
| 6 | `sum-list` | `accumulator-pattern` | `for-loop` | |
| 7 | `longest-word` | — | `accumulator-pattern`, `conditionals`, `for-loop` | Accumulator that carries a *choice*, not a total |
| 8 | `countdown` | `while-loop` | `conditionals` | `range` forbidden, or it is a for-loop mission again |
| 9 | `guess-the-limit` | — | `while-loop`, `variables` | **Relief.** Same loop, friendlier framing |
| 10 | `stats-report` | — | all six | Closing mission: combine, do not learn. Sentinel-controlled loop |

**Missions 2 and 3 carry a constraint the map has to respect:** they teach types, and
types come before conditionals, so neither may need an `if`. Mission 2 gets there with a
boolean expression and mission 3 with plain concatenation. The first draft of mission 2
used an `if`/`elif` chain and had to be rewritten — the one-new-concept rule is easy to
break by accident when the natural solution reaches for a construct that has not been
taught yet.

Reinforcement count, which is the check that matters:

| Concept | Introduced | Reinforced in |
|---|---:|---|
| `variables` | 1 | 2, 10 |
| `basic-types` | 2 | 3, 4, 10 |
| `conditionals` | 4 | 5, 7, 8, 10 |
| `for-loop` | 5 | 6, 7, 10 |
| `accumulator-pattern` | 6 | 7, 10 |
| `while-loop` | 8 | 9, 10 |

Every concept is reused at least twice. No orphans.

### variables
- **prereqs:** none
- **objective:** store a value and read it back later
- **misconceptions:** thinking `=` means mathematical equality; thinking the name holds
  the value rather than pointing at it
- **mastery:** predicts the output after a reassignment

### basic-types
- **prereqs:** variables
- **objective:** tell int, float, str and bool apart and convert between them
- **misconceptions:** `"5" + 5` should work; `int("5.0")` should work
- **mastery:** predicts which conversions raise and which do not

### conditionals
- **prereqs:** basic-types
- **objective:** branch execution on a condition
- **misconceptions:** `elif` chains all evaluate; `=` used instead of `==`
- **mastery:** writes a three-branch decision with no unreachable branch

### for-loop
- **prereqs:** variables, basic-types
- **objective:** repeat an action once per item in a sequence
- **misconceptions:** the loop variable persists meaningfully after the loop; modifying
  a list while iterating it is safe
- **mastery:** predicts the number of passes for a given input

### while-loop
- **prereqs:** conditionals, for-loop
- **objective:** repeat until a condition changes
- **misconceptions:** forgetting to advance the condition, producing an infinite loop
- **mastery:** identifies which of two loops terminates and explains why

### accumulator-pattern
- **prereqs:** for-loop
- **objective:** carry a running result across every pass of a loop
- **misconceptions:** creating the accumulator inside the loop; returning inside the loop
- **mastery:** solves a sum, a count, and a string build with the same pattern

---

## Island 2 — Collections

**Theme:** grouping data
**Band:** elementary to simple
**Missions:** 10

Concepts: `lists`, `indexing-and-slicing`, `dictionaries`, `sets`, `tuples`,
`nested-structures`, `list-comprehension`, `when-not-to-comprehend`

Design note: teach comprehensions **after** the explicit loop version, and include at
least one mission where a comprehension is the wrong answer because readability loses.

---

## Island 3 — Functions

**Theme:** naming and reusing behavior
**Band:** simple
**Missions:** 10

Concepts: `parameters`, `return-values`, `default-arguments`, `mutable-default-trap`,
`scope`, `pure-vs-side-effects`, `args-kwargs`, `first-class-functions`

The mutable default argument trap deserves its own mission. It is the classic Python
gotcha and it teaches how default values are evaluated once at definition time.

---

## Island 4 — Strings and Text

**Band:** simple
Concepts: `string-methods`, `slicing`, `f-strings`, `join-vs-concat`, `split-and-parse`,
`encoding-basics`

---

## Island 5 — Errors and Edge Cases

**Band:** simple to moderate
Concepts: `exceptions`, `try-except`, `raising`, `custom-exceptions`, `eafp-vs-lbyl`,
`input-validation`, `defensive-design`

---

## Island 6 — Files and Data

**Band:** moderate
Concepts: `open-and-read`, `context-managers`, `writing-files`, `json`, `csv`, `paths`

---

## Island 7 — Objects

**Band:** moderate
Concepts: `classes`, `instances`, `methods`, `dunder-methods`, `dataclasses`,
`composition-over-inheritance`, `properties`

---

## Island 8 — Pythonic Patterns

**Band:** challenging
Concepts: `iterators`, `generators`, `yield`, `decorators`, `custom-context-managers`,
`unpacking`, `enumerate-zip`

---

## Island 9 — Algorithms

**Band:** challenging
Concepts: `big-o`, `linear-search`, `binary-search`, `sorting`, `recursion`,
`memoization`, `two-pointer`

---

## Island 10 — Async and Concurrency

**Band:** expert
Concepts: `blocking-vs-nonblocking`, `async-await`, `event-loop`, `gather`, `threads`,
`gil`, `when-concurrency-helps`

Design note: at least one mission must show a case where async makes things **slower**.
Knowing when not to reach for a tool is the harder half of the skill.

---

## Coverage checklist

Checked for **Island 1 only**. Islands 2 to 10 are sketched, not designed — they get their
own pass before their missions are written.

- [x] Every concept has an explicit prereq list
- [x] No concept appears in a mission before its prereqs — verified against the mission map
- [x] Every concept is reused in at least two later missions — see the reinforcement table
- [x] Objectives are verbs, never "understand"
- [x] Misconceptions are written, so hints can target them
- [x] The curve has relief missions after hard ones — missions 3 and 9
- [x] No mission introduces two new concepts

### What this document does not yet cover

Islands 2 to 10 list concepts but have no mission map, no prereq graph and no
misconceptions. That is deliberate: designing 90 missions now would freeze decisions that
building Islands 1 and 2 is going to change. Each island gets a pass like the one above
immediately before its content is written.
