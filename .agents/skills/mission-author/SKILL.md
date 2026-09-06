---
name: mission-author
description: Write and review individual mission YAML files — the playful teaching material, analogies, briefs, test cases, and layered hints. Use when creating a new mission, improving an existing one, or checking that a mission's teaching quality and tests are good enough to ship.
---

# Mission Author

This is the one skill where the agent DOES write content freely. Missions are data,
not implementation code, and writing them is the pedagogical work of the project.

Before writing any mission, read the syllabus in `docs/curriculum/` and confirm which
concept this mission introduces. One mission introduces exactly one new concept.

## File location

`content/<language>/islands/<NN>-<island>/missions/<NN>-<slug>.yaml`

## Every mission ships bilingual: English, then a Portuguese mirror

Established with the Foundations island (`content/python-pt/`). Once the English
mission in `content/python/` is finished and passes review, produce its mirror in
`content/python-pt/` at the identical path. Rules for the mirror, no exceptions:

- `id`, `track`, `island`, `order`, `difficulty`, `xp`, `concepts`, `tags`,
  `signature.entrypoint`, `tests`, `constraints`, and `solution` are **byte-identical**
  to the English file. These are keyed into the save's progress table and checked by
  the same hidden tests in both languages — changing any of them breaks a save that
  switches language mid-game, or lets the two language versions silently test
  different things.
- Only prose gets translated: `title`, `teaching.*`, `brief`, `hints[].text`, and any
  comment inside `signature.stub` that isn't the entrypoint line itself.
- Translate the *teaching*, not just the words — an analogy that only works as a pun in
  English needs a real Portuguese equivalent, not a literal translation that loses the
  shape. If the analogy breaks in translation, find a new one for that language rather
  than force the original through.
- Run `codequest check --content content --track python-pt` after the mirror is done —
  the same solution file, unchanged, must still pass every hidden test. `--content` is
  the *root* content directory, not the language folder itself: `MissionService` joins
  `--content` with `--track` to find `track.yaml` (`<content>/<track>/track.yaml`), so
  `--content content/python-pt` doubles up into `content/python-pt/python-pt/track.yaml`
  and fails with a confusing `FileNotFoundError`. `python-pt` is a **directory name**
  passed as `--track`, not a second track id — the loaded `Track.id` inside the file is
  still `python` either way.

## The teaching block is the heart

Order matters. Analogy first, because intuition before formalism.

### analogy
A situation from ordinary life that has the same *shape* as the concept. Test it by
asking: does the mapping break down immediately? If yes, find another.

Good: a dictionary is a coat check. You hand over a coat, get a numbered ticket, and
the ticket is the only way back to that specific coat.

Bad: a dictionary is like a real dictionary. This explains nothing, it just renames.

### explanation
Three to six short sentences. Plain words. Define the term after the intuition exists,
never before.

### worked_example
Five to ten lines, complete and runnable, in a domain unrelated to the mission task.
If the mission asks for a sum, the example should use string concatenation. Otherwise
you have handed over the answer.

### key_points
Three to five bullets. Each one targets a specific misconception from the syllabus.
Phrase them as rules with a reason attached.

## The brief

Say what the function must do, not how. Include the shape of input and output. State
constraints in words as well as in the `constraints` block, because players read prose.

Add a light narrative frame if it helps, but never let the story hide the requirement.
Fun is a wrapper, clarity is the payload.

## Tests

**Visible tests teach.** Two or three, simple, representative. The player sees these
and uses them to understand the shape of the problem.

**Hidden tests verify.** Four or more, covering:

- empty input
- single element
- boundary values (zero, negative, maximum)
- the case that catches a hardcoded answer
- type variations the brief allows (int vs float, upper vs lower case)

If a player can pass all visible tests by returning a constant, the hidden set is not
doing its job.

## Hints are layered, never a solution

| Level | Gives |
|---|---|
| 1 | A question that points at the missing idea. No code. |
| 2 | Names the construct or the approach. Still no code for this problem. |
| 3 | A code fragment of the *pattern*, using different variable names and a different context. |

Level 3 must still leave assembly to the player. If pasting hint 3 solves the mission,
rewrite it.

## Required fields checklist

- [ ] `id` unique across the whole repo, format `<lang>-<island>-<NN>`
- [ ] `concepts` list matches ids that exist in the syllabus
- [ ] `difficulty` matches the island's band
- [ ] `xp` proportional to difficulty (elementary 10, expert 60)
- [ ] `signature.entrypoint` matches the function name in `stub` and in `solution`
- [ ] `constraints.forbidden_builtins` blocks the shortcut that skips the lesson
- [ ] `solution` present and passes every test, visible and hidden
- [ ] `tests.hidden` includes at least one empty or degenerate input

## Quality review questions

1. Can a player who read only the teaching block solve this? If not, teaching is thin.
2. Can a player skip the teaching block and still solve it? If yes, the mission is not
   teaching the concept, it is testing prior knowledge.
3. Does the analogy hold up if you push on it a little?
4. Does hint 3 give the answer away? It must not.
5. Would a hardcoded return value pass? Add a hidden test until the answer is no.
6. Is the brief unambiguous about the return type and the empty case?

## Tone rules for all written content

- Short, direct sentences.
- Simple vocabulary. No academic connectors.
- Second person, present tense: "you build a total", not "one shall accumulate".
- Never condescending. The player is an adult learning something new.
