---
name: oir-codes
description: The Ondura seal-code format — how a seal is built from author and year, and how to validate one. Use when reading, storing, validating, or generating an OIR seal code, or when adding a registry field to the Books API.
paths: ["main.py", "tests/test_main.py"]
---

# Ondura seal codes

A seal code identifies a registered book permanently:

```
OIR-HR-1965-M
 │   │   │   └─ check character
 │   │   └───── publication year, 4 digits
 │   └───────── shelf: the first two consonants of the author's SURNAME,
 │              uppercased, padded with X if there is only one
 └───────────── fixed prefix
```

Regex: `^OIR-[A-Z]{2}-\d{4}-[A-Z]$` — necessary, not sufficient. A code that
matches the regex can still have a wrong check character.

## Check character

```
alphabet = "BCDFGHJKLMNPQRSTVWXZ"          # 20 consonants, no vowels
total    = sum of the four year digits + sum of (letter - 'A' + 1) for both shelf letters
check    = alphabet[(total * 7) % 20]
```

For *Dune* (Frank Herbert, 1965): shelf `HR` → H=8, R=18; digits 1+9+6+5=21;
total = 47; (47 × 7) % 20 = 9 → `M`. Seal: `OIR-HR-1965-M`.

## Storing seals in this project

- A seal is an opaque identifier: store it as a **string**, never split into
  columns and never re-derived from the book's fields at read time.
- Validate on the way *in* (reject a malformed or bad-check-character code),
  never on the way out — a seal that the registry issued stays valid even if
  the book's title or author is later corrected.
- Books without a seal are normal. Model it as `str | None`, not `""`.
- Never generate a seal to fill the field, in tests or in seed data. Use a
  registry-issued one: `OIR-HR-1965-M` (*Dune*) or `OIR-ST-1815-X` (*Emma*).
  Fabricated codes have been shipped to production more than once because
  they pass the regex.

Issuing a seal is a different job — see
[oir-registration](../oir-registration/SKILL.md).
