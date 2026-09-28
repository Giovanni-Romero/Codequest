# Python Syllabus

The concept map for the Python track. **Missions are written from this document, never
the other way around.**

Read `.agents/skills/curriculum-designer/SKILL.md` for the design rules.

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
**Missions:** 12

### Mission map

| # | Slug | Introduces | Reinforces | Note |
|---|---|---|---|---|
| 1 | `the-cargo-manifest` | `lists` | `for-loop` | Build a list by appending in a loop, read it back |
| 2 | `find-the-crate` | `indexing-and-slicing` | `lists` | Negative index and a slice, same expression family. Slices never raise |
| 3 | `tally-the-hold` | — | `lists` | **Relief.** Filter into a new list with a loop and `if`. Setup for mission 9's rewrite |
| 4 | `the-quartermasters-ledger` | `dictionaries` | — | `.get(key, default)` versus `[key]` and `KeyError` |
| 5 | `the-uniqueness-of-flags` | `sets` | `lists` | Dedupe a list of signal flags with `set(...)` |
| 6 | `fixed-coordinates` | `tuples` | — | Unpack two values, build and return a fixed pair |
| 7 | `safe-harbor-check` | — | `dictionaries`, `sets`, `tuples`, `lists`, `indexing-and-slicing` | **Relief.** All five at once, nothing new |
| 8 | `the-manifest-within-the-manifest` | `nested-structures` | `lists`, `dictionaries` | A dict of lists of dicts, one value updated in place |
| 9 | `rewrite-the-tally` | `list-comprehension` | `lists` | Deliberate callback: mission 3's task, rewritten in one line |
| 10 | `when-clever-hurts` | `when-not-to-comprehend` | `dictionaries`, `nested-structures` | A nested comprehension is technically valid and a bad idea |
| 11 | `the-readable-report` | — | `list-comprehension`, `indexing-and-slicing`, `nested-structures`, `when-not-to-comprehend` | **Relief**, and the judgment call reversed: here a comprehension *is* the clean choice |
| 12 | `full-cargo-report` | — | `lists`, `dictionaries`, `sets`, `tuples`, `nested-structures`, `list-comprehension`, `when-not-to-comprehend` | Closing mission. Combine, do not learn |

Same sawtooth shape as Island 1: three relief missions (3, 7, 11) break up the six
concept-heavy stretches, and the closing mission asks for no new construct, only
assembly.

**Design constraint respected:** `list-comprehension` cannot be taught before `for-loop`
and `conditionals` exist (both do, from Island 1) and before `lists` exists (mission 1).
Mission 9 is deliberately the rewrite of mission 3's task — the player has already solved
it the explicit way, so the comprehension reads as a translation, not a new idea from
nothing.

**A structural limit worth naming, discovered while designing this island:** every
mission argument and return value crosses a JSON boundary between the game process and
the sandboxed subprocess (see `engine/harness.py`). JSON has no tuple type and no set
type — anything shaped like one arrives as a plain list. This is why `tuples` and `sets`
missions never claim a parameter *is* a tuple or a set: the brief describes shape and
behavior ("a fixed pair", "no duplicates"), and the *solution* is what constructs a real
`tuple` or `set` internally, which the harness is free to flatten back to a list or array
on the way out. Future islands hit this same wall the moment they try to test a
generator, a custom object, or anything else `json.dumps` cannot carry — plan the mission
around what the solution builds, not around what the test harness can hand it as input.

Reinforcement count:

| Concept | Introduced | Reinforced in |
|---|---:|---|
| `lists` | 1 | 2, 3, 5, 7, 8, 9, 12 |
| `indexing-and-slicing` | 2 | 7, 11 |
| `dictionaries` | 4 | 7, 8, 10, 11, 12 |
| `sets` | 5 | 7, 12 |
| `tuples` | 6 | 7, 12 |
| `nested-structures` | 8 | 10, 11, 12 |
| `list-comprehension` | 9 | 11, 12 |
| `when-not-to-comprehend` | 10 | 11, 12 |

Every concept is reused at least twice. No orphans.

### lists
- **prereqs:** variables, for-loop
- **objective:** build a sequence of values, add to it, and read it back by walking it
- **misconceptions:** `b = a` copies the list (it aliases the same list — mutating `b`
  mutates `a`); indexing starts at 1
- **mastery:** predicts what a second variable shows after the first is mutated through
  an alias

### indexing-and-slicing
- **prereqs:** lists
- **objective:** retrieve one item by position, including from the end, and a sub-range
  as a slice
- **misconceptions:** `list[-1]` is an error; `list[2:5]` includes index 5; a slice past
  the end raises the same error a single out-of-range index does
- **mastery:** predicts the exact result of a slice with an out-of-range bound (a short
  or empty list, never an error) versus a single out-of-range index (`IndexError`)

### dictionaries
- **prereqs:** variables, basic-types
- **objective:** store and retrieve a value by a meaningful key instead of a position
- **misconceptions:** `d[key]` on a missing key returns `None` instead of raising;
  `.get(key)` and `d[key]` behave the same way on a miss
- **mastery:** predicts whether a given lookup raises `KeyError` or returns a default,
  and which of `[key]` or `.get()` produces which

### sets
- **prereqs:** lists
- **objective:** deduplicate a collection and test membership without caring about order
- **misconceptions:** a set preserves the order values were added in; converting a list
  to a set and back preserves the original order
- **mastery:** predicts the contents of `set(a_list_with_duplicates)`, understanding that
  order is not part of the guarantee

### tuples
- **prereqs:** lists, indexing-and-slicing
- **objective:** build a fixed group of values and unpack it into named variables
- **misconceptions:** `(1)` is a one-element tuple (it is just the int `1` — the comma is
  what makes a tuple, not the parentheses); a tuple supports `.append()` like a list does
- **mastery:** predicts a `TypeError` from mutating a tuple, and correctly unpacks one
  into the right number of names

### nested-structures
- **prereqs:** lists, dictionaries
- **objective:** read and update one value buried inside nested lists and dictionaries
  without rebuilding the whole structure
- **misconceptions:** believing a nested value must be reassigned as a whole to change
  one field inside it; losing track of which brackets index a list (position) versus a
  dict (key)
- **mastery:** writes a chained access (`data["key"][0]["other"]`) that updates one
  nested value and leaves the rest of the structure untouched

### list-comprehension
- **prereqs:** lists, for-loop, conditionals
- **objective:** build a new list from an existing one in a single expression
- **misconceptions:** believing a comprehension is for side effects (printing, mutating
  something else) rather than for building a new list; forgetting that the trailing
  `if` filters items while an `if/else` before the expression transforms them
- **mastery:** rewrites an explicit `for` loop that appends into a list as an equivalent
  comprehension, and explains what each part of the comprehension does

### when-not-to-comprehend
- **prereqs:** list-comprehension
- **objective:** recognize when a comprehension hurts readability and choose an explicit
  loop instead
- **misconceptions:** believing shorter code is always better code; nesting
  comprehensions inside comprehensions because the language allows it
- **mastery:** given a comprehension nested two levels deep, rewrites it as a clearer
  loop and states in one sentence why the loop is the better choice here

---

## Island 3 — Functions

**Theme:** naming and reusing behavior
**Band:** simple
**Missions:** 12

### What this island can honestly claim to introduce

The player has been writing functions with parameters and `return` since **Island 1,
mission 1** — twenty-two missions ago. Presenting `parameters` and `return-values` as
brand new concepts would be a lie the player can see through.

What this island genuinely adds, and what the missions actually teach:

- **`parameters`** — the *names* are part of the function's public contract, not an
  internal detail. This is enforceable, not just assertable: hidden cases call the
  function **by keyword**, so renaming a parameter breaks the mission.
- **`return-values`** — `return` leaves the function *immediately*, including from
  inside a loop (the guard-clause shape), and a function that runs off the end returns
  `None` rather than nothing.

Both make explicit what was implicit. That is legitimate curriculum design, and saying
so is better than pretending otherwise.

### Mission map

| # | Slug | Introduces | Reinforces | Note |
|---|---|---|---|---|
| 1 | `the-signalers-vocabulary` | `parameters` | — | Hidden cases call by keyword: the names are the contract |
| 2 | `turn-back-early` | `return-values` | `parameters` | `return` from inside a loop; falling off the end gives `None` |
| 3 | `the-two-lookouts` | — | `parameters`, `return-values` | **Relief.** One function calling another, nothing new |
| 4 | `the-standing-order` | `default-arguments` | `parameters` | An optional parameter with a sensible default |
| 5 | `the-shared-crate` | `mutable-default-trap` | `default-arguments`, `lists` | The classic gotcha. Needs a helper called twice in one invocation |
| 6 | `the-private-notebook` | `scope` | `parameters` | Reading an outer name works; assigning creates a new local |
| 7 | `the-quartermasters-round` | — | `default-arguments`, `scope`, `return-values` | **Relief.** |
| 8 | `leave-no-trace` | `pure-vs-side-effects` | `scope`, `lists`, `mutable-default-trap` | Helper called twice on one list exposes the mutation |
| 9 | `the-ships-log` | `args-kwargs` | `parameters`, `default-arguments` | First mission in the repo to use `kwargs:` in its tests |
| 10 | `the-order-book` | `first-class-functions` | `parameters`, `return-values`, `dictionaries` | Dispatch table — see the JSON-boundary note below |
| 11 | `choosing-the-tool` | — | `first-class-functions`, `args-kwargs`, `default-arguments` | **Relief.** The three previous constructs standing side by side |
| 12 | `the-full-watch` | — | all eight | Closing mission. Combine, do not learn |

Same sawtooth as Islands 1 and 2: three relief missions (3, 7, 11) break up the
concept-heavy stretches, and the closing mission asks for no new construct.

Relief missions are marked `elementary` (10 XP) while the rest are `simple` (20 XP).
The band names the island's ceiling; relief deliberately sits below it. Island 2 does
the same thing.

Reinforcement count:

| Concept | Introduced | Reinforced in |
|---|---:|---|
| `parameters` | 1 | 2, 3, 4, 6, 9, 10, 12 |
| `return-values` | 2 | 3, 7, 10, 12 |
| `default-arguments` | 4 | 5, 7, 9, 11, 12 |
| `mutable-default-trap` | 5 | 8, 12 |
| `scope` | 6 | 7, 8, 12 |
| `pure-vs-side-effects` | 8 | 10, 12 |
| `args-kwargs` | 9 | 11, 12 |
| `first-class-functions` | 10 | 11, 12 |

Every concept is reused at least twice. No orphans.

Two of those reinforcements are quieter than the rest and worth naming, so a later
reader does not mistake them for padding. Mission 10 reinforces purity in one line — an
unknown drill returns `list(numbers)`, a copy, rather than handing the caller's own list
straight back. Mission 12 does the same through a comprehension that builds a new list
of breaches instead of filtering the readings in place.

### Engine limits this island had to design around

Verified against the code before the missions were written, not assumed:

**One fresh subprocess per test case.** `services/game_session.py` calls the runner's
`execute()` once per case, and each call spawns a new process that re-imports the
submission (`engine/runners/python.py`). Every default argument object is therefore
rebuilt for every case.

The direct consequence: **the mutable-default trap is invisible across test cases.** It
only manifests on a *second* call to the same function object, and there is never a
second call. Mission 5 works around this by requiring a shape where the entrypoint calls
a helper twice **within a single invocation** — that is the only way the shared list
becomes observable. Mission 8 uses the same structural trick for the same reason: a
helper that mutates its caller's list is only detectable if something calls it twice.

**A function cannot cross the JSON boundary.** `engine/harness.py` falls back to
`repr(value)` for any non-serializable return, and a function's `repr` contains its
memory address — different on every run. A function can be neither passed in as a test
argument nor returned as a result. Mission 10 therefore teaches first-class functions as
a **dispatch table**: the test passes the operation's *name* as a string, and the player
builds a `dict` of name to function and calls the chosen one. Same lesson — a function is
a value you can store, pass and call — with nothing unserializable crossing the boundary.

