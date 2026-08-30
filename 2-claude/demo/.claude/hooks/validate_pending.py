#!/usr/bin/env python3
"""PostToolUse: check bulk/pending.csv after anything writes to it.

Does not block — the edit already happened. It hands Claude the problems it
just introduced, so they are fixed in the same turn instead of surfacing as a
silently dropped record after the file is dropped at Ondura.
"""

import json
import os
import sys

CHECK_ALPHABET = "BCDFGHJKLMNPQRSTVWXZ"
DISPOSITIONS = ("LN", "RS", "WD")
TITLE_WIDTH = 64


def check_char(shelf: str, year: str) -> str:
    total = sum(int(d) for d in year) + sum(ord(c) - 64 for c in shelf)
    return CHECK_ALPHABET[(total * 7) % 20]


def problems_in(path: str):
    found = []
    with open(path, "rb") as handle:
        raw = handle.read()
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        return ["non-ASCII byte at offset {} — the host drops those records "
                "without reporting anything".format(error.start)]

    for number, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        fields = [field.strip() for field in line.split(",")]
        if len(fields) != 3:
            found.append("line {}: expected seal,title,disposition".format(number))
            continue
        seal, title, disposition = fields
        parts = seal.split("-")
        if len(parts) != 4 or parts[0] != "OIR":
            found.append("line {}: {!r} is not a seal code".format(number, seal))
        else:
            shelf, year, check = parts[1], parts[2], parts[3]
            expected = check_char(shelf, year)
            if check != expected:
                found.append(
                    "line {}: seal {} has check character {}, expected {} — "
                    "the record would be dropped silently".format(
                        number, seal, check, expected))
        if len(title) > TITLE_WIDTH:
            found.append("line {}: title is {} chars, limit is {}".format(
                number, len(title), TITLE_WIDTH))
        if disposition not in DISPOSITIONS:
            found.append("line {}: disposition {!r} not in {}".format(
                number, disposition, DISPOSITIONS))
    return found


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    path = (event.get("tool_input") or {}).get("file_path", "")
    if not path.endswith("pending.csv") or not os.path.exists(path):
        return 0

    found = problems_in(path)
    if not found:
        return 0

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "pending.csv problems introduced by this edit:\n- "
                                 + "\n- ".join(found),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
