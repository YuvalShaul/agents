---
name: oir-codes
description: Seal codes in their compact wire form, as written into bulk manifest files (HR1965M, not OIR-HR-1965-M). Use when building, reading, or debugging a .man manifest record, or when converting between API and file forms of a seal.
---

# Seal codes in manifest files

The batch interface uses a **compact** form of the seal code. The API form
never appears in a `.man` file, and the compact form must never be stored in
the catalogue.

```
API form   OIR-HR-1965-M     13 chars, what the registry issues and we store
File form  HR1965M            7 chars, what the manifest record carries
```

Conversion is textual: drop `OIR-` and the dashes. `consign.py:compact()`
does it; don't reimplement it inline.

## Rules

- The check character (last char) is preserved verbatim. It is the only
  integrity check the host performs, and a record whose check character is
  wrong is **dropped silently** — no error, no line in any log.
- Validate the check character *before* writing the file, not after. Once the
  file is dropped there is no feedback channel.
- Never store the compact form. It is a wire format: 7 characters is not
  enough to round-trip a seal issued to a different shelf, and the catalogue
  is the system of record.
- The compact form is fixed-width in the record (columns 7–13). It is never
  padded, because every compact code is exactly 7 characters.

For the API form — the format, the check-character formula, and how a seal is
stored in the catalogue — see the project-level `oir-codes` skill.