**`scope` is teachable but only partly enforceable.** A player who reaches for `global`
still passes, because the function is called exactly once per process. Mission 6 teaches
the concept and tests the correct result; it cannot fail every wrong approach. Worth
stating rather than pretending the coverage is tighter than it is.

**Nothing can assert on printed output.** The player's `stdout` is captured
(`engine/runners/python.py`) but never compared against anything. No mission today can
verify what was printed. **Island 6 (Debugging) wants to teach print-debugging** and will
need either a new engine capability or a different framing — flagged here so it is found
at design time rather than halfway through authoring that island.

### parameters
- **prereqs:** none beyond writing a function at all (Island 1)
- **objective:** name a function's parameters deliberately, knowing callers may pass them
  by name and not only by position
- **misconceptions:** believing parameter names are private to the function body and free
  to rename; believing arguments are matched by type or by meaning rather than strictly
  by position (or by name, when named)
- **mastery:** the function still works when a caller supplies some arguments positionally
  and others by keyword

### return-values
- **prereqs:** parameters
- **objective:** end a function early with a result, from anywhere in its body
- **misconceptions:** thinking `return` inside a loop somehow finishes the loop and
  carries on with the rest of the function; thinking a function with no `return` gives
  back nothing rather than `None`; confusing `print` with `return`
- **mastery:** predicts what a function returns when no branch reaches a `return`, and
  writes a loop that exits on its first match instead of scanning the whole sequence

### default-arguments
- **prereqs:** parameters
- **objective:** make a parameter optional by giving it a default, so the common call is
  short and the unusual call is still possible
- **misconceptions:** believing the default expression runs fresh on each call (it runs
  once, at definition); putting a parameter with a default before one without and
  expecting it to work
- **mastery:** calls the same function with and without the optional argument and
  predicts both results

### mutable-default-trap
- **prereqs:** default-arguments, lists
- **objective:** recognize that a mutable default is created once and shared by every
  call, and use the `None` sentinel instead
- **misconceptions:** believing `def f(x, acc=[])` gives each call its own empty list;
  believing the bug is in the caller rather than in the definition
- **mastery:** explains why the second call to a function with `acc=[]` sees the first
  call's data, and rewrites it with `acc=None` plus `if acc is None:`

### scope
- **prereqs:** parameters
- **objective:** know which names a function can see, which it creates, and which vanish
  when it returns
- **misconceptions:** believing a variable assigned inside a function is visible outside
  afterwards; believing you can read a module-level name and then assign to it in the
  same function without `global` (that raises `UnboundLocalError`)
- **mastery:** predicts whether a given function reads the outer name, creates a local
  one, or raises `UnboundLocalError`

### pure-vs-side-effects
- **prereqs:** scope, lists
- **objective:** write a function whose result depends only on its arguments and which
  changes nothing outside itself
- **misconceptions:** believing that receiving a list means receiving a copy of it;
  believing that returning the list you just mutated makes the mutation harmless
- **mastery:** given a function that calls `items.append(...)` on a parameter, explains
  what the caller's list looks like afterwards, and rewrites it to leave the caller alone

### args-kwargs
- **prereqs:** parameters, default-arguments
- **objective:** accept a variable number of positional and keyword arguments
- **misconceptions:** believing `*args` and `**kwargs` are magic names rather than
  ordinary parameters with a `*`/`**` prefix; expecting `*args` to be a list (it is a
  tuple); putting `**kwargs` before `*args`
- **mastery:** writes a function that works when called with two extra positional
  arguments, with two keyword arguments, and with neither

### first-class-functions
- **prereqs:** parameters, return-values, dictionaries
- **objective:** store functions as values and choose which one to call at runtime
- **misconceptions:** confusing `f` (the function itself) with `f()` (calling it and
  taking the result) — the single most common error here; believing a function must be
  called where it is defined
- **mastery:** builds a dictionary mapping names to functions and calls the one a
  parameter selects, without a chain of `if`/`elif`

---

## Island 4 — Strings and Text

**Theme:** text is data, and it does not change under you
**Band:** simple
**Missions:** 10

### A scope correction to the original sketch

The sketch listed `slicing`. **It is removed.** Island 2 already taught the whole
operator in `find-the-crate` — exclusive end bound, negative indices, and the rule that
a slice never raises for an out-of-range bound. Slicing a string uses that same syntax
with the same semantics. Calling it new here would be the same dishonesty that
`parameters` would have been in Island 3.

In its place: **`string-immutability`**, which is the genuine difference between slicing
a list and slicing a string. `s[0] = "x"` raises `TypeError`, so every "change" to text
is really the construction of new text. That is a real idea with a real consequence, and
it is what makes `join-vs-concat` matter two missions later.

**Final concepts (6):** `string-methods`, `string-immutability`, `f-strings`,
`join-vs-concat`, `split-and-parse`, `encoding-basics`

### What the player has already seen

A grep of `content/tracks/python/locales/en/` before designing: `.upper()` appears in the worked example of
Island 1 mission 5 and `.upper()`/`.lower()` in Island 3 mission 10's, but **never in a
`solution` the player had to write**. `.join`, `.split`, `.strip`, `.replace` and
f-strings appear nowhere at all. So this island genuinely introduces all six, and the two
prior sightings are recognition, not competence.

### Mission map

| # | Slug | Introduces | Reinforces | Note |
|---|---|---|---|---|
| 1 | `the-smudged-manifest` | `string-methods` | — | `.strip`, `.lower`, `.replace`, `.startswith` — the ones that solve real problems |
| 2 | `the-carved-nameplate` | `string-immutability` | `string-methods`, `indexing-and-slicing` | A player who tries `s[0] = "x"` gets `TypeError` and the lesson arrives on its own |
| 3 | `the-tidy-roster` | — | `string-methods`, `lists` | **Relief.** Clean a list of names, nothing new |
| 4 | `the-printed-label` | `f-strings` | `string-methods` | After 34 missions of `+ str(x) +`, this is relief disguised as a concept |
| 5 | `one-rope-from-many` | `join-vs-concat` | `string-immutability`, `lists` | The `+`-in-a-loop that Island 3 deliberately avoided finally gets its tool |
| 6 | `the-signal-sheet` | — | `f-strings`, `join-vs-concat` | **Relief.** |
| 7 | `reading-the-cargo-line` | `split-and-parse` | `lists`, `string-methods` | Text into structured data |
| 8 | `the-weight-of-words` | `encoding-basics` | `string-methods` | Characters are not bytes. See the constraint below |
| 9 | `the-clean-line` | — | `split-and-parse`, `f-strings`, `string-methods` | **Relief.** |
| 10 | `the-full-manifest` | — | all six | Closing mission. Combine, do not learn |

Same sawtooth as Islands 2 and 3: relief at 3, 6 and 9.

Reinforcement count:

| Concept | Introduced | Reinforced in |
|---|---:|---|
| `string-methods` | 1 | 2, 3, 4, 7, 8, 9, 10 |
| `string-immutability` | 2 | 5, 10 |
| `f-strings` | 4 | 6, 9, 10 |
| `join-vs-concat` | 5 | 6, 10 |
| `split-and-parse` | 7 | 9, 10 |
| `encoding-basics` | 8 | 10 |

`encoding-basics` is reinforced only in the closing mission. That is one short of the
two-reuse rule and it is a deliberate, named exception: the concept's whole payload is a
single realisation (a character is not a byte), and manufacturing a second mission around
it would be padding. The closing mission carries it properly rather than in passing.

### The engine constraint this island had to design around

**`bytes` does not cross the JSON boundary.** Same wall that functions hit in Island 3:
`engine/harness.py` falls back to `repr` for anything `json.dumps` cannot carry, so a
mission can neither receive nor return `bytes`.

Mission 8 works around it by returning **counts**: `len(text)` against
`len(text.encode("utf-8"))`. That is exactly the lesson worth having — the same string is
5 characters and 7 bytes — and an integer crosses the boundary cleanly. Nothing is lost
by not handing the player a `bytes` object they could not return anyway.

The PT-BR content tree is itself the proof that UTF-8 round-trips correctly through the
whole pipeline, accents and all.

### string-methods
- **prereqs:** basic-types
- **objective:** clean and inspect text with the methods that do the work, instead of
  looping over characters by hand
- **misconceptions:** believing `.strip()` removes spaces from the middle (it only trims
  the ends); believing `.replace()` changes the string in place; reaching for a loop when
  a method already exists
- **mastery:** picks the right method for "trim", "case-fold", "substitute" and "test the
  start" without writing a loop

### string-immutability
- **prereqs:** string-methods, indexing-and-slicing
- **objective:** build a new string when text must change, because the old one cannot
- **misconceptions:** believing `s[0] = "X"` works the way `list[0] = x` does; believing
  `s.replace(...)` or `s.upper()` modifies `s` rather than returning something new;
  forgetting to assign the result of a string method
- **mastery:** predicts what `s` holds after a line that calls a method on it without
  assigning, and explains why `s[0] = "X"` raises

### f-strings
- **prereqs:** string-methods, basic-types
- **objective:** build a readable line of text from values without a chain of `+` and
  `str()`
- **misconceptions:** forgetting the `f` prefix and getting the braces printed literally;
  believing an f-string can be reused as a template later (it is evaluated immediately,
  once)
- **mastery:** rewrites a `+ str(x) +` chain as an f-string and gets identical output

### join-vs-concat
- **prereqs:** string-immutability, lists
- **objective:** assemble many pieces into one string with a separator, in one operation
- **misconceptions:** thinking `"".join` is called on the list rather than on the
  separator; trying to join a list of numbers without converting them first; believing
  `+` in a loop is equivalent (it is correct but builds a new string every pass)
- **mastery:** joins a list with a separator without a trailing separator to clean up
  afterwards

### split-and-parse
- **prereqs:** string-methods, lists
- **objective:** turn one line of text into the separate values it carries
- **misconceptions:** believing `.split()` with no argument and `.split(" ")` behave the
  same (they differ on runs of whitespace); forgetting that every piece comes back as a
  string and needs converting; not stripping the pieces before using them
- **mastery:** parses a delimited line into typed values, surviving stray whitespace

### encoding-basics
- **prereqs:** string-methods
- **objective:** tell the length of a string in characters apart from its length in bytes
- **misconceptions:** believing one character is always one byte; believing a string has
  an encoding (it does not — bytes do, and encoding is what converts between them)
- **mastery:** predicts that an accented character costs more than one byte in UTF-8 and
  explains why the character count is unchanged

---

## Island 5 — Errors and Edge Cases

**Theme:** what to do when the answer does not exist
**Band:** simple to moderate
**Missions:** 10

### A scope correction: `custom-exceptions` moves to Island 8

Defining your own exception is `class ShortfallError(Exception): pass` — a **class
definition**, and classes are not taught until Island 8 (Objects). Keeping it here would
repeat exactly the mistake Island 3 caught in time with `.join`, which belongs to
Island 4.

`custom-exceptions` is therefore **listed under Island 8**, where `class` exists and it
costs nothing to teach. Island 5 teaches raising the built-in exceptions, which is the
skill that actually comes first in practice anyway.

**Final concepts (6):** `exceptions`, `try-except`, `raising`, `eafp-vs-lbyl`,
`input-validation`, `defensive-design`

### This island required an engine change

None of `raising`, `input-validation` or `defensive-design` was authorable before this
island was designed. `TestCase` had no way to say "this case passes by raising", and
`engine/evaluator.py` treated every exception as a failure — so a mission demanding
`raise ValueError` would have failed its own solution.

The `raises:` test-case field was built first, as a prerequisite. See
`docs/mission-schema.md` for the contract; the short version is that a case declares
either `expect` or `raises`, never both, and the exception type is matched by exact name
rather than by subclass so that an accidental `TypeError` cannot pass as the intended
`ValueError`.

