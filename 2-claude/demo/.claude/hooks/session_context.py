#!/usr/bin/env python3
"""SessionStart: tell Claude the state of the world before it is asked.

Whether the registry is reachable is a fact about *right now*, so it cannot
live in CLAUDE.md. Injecting it at session start means Claude never opens by
guessing, or by spending a tool call to find out.
"""

import glob
import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("OIR_URL", "http://127.0.0.1:8787")


def registry_line() -> str:
    try:
        with urllib.request.urlopen(BASE + "/v1/applications", timeout=1) as response:
            applications = json.load(response).get("applications", [])
    except (urllib.error.URLError, OSError, ValueError):
        return ("Ondura registry: UNREACHABLE at {}. Do not invent seals or "
                "application states; say it is down and stop.".format(BASE))

    if not applications:
        return "Ondura registry: up at {}, no open applications.".format(BASE)

    states = {}
    for application in applications:
        states[application["state"]] = states.get(application["state"], 0) + 1
    summary = ", ".join("{} {}".format(count, state) for state, count in sorted(states.items()))
    pending = states.get("pending", 0)
    line = "Ondura registry: up at {}, {} open application(s) — {}.".format(
        BASE, len(applications), summary)
    if pending == 1:
        line += " One is pending its oath, so ticking the registry clock would lapse it."
    elif pending:
        line += (" {} are pending their oath, so ticking the registry clock "
                 "would lapse them.".format(pending))
    return line


def main() -> int:
    project = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    manifests = sorted(glob.glob(os.path.join(project, "bulk", "manifests", "*.man")))
    context = [
        registry_line(),
        "Manifests on disk: {}.".format(
            ", ".join(os.path.basename(p) for p in manifests) or "none"),
    ]
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n".join(context),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
