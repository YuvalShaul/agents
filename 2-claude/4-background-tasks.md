# Lab: Background Tasks in Claude Code

**Time:** 30–40 minutes
**Prerequisites:** an Ubuntu VM with Claude Code installed, two terminals open:

- **Terminal A** — running `claude` (your Claude Code session)
- **Terminal B** — a plain shell, for observing the OS

## Intro

Claude Code can run shell commands as **background tasks**: the command keeps
running while you and Claude continue the conversation. This is how you keep a
dev server, a watch build, or a `tail -f` on logs alive while Claude works on
other things.

Two identity layers are involved, and they are not the same thing:

- The **task ID** — a short alphanumeric string assigned by Claude Code when
  the task starts. It exists only inside your Claude Code session and is what
  Claude's task tools (and the `/tasks` view) operate on.
- The **PID** — the process ID assigned by the Linux kernel. It exists in the
  OS process table and is what `ps`, `pgrep`, and `kill` operate on.

**Goal of this lab:** by starting, watching, and killing the same process from
both sides, understand exactly where the task-ID → process mapping lives and
what happens when the two layers disagree.

## Setup

In **Terminal B**, in any working directory (use the same directory where you
started `claude`), create a small "server" — a script that prints a timestamped
line every 2 seconds, forever:

```bash
cat > ticker.sh <<'EOF'
#!/usr/bin/env bash
while true; do
  echo "[$(date '+%H:%M:%S')] ticker alive"
  sleep 2
done
EOF
chmod +x ticker.sh
```

Sanity-check it, then Ctrl-C out:

```bash
./ticker.sh
```

## Exercise 1 — Start and identify

**Goal:** start one background task and record both of its identities — the task ID and the PID.

1. In **Terminal A**, ask Claude:

   > Run ./ticker.sh in the background.

2. Claude will report that the command is running in the background, along
   with a **task ID** (a short alphanumeric string — note that it is *not* a
   number) and the path of an **output file** it is writing to. Write both
   down.

3. In **Terminal B**, find the real process:

   ```bash
   pgrep -af ticker.sh
   ```

   You will likely see **two** matches: a wrapper shell (`/bin/bash -c
   source ... eval './ticker.sh' ...` — Claude Code wraps every command in a
   shell that restores your environment) and the script itself
   (`bash ./ticker.sh`). Record the script's PID.

4. Look at the ancestry:

   ```bash
   ps -o pid,ppid,stat,etime,cmd -p <script-pid>
   ps -o pid,ppid,cmd -p <the ppid you just saw>
   ```

   Walk up the parent chain: script → wrapper shell → the `claude` process
   itself.

**Expected result:** you hold two different identifiers for one running
program — a task ID that appears nowhere in `ps` output, and a PID that Claude
never mentioned. The process is a direct descendant of the `claude` process.

**Think about it:** the task ID doesn't exist in the OS, and the PID doesn't
exist in your conversation. Where does each one "live", and what is the only
piece of software that knows both?

## Exercise 2 — Observe output

**Goal:** see the mechanism Claude uses to read a background task's output.

1. In **Terminal A**, ask:

   > What has the ticker task printed so far?

   Claude will show you the timestamped lines produced so far.

2. In **Terminal B**, find the output file on disk. Claude already told you
   the path in Exercise 1; if you lost it, search for recently modified
   `.output` files:

   ```bash
   find /tmp/claude-$(id -u) -name '*.output' -mmin -10 2>/dev/null
   ```

   Note the path shape: a per-session directory containing a `tasks/`
   subdirectory, with one `<task-id>.output` file per task — the task ID is
   right there in the filename.

3. Watch it live:

   ```bash
   tail -f /path/to/<task-id>.output
   ```

   Leave it running for a few ticks, then Ctrl-C.

4. Back in **Terminal A**, ask Claude again what the task has printed, and
   compare with what `tail` showed you.

**Expected result:** the file grows by one line every 2 seconds, and its
content is exactly what Claude quotes to you.

**Think about it:** Claude is not attached to the process's terminal — there
isn't one. Stdout/stderr are redirected to this file, and Claude *reads the
file* when asked. What does that imply about output produced while Claude
isn't looking? Is anything lost?

## Exercise 3 — Stop from inside

**Goal:** stop the task through Claude and confirm the OS process actually dies.

1. In **Terminal A**, ask:

   > Stop the ticker task.

   Claude uses its `TaskStop` tool, giving it the **task ID** — no PID
   involved from Claude's point of view.

2. In **Terminal B**, verify:

   ```bash
   pgrep -af ticker.sh || echo "gone"
   ```

3. In **Terminal A**, type `/tasks` and check the task list.

4. The output file is still on disk — confirm with `ls` on the `tasks/`
   directory from Exercise 2.

**Expected result:** the wrapper and script processes are both gone from the
process table; the task no longer shows as a running task in `/tasks`; the
`.output` file remains as a record.

**Think about it:** Claude named the task by its ID, yet the right PID got
killed. What had to translate between the two, and at what moment was that
translation recorded?

