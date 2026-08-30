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
