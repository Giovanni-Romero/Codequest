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
**Missions:** 8

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

- [ ] Every concept has an explicit prereq list
- [ ] No concept appears in a mission before its prereqs
- [ ] Every concept is reused in at least two later missions
- [ ] Objectives are verbs, never "understand"
- [ ] Misconceptions are written, so hints can target them
- [ ] The curve has relief missions after hard ones