## Exercise 4 — Kill from outside (the key exercise)

**Goal:** kill the process behind Claude's back and see how — and how accurately — the task layer finds out.

1. In **Terminal A**, ask:

   > Run ./ticker.sh in the background again.

   Note the task ID — it's a **new** one. Task IDs name a *run*, not a
   program.

2. In **Terminal B**, find the script's PID again and kill it directly:

   ```bash
   pgrep -af ticker.sh        # pick the './ticker.sh' line, not the wrapper
   kill <pid>
   pgrep -f ticker.sh || echo "gone"
   ```

3. In **Terminal A**, ask:

   > What's the status of the ticker task?

   Watch what Claude reports. Then check `/tasks` yourself, and in
   **Terminal B** look at the end of the task's output file:

   ```bash
   tail -3 /path/to/<new-task-id>.output
   ```

**Expected result:** Claude Code *does* notice — the task is no longer
running. Because Claude Code is the parent supervising the process, the death
is delivered to it as a normal child exit: the task ends in a **failed**
state with **exit code 143** (128 + 15, i.e. terminated by SIGTERM), and the
output file ends with a `Terminated` line and the exit code. Once the task
has ended, Claude may no longer be able to query that task ID at all — the
live task entry is cleaned up; only the output file remains.

**Think about it:** what drifted apart here is not "alive vs. dead" — the
supervisor caught the exit — it's *meaning*. From the OS side you performed a
deliberate administrative kill; from the task side it is indistinguishable
from a crash ("failed, exit 143"). What does that tell you about where the
task-ID → PID mapping lives (kernel? disk? the Claude Code process's memory?),
and about which direction information flows between the two layers?

## Exercise 5 — Timeout auto-backgrounding

**Goal:** watch a foreground command get promoted to a background task when it outlives its timeout.

Foreground commands in Claude Code have a default timeout of 2 minutes. A
command that hits the timeout isn't simply killed — it is **moved to the
background** and becomes a task like any other. (Exception: commands starting
with `sleep` are never auto-backgrounded — they are just killed with a timeout
error. So we use the ticker, and to keep the lab short we ask for an
explicitly small timeout.)

1. In **Terminal A**, ask:

   > Run ./ticker.sh in the foreground with a 15-second timeout. Don't background it yourself.

   (If Claude runs it without setting a timeout, that's fine too — you'll
   just wait the full 2 minutes for the same effect.)

2. Watch the result: after the timeout expires, Claude receives a message
   saying the command did not complete within its timeout and **was moved to
   the background**, with a new task ID and output file path. Record them.

3. In **Terminal B**, confirm the process is still alive and the output file
   is still growing:

   ```bash
   pgrep -af ticker.sh
   tail -f /path/to/<task-id>.output   # Ctrl-C when satisfied
   ```

4. Contrast with the `sleep` exemption — in **Terminal A**, ask:

   > Run `sleep 300` with a 15-second timeout.

   This one fails with a plain timeout error (exit 143). No task ID, no
   backgrounding.

5. Clean up — in **Terminal A**:

   > Stop the ticker task.

   And in **Terminal B**, verify nothing is left: `pgrep -f ticker.sh`.

**Expected result:** the timed-out ticker survives its timeout as a real
background task, identical in every observable way to the tasks you started
deliberately in Exercises 1–4; the timed-out `sleep` just dies.

**Think about it:** why would the design promote a slow command to a task
instead of killing it — and why is `sleep` the exception?

## Wrap-up

| | **Task ID** | **PID** |
|---|---|---|
| **Assigned by** | Claude Code, when the task starts | The Linux kernel, at `fork` |
| **Lives in** | The Claude Code process's memory (plus the filename of the `.output` file on disk) | The kernel's process table |
| **Operated on by** | Claude's task tools (`TaskOutput`, `TaskStop`), the `/tasks` view | `ps`, `pgrep`, `kill`, `top`, signals |
| **Names** | One *run* of a command (a new run gets a new ID) | One process (and is recycled by the OS over time) |
| **When the process dies** | Task ends (completed/failed with an exit code); the live entry is cleaned up, the `.output` file remains | PID disappears from the process table |
| **When the session ends** | Meaningless — nothing outside the session can resolve it | Unaffected as a concept; the session's child processes are torn down with it |

### Review questions

1. In Exercise 4 you killed the process with `kill <pid>`, and Claude Code
   recorded the task as *failed with exit code 143*. Explain the mechanism by
   which Claude Code learned about the death, and why it cannot tell your
   deliberate kill apart from a crash.

2. A teammate says: "I'll write down the task ID so we can check on the
   server tomorrow from a fresh session." What's wrong with this plan, and
   what *would* survive until tomorrow?

3. Claude answers "what has the task printed?" by reading a file, not by
   being attached to a terminal. Name one practical advantage and one
   limitation of that design (hint: think about output produced while Claude
   is busy, and about programs that behave differently when stdout is not a
   TTY).
