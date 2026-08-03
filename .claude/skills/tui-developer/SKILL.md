---
name: tui-developer
description: Frontend work for the Textual terminal interface — screens, widgets, layout, keybindings, reactive state, and styling. Use when building or fixing anything under src/codequest/tui.
---

# TUI Developer

Textual is the frontend framework. Think of it as React for the terminal: a component
tree, reactive state, an event loop, and CSS-like styling in `.tcss` files.

Teaching contract applies. Explain the pattern, give the class skeleton, let Giovanni
fill the logic.

## Screen build order

Each depends on the previous, so do not reorder:

1. `main_menu.py` — choose language (Python now, Java and TS greyed out)
2. `save_select.py` — four career slots, create, resume, delete with confirmation
3. `island_map.py` — islands as cards, locked ones visibly locked with the requirement shown
4. `mission.py` — the main screen, four regions: teaching, brief, editor, results
5. `settings.py` — mentor on/off, theme, editor preferences

## The mission screen layout

```
+----------------------------------------------------------+
| Island 1 / Mission 2  -  Sum of a list        XP 40  L2   |
+---------------------------+------------------------------+
| TEACHING                  | CODE EDITOR                  |
| analogy, explanation,     | stub pre-filled              |
| worked example, key points| player types here            |
| (scrollable)              |                              |
+---------------------------+------------------------------+
| BRIEF                     | RESULTS                      |
| what to build             | per-test pass/fail + reason  |
+---------------------------+------------------------------+
| [F5] Run  [F1] Hint  [F2] Mentor  [Esc] Map              |
+----------------------------------------------------------+
```

The mentor chat is a collapsible panel, not a permanent region. Default collapsed.

## Rules for this layer

- **No business logic in a screen.** A screen calls a service and renders the answer.
  If you find yourself computing XP or deciding what unlocks inside `tui/`, stop.
- **Never block the event loop.** Running a submission takes seconds. Use Textual's
  `@work` decorator (worker threads) or async, and show a running state.
- **Keyboard first.** Every action must have a binding. Mouse is a bonus.
- **All colors and spacing in `styles.tcss`.** No inline style strings scattered in
  Python.

## Textual concepts to teach, in order

1. `App` and `Screen` — the app is the window, screens are pages you push and pop
2. `compose()` — declares the widget tree once, like a render function
3. `reactive` attributes — change the value, the UI updates itself, no manual redraw
4. Message passing — a widget posts a message, a parent handles it. This is how you
   keep widgets from reaching into each other
5. `@work` — long tasks off the main thread so the UI stays alive
6. `.tcss` — selectors, docks, grid layout

Analogy for reactive state: a spreadsheet cell with a formula. You never redraw the
cell by hand. You change the input and everything downstream updates itself.

## Accessibility and feel

- Never signal state by color alone. Pair color with a symbol (check, cross, dot).
- Show progress during a run. A frozen screen reads as a crash.
- Failure output must be readable at a glance: which test, what was expected, what came
  back, in that order.
- Confirm destructive actions (delete save) with an explicit dialog.

## Review checklist

- [ ] Screen imports only from `services/` and `models/`
- [ ] No `sqlite3`, no `subprocess`, no `yaml` anywhere in `tui/`
- [ ] Long operations run in a worker, UI stays responsive
- [ ] Every action reachable by keyboard, bindings shown in the footer
- [ ] Styling in `.tcss`, not inline
- [ ] The screen works when the mentor module is absent
