# Project audit — 2026-08-11

Run the day after the Python track closed. The question was not "does it work" — it
does — but "is anything owed that nobody is tracking". Eight things were, plus one red
test that had been dismissed as flakiness for two islands running.

Everything below was checked against the repository, never against the plan. Where the
plan and the disk disagreed, the disk won and the plan was corrected.

---

## What was owed, and is now paid

### 1. The Phase 5.1 HTML lesson did not exist

`CLAUDE.md` §7 and §9.2 are unambiguous — *no lesson, no phase* — and `PROJECT_PLAN.md`
said Phase 5.1 *"closes when Island 11 (Async) ships, at which point it gets its HTML
lesson"*. Island 11 shipped on 2026-08-10 and the lesson had not been written.

Written as `D:\Projetos\2026\_AI_Eng_Aulas\Fase7-Curriculo-como-Eval-Design.html`. The
lessons are numbered by lesson, not by plan phase — Fase 6 is "Arquivos no Sandbox",
which was Island 7's `files:` feature — so this is the seventh.

### 2. `[AI-ENG:debugging-methodology]` was promised and never attached

`docs/curriculum/python-syllabus.md` said *"bridge, to attach when mission 4 is
written"*. Island 6 mission 4 was written months ago and the bridge was nowhere: not in
`src/`, not in the mission, not in the index.

The contrast is what made it a finding rather than a nit. `[AI-ENG:concurrency-cost]`,
promised the same way for Island 11, **was** delivered. The pattern existed and Island 6
had been skipped.

Now attached to `content/python/islands/06-debugging/missions/04-halve-the-search.yaml`
and its Portuguese mirror.

### 3. Bridges that live in content had no index and no verification

`docs/ai-eng-bookmarks.md` indexed 19 bookmarks, all in `src/`. `concurrency-cost` lived
in a mission YAML and appeared in no index at all.

This mattered more than it looked. The whole argument for the index is that a stale
`file:line` is worse than no citation, and it is `scripts/refresh_bookmarks.py` plus
`tests/unit/test_bookmarks.py` that make the claim enforceable. A bridge outside that
loop has none of the guarantee.

Both tools now walk `content/**/*.yaml` alongside `src/**/*.py`, skipping `-pt` mirrors
so the indexed target cannot flip between languages. **21 bookmarks**, all verified by
the same test.

### 4. The README understated the project by 80%

> | **Content** | Islands 1-2, Foundations and Collections: 22 missions, in English and Portuguese |

Eleven islands. 117 missions. This was the most visible line in the repository, and for
a project whose stated purpose includes being a portfolio, it was the worst single
finding in the audit.

The example island map was stale too: it showed Collections with 10 missions (it has 12)
and *"finish 8 missions on Collections"* as the unlock rule, when unlocking is a running
total across the track. Both replaced with the real symbols and the real numbers.

### 5. `CLAUDE.md` described a CI that had changed

It said the `windows:` job was gated with `if: false` and *"must be enabled once the
fallback exists"*. The fallback exists and the job has been running all three suites on
`windows-latest`. An operating instruction that is wrong is worse than one that is
missing, because this file is read at the start of every session.

### 6. `docs/mission-schema.md` did not know async existed

Zero occurrences of `async` or `coroutine`, while ten shipped missions used an async
entrypoint. A mission author reading the schema to find out what they may write would
have concluded, correctly from the document and wrongly in fact, that they may not.

Now documented, with the three rules Island 11 learned by being written: the engine
awaits the entrypoint, the solution must not call `asyncio.run` on itself, and a
*synchronous* entrypoint may call it freely.

### 7 and 8. Two snapshot tests were red, and it was not flakiness

`test_results_after_a_failing_run` and
`test_editor_stays_visible_with_many_failing_cases` failed roughly two runs in three.
Both had been written off as intermittent during Island 9 and again during Island 10.

There were two causes stacked on each other, and finding the second one required
disproving the first.

**Cause one: waiting on a clock instead of on a condition.** Both tests ran
`await pilot.pause(delay=8)` after pressing F5. A run spawns one subprocess per test
case on a worker thread, so how long it takes depends on the machine. Too short and the
snapshot caught the results panel mid-render; too long and every run paid for the worst
case. `MissionScreen.running` — set in `action_run`, cleared in `_show_outcome` — was
already the screen's own answer to "am I done" and nobody was reading it.

