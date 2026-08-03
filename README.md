# CodeQuest

**A terminal game that teaches you to program, from your first variable to async and
system design. Runs entirely on your machine. No account, no internet, no tracking.**

> Pick a language. Create a career. Sail from island to island. Every island teaches
> you something new, and the only way forward is to write code that works.

---

## Why this exists

Most coding practice sites give you a puzzle and a blank editor. If you already know
the concept, you solve it. If you do not, you get stuck and go read somewhere else.

CodeQuest puts the lesson **inside the mission**. Every mission opens with an analogy,
an explanation, and a worked example. Then it asks you to build something. The teaching
is written by hand and lives in this repository as plain YAML files. It is not generated,
and it does not need a network connection.

There is an optional AI mentor in the corner of the screen for when you want to ask a
question. The game teaches perfectly well with it turned off.

---

## Status

| | |
|---|---|
| **Current version** | 0.1.0 (in development) |
| **Playable** | Not yet, Phase 0 |
| **Languages available** | Python (in progress) |
| **Planned** | Java, TypeScript, plus Architecture, Security and AI Engineering tracks |

---

## Install

**Requirements:** Python 3.11 or newer, a terminal that supports 256 colors, git.

```bash
git clone https://github.com/<your-user>/codequest.git
cd codequest

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
```

Run it:

```bash
python -m codequest
```

### Optional: the AI mentor

The mentor is off by default. To enable it you need [Ollama](https://ollama.com)
running locally:

```bash
ollama pull gemma4:cloud
ollama serve
```

Then copy `.env.example` to `.env` and set:

```
CODEQUEST_MENTOR_ENABLED=true
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma4:cloud
```

If Ollama is not running the mentor panel shows "offline" and everything else works
normally.

---

## How to play

### 1. Choose your language

The main menu asks which language you want to learn. Each language is a separate world
with its own islands, its own missions, and its own progress.

### 2. Create a career

You get **four save slots**. A save holds one language, your level, your XP, which
islands you unlocked, and every solution you have written.

Four slots means you can run a Python career and a Java career side by side, or restart
one without losing the other.

### 3. Sail the islands

The map shows islands in order. Island 1 is open from the start. The rest are locked,
and each locked island tells you exactly what it needs:

```
  [1] Foundations        ########## 8/8    DONE
  [2] Collections        #####..... 5/10
  [3] Functions          LOCKED - finish 8 missions on Collections
  [4] Strings and Text   LOCKED
```

### 4. Solve a mission

The mission screen has four panels:

| Panel | What it holds |
|---|---|
| **Teaching** | The analogy, the explanation, a worked example, the key points |
| **Brief** | What your function must do |
| **Editor** | Your code, pre-filled with a starting stub |
| **Results** | What passed, what failed, and why |

Read the teaching panel first. It is not decoration, it contains what you need.

Press **F5** to run. The game executes your code in an isolated process with a time
limit, runs it against the tests, and reports back.

**Visible tests** are shown to you up front. They teach you the shape of the problem.
**Hidden tests** run too, and they cover the edge cases: empty inputs, negative numbers,
boundary values. You cannot pass by hardcoding an answer.

### 5. Stuck? Use the hints

Press **F1**. Hints come in three levels and you unlock them one at a time.

| Level | What you get |
|---|---|
| 1 | A question that points at what you are missing |
| 2 | The name of the concept or approach you need |
| 3 | A code example of the *pattern*, using a different problem |

Level 3 never gives you the answer to the mission in front of you. Assembling it is
still your job.

### 6. Ask the mentor

Press **F2** to open the chat. It knows which mission you are on and what your code
currently looks like. It will not hand you a solution. It asks questions and points at
concepts, the way a study partner would.

---

## Keybindings

| Key | Action |
|---|---|
| `F5` | Run your code |
| `F1` | Next hint |
| `F2` | Toggle mentor chat |
| `F3` | Toggle teaching panel |
| `Ctrl+S` | Save progress |
| `Ctrl+R` | Reset editor to the original stub |
| `Esc` | Back to the island map |
| `Ctrl+Q` | Quit |

Everything is reachable from the keyboard. The mouse works, but you never need it.

---

## Progression

- Each mission awards XP based on difficulty (10 for elementary, up to 60 for expert)
- Using a hint reduces the XP for that mission, but never to zero. Hints are a tool,
  not a punishment
- Islands unlock when you complete enough missions on the previous one
- Your solutions are kept, so you can go back and read what you wrote three weeks ago
  and see how much you have changed

---

## The learning tracks

### Language tracks

| Track | Covers |
|---|---|
| **Python** | Foundations, collections, functions, strings, errors, files, objects, pythonic patterns, algorithms, async |
| **Java** *(planned)* | Types, classes, collections, generics, streams, concurrency |
| **TypeScript** *(planned)* | Types, functions, objects, generics, async, DOM basics |

### Cross-cutting tracks *(planned)*

These unlock after you finish the fundamentals of a language, and they are not about
syntax:

| Track | Covers |
|---|---|
| **Architecture** | Design patterns, SOLID, layering, refactoring, Git flow, CI/CD |
| **Security** | Input validation, injection, secrets, least privilege, dependency risk |
| **AI Engineering** | Embeddings, chunking, retrieval, prompt design, evals, MCP |

Missions in these tracks look different. Instead of "write a function", you get working
but badly structured code and you have to fix it, or vulnerable code and you have to
find the flaw.

---

## Contributing a mission

Missions are YAML files. You do not need to touch the engine to write one.

1. Read `docs/mission-schema.md`
2. Read `docs/curriculum/python-syllabus.md` and pick a concept that needs coverage
3. Copy an existing mission from `content/python/islands/01-foundations/missions/`
4. Fill in the teaching block, the brief, the tests, the hints, and a working solution
5. Run `pytest tests/content` — it verifies your solution actually passes your own tests
6. Open a pull request

The rule that matters most: one mission introduces **one** new concept.

---

## Honest limitations

- **The sandbox is not a security boundary.** Your code runs in a subprocess with a
  timeout and memory limits. That stops accidents like infinite loops. It does not stop
  someone determined to break out. This is fine because you are running your own code on
  your own machine. It would **not** be fine if this ever became a web service.
- **Memory limits are POSIX only.** On Windows the game falls back to timeout only.
- **The forbidden-builtins check can be bypassed.** It exists to keep the lesson honest,
  not to stop an attacker.
- **The mentor is a small local model.** It will sometimes be wrong. The hand-written
  teaching content is the authority, not the chat.

---

## Documentation

| Doc | What it covers |
|---|---|
| `PROJECT_PLAN.md` | Architecture, roadmap, technical decisions |
| `docs/architecture.md` | How the layers fit together |
| `docs/mission-schema.md` | Every field in a mission file |
| `docs/curriculum/` | Concept ordering and learning objectives |
| `AGENTS.md` | How AI agents should work in this repo |

---

## License

MIT
