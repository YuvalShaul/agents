---
paths:
  - "**/manifests/*.man"
  - "**/bulk/consign.py"
  - "**/bulk/pending.csv"
---

# Working with manifest files

- Never edit a `.man` file in place — not to fix a title, not to fix a
  checksum, not to remove a record. Rebuild it, or supersede it with a new
  consignment.
- Never hand-edit the header. The count and the checksum are derived from the
  records; if they disagree with the body, the body is right and the file
  must be rebuilt with `consign.py`.
- Records are space-padded and left-aligned; only the sequence number is
  zero-padded. Trailing spaces are significant — do not strip them.
- Line endings are CRLF, and the file ends with exactly one CRLF. An editor
  that "helpfully" normalizes line endings will silently break the drop.
- ASCII only. A title with a curly quote or an accented character makes the
  host drop that record without reporting anything. Transliterate at the
  source, in `pending.csv`, never in the manifest.
- Always run `check_manifest.py` on a file before treating it as done.
