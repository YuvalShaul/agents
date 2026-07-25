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

## Conventions

- Pydantic schemas for request/response validation.
- Type hints everywhere.
- Keep it a single file unless it grows enough to justify splitting into
  `schemas.py` / `routes.py` / `store.py`.

## Notes

- Storage is intentionally in-memory — don't add a database or ORM here.
- Tests call `books.clear()` in `setup_function` to reset state between
  tests, since the store is a module-level dict.