Fixing that alone took the failure rate from ~2 in 3 down to ~1 in 10, and cut 16
seconds of pure sleep from the suite. It did not reach zero, which is where guessing
stopped and measuring started.

**Cause two: the editor's cursor blinks.** Forty instrumented runs caught four failures
and every one of them differed the same way — an extra `.terminal-r9 { fill: #121212 }`
in the stylesheet, renumbering every class after it. A visible cursor is one more
distinct colour, so whether the snapshot lands on a lit or unlit blink phase changes the
whole CSS table. That is nondeterminism by construction, and no amount of waiting fixes
it.

`_open_mission` now sets `cursor_blink = False`. Blinking is right in the game and
meaningless in a still image.

**Result: 25 consecutive green runs** of the full snapshot suite, and the whole file
runs in about four seconds instead of twenty.

The lesson worth keeping is the middle step. "It is flaky" is a diagnosis that forecloses
investigation, and this one survived two islands because nobody made it produce evidence.
Both causes were real; fixing only the obvious one would have looked like progress and
left the test red.

---

## Verified healthy — checked, not assumed

- **The unlock chain is exact.** Cumulative mission counts across the eleven islands are
  0, 10, 22, 34, 44, 54, 64, 74, 85, 96, 107, and every `island.yaml` requirement matches
  its position in that sequence. 117 missions total.
- **No `TODO`, `FIXME`, `XXX` or `HACK` anywhere in `src/`.**
- **The Windows CI job is enabled** and runs unit, content and integration on
  `windows-latest`, which is the platform where the sandbox has no memory cap and
  degrades to a wall-clock timeout.
- **The portable build shipped** (`a123c5f`): `codequest.spec`, `pyinstaller` in a
  build-only extra, `config.py` frozen-aware.
- **EN/PT parity holds** across all 117 mission pairs on the twelve locked fields.

---

## Deferred on purpose — not defects

These are recorded so that "not done" cannot later be mistaken for "overlooked".

### F8 — ask the mentor to explain

`mentor/prompts.py` has `build_messages` and no `build_explain_messages`; there is no F8
binding in `tui/`. Sequenced by Giovanni's decision to come after the game is complete,
which has now happened. `PROJECT_PLAN.md` Phase 5 carries the full design.

### The teaching retrofit of Islands 1 to 7

The audit put a number on the complaint that produced F8. First mission of Island 1:
**117 lines**. First mission of Island 11: **265 lines**. The older panels carry roughly
half the teaching of the newer ones, and it is now a measurement rather than an
impression.

Deferred by Giovanni, island by island.

### Phases 6 and 7

Java track, then the Architecture / Security / AI Engineering cross-cutting tracks.
Roadmap, not backlog.

---

## What this audit did not cover

Stated so the next reader knows the edges:

- **No playtesting.** Every check here is static or automated. Whether Island 11's
  missions are *enjoyable* is a question only Giovanni playing them answers, and the
  briefs of missions 4 and 5 — which prescribe loop structure to make counts gradable —
  are the ones most worth his opinion.
- **The portable build was not rebuilt or re-verified on a machine without Python.** Its
  checkpoint in `PROJECT_PLAN.md` §5.2 was met when it shipped; nothing since then
  touched packaging, but nothing re-confirmed it either.
- **No performance work beyond the one measurement that forced itself.** Importing
  `asyncio` at the top of `harness.py` cost ~75 ms against a ~5 ms baseline on every test
  case of every mission, which is why it is now imported lazily. Nothing else was
  profiled.

---

## One loose end, recorded rather than closed

During the final validation pass, `codequest check --track python` reported **116/117**
once, while the integration suite was running concurrently on the same machine. Every
subsequent run — including three deliberate attempts under heavier contention, with six
competing processes — came back 117/117.

The likely explanation is a wall-clock budget lost under load: a handful of missions are
graded on time (Island 10 mission 9, and the Island 11 missions that sleep), and
`max_runtime_ms` is enforced by the parent against a fresh subprocess. Contention is
exactly what those are vulnerable to.

Two honest notes rather than a conclusion:

1. **The failing mission's name was never captured**, because the command was run through
   `tail -2` and only the summary line survived. A one-line shell habit destroyed the
   evidence for the one failure that mattered. Next time: grep for the failure, not the
   tail.
2. **It is not reproducible on demand**, so it is not fixed and should not be described
   as fixed. If CI ever reports a count below 117, this paragraph is the first place to
   look, and the run should be repeated *without* `tail`.
