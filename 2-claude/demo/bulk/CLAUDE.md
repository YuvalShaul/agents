# Bulk consignment

Builds the nightly **manifest file** that Ondura's batch host ingests. This
is a *different interface* from the JSON API used everywhere else in this
project: no HTTP, no JSON, no seals returned — a fixed-width file dropped in
`manifests/`, picked up by the host, and never acknowledged.

## Commands

```
python3 consign.py --date 2026-08-14        # build manifests/20260814.man
python3 .claude/skills/build-manifest/scripts/check_manifest.py manifests/20260814.man
```

## Structure

- `pending.csv` — what goes into the next manifest: `seal,title,disposition`.
- `consign.py` — builds a manifest from `pending.csv`.
- `manifests/` — one `.man` file per consignment date.

## Rules that differ from the rest of the project

- **Python 3.8.** The batch host runs an old interpreter. No `list[str]`
  annotations, no walrus, no f-strings with `=`. Use `typing.List` and
  `str.format()`. The root project's 3.10+ style does not apply here.
- **Manifests are immutable.** A `.man` file that has been written is never
  edited. A correction is a *new* manifest: withdraw with `WD`, then re-add.
- **No dependencies.** Standard library only, even for tests. FastAPI and
  Pydantic exist in the root project; they are not importable on the host.
- **The host fails silently.** A malformed record is dropped without an
  error anywhere. Validate before dropping the file, always.

## Ondura Standard Time

The date in a manifest header is UTC+3, not UTC and not local time. A
manifest built after 21:00 UTC carries the *next* day's date. Getting this
wrong produces a file the host accepts and files under the wrong day, which
is only noticed at the end of the quarter.
