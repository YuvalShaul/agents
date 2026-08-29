# Lab: Divide and Conquer — Parallel Subagents in Claude Code

**Time:** 30–40 minutes
**Prerequisites:** an Ubuntu VM with Claude Code installed, this repo cloned,
and two terminals open:

- **Terminal A** — running `claude`, started inside `2-claude/demo/`
- **Terminal B** — a plain shell, for observing from the outside

## 1. The scenario

You've just inherited the Books API in [`demo/`](./demo) — one FastAPI file,
an in-memory dict, a handful of tests — and you've been asked to get it ready
for a review meeting tomorrow. Three things need to happen before then:

1. **A code review** of `main.py` for correctness bugs and API-design issues
   (status codes, validation, edge cases like updating a missing book).
2. **A test-coverage audit** — which endpoints and error paths do
   `tests/test_main.py` actually exercise, and which are missing?
3. **A documentation check** — does `CLAUDE.md` still describe the code
   accurately, and what is a newcomer *not* told?

Each job means reading a few files, thinking, and writing a short report.
None of them needs the others' answers. Doing them one after the other in a
single conversation works, but it's slow, and by the third job Claude's
context is full of details from the first two that have nothing to do with
the task at hand.

Instead, you'll hand each job to its own **subagent** and run all three at
once.

## 2. Why is it good

- **Wall-clock time.** Three independent jobs run concurrently finish in
  roughly the time of the slowest one, not the sum of all three.
- **Clean context per job.** Each subagent starts with a fresh context
  window containing only its own instructions. The reviewer isn't distracted
  by test-coverage details, and vice versa. Focused context tends to mean
  better answers.
- **Your context stays small.** All the file reading, grepping, and
  intermediate reasoning happens inside the subagents. Only the *final
  report* comes back to your main conversation — a few paragraphs instead of
  hundreds of lines of tool output. Your session can go on for longer before
  it needs to compact.
- **Independence as a review property.** Three agents that can't see each
  other's work give you three genuinely independent opinions. If two of them
  flag the same line, that's signal.

## 3. Why is it possible *in this case*

Parallelism is only safe when the jobs don't step on each other. Check the
scenario against these conditions:

| Condition | Here? |
|---|---|
| The jobs are **independent** — none needs another's output as input | ✅ Review, coverage audit, and doc check each stand alone |
| The jobs are **read-only** (or write to disjoint places) | ✅ All three only read `main.py`, `tests/`, `CLAUDE.md` and return text |
| Each job can be **described in one self-contained prompt** — the subagent has no access to your conversation history | ✅ "Review `main.py` for X and report Y" is complete on its own |
| The result is **small enough to summarize** — you want the conclusion, not every file the agent looked at | ✅ A short report per job |

