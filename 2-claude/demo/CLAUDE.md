# Books API

A small FastAPI REST API for managing books. Data is stored **in memory**
(a plain dict in `main.py`) — nothing is persisted, and all data is lost on
restart.

## Commands

```
# install deps
pip install -r requirements.txt

# run the dev server
uvicorn main:app --reload

# run tests
pytest
```

## Structure

- `main.py` — schemas (`BookCreate`, `Book`) and all routes in one file.
- `tests/test_main.py` — endpoint tests using FastAPI's `TestClient`.
- `bulk/` — the nightly consignment builder for Ondura's batch interface.
  It has its own `CLAUDE.md`, its own `.claude/rules/`, and its own skills,
  because almost none of the conventions above apply there.

## Conventions

- Pydantic schemas for request/response validation.
- Type hints everywhere.
- Keep it a single file unless it grows enough to justify splitting into
  `schemas.py` / `routes.py` / `store.py`.

## Notes

- Storage is intentionally in-memory — don't add a database or ORM here.
- Tests call `books.clear()` in `setup_function` to reset state between
  tests, since the store is a module-level dict.

## Subagents

Two agent types are defined in [`.claude/agents/`](.claude/agents), so they
are part of the project rather than one person's habit:

- `api-reviewer` — read-only review of `main.py` and the tests. It has no
  `Write` or `Edit` tool, by design.
- `test-writer` — adds tests and runs `pytest` in its own git worktree, so it
  never edits this checkout.

## Ondura Interlibrary Registry

Books in this catalogue may carry a **seal** issued by the Ondura
Interlibrary Registry (OIR), an external service with its own application
protocol and code format. None of those rules are guessable from this
codebase, so they live in [`.claude/skills/`](.claude/skills) rather than
here:

- `/oir-registration` — the application procedure, plus the registry client.
- `oir-codes` — the seal-code format and how to store one. Claude loads it
  on its own when working on `main.py` or the tests.
- `/registry-status` — triage of all open applications.

The registry itself is external; for local work, run the stand-in:
`python3 .claude/skills/oir-registration/scripts/oir_mock.py`.

## Enforcement

Some of the rules above are enforced by hooks in
[`.claude/settings.json`](.claude/settings.json), not left to good intentions:

- A `.man` file under `bulk/manifests/` cannot be edited by any tool call —
  file tools or shell. Correct `pending.csv` and supersede the consignment.
- Edits to `bulk/pending.csv` are checked for bad seals, over-long titles and
  unknown dispositions, and the problems come straight back.
- Each session opens with the registry's live state injected.
- A turn will not end while a manifest *this working tree changed* fails
  validation (once per session).

The scripts are in [`.claude/hooks/`](.claude/hooks). They are shell commands
this repository runs on your machine — read them before trusting the folder.

## MCP

The registry is also available as an MCP server — the same operations as
`oir_cli.py`, offered as typed tools (`mcp__oir__apply`, `mcp__oir__attest`,
…). It is declared in [`.mcp.json`](.mcp.json) at project scope, so it needs
approving once per machine, and its source is [`mcp/`](mcp).

The server is *access only*. The order of the steps, the oath window and the
tick trap live in the `oir-registration` skill; a tool list does not replace
a procedure.
