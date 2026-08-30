---
name: build-manifest
description: Build and validate a nightly Ondura bulk manifest from pending.csv. Use when asked to build, generate, drop, or validate a manifest or consignment file.
argument-hint: [YYYY-MM-DD]
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/check_manifest.py *)
---

# Building a manifest

1. **Pick the date.** It is the Ondura Standard Time (UTC+3) date, not the
   local or UTC date. After 21:00 UTC that is tomorrow. If the user gave a
   date, use theirs and say which day it lands on.

2. **Check `pending.csv`.** Every row is `seal,title,disposition`.
   Dispositions are `LN` (lend), `RS` (reserve), `WD` (withdraw). Titles
   must be ASCII and 64 characters or fewer — fix them here, never in the
   manifest.

3. **Build:** `python3 consign.py --date <YYYY-MM-DD>`. It refuses to
   overwrite an existing manifest; that refusal is correct — a consignment
   is never rebuilt in place. If the day's file exists and is wrong,
   supersede it with the next day's manifest (`WD`, then re-add).

4. **Validate, always:**

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/check_manifest.py manifests/<YYYYMMDD>.man
   ```

   Every problem it prints is fatal — the host drops bad records without
   reporting anything, so a file that fails validation must not be dropped.

5. **Report** the path, the record count, and the validator's verdict. Do not
   describe the consignment as sent; dropping the file is a separate,
   manual step.

## When validation fails

- **`checksum is X, expected Y`** — the file was edited after it was built.
  Rebuild it from `pending.csv`; never patch the header to match.
- **`seal … has check character X, expected Y`** — the seal in `pending.csv`
  is wrong, not the manifest. Fix the source row and rebuild. See the
  `oir-codes` skill for this directory.
- **`line endings must be CRLF`** — something normalized the file. Rebuild.
