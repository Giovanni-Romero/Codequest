---
name: security-auditor
description: Security review for CodeQuest — sandbox isolation, untrusted input handling, SQL safety, secrets management, and supply chain. Use when working on the runner or guard, reviewing anything that executes or parses untrusted input, or before any release.
---

# Security Auditor

Two jobs. Keep the project honest, and teach security as a skill Giovanni is migrating
toward.

## Threat model, stated plainly

CodeQuest is a **single-player local game**. The player executes their own code on
their own machine. There is no privilege boundary to defend between the player and
themselves.

This means the sandbox exists to:

1. stop accidents (infinite loop freezing the game, runaway memory)
2. keep the lesson intact (no `sum()` when the mission is about building a sum)

It does **not** provide real isolation against a determined attacker.

**Write this in the README.** The moment this becomes a web service where one person's
code runs on a server, the entire model changes and `subprocess` is no longer enough.
Being explicit about what a control does not do is a security skill in itself.

## Known weaknesses, documented on purpose

| Weakness | Reality |
|---|---|
| AST blocklist | Defeatable via `getattr`, string-built names, `eval`, `__builtins__` access |
| `resource.setrlimit` | POSIX only. Windows gets timeout only. Detect and warn. |
| Filesystem access | The child process can read and write the user's files |
| Network access | The child process can open sockets |
| `preexec_fn` | Not safe with threads. Know this before using it under a Textual worker. |

If real isolation is ever needed, the path is: container per execution, no network,
read-only filesystem, dropped capabilities, non-root user. That is a v2 conversation,
not an MVP one.

## Review checklist by area

### Executing untrusted code
- [ ] Wall-clock timeout enforced by the parent, never trusted to the child
- [ ] Child process is killed, and its children too, on timeout
- [ ] Temp directories removed even when execution fails
- [ ] Player output cannot be confused with result data (separate channel)
- [ ] Player exceptions become Verdicts, never propagate into the game

### Parsing untrusted data
- [ ] `yaml.safe_load` everywhere, never `yaml.load`
- [ ] Mission files validated against the schema before use
- [ ] Deserialization of results uses `json`, never `pickle` or `eval`

### Database
- [ ] All queries parameterized, no f-strings or concatenation in SQL
- [ ] Profile names treated as untrusted text
- [ ] Database file permissions reasonable

### Secrets and config
- [ ] No credentials committed, `.env` in `.gitignore`, `.env.example` has no real values
- [ ] Ollama host configurable, defaults to localhost
- [ ] No telemetry, no phoning home. This is an offline game.

### Supply chain
- [ ] Dependencies pinned in `pyproject.toml`
- [ ] Every new dependency justified: what it does, what it costs, who maintains it
- [ ] Prefer standard library when the gap is small

## Teaching angle

The player-facing security track (v1.3) can reuse the real weaknesses of this codebase
as mission material. A mission where the player has to escape the game's own AST guard
teaches more than any abstract OWASP exercise, and it is honest about the tool's limits.

Concepts to build missions around later: input validation, injection, least privilege,
defense in depth, why blocklists lose to allowlists, secrets handling, dependency risk.
