# FINAL_PLAN.md — How to start CodeQuest in Claude Code

This file is the launch procedure. Read it once, do the setup, then paste the bootstrap
prompt into Claude Code inside VS Code.

---

## 1. Setup before the first prompt

```bash
# 1. Create the project folder and go into it
mkdir codequest && cd codequest

# 2. Copy every file from this delivery into it, keeping the structure:
#    AGENTS.md  README.md  PROJECT_PLAN.md  FINAL_PLAN.md
#    pyproject.toml  .gitignore  .env.example
#    .claude/skills/*  content/*  docs/*  .github/workflows/ci.yml

# 3. Git
git init
git add .
git commit -m "chore: project charter, architecture, skills and content schema"
git branch -M main
git checkout -b develop

# 4. Python environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 5. Open in VS Code
code .
```

Then start Claude Code in the VS Code terminal and paste the prompt in section 2.

**Check before you start:** `AGENTS.md` and `.claude/skills/` must exist in the project
root. Without them the agent will not know the teaching contract and will write your
code for you, which defeats the purpose.

---

## 2. Bootstrap prompt — paste this into Claude Code

```
Read AGENTS.md and PROJECT_PLAN.md in full before answering anything.

Context: I am Giovanni, an intermediate developer migrating into AI Engineering.
This repository is CodeQuest, a terminal game that teaches programming through
missions. It is both a portfolio project and my own training ground.

The rule that matters most, and it is in AGENTS.md section 0:
I write the implementation code. You teach, give signatures, and review.
You do not write function bodies in src/codequest/ unless I say the exact words
"write this one for me".

How I want you to work with me:
- Reply in Portuguese, write every file in English.
- Explain with an everyday analogy first, then the formal definition.
- When there are several approaches, give me the trade-offs: performance,
  readability, maintenance, scalability.
- When something is opinion or community convention, say so. Do not present a
  preference as a fact.
- Be direct. Tell me when I am wrong and what specifically is wrong.
- Treat me as a competent colleague, but explain advanced jargon the first time.

We are starting Phase 0 from PROJECT_PLAN.md.

For this first session, do these three things in order:

1. Confirm you read AGENTS.md and state the teaching contract back to me in one
   sentence, so I know it is loaded.

2. Walk me through the folder structure in PROJECT_PLAN.md section 4. For each
   top-level folder under src/codequest/, tell me in one line what lives there and
   which layer may import it. Then ask me two questions that check whether I
   actually understood the import rules.

3. Then teach me Phase 0 step by step. Start with pyproject.toml: explain what a
   build backend is, what "editable install" means and why it matters here, and
   what the difference is between dependencies and optional-dependencies. After the
   explanation, tell me what to run and let me run it.

Do not create any files in src/ yet. We do Phase 0 first.
```

---

## 3. Session sequence

One session per item. Do not skip forward. Each ends with something that runs.

| # | Phase | Session goal | Skill to load |
|---|---|---|---|
| 1 | 0 | Environment, packaging, git flow, CI skeleton | `game-architect` |
| 2 | 0 | `python -m codequest` prints a version and exits | `engine-developer` |
| 3 | 1.1 | `models/mission.py` dataclasses | `engine-developer` |
| 4 | 1.2 | `engine/loader.py` reads and validates YAML | `engine-developer` |
| 5 | 1.2 | Unit tests for the loader | `test-engineer` |
| 6 | 1.3 | `engine/guard.py` AST checks | `security-auditor` |
| 7 | 1.4 | `engine/runners/base.py` protocol | `game-architect` |
| 8 | 1.4 | `engine/runners/python.py` sandbox | `engine-developer` |
| 9 | 1.4 | Runner tests: timeout, crash, memory | `test-engineer` |
| 10 | 1.5 | `engine/evaluator.py` and the verdict taxonomy | `engine-developer` |
| 11 | 1 | CLI checkpoint: run a mission file, print pass/fail | `engine-developer` |
| 12 | 2 | SQLite schema and repositories | `engine-developer` |
| 13 | 2 | `ProgressService`: XP, levels, unlocking | `engine-developer` |
| 14 | 3 | Finish the Python syllabus document | `curriculum-designer` |
| 15 | 3 | Write missions 1 to 8 of Foundations | `mission-author` |
| 16 | 3 | `tests/content/test_all_missions.py` | `test-engineer` |
| 17 | 4 | Textual app shell and main menu | `tui-developer` |
| 18 | 4 | Save select, four slots | `tui-developer` |
| 19 | 4 | Island map | `tui-developer` |
| 20 | 4 | Mission screen | `tui-developer` |
| 21 | 4 | Hint panel, XP feedback | `tui-developer` |
| 22 | 5 | Ollama client and anti-spoiler policy | `ai-mentor-integrator` |
| 23 | 5 | Mentor chat widget | `tui-developer` |
| 24 | — | v1.0 release: README, screenshots, tag | `docs-writer` |

**Milestone v1.0** is session 24. Java (Phase 6) does not start before that.

---

## 4. How to open each session after the first

```
Read AGENTS.md. Load the skill .claude/skills/<skill>/SKILL.md.

We are on session <N>, Phase <X> from PROJECT_PLAN.md.
Last session I built <what>. It works / it has this problem: <describe>.

Today's goal: <goal from the table>.

Teach first, then give me the signature, then let me write it.
```

---

## 5. Rules to protect the point of the project

**Do not let the agent write your code.** If a full implementation appears without
you asking, stop and say: "you broke the contract in AGENTS.md section 0, explain
instead". The rule only works if you enforce it.

**Do not skip the tests.** Every module gets tests before the next module starts.
Skipping them is borrowing time from a future session at a bad interest rate.

**Do not build three phases ahead.** The checkpoint at the end of each phase exists
so you have something working. A half-built engine plus a half-built TUI is worth
less than a finished engine alone.

**Commit small and often.** One concept per commit, Conventional Commits format. Your
git history is part of the portfolio and a recruiter will read it.

**Write down what you learned.** One line in the PR description per feature branch.
In six months this is how you will know how far you moved.

---

## 6. What you will have at v1.0

A working game, and evidence of these skills:

| Area | Evidence |
|---|---|
| Python | An engine with layered architecture, protocols, dataclasses, AST work |
| Security | Process isolation, resource limits, static analysis, a documented threat model |
| Data | Relational schema design, SQL, migrations, repository pattern |
| Testing | Unit, integration, and content validation suites, CI on every push |
| Frontend | A full TUI with reactive state and workers |
| AI | LLM integration, prompt design, guardrails, graceful degradation |
| Process | Gitflow, Conventional Commits, PRs, CI/CD, documentation |

That is a portfolio project that shows engineering judgment, not just syntax.

---

## 7. First command

```bash
code .
```

Then paste the prompt from section 2.