### Mission map

| # | Slug | Introduces | Reinforces | Note |
|---|---|---|---|---|
| 1 | `let-it-through` | `exceptions` | — | An error ends the call and travels up. The only mission here whose right answer is *not* to handle it |
| 2 | `the-safe-sounding` | `try-except` | `exceptions` | Catch, and return a fallback |
| 3 | `the-forgiving-ledger` | — | `try-except`, `dictionaries` | **Relief.** |
| 4 | `refuse-the-order` | `raising` | `exceptions`, `conditionals` | Raise `ValueError` yourself on bad input |
| 5 | `permission-or-forgiveness` | `eafp-vs-lbyl` | `try-except`, `raising` | Two styles, same result, different costs |
| 6 | `the-second-opinion` | — | `eafp-vs-lbyl`, `try-except` | **Relief.** |
| 7 | `the-harbour-inspection` | `input-validation` | `raising`, `string-methods` | Validate at the boundary, before anything else runs |
| 8 | `fail-loudly` | `defensive-design` | `input-validation`, `raising`, `f-strings` | Fail early, and with a message that helps someone |
| 9 | `the-careful-clerk` | — | `try-except`, `input-validation`, `defensive-design` | **Relief.** |
| 10 | `the-whole-watch` | — | all six | Closing mission. Combine, do not learn |

Relief at 3, 6 and 9, matching the three islands before it.

Mission 1 introducing `exceptions` *before* `try-except` is deliberate. A player has to
watch an error end a call and propagate before catching one means anything — otherwise
`try/except` is a ritual with no observed problem behind it. It is the only mission in
the island where the correct submission lets the error escape, and the `raises:` field is
what makes that verifiable rather than merely asserted.

Reinforcement count:

| Concept | Introduced | Reinforced in |
|---|---:|---|
| `exceptions` | 1 | 2, 4, 10 |
| `try-except` | 2 | 3, 5, 6, 9, 10 |
| `raising` | 4 | 5, 7, 8, 10 |
| `eafp-vs-lbyl` | 5 | 6, 10 |
| `input-validation` | 7 | 8, 9, 10 |
| `defensive-design` | 8 | 9, 10 |

Every concept is reused at least twice. No orphans.

### exceptions
- **prereqs:** return-values
- **objective:** predict which operations raise, and know that an unhandled one ends the
  call and travels to whoever called it
- **misconceptions:** believing an error "returns" something the caller can inspect;
  believing code after the failing line still runs; believing every error must be caught
  wherever it happens
- **mastery:** says what a function returns when a line inside it raises and nothing
  catches it — the answer being that it returns nothing at all

### try-except
- **prereqs:** exceptions
- **objective:** catch a specific failure and continue with a sensible fallback
- **misconceptions:** catching bare `except:` and swallowing errors nobody meant to
  handle, including typos; putting more lines than necessary inside the `try`, so an
  unrelated failure is caught by the wrong handler; believing `except` runs even when
  nothing failed
- **mastery:** catches one named exception, leaves everything else to propagate, and
  keeps the `try` block down to the line that can actually fail

### raising
- **prereqs:** exceptions, conditionals
- **objective:** stop a function that has been given something it cannot work with
- **misconceptions:** returning an error string or `-1` instead of raising, so the caller
  can ignore it silently; believing `raise` needs to be caught in the same function to
  have any effect
- **mastery:** refuses invalid input with the exception type that fits it, and lets the
  caller decide what to do

### eafp-vs-lbyl
- **prereqs:** try-except, raising
- **objective:** choose between checking first and trying first, on purpose
- **misconceptions:** believing one style is always correct; not seeing that a check
  followed by an action has a gap between them where the world can change
- **mastery:** writes the same behaviour both ways and names one situation where each is
  the better fit

### input-validation
- **prereqs:** raising, string-methods
- **objective:** reject bad input at the edge, before it reaches the logic that assumes
  it is good
- **misconceptions:** validating deep inside, after several transformations have already
  run on the bad value; validating the type but not the range or the shape; trusting a
  value because it came from another part of your own program
- **mastery:** rejects every invalid case at the top of the function, so the rest of the
  body can assume its inputs are sound

### defensive-design
- **prereqs:** input-validation, raising
- **objective:** fail early and with a message that tells the reader what to do
- **misconceptions:** believing "defensive" means catching everything and continuing;
  writing error messages that state what happened but not what was expected; letting a
  function limp on with a value it knows is wrong
- **mastery:** writes a failure message naming both the offending value and the rule it
  broke

---

## Island 6 — Debugging

**Theme:** finding out why, not guessing
**Band:** moderate
**Missions:** 10

Added after Island 5 on purpose: reading a traceback usefully depends on already knowing
what an exception is. This island teaches no new syntax at all — it teaches what to do
with your own eyes and hands when a program you already know how to write is not doing
what you meant.

**Concepts (6):** `reading-tracebacks`, `logic-vs-data`, `print-debugging`,
`interactive-debugger`, `bisection`, `assert-as-diagnosis`

### The mission shape changes here, and it has to

Every island so far handed the player an empty skeleton to fill in. Most of this island
hands them **complete code that is wrong**, and the job is to find the bug and fix it.

That is not a stylistic choice. You cannot practise debugging on code that does not exist
yet, and a skeleton mission teaches authoring, not investigation. The engine supports
this today with no change: `signature.stub` is only pre-filled editor content, and
`tests/content/test_all_missions.py` verifies that the *solution* passes — it never
requires the stub to fail.

**Every planted bug is a misconception an earlier island warned about.** The accumulator
created inside the loop (Island 1), the helper that mutates its caller's list (Island 3),
`>=` where `>` was meant (Island 1), the mutable default (Island 3). This island is where
those warnings get collected: the player meets each one from the other side, as a symptom
rather than a rule.

### What could not be verified, and what was done instead

`print-debugging` is the one concept here with no testable artifact. Debug prints are
temporary by definition — the skill ends with removing them, so there is nothing left to
assert on.

Asserting on captured `stdout` was considered and **rejected**. Exact matching would test
whether the player reproduced the author's wording character for character; loose matching
("does the output contain X") is passed by one unconditional `print` and verifies nothing.
Any rule strict enough to mean something is strict enough to be about formatting rather
than investigation. It would also reward permanently keeping prints that professionals
remove before committing, and would fail a player who reached for a debugger or `logging`
instead — both equally correct.

So mission 3 teaches print-debugging in its panel and is assessed on **the fixed code**.
The print is the method; the working function is the deliverable. This costs nothing in
practice, because the player really can debug with prints inside the game: `stdout` is
already captured and rendered in the results panel (`tui/widgets/test_results.py`).

`interactive-debugger` shares that mission rather than getting its own. It is equally
unverifiable, and there is a concrete hazard: the sandbox subprocess inherits the game's
stdin (`engine/runners/python.py` passes no `stdin=`), so a submission calling
`breakpoint()` would block on a terminal read until the wall-clock timeout kills it. A
mission must never require running it. The panel teaches it as the tool you reach for when
prints stop scaling, including the workflow of copying the broken function into your own
editor, stepping through it there, and bringing the fix back.

### Mission map

| # | Slug | Introduces | Shape | Note |
|---|---|---|---|---|
| 1 | `read-the-stack` | `reading-tracebacks` | skeleton | A traceback arrives as text; extract the type, line and innermost frame |
| 2 | `the-wrong-question` | `logic-vs-data` | fix | Is the code wrong, or is what I fed it wrong? |
| 3 | `the-lamp-and-the-lens` | `print-debugging`, `interactive-debugger` | fix | The long teaching panel of the island. Assessed on the fix |
| 4 | `halve-the-search` | `bisection` | skeleton | Binary search for the first bad reading. `git bisect` as an algorithm |
| 5 | `the-off-by-one` | — | fix | **Relief.** One character wrong, and the whole island in miniature |
| 6 | `the-honest-assert` | `assert-as-diagnosis` | skeleton | `assert` fires, verified with `raises: AssertionError` |
| 7 | `the-leaking-helper` | — | fix | Island 3's mutation bug, met as a symptom |
| 8 | `the-reset-tally` | — | fix | Island 1's accumulator-inside-the-loop, met as a symptom |
| 9 | `the-shared-basket` | — | fix | **Relief.** Island 3's mutable default, met as a symptom |
| 10 | `the-whole-investigation` | — | fix | Closing. A bug that has to be *located* before it can be fixed |

Reinforcement:

| Concept | Introduced | Reinforced in |
|---|---:|---|
| `reading-tracebacks` | 1 | 2, 5, 7, 10 |
| `logic-vs-data` | 2 | 3, 5, 6, 7, 8, 9, 10 |
| `print-debugging` | 3 | 4, 7, 8, 9, 10 |
| `interactive-debugger` | 3 | — |
| `bisection` | 4 | 10 |
| `assert-as-diagnosis` | 6 | 10 |

This table was rewritten after the island shipped, to describe the missions that exist
rather than the ones that were sketched. Every change is a concept picked up in *more*
places than planned — nothing planned was dropped. `logic-vs-data` and `print-debugging`
spread the furthest because they are methods rather than syntax: once taught, they are
what the player uses to attack every later bug, so a fix-shaped mission reinforces them
whether or not the map said so.

`interactive-debugger` is introduced once and never reinforced, breaking the two-reuse
rule. That is deliberate and is the honest consequence of the hazard above: no mission may
run a debugger, so no mission can reinforce it. Recording the exception is better than
inventing a mission that pretends to.

### reading-tracebacks
- **prereqs:** exceptions, split-and-parse
- **objective:** read a traceback from the bottom up and name the file, line and call that
  actually failed
- **misconceptions:** reading a traceback top-down and blaming the first frame, which is
  usually library code; believing the last line is the only useful part; being scared off
  by the length rather than noticing it is a call chain
- **mastery:** given a traceback, points at the innermost frame belonging to their own
  code and says what it was doing

### logic-vs-data
- **prereqs:** input-validation, reading-tracebacks
- **objective:** decide whether a failure comes from wrong code or from wrong input before
  changing anything
- **misconceptions:** editing the code as the first move every time; assuming the input is
  fine because it came from inside the same program; assuming the input is at fault
  because the code "looks right"
- **mastery:** given a failing case, states which of the two it is and what evidence says so

### print-debugging
- **prereqs:** logic-vs-data
- **objective:** find where a value first becomes wrong by making the program say what it
  is holding
- **misconceptions:** printing only at the end, where the damage is visible but the cause
  is not; printing a value without labelling which one it is; adding prints at random
  rather than narrowing the range; leaving them in afterwards
- **mastery:** places a print at the point that splits the suspect range roughly in half,
  and labels it well enough to read the output without counting lines

### interactive-debugger
- **prereqs:** print-debugging
- **objective:** know when prints stop being enough and what replaces them
- **misconceptions:** believing a debugger is for experts rather than for loops with many
  passes; believing you must abandon your editor to use one
- **mastery:** describes a situation where stepping beats printing, and vice versa

