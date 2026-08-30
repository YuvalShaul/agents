#!/usr/bin/env python3
"""PreToolUse: refuse any in-place change to a written manifest.

`bulk/CLAUDE.md` and `bulk/.claude/rules/manifest-files.md` both say a `.man`
file is never edited once written. Those are context: Claude usually follows
them. This hook is enforcement: the tool call does not happen.

Covers the file tools *and* the shell, because a rule that only guards
Edit/Write is one `sed -i` away from being useless.
"""

import json
import re
import sys

MANIFEST = re.compile(r"[\w./-]*manifests/[\w.-]+\.man")
MUTATORS = (">", ">>", "sed -i", "tee ", "mv ", "cp ", "rm ", "truncate", "dd ")

REASON = (
    "Blocked by hook: manifests are immutable once written "
    "(bulk/CLAUDE.md). Do not edit {target} in place — not to fix a title, "
    "not to fix a checksum. Correct the source row in bulk/pending.csv and "
    "supersede the consignment: withdraw with WD, then build the next day's "
    "manifest with consign.py."
)


def target_path(event: dict) -> str:
    tool = event.get("tool_name", "")
    data = event.get("tool_input", {}) or {}

    if tool in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
        path = data.get("file_path") or data.get("notebook_path") or ""
        return path if MANIFEST.search(path) else ""

    if tool == "Bash":
        command = data.get("command", "")
        match = MANIFEST.search(command)
        if match and any(token in command for token in MUTATORS):
            return match.group(0)
    return ""


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0                      # malformed input: stay out of the way

    target = target_path(event)
    if not target:
        return 0                      # no decision; normal permission flow

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": REASON.format(target=target),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