When one of these fails, parallelism gets harder, not impossible: jobs that
*write* files concurrently need isolation (each agent in its own git
worktree — that's [Lab 6](./6-parallel-writes.md)), and jobs that depend on
each other need to be sequenced (do A, *then* fan out B and C).

Notice what makes the demo project a good fit: it's tiny and it's fully
described by three files. A subagent that has never seen your conversation
can still do a complete job from a two-sentence prompt.

## 4. How to technically run it

Claude Code has an **`Agent` tool**. When Claude calls it, a new, separate
Claude conversation is created with the prompt Claude wrote, runs its own
tool-use loop (reading files, running commands) until it's done, and returns
its final message as the tool result. Several `Agent` calls issued in the
same turn run **concurrently**.

You don't call the tool yourself — you ask for parallel work and Claude
decides to use it. Being explicit helps.

### Exercise 1 — Fan out three subagents

**Goal:** launch three independent subagents in one turn and get three reports back.

1. In **Terminal B**, `cd` to `2-claude/demo` and skim the three inputs so
   you can judge the reports later:

   ```bash
   cat main.py
   cat tests/test_main.py
   cat CLAUDE.md
   ```

2. In **Terminal A** (Claude Code started in `2-claude/demo/`), paste:

   > Launch three subagents **in parallel**, in a single turn, each read-only:
   > 1. Review `main.py` for correctness bugs and API-design issues (status
   >    codes, validation, missing-resource handling). Report findings as
   >    `file:line — issue — suggested fix`.
   > 2. Audit `tests/test_main.py`: list every endpoint and error path in
   >    `main.py` and mark which ones have a test. Report the gaps.
   > 3. Check whether `CLAUDE.md` accurately describes the current code, and
   >    list anything a newcomer would need that it doesn't say.
   >
   > Don't modify any files. When all three finish, give me one combined
   > summary with a section per agent.

3. Watch the transcript. You should see **three `Agent` tool calls in the
   same assistant turn** — that's what makes them concurrent. If Claude runs
   them one at a time, say so and ask it to issue all three in one turn.

4. Wait for the combined summary.

**Expected result:** three tool calls start together, each finishes on its
own schedule, and you receive one summary you can read in a minute — without
ever seeing the file contents the agents read.

**Think about it:** the subagents never saw your conversation. Everything
they knew came from the prompt Claude wrote for them. Scroll up and read those
prompts (see *How to monitor*, below) — did Claude include enough context?
What would you add?

### Exercise 2 — Continue a subagent instead of starting over

**Goal:** see that a finished subagent keeps its context and can be asked follow-ups.

1. Pick one finding from the review agent's section that you'd like more
   detail on. In **Terminal A**, ask:

   > Ask the review subagent (the same one, don't start a new one) to
   > explain finding #1 in more detail and show the exact code path.

2. Claude uses `SendMessage` with the agent's name/ID rather than a fresh
   `Agent` call. The follow-up answer should reference specifics without
   the agent re-reading everything.

**Expected result:** the continued agent answers quickly and consistently
with its earlier report, because it still has the files in context.

> **Keep the three reports** — Lab 6 turns two of them into code changes.
> The easiest way: ask Claude to save the combined summary to
> `reports.md` in `demo/` (it's fine to commit or discard it later).

**Think about it:** when is continuing an agent better than spawning a new
one — and when is a fresh one better (hint: stale context, or a job that
should be independent of the first)?

## 5. How to monitor

Subagents are easy to lose track of precisely because their work is hidden
from your context. Four places to look:

**Inside the session**

- **The progress tree.** While agents run, Claude Code shows a live block
  under the tool call: each agent's label, elapsed time, and its current
  tool call. This is your first stop.
- **`/tasks`.** Lists everything running in the background for this
  session — subagents alongside background shell tasks from Lab 4. Use it
  to see what's still alive and to stop a runaway agent.
- **Verbose transcript (`Ctrl+O`).** Toggles the full transcript, including
  the *prompt Claude wrote for each agent* and the raw result that came back.
  Read the prompts — they tell you whether Claude scoped the jobs well.
- **Task notifications.** When an agent finishes, a notification lands in
  the conversation and Claude picks up the result. If you asked a question
  before that, Claude should tell you the agent is still running — it cannot
  (and must not) guess the result.

**From outside (Terminal B)**

- **Transcripts on disk.** Every subagent's conversation is written to a
  JSONL file under your project's transcript directory. Find the fresh ones:

  ```bash
  find ~/.claude/projects -name 'agent-*.jsonl' -mmin -15 2>/dev/null
  ```

  `tail -f` one while its agent runs and you'll see every tool call the
  agent makes, in real time, without it touching your session's context.
  (The path layout may vary by version — the `-mmin` search is the robust
  way to find them.)

- **Processes.** Try `pgrep -af claude` in Terminal B while three agents
  are running. You'll find **one** `claude` process. Subagents are not OS
  processes — they are additional API conversations driven by the same
  process. Only the *commands* they run (a `pytest`, a `grep`) show up as
  children, briefly.

## Wrap-up

| | **Your main conversation** | **A subagent** |
|---|---|---|
| **Starts with** | Your whole history | Only the prompt Claude wrote for it |
| **Sees** | Subagents' final reports | Its own tool output; nothing of yours |
| **Runs as** | The `claude` process | Another conversation inside the same process |
| **Costs you** | Context space for each report | Nothing in your context beyond the report |
| **Listed in** | — | Progress tree, `/tasks`, `agent-*.jsonl` on disk |
| **Continued by** | You typing | `SendMessage` to its ID (context retained) |
| **Safe to write files** | Yes | Only alone, or in its own worktree (Lab 6) |

The recipe: **independent + read-only + self-contained prompt + small
result** → fan out. Anything else → sequence it, or isolate it (next lab).

### Review questions

1. In Exercise 1, three agents ran concurrently but `pgrep` showed one
   `claude` process. Where does the parallelism actually happen, and what
   does that imply about what limits how many agents you can run at once?

2. You want to refactor `main.py` into `schemas.py`, `routes.py`, and
   `store.py`, *and* write tests for the result. A colleague suggests two
   parallel agents: one refactors, one writes tests. Which condition from
   section 3 does this violate, and how would you restructure the work?

3. Compaction: after a long session, Claude Code summarizes your history.
   Explain why offloading file reads into subagents delays the point at
   which that becomes necessary — and name one thing that is *lost* when
   you delegate (hint: what can you no longer scroll up and check without
   opening a transcript file?).
