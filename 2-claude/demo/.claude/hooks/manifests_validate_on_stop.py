#!/usr/bin/env python3
"""Stop: don't let the turn end with an invalid manifest on disk.

Exit 2 blocks the stop and hands the message back to Claude, which then keeps
working instead of reporting success.

Two things keep it from being a nuisance:

* It only looks at manifests this working tree has actually changed — a
  committed, unmodified fixture is somebody else's business.
* Nothing stops a Stop hook from blocking forever, so it blocks at most once
  per session; the stamp file is the circuit breaker. A hook that can trap a
  session is a worse bug than the thing it was guarding against.
"""

import glob
import json
import os
import subprocess
import sys
import tempfile

CHECKER = os.path.join(
    "bulk", ".claude", "skills", "build-manifest", "scripts", "check_manifest.py")


def is_dirty(project: str, path: str) -> bool:
    """True unless git says the file is tracked and unchanged."""
    try:
        result = subprocess.run(
            ["git", "-C", project, "status", "--porcelain", "--", path],
            capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return True                   # no git: police everything
    if result.returncode != 0:
        return True
    return bool(result.stdout.strip())


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    project = os.environ.get("CLAUDE_PROJECT_DIR", event.get("cwd", os.getcwd()))
    checker = os.path.join(project, CHECKER)
    if not os.path.exists(checker):
        return 0

    stamp = os.path.join(
        tempfile.gettempdir(),
        "oir-stop-{}".format(event.get("session_id", "unknown")))

    failures = []
    for manifest in sorted(glob.glob(os.path.join(project, "bulk", "manifests", "*.man"))):
        if not is_dirty(project, manifest):
            continue
        result = subprocess.run(
            [sys.executable, checker, manifest],
            capture_output=True, text=True)
        if result.returncode != 0:
            failures.append("{}:\n{}".format(
                os.path.basename(manifest), result.stdout.strip()))

    if not failures:
        if os.path.exists(stamp):
            os.remove(stamp)          # clean slate once everything validates
        return 0

    if os.path.exists(stamp):
        return 0                      # already raised this session; don't trap it

    open(stamp, "w").close()
    sys.stderr.write(
        "A manifest on disk does not validate. Fix it before finishing "
        "(rebuild it — never patch the file):\n\n" + "\n\n".join(failures) + "\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
