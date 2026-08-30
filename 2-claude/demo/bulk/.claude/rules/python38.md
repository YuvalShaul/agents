---
paths:
  - "**/bulk/*.py"
---

# Python 3.8 in this package

The batch host pins Python 3.8, so code under `bulk/` must stay importable
there even though the rest of the project targets 3.10+:

- `typing.List` / `typing.Tuple`, never `list[str]` or `tuple[str, ...]`.
- `str.format()` or `%`, not f-strings with `=` (`f"{x=}"`).
- No walrus operator, no `match`, no `X | Y` unions in annotations.
- Standard library only.

If you need a 3.10+ feature, the answer is to not need it. Nothing here is
performance-sensitive enough to justify a second interpreter on the host.