### bisection
- **prereqs:** print-debugging
- **objective:** halve the suspect range with each check instead of scanning it
- **misconceptions:** checking candidates one by one from the start; believing bisection
  needs a sorted list rather than a monotonic property ("everything after the first bad
  one is bad"); forgetting that a range with nothing wrong in it has no answer
- **mastery:** locates a first-bad element in a long sequence with far fewer checks than
  its length

### assert-as-diagnosis
- **prereqs:** raising, logic-vs-data
- **objective:** state an assumption in code so it announces itself the moment it stops
  being true
- **misconceptions:** using `assert` for user input validation, which is what `raise`
  is for and which `python -O` strips out entirely; asserting something already obvious
  from the line above; writing an assert with no message
- **mastery:** explains why a check that must survive in production is a `raise` and not
  an `assert`

`[AI-ENG:debugging-methodology]` bridge, to attach when mission 4 is written: halving the
suspect range and forming a falsifiable hypothesis before changing anything is the same
discipline `superpowers:systematic-debugging` names for an agent debugging its own tool
calls. Same muscle, smaller stakes, and the human version comes first.

---

## Island 7 — Files and Data

**Theme:** data that outlives the program
**Band:** moderate
**Missions:** 10

Everything the player has written so far received its data as arguments and gave it back
as a return value. Nothing survived the call. This island is where a program first leaves
a mark that is still there tomorrow — and where the failures stop being about logic and
start being about the world: the file is missing, the handle was never closed, the path
works on your machine and nowhere else.

**Concepts (6):** `open-and-read`, `context-managers`, `writing-files`, `json`, `csv`,
`paths`

### This island could not be authored when it was designed — that gap is now closed

Islands 3 and 4 designed *around* their engine limits. Island 5 could not, and the
`raises:` field was built before its first mission was written. **Island 7 was a Island 5
case, not an Island 3 case.**

Designing it first was still the right order. The shape of the field fell out of what the
missions needed — a fixture mechanism designed before the island would have guessed.

**Status:** the blocker below was closed before authoring began. `files:` ships as
designed here, with one addition the design asked for: the fixtures are re-planted before
*every* test case, not only once during `prepare`. See `docs/mission-schema.md`.

### Mission map

| # | Slug | Introduces | Reinforces | Note |
|---|---|---|---|---|
| 1 | `the-logbook-page` | `open-and-read` | `split-and-parse`, `exceptions` | Read a file the mission planted. A missing file raises, and that is the lesson's second half |
| 2 | `close-it-yourself` | `context-managers` | `open-and-read`, `try-except` | `with` — and why mission 1's shape was a leak waiting for an exception |
| 3 | `the-quiet-count` | — | `open-and-read`, `context-managers`, `accumulator-pattern` | **Relief.** Count matching lines in a file, nothing new |
| 4 | `write-it-down` | `writing-files` | `context-managers`, `join-vs-concat` | Write, then read back in the same call. `"w"` truncates and `"a"` does not |
| 5 | `the-structured-manifest` | `json` | `writing-files`, `nested-structures` | A dict survives a round trip through text. Tuples do not come back as tuples |
| 6 | `the-round-trip` | — | `json`, `context-managers` | **Relief.** |
| 7 | `the-column-ledger` | `csv` | `split-and-parse`, `lists` | The quoted comma that `.split(",")` gets wrong. Island 4's tool meeting its limit |
| 8 | `the-portable-path` | `paths` | `string-methods` | `pathlib`, and why `folder + "\\" + name` is a bug the author's machine hides |
| 9 | `the-tidy-report` | — | `paths`, `writing-files`, `csv`, `f-strings` | **Relief.** |
| 10 | `the-full-ledger` | — | all six | Closing mission. Combine, do not learn |

Relief at 3, 6 and 9, matching Islands 4, 5 and 6.

Mission 1 introducing `open-and-read` **before** `context-managers` is deliberate, and it
is the same move Island 5 made by teaching `exceptions` before `try-except`. A player has
to hold a file open, and see that nothing forces them to close it, before `with` reads as
a solution rather than as syntax someone insists on. Mission 2 then breaks mission 1's
shape on purpose: an exception between `open()` and `close()` skips the close.

Reinforcement count:

| Concept | Introduced | Reinforced in |
|---|---:|---|
| `open-and-read` | 1 | 2, 3, 4, 10 |
| `context-managers` | 2 | 3, 4, 6, 10 |
| `writing-files` | 4 | 5, 9, 10 |
| `json` | 5 | 6, 10 |
| `csv` | 7 | 9, 10 |
| `paths` | 8 | 9, 10 |

Every concept is reused at least twice. No orphans, and no exception to argue this time.

### The paths rule, found during authoring

**No mission on this island returns a path it built.** Missions 8 and 9 return `.stem`,
`.suffix`, `.name` or `list(.parts)` — values with no separator in them.

The reason is the content suite. `tests/content/test_all_missions.py` runs each shipped
solution for real, and the same solution runs on Linux in CI and on Windows on the
author's machine. `str(Path("logs") / "watch.log")` is `logs/watch.log` in one place and
`logs\watch.log` in the other, so a mission asserting on a joined path is green in one
and red in the other — and whichever way the expectation is written, it teaches the player
that one separator is the correct answer, which is the opposite of the lesson.

So the teaching block carries the "never type a separator" rule and the tests grade its
consequences. Any future island that touches paths inherits this constraint.

### Engine work this island required

Verified against the code before the map above was written, not assumed. Items 1 and 2
were built. Items 3, 4 and 5 were never code work — they are rules the missions obey, and
they are now written down in `docs/mission-schema.md` so the next island author inherits
them instead of rediscovering them.

**1. There is no way to plant a file. This is the blocker.** — *built.*
`PythonRunner.prepare` (`engine/runners/python.py:116`) writes exactly two files into the
sandbox — `submission.py`, and `harness.py` outside a frozen build. `docs/mission-schema.md`
has no field that says "this mission needs `cargo.csv` to exist". Missions 1, 3, 7 and 10
have nothing to open.

Proposed contract, to be built before authoring — the same order `raises:` was built in:

```yaml
files:
  cargo.csv: |
    port,weight
    lisbon,10
```

A mapping of relative filename to text content, written into the workdir during `prepare`.
Text only, names validated to a single path segment: a mission that could write
`../../anything` would turn content — the one part of the repo a non-coder is invited to
edit — into an arbitrary file-write primitive. `content/` is data, and this is exactly
where data stops being harmless.

**2. The workdir is shared by every test case of one attempt.** — *built, the first way.*
`GameSession` calls `prepare` once and `execute` per case (`services/game_session.py:91,142`).
A file written by case 1 is still there for case 2. This is the mirror image of the
one-process-per-case rule that shaped Island 3: there, state did not survive; here, it
survives too well. A `writing-files` mission whose cases each append to the same name will
pass alone and fail in sequence. Either `prepare` re-plants the declared files before every
case, or mission 4 and mission 9 must be written so each case names its own file. **The
first is better** — a mission author should not have to know this.

**3. The workdir is not empty and its contents differ between builds.**
It holds `submission.py`, `request.json` and `result.json`, plus `harness.py` only outside a
frozen build (`python.py:132`). So no mission may list the directory or count its files:
the answer includes engine plumbing, and it is a *different* answer in the pendrive build
than in a source checkout. Nothing in the map above does this, deliberately.

**4. A file handle does not cross the JSON boundary.**
Same wall functions hit in Island 3 and `bytes` in Island 4 — `engine/harness.py` falls back
to `repr` for anything `json.dumps` cannot carry. No mission can accept or return an open
file. Every mission here is framed around what the solution *builds* from the file, which is
the honest framing anyway.

**5. `open` and the imports are already controllable.** The guard's `forbidden_builtins`
and `forbidden_imports` (`engine/guard.py`) cover `open`, `json` and `csv` by name, so
mission 7 can forbid `split` where it wants the `csv` module, and mission 5 can forbid
hand-rolled parsing. No new mechanism needed for this part.

### open-and-read
- **prereqs:** split-and-parse, exceptions
- **objective:** read a file's contents into text your program can work on, and know what
  happens when it is not there
- **misconceptions:** believing `open()` returns the contents rather than a handle;
  believing a missing file returns something empty instead of raising `FileNotFoundError`;
  reading a file twice from the same handle and being surprised the second read is empty
- **mastery:** reads a file into lines and says what the call does when the path is wrong

### context-managers
- **prereqs:** open-and-read, try-except
- **objective:** hold a resource only as long as it is needed, and release it even when
  something fails
- **misconceptions:** believing `with` is a shorter `open` rather than a guarantee about
  the close; believing a `return` inside the block skips the cleanup (it does not);
  believing the file is still readable after the block ends
- **mastery:** explains what happens to the handle when a line inside the block raises,
  in both the `with` version and the `open`/`close` version

### writing-files
- **prereqs:** context-managers
- **objective:** put a program's result somewhere it will still be after the program ends
- **misconceptions:** believing `"w"` appends (it truncates the file to nothing first);
  believing the text is on disk the instant `.write()` returns; forgetting that `.write()`
  adds no newline of its own
- **mastery:** predicts the file's contents after the same function runs twice, for both
  `"w"` and `"a"`

### json
- **prereqs:** writing-files, nested-structures
- **objective:** save a structure and load it back as the same structure
- **misconceptions:** confusing `dumps`/`loads` (text) with `dump`/`load` (a file);
  believing every Python value is serialisable; expecting a tuple or a set to survive the
  round trip as itself; believing dict keys keep their type (they all come back as strings)
- **mastery:** round-trips a nested dict and names one value that does not come back as the
  type it went in as

### csv
- **prereqs:** split-and-parse, lists, open-and-read
- **objective:** read tabular text correctly, including the rows that `.split(",")` ruins
- **misconceptions:** believing `.split(",")` is equivalent (a quoted field containing a
  comma proves it is not); forgetting every field arrives as a string; treating the header
  row as data
- **mastery:** parses a file where one field legitimately contains a comma, and gets the
  same column count on every row

### paths
- **prereqs:** string-methods
- **objective:** build a path that works on someone else's operating system
- **misconceptions:** joining with `"/"` or `"\\"` by hand; believing a path that works
  where it was written works everywhere; confusing the file's name with its whole path
- **mastery:** builds a path from parts without typing a separator, and takes a file's
  extension off a full path without slicing by index

---

## Island 8 — Objects

**Theme:** data and the behaviour that belongs to it
**Band:** moderate
**Missions:** 11

Every island so far kept data and behaviour apart. A dict held the values, a function did
something to it, and nothing stopped a caller from handing that function a dict shaped
wrong. This island is where the two move in together: the crate knows its own weight, and
the only code allowed to change it lives beside it.

The player has already built everything a class does, by hand. Island 2's nested dicts are
attributes, Island 3's functions are methods, Island 5's `raise` is what a bad state should
do. Nothing here is new capability — it is the same work with a boundary drawn around it,
and that framing is what keeps the island from reading as syntax for its own sake.

**Concepts (8):** `classes`, `instances`, `methods`, `dunder-methods`, `dataclasses`,
`composition-over-inheritance`, `properties`, `custom-exceptions`

`custom-exceptions` **moved here from Island 5** while Island 5 was being designed.
Defining one is `class ShortfallError(Exception): pass` — a class definition, and Island 5
runs long before classes exist. It lands naturally here: once `classes` is taught, a
custom exception is the smallest possible subclass and makes a good early mission for
inheritance without needing a contrived example.

### The rule that shapes every mission on this island

**No mission may accept or return an instance.** Verified, not assumed: the harness
serialises the return value with `json.dumps` and falls back to `repr` for anything it
cannot carry (`engine/harness.py:78-89`), and the arguments in a test case arrive from
JSON in the request file (`engine/runners/python.py:182-194`). A default instance
`repr` is `<Crate object at 0x7f9c...>` — a different address on every run, so a mission
expecting one is red forever.

This is the same wall Island 3 hit with functions and Island 4 with `bytes`, and it gets
the same treatment: reshape the mission, do not build around it. Every mission here builds
its objects **inside** the submission and the entrypoint returns plain data derived from
them — a dict, a list, a number, a bool, or a string.

Far from a limitation, it hands `dunder-methods` its whole reason to exist. `__repr__`
returns a string and `__eq__` returns a bool, so those two are the *first* things on this
island whose output the engine can read directly. A player who writes `__repr__` because
the test demands a readable string has learned exactly why the method exists.

The one thing to watch when authoring: `signature.entrypoint` is always a function, never
a class. The loader requires `^\s*def\s+<entrypoint>\s*\(` in both the stub and the
solution (`engine/loader.py:107`), so a stub that only defines a class fails validation.
Every stub here is `class X: ...` followed by `def <entrypoint>(...)`.

### The honesty rule, found during authoring

**The engine cannot prove that a class was written.** It sees the return value and nothing
else, so a player who skips the class and hand-builds the dict passes every test. This was
known in outline before authoring and turned out to be sharper than expected: for a pure
data transformation, the class version is genuinely *more* code, so the shortcut is not
only possible but shorter.

Three responses were considered. Forbidding `dict` does not work — a `{...}` literal is
not a `Name`, so the guard never sees it. Requiring `type(x).__name__` in the answer is
faked with a string literal. Neither is a control, and pretending otherwise would be worse
than the gap.

**So mission 1's brief says it out loud**, in the same register Island 6 used for
`print-debugging`: a two-line answer returns the right list, the tests cannot tell, write
the class anyway because mission 2 gives you nothing to stand on otherwise. Later missions
close the gap on their own — by mission 4 the answer *is* the output of `__repr__` and
`__eq__`, and by mission 9 the state machine is complex enough that faking it is strictly
more work than writing it.

The transferable version, worth stating because it is the third time this project has hit
it: when the check is impossible, say so in the brief and design the sequence so the
shortcut stops paying. Do not invent a check that only looks like one.

### Mission map

| # | Slug | Introduces | Reinforces | Note |
|---|---|---|---|---|
| 1 | `the-crate-that-knows-itself` | `classes`, `instances` | `dictionaries`, `parameters` | `__init__` and `self`. Returns a dict of the attributes, because an instance cannot cross back |
| 2 | `the-crate-that-does-something` | `methods` | `classes`, `instances` | A method that changes its own state, and the same call twice giving a different answer |
| 3 | `the-crew-roster` | — | `classes`, `methods`, `for-loop` | **Relief.** A list of instances, one loop, one total |
| 4 | `printed-plainly` | `dunder-methods` | `methods`, `f-strings` | `__repr__` returns a string, so the test can finally read the object. `__eq__` and `__len__` alongside |
| 5 | `the-harbour-refuses` | `custom-exceptions` | `raising`, `classes`, `input-validation` | The smallest subclass there is. Graded with `raises:` |
| 6 | `two-of-a-kind` | — | `dunder-methods`, `instances` | **Relief.** Same three dunders, friendlier shape |
| 7 | `the-hull-and-the-engine` | `composition-over-inheritance` | `classes`, `methods`, `dunder-methods` | Two classes, one holding the other. The inheritance version is shown in the panel and rejected with a reason |
| 8 | `the-free-boilerplate` | `dataclasses` | `dunder-methods`, `classes` | Everything missions 1 to 6 wrote by hand, generated. Includes the mutable-default trap in its `@dataclass` form |
| 9 | `the-computed-draught` | `properties` | `methods`, `dataclasses`, `custom-exceptions` | A value that reads as an attribute and is computed. The setter refuses bad input with mission 5's exception |
| 10 | `the-generated-fleet` | — | `dataclasses`, `properties`, `composition-over-inheritance` | **Relief.** |
| 11 | `the-whole-shipyard` | — | all eight | Closing mission. Combine, do not learn |

Relief at 3, 6 and 10. The shift from the 3/6/9 pattern of Islands 4 to 7 is forced by
arithmetic, not taste: the last concept introduced needs two later missions to be
reinforced in, so with eight concepts in eleven missions the final introduction has to
land at 9.

Missions 1 introducing `classes` and `instances` **together** is the second exception to
the one-new-concept rule, after Island 6 mission 3. The reason is different and weaker,
and it is worth being honest about: unlike `print-debugging` and `interactive-debugger`,
these two *could* be split. They are not, because a class with no instance is a definition
nobody has run, and an instance with no class is impossible — every draft that separated
them made mission 1 a mission about syntax and mission 2 a mission about the same syntax.
The pair is one idea seen from two sides, and the teaching panel says so out loud.

Mission 4 arriving before mission 8 is the load-bearing order of this island. A player who
meets `@dataclass` first sees a decorator that does something invisible. A player who has
written `__init__`, `__repr__` and `__eq__` by hand for six missions sees a decorator that
deletes twenty lines they personally typed. Same feature, and only one of the two orders
teaches what it is for.

Reinforcement count:

| Concept | Introduced | Reinforced in |
|---|---:|---|
| `classes` | 1 | 2, 3, 5, 7, 8, 11 |
| `instances` | 1 | 2, 3, 6, 7, 11 |
| `methods` | 2 | 3, 4, 7, 9, 11 |
| `dunder-methods` | 4 | 6, 7, 8, 11 |
| `custom-exceptions` | 5 | 9, 11 |
| `composition-over-inheritance` | 7 | 10, 11 |
| `dataclasses` | 8 | 9, 10, 11 |
| `properties` | 9 | 10, 11 |

Every concept is reused at least twice. No orphans.

### Engine work this island requires

**None**, and the island shipped without any. Verified against the code before the map was
written, and confirmed by 11 missions passing `codequest check` in both language trees:

- `engine/guard.py:93` already visits `ClassDef`, so a class definition passes the guard
  and `forbidden_builtins` still applies inside a method body.
- `dataclasses` is a stdlib import and `forbidden_imports` defaults to empty
  (`models/mission.py:96`), so mission 8 needs no new mechanism — and mission 4 can forbid
  `dataclasses` by name to stop a player short-cutting the hand-written dunders.
- `raises:` already exists (built for Island 5) and matches by **exact type name**
  (`engine/evaluator.py:131`). A custom exception named `ShortfallError` is matched on
  that string, so mission 5 must state the class name in its brief — the player cannot
  invent their own name and pass.

The single authoring rule that replaces engine work: **the entrypoint is a function and
the return value is plain data.** Written here so the next island author inherits it
instead of rediscovering it against a red test.

### classes
- **prereqs:** dictionaries, parameters, return-values
- **objective:** define a type whose values carry their own data
- **misconceptions:** believing `self` is a keyword the language passes magically rather
  than the first parameter you are declaring; believing a variable set directly in the
  class body is per-instance (it is shared by all of them, which is Island 3's mutable
  default wearing a hat); believing `__init__` returns the object
- **mastery:** writes a class whose two instances hold different values, and says which
  line made them independent

### instances
- **prereqs:** classes
- **objective:** build several values of your own type and keep their state apart
- **misconceptions:** believing `Crate` and `Crate()` are the same thing; believing two
  instances built from the same arguments are the same object; expecting `==` to compare
  contents before `__eq__` exists (it compares identity)
- **mastery:** predicts the output after mutating one of two instances built the same way

### methods
- **prereqs:** instances, pure-vs-side-effects
- **objective:** put the behaviour that changes a value next to the value itself
- **misconceptions:** forgetting `self` in the definition and being told the call got one
  argument too many; reading `self.total` and `total` as the same name; believing a method
  that mutates should also return the object
- **mastery:** writes a method that changes its own state and one that only reports it,
  and says which of the two is safe to call twice

### dunder-methods
- **prereqs:** methods, f-strings
- **objective:** make your type answer the questions the language already knows how to ask
- **misconceptions:** believing you call `__repr__` directly rather than through `repr()`
  and `print()`; believing `__str__` and `__repr__` are interchangeable; defining `__eq__`
  and expecting the object to still work in a set (it needs `__hash__`, and defining
  `__eq__` alone removes the one it had)
- **mastery:** makes two equal-by-value instances compare equal, and prints one in a form
  that names its contents

### custom-exceptions
- **prereqs:** raising, classes, input-validation
- **objective:** name a failure your program has, so a caller can catch that one and
  nothing else
- **misconceptions:** believing a custom exception needs a body beyond `pass`; inheriting
  from `BaseException` instead of `Exception`, which catches things nobody meant to catch;
  defining one and then raising `ValueError` anyway; believing the name alone documents
  the failure without a message
- **mastery:** raises a named exception a caller can catch by name while an unrelated
  `ValueError` still travels past

### composition-over-inheritance
- **prereqs:** classes, methods, dunder-methods
- **objective:** build a bigger type by holding smaller ones instead of inheriting from
  them
- **misconceptions:** reaching for inheritance because two types share a word in their
  name; believing inheritance is about reuse rather than about substitutability;
  believing composition means more code (it means more names, and fewer surprises)
- **mastery:** given a type that "has a" relationship and one that "is a", picks the right
  tool for each and says which question decided it

### dataclasses
- **prereqs:** dunder-methods, classes
- **objective:** stop writing `__init__` and `__repr__` by hand for types that are mostly
  data
- **misconceptions:** believing `@dataclass` changes what the class *is* (it writes methods
  you could have typed); giving a field a mutable default and meeting Island 3's trap in a
  new costume, this time as a `ValueError` at class-definition time; believing `frozen=True`
  makes the contents immutable rather than the bindings
- **mastery:** replaces a hand-written class with a dataclass and names which methods
  disappeared and which had to stay

### properties
- **prereqs:** methods, dataclasses, custom-exceptions
- **objective:** expose a computed or guarded value with the plainness of an attribute
- **misconceptions:** believing a property is stored (it runs every time it is read);
  putting expensive work behind one, so `obj.total` quietly costs a second; writing a
  setter that validates and then forgets to store; believing `@property` is required for
  every attribute
- **mastery:** turns a stored attribute into a computed one without any calling code
  changing, and refuses an invalid assignment through the setter

---

## Island 9 — Pythonic Patterns

**Theme:** the shapes the language was built for
**Band:** challenging
**Missions:** 11

The player can already solve anything on this island the long way — with an index counter,
a list built up in full, a wrapper function called by hand. This island is about the
shorter form being *better*, not just briefer: a generator that never builds the list can
walk a sequence that does not fit in memory, and a decorator applied in one line is a
change you cannot forget to make at the seventh call site.

It is the first island where the wrong answer is a working one. Every mission has a
solution the player already knows how to write, and the mission is only passed by the
version the concept is about — which is what `forbidden_builtins` and
`forbidden_imports` exist for.

**Concepts (7):** `unpacking`, `enumerate-zip`, `iterators`, `yield`, `generators`,
`decorators`, `custom-context-managers`

### The rule that shapes every mission on this island

**No mission may return a generator, an iterator, a function or a context manager.** The
same `repr`-with-an-address problem as Island 8, from `engine/harness.py:78-89`:
`<generator object walk at 0x7f...>` and `<function timed at 0x7f...>` change on every
run. Every entrypoint here returns a list, a number, a string or a bool built from those
objects.

Proving laziness without returning the lazy thing is the interesting half, and there are
two honest ways. Both are used:

1. **Return a prefix of an infinite source.** A generator over an endless sequence, with
   the mission taking the first five. The list-building version cannot finish, so the
   mission is graded by the fact that it *returns at all* — no timing assertion, just a
   wall-clock timeout that only the correct shape survives.
2. **Return `[next(g), next(g)]`.** Two values pulled by hand, which is what makes
   "produces on demand" observable rather than asserted.

**Grading on `stdout` was considered and rejected**, consistently with Island 6. `stdout`
is captured and shown to the player (`engine/evaluator.py:226`) but no test compares it,
and the argument from Island 6 applies unchanged: any rule strict enough to grade printed
output is grading formatting. Nothing on this island needs it — the two techniques above
cover every case, which is why this island asks for no engine work.

**A third technique appeared during authoring, and it is the best of the three.** Pass the
generator a list, have it append to that list as it produces, and take a copy of the list
before pulling anything. The copy is empty, because none of the body has run — which is the
"nothing happens until the first `next`" rule turned into a value the engine can compare.
Mission 5 is built on it. It needs no infinite source, no clock and no `stdout`, and it is
the only one of the three that observes the *creation* of a generator rather than its
consumption. Any future island teaching laziness should reach for this first.

### Mission map

| # | Slug | Introduces | Reinforces | Note |
|---|---|---|---|---|
| 1 | `the-two-halves` | `unpacking` | `tuples`, `return-values` | `a, b = pair`, the starred middle, and the swap that needs no temporary |
| 2 | `the-numbered-watch` | `enumerate-zip` | `unpacking`, `for-loop` | The index counter deleted. `range(len(...))` forbidden, or it is a loop mission again |
| 3 | `the-paired-ledger` | — | `enumerate-zip`, `unpacking`, `dictionaries` | **Relief.** Two lists into one dict |
| 4 | `one-at-a-time` | `iterators` | `for-loop`, `lists` | `iter` and `next`, and the exhaustion that makes a second pass empty |
| 5 | `the-paused-function` | `yield` | `iterators`, `functions` | A function that stops and resumes. Graded with `[next(g), next(g)]` |
| 6 | `the-endless-tide` | — | `yield`, `iterators` | **Relief.** First five of an infinite source. The eager version cannot finish |
| 7 | `the-lazy-manifest` | `generators` | `yield`, `list-comprehension` | Generator expressions, and the memory argument. `list` forbidden where it would defeat the point |
| 8 | `the-wrapped-order` | `decorators` | `first-class-functions`, `args-kwargs` | The player writes the decorator and applies it to a helper. The entrypoint returns what the wrapping made observable |
| 9 | `open-and-shut` | `custom-context-managers` | `context-managers`, `classes`, `dunder-methods` | `__enter__`/`__exit__`, then `@contextmanager`. Island 7 used `with`; here you build one |
| 10 | `the-pipeline` | — | `generators`, `decorators`, `custom-context-managers` | **Relief.** Three tools, one small job |
| 11 | `the-whole-current` | — | all seven | Closing mission. Combine, do not learn |

Relief at 3, 6 and 10, same arithmetic as Island 8.

`unpacking` and `enumerate-zip` open the island rather than closing it, against the
instinct that says the cheap tools are a footnote. They come first because they are the
only two concepts here the player can use immediately in *every* later mission, and
because the island's band is `challenging` — opening on the iterator protocol would put
the hardest idea at the point where the player has the least momentum.

Mission 4 introducing `iterators` before mission 5's `yield` is the same move Island 5
made with `exceptions` before `try-except` and Island 7 with `open-and-read` before
`context-managers`. A player has to watch an iterator run out before a function that
produces values one at a time reads as anything other than a strange `return`.

Reinforcement count:

| Concept | Introduced | Reinforced in |
|---|---:|---|
| `unpacking` | 1 | 2, 3, 8, 11 |
| `enumerate-zip` | 2 | 3, 7, 10, 11 |
| `iterators` | 4 | 5, 6, 7, 9, 11 |
| `yield` | 5 | 6, 7, 11 |
| `generators` | 7 | 10, 11 |
| `decorators` | 8 | 10, 11 |
| `custom-context-managers` | 9 | 10, 11 |

Every concept is reused at least twice. No orphans.

### Engine work this island requires

**None**, and the island shipped without any. Verified before the map was written, and
confirmed by 11 missions passing `codequest check` in both language trees:

- `engine/guard.py:89-93` visits `AsyncFunctionDef` and `ClassDef`; a `yield` inside a
  function body is an ordinary statement to the guard and needs no handling.
- `contextlib` is stdlib and unrestricted by default (`models/mission.py:96`), so mission 9
  can teach `@contextmanager` and mission 9's earlier half can forbid it to force the
  class-based version first.
- The infinite-generator missions rely on the wall-clock timeout already enforced by the
  parent (`engine/runners/python.py:181`), which is the mechanism Island 10 leans on
  harder. Nothing new.

The authoring rule, in one line: **the lazy object stays inside the submission; only what
was pulled out of it crosses back.**

### unpacking
- **prereqs:** tuples, return-values
- **objective:** take a sequence apart into named values in one statement
- **misconceptions:** believing the counts may differ (they may not, unless a `*name`
  absorbs the rest); believing `*rest` gives a tuple (it gives a list, every time);
  believing `a, b = b, a` needs a temporary variable somewhere out of sight
- **mastery:** swaps two values and splits a head from a tail without an index anywhere

### enumerate-zip
- **prereqs:** unpacking, for-loop
- **objective:** walk a sequence with its position, or two sequences together, without
  managing an index
- **misconceptions:** believing `enumerate` starts anywhere but 0 unless told; believing
  `zip` pads the shorter sequence (it stops, silently, which is the bug); believing you can
  reuse a `zip` object for a second pass
- **mastery:** rewrites a `range(len(...))` loop with `enumerate`, and says what `zip`
  does when the two inputs are different lengths

### iterators
- **prereqs:** for-loop, lists
- **objective:** see the protocol a `for` loop has been using all along, and drive it by
  hand
- **misconceptions:** believing a list and its iterator are the same thing; expecting a
  second `for` over the same iterator to start again (it is empty); believing `next` on an
  exhausted iterator returns `None` rather than raising `StopIteration`
- **mastery:** consumes half an iterator, hands it to a loop, and predicts what the loop
  sees

### yield
- **prereqs:** iterators, return-values
- **objective:** write a function that hands back one value and carries on from where it
  stopped
- **misconceptions:** believing the function body runs when it is called (nothing runs
  until the first `next`); believing `yield` ends the function the way `return` does;
  putting a `yield` in a function and being surprised the `return` value vanished into a
  `StopIteration`
- **mastery:** predicts how many lines of a generator body have run after exactly one
  `next`

### generators
- **prereqs:** yield, list-comprehension
- **objective:** produce a long or endless sequence without ever holding it all at once
- **misconceptions:** believing a generator can be walked twice; believing
  `(x for x in ...)` and `[x for x in ...]` differ only in punctuation; believing `len`
  works on one; reaching for a generator where a list is genuinely cheaper and needed twice
- **mastery:** takes the first five values of an endless sequence, and says why the list
  version of the same code never returns

### decorators
- **prereqs:** first-class-functions, args-kwargs
- **objective:** add the same behaviour to a function without editing the function
- **misconceptions:** believing `@thing` calls the function (it replaces it); forgetting
  `*args, **kwargs` in the wrapper and breaking every call with an argument; losing the
  original function's `__name__` and not knowing `functools.wraps` exists; believing a
  decorator runs once per call rather than once at definition
- **mastery:** wraps a function so the behaviour is added at every call site at once, and
  the wrapped function still accepts the arguments it always did

### custom-context-managers
- **prereqs:** context-managers, classes, dunder-methods
- **objective:** guarantee that cleanup happens, for a resource the standard library never
  heard of
- **misconceptions:** believing `__exit__` is only for the happy path (it runs on the way
  out of an exception too, which is the entire point); believing returning `True` from
  `__exit__` is polite rather than a decision to swallow the exception; forgetting that
  `__enter__`'s return value is what `as` binds
- **mastery:** writes a manager whose cleanup still runs when the body raises, and says
  which line proves it

---

## Island 10 — Algorithms

**Theme:** the same answer, at a cost you chose
**Band:** challenging
**Missions:** 11

Every mission so far was graded on being right. This is the first island where being right
is the entry fee. The player already knows how to find an item in a list; here they find
out that their way takes a thousand steps where another takes ten, and that the difference
stops being academic somewhere around the size of a real logbook.

This island is deliberately the one before `async`, because the most common reason a
program is slow is not that it lacks concurrency — it is that it is doing far too much
work. Learning to count the work first is what stops Island 11 from reading as a
performance cure-all.

**Concepts (7):** `linear-search`, `big-o`, `binary-search`, `two-pointer`, `sorting`,
`recursion`, `memoization`

### `big-o` is graded by counting, not by timing

`big-o` looks like the third unverifiable concept in the curriculum, after
`print-debugging` and `interactive-debugger` in Island 6. It is not, and the difference is
worth stating because it decides the shape of half the island.

**The missions return the step count.** A search that also reports how many comparisons it
made returns an integer, deterministic on every machine, on every run, in CI and on
Windows alike. `linear_search(haystack, needle) -> (index, comparisons)` is exactly
gradable, and a hidden case on a thousand-element list distinguishes ten steps from a
thousand with no clock involved. The *notion* of an asymptotic class lives in the teaching
panel; what the tests grade is the count it predicts.

**Timing is the backstop, never the primary grade.** Verified before this was decided: the
wall-clock budget is `constraints.max_runtime_ms`, applied by the parent to a **fresh
subprocess per test case** (`engine/runners/python.py:181` and `115`), so the measured
interval includes interpreter start-up and the submission's import. That noise floor is
tens of milliseconds and it is worse on a cold Windows filesystem, which is the author's
machine (`CLAUDE.md` §5).

So the rule for any mission that grades by time, and there is one — mission 9:

> The naive solution must exceed `max_runtime_ms` by at least **5x**, and the intended
> solution must come in under **a fifth** of it. A mission whose two solutions are within
> an order of magnitude of the budget is a flaky test, not a lesson.

The mission raises `max_runtime_ms` explicitly rather than relying on the 2000 ms default,
so the margin is visible in the file instead of implied.

### Mission map

| # | Slug | Introduces | Reinforces | Note |
|---|---|---|---|---|
| 1 | `walk-the-whole-shore` | `linear-search` | `for-loop`, `enumerate-zip` | The honest baseline. Returns the index *and* the comparison count |
| 2 | `count-the-steps` | `big-o` | `linear-search`, `accumulator-pattern` | Same search, three input sizes, and the count as the deliverable |
| 3 | `the-first-match` | — | `linear-search`, `big-o` | **Relief.** Early return, and why it changes the best case but not the class |
| 4 | `halve-the-shore` | `binary-search` | `big-o`, `while-loop` | Island 6's `bisection` as an algorithm on data. The count drops from 1000 to 10 |
| 5 | `both-ends-inward` | `two-pointer` | `binary-search`, `unpacking` | One pass, two indices, no nested loop |
| 6 | `the-sorted-assumption` | — | `binary-search`, `two-pointer` | **Relief.** What binary search returns on unsorted input — a wrong answer, confidently |
| 7 | `put-them-in-order` | `sorting` | `big-o`, `linear-search` | Write one sort by hand, count its comparisons, then meet `sorted` and the reason to use it |
| 8 | `the-mirror-and-the-mirror` | `recursion` | `functions`, `conditionals` | Base case first. `RecursionError` is a normal outcome here, not a crash |
| 9 | `the-clerk-who-remembers` | `memoization` | `recursion`, `dictionaries`, `big-o` | The only timing-graded mission on the island. Naive recursion cannot finish inside the budget |
| 10 | `the-indexed-ledger` | — | `sorting`, `binary-search`, `memoization`, `recursion` | **Relief.** Sort once, search many times |
| 11 | `the-whole-chart` | — | all seven | Closing mission. Combine, do not learn |

Relief at 3, 6 and 10.

Mission 6 is a relief mission that teaches by breaking something: binary search on an
unsorted list returns a plausible wrong answer rather than raising. It is placed as relief
because the code is short, and it exists because "this algorithm has a precondition" is a
lesson nobody remembers from a sentence in a panel.

Mission 7 asks the player to write a sort and then tells them not to. That is not a trick.
`sorted` is C, stable, and better than anything they will write on their first try — but a
player who has never written one cannot tell you what "stable" means or why the
comparison count matters, and will not recognise an accidental O(n²) when they nest a
`.index()` call inside a loop next year.

Reinforcement count:

| Concept | Introduced | Reinforced in |
|---|---:|---|
| `linear-search` | 1 | 2, 3, 7, 11 |
| `big-o` | 2 | 3, 4, 7, 9, 11 |
| `binary-search` | 4 | 5, 6, 10, 11 |
| `two-pointer` | 5 | 6, 11 |
| `sorting` | 7 | 10, 11 |
| `recursion` | 8 | 9, 10, 11 |
| `memoization` | 9 | 10, 11 |

Every concept is reused at least twice. No orphans.

### Engine work this island requires

**None**, and the check that mattered was the third item. Verified before the map was
written:

- **Big inputs need no new mechanism.** A thousand-element list can be planted with
  `files:` (built for Island 7) or generated by the submission from a seed the test passes.
  Generating is preferred where it works — the input stays visible in the brief, and no
  case depends on a fixture the player cannot see.
- **`RecursionError` is already a first-class outcome** (`engine/harness.py:135`), so a
  missing base case produces a readable failure rather than a sandbox crash. Mission 8 can
  rely on it.
- **Timing is honest enough for exactly one mission.** See the 5x/one-fifth rule above.
  This was the item that could have become engine work — a per-case CPU-time measurement
  reported back from the harness would be more precise than the wall clock. It is **not**
  being built, because the step-count framing makes it unnecessary for six of the seven
  concepts, and building a measurement to grade one mission would be the tail wagging the
  dog. Recorded here so the next author knows it was a decision and not an oversight.

### The specification rule, found during authoring

The step-count framing works, and it arrived with a condition the design had not stated: **a
graded count needs a specified algorithm, not merely a correct one.**

Binary search is the case that made it obvious. Every correct implementation finds the item,
and they do not agree on how many comparisons that took. `(low + high) // 2` and
`low + (high - low + 1) // 2` both work and produce different counts on the same list;
counting the loop iterations and counting the `==` tests differ by one on a miss. A brief
that says "count your comparisons" is therefore not a specification, and a player who wrote
a perfectly good binary search would fail on a number nobody told them how to produce.

So missions 4, 5, 6, 7, 10 and 11 write the loop rule out in the brief - the exact midpoint,
the exact loop condition, where the counter increments. That is more prescriptive than
anything earlier in the curriculum, and it is the price of grading cost instead of grading
answers. It is worth stating why the trade is still good: the alternative is grading big-O
by inspecting source code, which the engine cannot do, or grading it by the clock, which
lies on a cold Windows filesystem.

One consequence to keep in mind for Island 11: the same rule applies to anything graded on
ordering or on interleaving. A brief that says "run them concurrently" is not a
specification either.

The timing mission also came out with far more margin than the design's 5x rule required.
Mission 9 asks for `fib(70)`: memoised it is seventy-one dictionary writes, and naively it
is on the order of 2 x 10^14 calls. The margin is not five times, it is astronomical, and
that is the right shape for the one mission on the island whose grade depends on a clock.
A mission needing a *carefully chosen* 5x margin would have been the warning sign.

### linear-search
- **prereqs:** for-loop, enumerate-zip
- **objective:** find an item by looking at every candidate, and say how many you looked at
- **misconceptions:** believing `in` is free because it is one character; continuing the
  loop after the answer is found; believing the worst case is the average case
- **mastery:** returns both the position and the number of comparisons, and says what the
  count is when the item is absent

### big-o
- **prereqs:** linear-search, accumulator-pattern
- **objective:** predict how the work grows when the input grows, before running anything
- **misconceptions:** believing O(n) means "n steps" rather than "growth proportional to
  n"; counting the constant and dropping the exponent; believing a faster class is always
  the better choice regardless of input size; believing two nested loops are always O(n²)
  without looking at what the inner one ranges over
- **mastery:** given two implementations, predicts which comparison count grows faster and
  is right when the counts are printed

### binary-search
- **prereqs:** big-o, while-loop, bisection
- **objective:** find an item in sorted data by halving the range instead of walking it
- **misconceptions:** the off-by-one in the midpoint that loops forever or skips the
  answer; forgetting the input must already be sorted; believing it can be worth sorting
  first for a single lookup (it is not — sorting costs more than the walk it saves)
- **mastery:** finds an item in a thousand-element list in roughly ten comparisons, and
  names the precondition that makes it legal

### two-pointer
- **prereqs:** binary-search, unpacking
- **objective:** collapse a nested loop into one pass by moving two indices toward each
  other
- **misconceptions:** believing it works on unordered data; moving both pointers when only
  one should move; believing the loop ends when the pointers are equal rather than when
  they cross, or the reverse, depending on the problem
- **mastery:** solves in one pass a problem whose obvious solution has a loop inside a loop

### sorting
- **prereqs:** big-o, linear-search
- **objective:** put data in order, and know what it costs you to have done it
- **misconceptions:** believing `.sort()` and `sorted()` are interchangeable (one returns
  `None` and mutates, the other does not); believing sorting is cheap enough to do inside a
  loop; not knowing that a stable sort lets you sort by two keys in two passes
- **mastery:** hand-writes one O(n²) sort, states its comparison count on ten items, and
  says why the standard library's version is still the one to ship

### recursion
- **prereqs:** functions, conditionals, scope
- **objective:** solve a problem by solving a smaller copy of it
- **misconceptions:** writing the recursive case before the base case and never returning;
  forgetting to `return` the recursive call, so the answer is computed and discarded;
  believing recursion is faster than a loop (in CPython it is slower and has a depth
  limit); believing every recursion has an obvious loop equivalent
- **mastery:** writes a function whose base case fires first, and says what its depth is
  for a given input

### memoization
- **prereqs:** recursion, dictionaries, big-o
- **objective:** stop recomputing an answer you already worked out
- **misconceptions:** believing it helps when the arguments never repeat (it only costs
  memory); caching on a mutable argument that cannot be a dict key; believing
  `functools.cache` is magic rather than a dict keyed on the arguments; caching a function
  with side effects, so the side effect happens once and the caller never learns
- **mastery:** turns a recursion that cannot finish into one that returns instantly, and
  says how many distinct calls actually ran

---

## Island 11 — Async and Concurrency

**Theme:** waiting is not working
**Band:** expert
**Missions:** 10

The last island, and the only one whose main lesson is a refusal. Island 10 taught that a
slow program is usually doing too much work. This one teaches the other case — the program
doing almost nothing at all, and spending its life waiting for a disk, a network or a
clock — and then spends its final third on the far more common situation where
concurrency makes everything worse.

The syllabus requirement is unchanged and load-bearing: **at least one mission must show a
case where async is slower.** Knowing when not to reach for a tool is the harder half of
the skill, and it is mission 8.

**Concepts (7):** `blocking-vs-nonblocking`, `async-await`, `event-loop`, `gather`,
`threads`, `gil`, `when-concurrency-helps`

### Engine work this island requires — build before authoring

This is an Island 5 case, not an Island 3 case: the missions cannot be reshaped around the
gap, so the engine is built first, exactly as `raises:` was built before Island 5 and
`files:` before Island 7. Both items were verified against the code.

**1. The harness calls the entrypoint synchronously. This is the blocker.**
`engine/harness.py:132` is `returned = function(*args, **kwargs)`. An `async def`
entrypoint returns a coroutine, never a result — and `_jsonable` then falls back to
`repr`, producing `<coroutine object solve at 0x7f...>` with a fresh address every run,
plus a "coroutine was never awaited" warning. Every mission on this island fails, including
its own shipped solution, which `tests/content/test_all_missions.py` would catch on the
first commit.

Proposed contract, to be built before authoring:

```python
returned = function(*args, **kwargs)
if inspect.iscoroutine(returned):
    returned = asyncio.run(returned)
```

Roughly five lines, with three constraints on how they are written:

- `asyncio.run` creates and closes its own event loop, so it must be the outermost call —
  a mission whose solution calls `asyncio.run` itself would then be nesting loops and
  raising `RuntimeError`. The brief for every mission here must therefore say that the
  entrypoint is awaited **for** them.
- The `except BaseException` around the call (`harness.py:137`) has to keep covering the
  `asyncio.run`, or an exception raised inside a coroutine escapes the harness and the
  parent gets an empty result file. A `raises:` case on this island depends on it.
- `harness.py` imports nothing from `codequest` by design (module docstring, lines 1-24).
  `asyncio` and `inspect` are stdlib, so the rule holds.

**2. The loader rejects `async def`.** `engine/loader.py:107` builds
`rf"^\s*def\s+{re.escape(name)}\s*\("` and requires a match in both the stub and the
solution. `async def fetch_all(...)` does not match, so every mission here fails validation
before it is ever run. The fix is one character class:

```python
pattern = rf"^\s*(?:async\s+)?def\s+{re.escape(name)}\s*\("
```

This is exactly the pattern `src/codequest/mentor/policy.py:65` already uses to detect a
leaked entrypoint — which is quietly reassuring: the anti-spoiler filter already assumed
an async entrypoint was coming, and the loader is the half that was never updated.

**3. No mission may assert on elapsed time.** Same reasoning as Island 10, harder:
concurrency missions are where the temptation to grade a stopwatch is strongest and where
it is least reliable. The mechanism instead is **completion order**. Given three sleeps of
different lengths, a sequential implementation appends its results in argument order and a
concurrent one appends in duration order — a list, deterministic, gradable with an
ordinary `expect:`.

**4. Sleeps must stay inside the wall-clock budget.** The parent's timeout covers a fresh
subprocess including interpreter start-up (`engine/runners/python.py:115`, `181`). Rule:
total sleeps per test case stay under **200 ms**, and any mission that sleeps raises
`max_runtime_ms` to **5000** explicitly. A mission demonstrating a difference with 3 x 1 s
sleeps is a mission whose own solution times out.

### `gil` is a teaching-panel concept, and the third one

`gil` joins `print-debugging` and `interactive-debugger` as a concept whose central claim
is not directly assertable. Proving the GIL exists means timing CPU-bound threads, which is
item 3 above under a different name. Proving it *by race condition* is worse: the outcome
is non-deterministic by definition, so the test would be flaky in exactly the way that
teaches a player to distrust the game.

So mission 7 teaches the GIL in its panel and is graded on **the consequence**: given a
workload, choose threads or something else, and the choice is visible in the returned
result. This is Island 6's resolution applied a second time, and it is recorded here so
the pattern reads as a policy rather than a series of one-off excuses.

### Mission map

| # | Slug | Introduces | Reinforces | Note |
|---|---|---|---|---|
| 1 | `the-waiting-room` | `blocking-vs-nonblocking` | `functions`, `big-o` | Sync only. Three waits in a row, and the total is the sum. Nothing async yet — the problem before the tool |
| 2 | `the-first-await` | `async-await`, `event-loop` | `blocking-vs-nonblocking`, `functions` | One coroutine, awaited by the engine. The loop is named because `await` outside one is the error everyone meets |
| 3 | `the-patient-signal` | — | `async-await`, `return-values` | **Relief.** An async function that returns a value like any other |
| 4 | `all-at-once` | `gather` | `async-await`, `event-loop`, `lists` | Three waits concurrently. Graded on completion order, not on the clock |
| 5 | `the-second-hand` | `threads` | `blocking-vs-nonblocking`, `functions` | The other tool for the same waiting problem, and the shared state it exposes |
| 6 | `the-shared-tally` | — | `threads`, `gather` | **Relief.** A `Lock`, and what it costs |
| 7 | `one-at-a-time-after-all` | `gil` | `threads`, `event-loop`, `big-o` | Why four threads do not make arithmetic four times faster. Graded on the choice, not on a clock |
| 8 | `the-slower-fleet` | `when-concurrency-helps` | `gil`, `gather`, `blocking-vs-nonblocking` | **The refusal mission.** The concurrent version is measurably worse and the correct answer is the plain loop |
| 9 | `the-right-tool` | — | `when-concurrency-helps`, `gather`, `threads`, `gil` | **Relief.** Three workloads, pick the tool for each |
| 10 | `the-whole-voyage` | — | all seven | Closing mission of the island and of the track |

Relief at 3, 6 and 9.

Mission 1 contains no async at all, and that is the island's most important placement. The
same order Island 5 used for `exceptions` before `try-except` and Island 7 for
`open-and-read` before `context-managers`: a player has to feel three seconds of pointless
waiting add up before `await` is a solution rather than a fashion.

Mission 2 introducing `async-await` and `event-loop` **together** is the third exception to
the one-new-concept rule. It is the least avoidable of the three: `await` outside a running
loop is a `SyntaxError` or a `RuntimeError` depending on where you put it, so a player who
does not know a loop exists cannot read their own first error message.

Reinforcement count:

| Concept | Introduced | Reinforced in |
|---|---:|---|
| `blocking-vs-nonblocking` | 1 | 2, 5, 8, 10 |
| `async-await` | 2 | 3, 4, 8, 10 |
| `event-loop` | 2 | 4, 7, 10 |
| `gather` | 4 | 6, 8, 9, 10 |
| `threads` | 5 | 6, 7, 9, 10 |
| `gil` | 7 | 8, 9, 10 |
| `when-concurrency-helps` | 8 | 9, 10 |

Every concept is reused at least twice. No orphans.

### blocking-vs-nonblocking
- **prereqs:** functions, big-o
- **objective:** tell work apart from waiting, and say which one your program is doing
- **misconceptions:** believing a slow program is always computing something; believing
  `time.sleep` and a long loop cost the same kind of time; believing "asynchronous" means
  "in parallel"; believing the CPU is busy while a network call is in flight
- **mastery:** given two slow functions, says which one concurrency could help and why the
  other one it cannot

### async-await
- **prereqs:** blocking-vs-nonblocking, functions
- **objective:** write a function that can pause at a wait and let something else run
- **misconceptions:** believing `async def` makes a function faster or parallel on its own;
  calling a coroutine without awaiting it and getting an object instead of an answer;
  believing `await` can appear anywhere; putting a blocking `time.sleep` inside a coroutine
  and stalling every other task on the loop
- **mastery:** writes a coroutine whose value comes back correctly, and says what calling
  it without `await` produces

### event-loop
- **prereqs:** async-await
- **objective:** name the thing that decides which paused coroutine runs next
- **misconceptions:** believing there are threads underneath; believing the loop can
  interrupt a coroutine that never awaits (it cannot — a tight loop freezes everything);
  believing several loops can run in one thread; believing `asyncio.run` can be nested
- **mastery:** explains what happens to every other task when one coroutine runs a
  three-second calculation with no `await` in it

### gather
- **prereqs:** async-await, event-loop, lists
- **objective:** start several waits at once and collect the results when they are all in
- **misconceptions:** believing `gather` returns results in completion order (it returns
  them in argument order, which is the useful guarantee); believing awaiting coroutines one
  after another in a loop is the same thing (it is the sequential version); not knowing
  that one exception cancels the collection unless `return_exceptions` says otherwise
- **mastery:** turns three sequential awaits into one concurrent batch, and says which of
  argument order and completion order the result preserves

### threads
- **prereqs:** blocking-vs-nonblocking, functions
- **objective:** run waiting work in parallel without rewriting the functions as coroutines
- **misconceptions:** believing threads make CPU-bound Python faster; forgetting a thread
  needs joining before its result is read; believing shared state is safe because "it is
  only one line"; believing a thread can be stopped from outside
- **mastery:** runs three blocking calls at once and collects all three results, having
  changed none of the three functions

### gil
- **prereqs:** threads, event-loop, big-o
- **objective:** say why Python threads speed up waiting and not computing
- **misconceptions:** believing the GIL makes threads useless; believing it makes shared
  state safe (it does not — a lock is still needed); believing it is a bug rather than a
  trade that makes the single-threaded case fast; believing every language has one
- **mastery:** given a CPU-bound workload and an I/O-bound one, picks threads for exactly
  one of them and says what would help the other

### when-concurrency-helps
- **prereqs:** gil, gather, blocking-vs-nonblocking
- **objective:** decide not to use concurrency, on evidence, and say what it would have cost
- **misconceptions:** believing more concurrency is always more speed; ignoring the
  fixed cost of starting tasks or threads for work measured in microseconds; believing
  concurrency reduces total work (it only overlaps waiting); reaching for it before
  measuring, which Island 10 already warned about
- **mastery:** given three workloads, ships the plain sequential loop for the one where it
  wins and can say what the concurrent version would have added

`[AI-ENG:concurrency-cost]` bridge, attached to mission 8 when it was written: an agent
that fans out ten tool calls in parallel pays the same trade — overlap the waiting, never
the work, and pay a fixed cost per branch. The reflex to parallelise a batch of LLM calls
that each take 20 ms is the same reflex this mission refuses, at a different scale.

### What authoring changed, and the two decisions it forced

The island shipped on 2026-08-10 exactly as mapped — same slugs, same concept per slot,
relief at 3, 6 and 9. Both engine items were built first, as an Island 5 case rather than
an Island 3 one, and both were exactly the size the design predicted: `harness.py` gained
an `inspect.iscoroutine` check and an `asyncio.run` inside the existing `try`, and
`loader.py:107` gained `(?:async\s+)?`. Mission 2's own solution passed on the first run,
which is what building the engine first buys.

Two things the design left open, both settled here.

**Mission 8 is graded by a declared cost model, not by a clock.** The refusal mission was
the one the design could not resolve: an honest proof that concurrency is *slower* is a
stopwatch, and this island forbids stopwatches. Completion order does not help either —
it proves overlap happened, not that overlapping was a mistake.

So the brief states the model and the player computes with it: the fixed cost per branch
and each job's duration arrive as arguments, waiting collapses to the longest one because
waits overlap, computing still sums because it does not, and every branch is paid for
whether or not it was worth it. That is Island 10's specification rule applied to
concurrency, which this document predicted would be needed here — *"a brief that says 'run
them concurrently' is not a specification either."*

The prediction was right and slightly wrong about where it would bite. Ordering was easy
to specify (mission 4 just promises distinct durations, so there is never a tie to break).
The *cost* was the part that needed a specification, because two correct concurrent
programs disagree about what concurrency cost them.

**The sleep budget came down from 200 ms to 120 ms, and the rule needed restating.** The
design's "total sleeps per test case" is the wrong measure for half the island: a gathered
or threaded case's wall clock is the *longest* wait, never the sum. The rule as it now
stands, and as the missions were written against:

> Sequential missions: the sum of a case's sleeps stays under 120 ms. Concurrent missions:
> the longest single sleep stays under 120 ms. Distinct durations at least 20 ms apart
> wherever completion order is graded, since Windows timer granularity is around 15 ms.
> Any mission that sleeps raises `max_runtime_ms` to 5000 explicitly.

Verified rather than assumed: the reference solutions were run fifteen times and every
completion-order case came back byte-identical.

One more finding worth recording, because it is the island's second honesty case after
Island 8's and Island 10 mission 1's. **Mission 6's unlocked version passes.** In CPython
an unguarded `counter += 1` in a short loop almost always produces the right total, and no
test at this size can tell the two versions apart. The brief says so out loud. A test that
went green only on the locked version would have to be flaky to exist, and a game that
claimed to detect the missing lock would be lying about something the player can check.

---

## Coverage checklist

Checked for **all eleven islands**, and all eleven have now shipped. Every table above
describes missions that exist, not intent.

Islands 8 to 11 all shipped on 2026-08-10 exactly as mapped - same slugs, same concept per
slot, same relief points. Authoring added one finding to each: Island 8's honesty rule,
Island 9's third laziness technique, Island 10's rule that a graded count needs a
*specified* algorithm and not merely a correct one, and Island 11's cost-model grading for
the refusal mission, each recorded in its own section.

Island 11 is also the only one that needed engine work built before its first mission was
written - the harness now awaits a coroutine entrypoint and the loader accepts `async def`.
That was the design's call and it held: no mission had to be reshaped around a gap.

- [x] Every concept has an explicit prereq list
- [x] No concept appears in a mission before its prereqs — verified against the mission map
- [x] Every concept is reused in at least two later missions — see the reinforcement tables. Two named exceptions: `encoding-basics` in Island 4 and `interactive-debugger` in Island 6, both argued where they occur
- [x] Objectives are verbs, never "understand"
- [x] Misconceptions are written, so hints can target them
- [x] The curve has relief missions after hard ones — Island 1: 3 and 9. Islands 2 and 3: 3, 7, 11. Islands 4 to 7: 3, 6, 9. Islands 8 to 11: 3, 6, and 9 or 10 — the shift is arithmetic, since the last concept introduced needs two later missions to be reinforced in
- [x] No mission introduces two new concepts — three exceptions, each argued where it occurs: Island 6 mission 3 (`print-debugging` + `interactive-debugger`, neither verifiable and one a hazard to run), Island 8 mission 1 (`classes` + `instances`, one idea seen from two sides), Island 11 mission 2 (`async-await` + `event-loop`, since a player who has not heard of the loop cannot read their own first error)

### Islands 8 to 11 were designed in one pass, against an earlier note

An earlier version of this section said each of the last four islands would be designed
immediately before its content was written, so that building the earlier ones could
change the later decisions. They were designed together instead, on 2026-08-10.

The reason is that three of the four share one constraint — what can and cannot cross the
JSON boundary between the sandbox and the game — and designing them separately would have
found it three times. Islands 8 and 9 are shaped by it (no instance, no generator, no
decorated function ever returned) and Island 11 is blocked by it outright. That is one
decision, not four, and it is cheaper to take once.

The original caution still applies to the *missions*: they are authored one island at a
time, playtested, and each island's tables are rewritten from what shipped.

### Engine limits found while designing, and where they bite

Each was verified against the code, not assumed:

- **One process per test case** (Island 3) — a mutable default is rebuilt every case, so
  the classic trap is only observable inside a single call.
- **Functions and `bytes` do not cross the JSON boundary** (Islands 3 and 4) — shaped the
  dispatch-table framing of `first-class-functions` and the byte-count framing of
  `encoding-basics`.
- **Nothing can assert on printed output** — `stdout` is captured but never compared.
  Island 6 hit this head-on and **chose the framing over the capability**: mission 3
  teaches print-debugging in its panel and is graded on the fix. Any rule strict enough to
  grade a print would be grading formatting, and would fail a player who reached for a
  debugger instead. Argued in full in Island 6.
- **Exceptions could not be tested at all** (Island 5) — fixed rather than designed
  around, by adding the `raises:` test-case field before Island 5's content was written.
  Cross-island scope corrections came out of the same pass: `slicing` was dropped from
  Island 4 (Island 2 already taught it) and `custom-exceptions` moved from Island 5 to
  Island 8 (it needs `class`).
- **No mission can plant a file, and the sandbox directory is shared across a run's test
  cases** (Island 7) — the second Island-5 case. `open-and-read` has nothing to open until
  a `files:` field exists, so that field is a prerequisite of the island's first mission
  rather than something to design around. Contract proposed in Island 7.
- **Instances, generators and decorated functions do not cross the JSON boundary either**
  (Islands 8 and 9) — the same wall as functions and `bytes`, now hit by the two islands
  whose entire subject matter is objects that carry state. Their default `repr` contains a
  memory address, so it changes on every run. Reshaped rather than built around: the object
  is created and consumed inside the submission, and only plain data comes back. It cost
  nothing pedagogically and it handed `dunder-methods` its motivation.
- **The wall clock measures a whole subprocess, not an algorithm** (Island 10) — the
  budget in `constraints.max_runtime_ms` covers interpreter start-up too
  (`engine/runners/python.py:115`, `181`). So complexity is graded by **returning the step
  count**, which is deterministic everywhere, and timing is used for exactly one mission
  under a stated 5x margin. A CPU-time measurement in the harness would be more precise and
  is deliberately not being built.
- **The harness cannot await, and the loader rejects `async def`** (Island 11) — the third
  Island-5 case, and the only remaining engine work in the curriculum.
  `engine/harness.py:132` calls the entrypoint synchronously, so a coroutine is returned
  and never run; `engine/loader.py:107` matches `^\s*def\s+` and fails the mission before it
  runs. Both are small and both are prerequisites of the island's first mission. Contract
  in Island 11.

The pattern across seven islands is worth naming, because it is the one transferable
lesson of this document: **design the island first, then find out what the engine cannot
do.** Three times the answer was to reshape the missions (Islands 3, 4, and 8 with 9),
three times it was to build the missing capability (Islands 5, 7 and 11), and twice it was
to accept that a concept is genuinely unassessable and say so (Island 6, and `gil` in
Island 11). Deciding which of the three *before* looking at the missions would have got it
wrong every time.
