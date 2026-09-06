---
name: curriculum-designer
description: Design the teaching plan for a language track — concept ordering, island structure, difficulty curve, prerequisites, and learning objectives. Use before writing any missions, when planning a new track (Python, Java, TypeScript), or when the difficulty curve feels wrong.
---

# Curriculum Designer

Missions are never written first. The syllabus comes first, missions implement it.
Output lives in `docs/curriculum/<language>-syllabus.md`.

## The unit of design is the concept, not the puzzle

A concept has:

- **id** — stable slug, e.g. `accumulator-pattern`
- **name** — human name
- **prerequisites** — concept ids that must be mastered first
- **objective** — what the player can DO after, phrased as a verb ("build a running
  total inside a loop"), never "understand loops"
- **misconceptions** — what beginners get wrong about it, in specific terms
- **mastery signal** — the observable thing that proves they got it

## Ordering rules

1. Never introduce two new concepts in one mission. One new thing, everything else
   already mastered.
2. A concept can only depend on concepts from the same island or an earlier one.
3. Every concept must be used again at least twice in later missions. Introduce, then
   reinforce, then combine. A concept used once is a concept forgotten.
4. Order by dependency, not by how the language documentation orders it. Docs are
   organized for reference, not for learning.

## Island design

An island is a coherent chapter, 8 to 12 missions, one theme, one difficulty band.

```yaml
id: foundations
name: Foundations
order: 1
theme: "Values, decisions, and repetition"
concepts: [variables, types, conditionals, for-loop, accumulator-pattern]
unlock_requires:
  missions_completed: 0
completion_reward_xp: 120
```

Difficulty bands map to islands, not to individual missions inside them:

| Band | Islands | What it means |
|---|---|---|
| elementary | 1-2 | One concept, guided, hints are generous |
| simple | 3-4 | Two known concepts combined |
| moderate | 5-8 | Player must choose the approach |
| challenging | 9-10 | Efficiency and edge cases matter |
| expert | 11+ | Open-ended, multiple valid designs |

## The difficulty curve

Aim for a sawtooth, not a ramp. After a hard mission, put an easier one that reuses
the same concept in a friendlier shape. Constant escalation burns people out. The
feeling to design for is "that was hard, and now I can do it again easily."

## Python track shape (v1.1 reference)

1. **Foundations** — variables, types, conditionals, loops, accumulator
2. **Collections** — lists, dicts, sets, tuples, comprehensions, when NOT to comprehend
3. **Functions** — parameters, defaults, return values, scope, pure vs side effects
4. **Strings and text** — slicing, formatting, parsing, encoding basics
5. **Errors and edge cases** — exceptions, validation, defensive design
6. **Debugging** — reading tracebacks, print-debugging, bisection, the debugger, logic vs data
7. **Files and data** — reading, writing, JSON, CSV, context managers
8. **Objects** — classes, methods, dataclasses, composition over inheritance
9. **Pythonic patterns** — iterators, generators, decorators, context managers
10. **Algorithms** — complexity, searching, sorting, recursion
11. **Async and concurrency** — when it helps, when it does not

## Cross-cutting tracks (v1.3)

These reuse the same engine but the missions are shaped differently:

- **Architecture** — the brief gives working but bad code, the task is to restructure it
- **Security** — the brief gives vulnerable code, the task is to find and fix the flaw
- **AI Engineering** — build a chunker, a retriever, a prompt template, an eval harness

## Checklist before signing off a syllabus

- [ ] Every concept has an explicit prerequisite list
- [ ] No orphan concepts (introduced, never reused)
- [ ] No concept appears before its prerequisite
- [ ] Objectives are verbs, not "understand"
- [ ] Misconceptions written for each concept, so mission hints can target them
- [ ] The curve has relief points, not constant escalation
