# Art Direction

The visual contract for the Textual interface. Written **before** Phase 4 so that no
screen invents its own colour, and so that two widgets built weeks apart still look like
the same program.

If a value is not in this document, it does not go in a `.tcss` file.

---

## 1. The idea

**A nautical chart read under a lamp.**

Deep ink-blue ground. Rules and frames in aged brass. Paper only where there is long text
to read — the teaching panel and the brief. The rest is chart, not page.

The metaphor is not decoration: the game is already about islands, sailing and a career.
The interface should look like the object a navigator would actually have on the table.

**What this rules out.** No neon. No gradients. No emoji as decoration. No rounded
"friendly app" look. The reference points are `lazygit`, `btop` and the Charm tools —
dense, precise, and unmistakably a terminal instrument.

---

## 2. Palette

Dark ground, chosen because a light panel inside a dark terminal reads as a window pasted
on top, and because sessions are long.

Every colour has a semantic name. Screens reference the name, never the hex.

| Token | Hex | Use |
|---|---|---|
| `ink` | `#0e1720` | Application background. The deep water of the chart |
| `ink-raised` | `#152230` | Panel background, one step off the ground |
| `sea` | `#1d3042` | Secondary surface: map, lists, table rows |
| `parchment` | `#e8dcc4` | Text on the teaching and brief panels |
| `parchment-dim` | `#b6ab95` | Secondary text, captions, hint metadata |
| `brass` | `#c9a227` | Frames, rules, headings, the focused border |
| `brass-dim` | `#7a6520` | Unfocused frames and separators |
| `beacon` | `#4fb3d9` | The single accent: focus, primary action, current island |
| `verified` | `#5fae7f` | A case passed |
| `adrift` | `#d2603f` | A case failed |
| `becalmed` | `#828d99` | Not run, locked, disabled |

**Contrast.** Two thresholds apply, and confusing them is how "accessible" palettes ship
broken. Text needs **4.5:1** (WCAG AA, 1.4.3). Frames and rules carry no text and need
**3:1** (WCAG 1.4.11, non-text contrast).

Measured, not estimated:

| Pair | Use | Ratio | Floor |
|---|---|---:|---:|
| `parchment` on `ink` | body text | 13.3:1 | 4.5 |
| `parchment` on `ink-raised` | panel text | 11.9:1 | 4.5 |
| `parchment` on `sea` | list rows | 10.0:1 | 4.5 |
| `brass` on `sea` | selected mission row | 5.6:1 | 4.5 |
| `verified` on `ink-raised` | completed mission row | 6.0:1 | 4.5 |
| `verified` on `sea` | completed row, selected | 5.1:1 | 4.5 |
| `parchment-dim` on `ink` | secondary text | 8.0:1 | 4.5 |
| `beacon` on `ink` | accent text | 7.6:1 | 4.5 |
| `brass` on `ink` | headings | 7.5:1 | 4.5 |
| `verified` on `ink` | pass label | 6.8:1 | 4.5 |
| `brass` on `ink-raised` | panel headings | 6.7:1 | 4.5 |
| `becalmed` on `ink` | disabled text | 5.4:1 | 4.5 |
| `adrift` on `ink` | fail label | 4.7:1 | 4.5 |
| `brass-dim` on `ink` | unfocused frame | 3.2:1 | 3.0 |

**Two values were corrected while writing this table**, which is the argument for
measuring instead of eyeballing:

- `becalmed` started at `#6b7785` and measured **3.96:1** — it carries text ("locked",
  disabled labels) so it failed. Lightened to `#828d99`.
- `brass-dim` at **3.2:1** would fail as text. It is frames only, so the 3:1 rule applies
  and it passes — but that is an argument for never putting a label in `brass-dim`.

`adrift` at 4.7:1 and `brass-dim` at 3.2:1 sit closest to their floors. Darken either and
re-measure before shipping.

**One accent, on purpose.** `beacon` marks exactly one thing per screen: where you are, or
what to press. An interface where four things glow has no accent at all.

**The island map's mission list breaks the plain list rule, and only there.** A track list
has three rows and a save list has two, so `parchment` on `sea` is enough to find the
selection. The mission list has a hundred nearly identical lines, and it was not — playing
the game is what showed it. So there, and nowhere else:

- the selected row is `brass`, bold
- a completed row is `verified`

A selected row goes brass whole, glyph included — the check does not stay green while it
is selected. The rule is that colour never carries meaning *alone*, and the `✔` keeps its
shape, so completion is still readable there. The third contrast pair above is measured
because a completed row is green until the moment it is picked.

This is the one place `brass` carries body text instead of a frame or a heading.

---

## 3. Character vocabulary

Unicode box-drawing throughout, no ASCII fallback. Windows Terminal and the VS Code
terminal render all of it, and the thin rules *are* the chart aesthetic.

Fixed vocabulary so two screens built a month apart do not disagree:

### Frames

```
Unfocused          Focused
┌──────────┐       ╔══════════╗
│          │       ║          ║
└──────────┘       ╚══════════╝
```

The focused panel gets a double rule in `brass`; everything else is single in
`brass-dim`. That is the whole focus indicator — no background change, no glow.

### Progress

```
█ ▉ ▊ ▋ ▌ ▍ ▎ ▏
```

Eighth-blocks give a bar with eight times the resolution of a cell. A 10-cell bar
therefore has 80 steps, which is enough that progress never looks stuck.

```
Foundations  ████████▌·······  8/10
```

### State

Never signalled by colour alone — colour **always** carries a symbol alongside it. This
covers colour blindness and a monochrome terminal, and it is already a rule in the
`tui-developer` skill.

| Symbol | Meaning | Colour |
|---|---|---|
| `✔` | passed | `verified` |
| `✘` | failed | `adrift` |
| `·` | not run | `becalmed` |
| `▸` | current position | `beacon` |
| `◇` | available, not started | `parchment-dim` |
| `▪` | locked | `becalmed` |

`▪` rather than a padlock emoji: emoji width is inconsistent across terminal fonts and a
double-width glyph breaks column alignment.

### Map

| Symbol | Meaning |
|---|---|
| `≈` | open sea |
| `▲` | island |
| `◆` | the island you are on |
| `┈` | a charted route between islands |

---

## 4. Typography and rhythm

The terminal supplies the font, so the only levers are weight, case and space.

- **Headings** — `brass`, small caps by convention (`ISLAND 1 · FOUNDATIONS`), never bold
  and coloured at the same time
- **Body** — `parchment`, normal weight
- **Metadata** — `parchment-dim`, and never longer than the thing it describes
- **Code** — the terminal font, syntax highlighting from the Textual `TextArea`
- **One blank line** between blocks inside a panel; panels are separated by their frame,
  never by extra padding

Number alignment matters more than it sounds: XP totals, case counts and progress
fractions are right-aligned so the eye compares columns instead of reading digits.

---

## 5. Responsive rule

The four-panel layout needs room. Three bands, and the game never simply refuses to run.

| Width | Layout |
|---|---|
| **≥100 cols** | Four panels side by side, as in the `tui-developer` diagram |
| **80–99 cols** | Teaching and Results become tabs in the right column; editor stays full height |
| **<80 cols** | Single panel with a tab bar, plus a one-line notice that the view is reduced |

Height follows the same principle: below 30 rows the teaching panel collapses to a
scrollable strip rather than squeezing every panel to nothing.

**Never a hard refusal.** A "your terminal is too small" wall is hostile to anyone running
the game in a split next to their editor. Degrade, tell the truth about degrading, keep
playing.

---

## 6. Motion

Terminals redraw whole cells, so animation is cheap to get wrong and expensive to read.

- A run in progress shows a **determinate** indicator — case 3 of 8 — not a spinner. The
  engine knows how many cases there are, so a spinner would be hiding information it has.
- No transitions between screens. Instant is a feature in a keyboard-driven interface.
- The only animated element permitted is the progress bar during a run.

---

## 7. Applying this in Phase 4

- Every colour becomes a `$token` in `styles.tcss`; screens use the token
- A widget that needs a colour not on this list means either the list is incomplete or the
  widget is doing something the design did not intend. Resolve which before adding a hex
- Symbols live in one module-level constant table, not scattered as literals
- The contrast table above is the acceptance criterion, not a suggestion

Screen order, the mission-screen layout and the layer rules stay in
`.claude/skills/tui-developer/SKILL.md`. This document owns *how it looks*; that one owns
*how it is built*.
