# Lab: Many Hands, One Repo — Parallel Writes with Worktree Isolation

**Time:** 30–40 minutes
**Prerequisites:** [Lab 5](./1-parallel-agents.md) completed (you have the
three reports — ideally saved as `demo/reports.md`), and two terminals open:

- **Terminal A** — running `claude`, started inside `2-claude/demo/`
- **Terminal B** — a plain shell in the same directory, for observing git

## 1. The scenario

Lab 5 left you with three reports on the Books API: a code review, a
test-coverage audit, and a `CLAUDE.md` accuracy check. The meeting is
tomorrow and two of those reports translate directly into work:

1. **Add the missing tests** the coverage audit identified to
   `tests/test_main.py`, and make `pytest` pass.
2. **Fix `CLAUDE.md`** so it matches what the code actually does.

Both are small, both are clearly specified by a report you already have, and
neither depends on the other. Exactly the shape that Lab 5 taught you to fan
out — except this time the agents have to **edit files**, and they'll be
doing it at the same time, in the same repository.

## 2. Why is it good

Everything from Lab 5 still applies — less wall-clock time, a clean context
per job, only diffs coming back to your conversation. Two more benefits
appear once agents write code:

- **Reviewable units.** Each agent produces one branch with one coherent
  change. You review "the tests branch" and "the docs branch" separately,
  instead of untangling one mixed diff.
- **Cheap to throw away.** If one agent's result is bad, you delete its
  branch. The other agent's work is untouched. In a single shared checkout,
  undoing one of two interleaved edits is much harder.

## 3. Why is it possible *in this case*

Lab 5's checklist had a condition these jobs fail:

| Condition | Here? |
|---|---|
| Independent | ✅ Tests don't need the doc fix, and vice versa |
| Self-contained prompt | ✅ Each report *is* the spec |
| Small result | ✅ A diff and a one-line summary each |
| **Read-only** | ❌ Both agents write to disk |

Two agents writing into one working directory is a race: agent 1 runs
`pytest` while agent 2 has `CLAUDE.md` half-written; both run `git add`;
one's edit tool reads a file the other just changed. Even when they touch
*different* files — as here — the shared checkout and shared git index are
the problem, not the files.

What makes it possible anyway is **git worktrees**: one repository, several
working directories, each on its own branch. Claude Code can start a subagent
in a fresh worktree (`isolation: "worktree"` on the `Agent` tool). Each agent
then sees a complete, private checkout; nothing it does is visible to the
other until you merge.

So the rule extends: **independent + self-contained + small result + (read-
only OR isolated)** → fan out.

## 4. How to technically run it

The `demo/` directory lives inside the course repository, so git worktrees
created for it will belong to that repo — that's fine, but watch the branch
list grow.

### Exercise 1 — Fan out two writing agents

**Goal:** two agents edit the repo concurrently, each in its own worktree, with no interference.

1. In **Terminal B**, record the starting state:

   ```bash
   git status --short
   git worktree list
   git branch --list | wc -l
   ```

2. In **Terminal A**, paste (adjust if your reports are somewhere other
   than `reports.md`):

   > Launch two subagents **in parallel, each in its own git worktree**:
   > 1. Using the test-coverage section of `reports.md`, add the missing
   >    tests to `tests/test_main.py`. Run `pytest` and make sure it passes.
   > 2. Using the documentation section of `reports.md`, fix `CLAUDE.md` so
   >    it accurately describes the code. Don't touch any other file.
   >
   > Each agent should commit its work on its branch. Report the branch and
   > worktree path each one used, and a summary of its diff.

3. Confirm in the transcript that both `Agent` calls were issued in the same
   turn and carry worktree isolation.

**Expected result:** two agents run at once; when both finish you get two
branch names and two diff summaries. Your main checkout is untouched
(`git status --short` in Terminal B is still clean).

**Think about it:** the agents never saw each other's work. What would
have happened if agent 1's tests depended on a fact agent 2 was changing in
`CLAUDE.md`? Which of Lab 5's conditions would that violate?

### Exercise 2 — Inspect and merge

**Goal:** treat each agent's output as a normal branch: review it, then integrate it.

1. In **Terminal B**, list the branches and look at each diff:

   ```bash
   git worktree list
   git log --oneline main..<tests-branch>
   git diff main..<tests-branch>
   git diff main..<docs-branch>
   ```

2. Run the new tests yourself, from inside the tests agent's worktree:

   ```bash
   cd <tests-worktree-path> && pytest && cd -
   ```

3. Merge both into your working branch (one at a time), then clean up:

   ```bash
   git merge <tests-branch>
   git merge <docs-branch>
   git worktree remove <tests-worktree-path>
   git worktree remove <docs-worktree-path>
   git branch -d <tests-branch> <docs-branch>
   ```

   You can also ask Claude in **Terminal A** to do the merge and cleanup —
   but do the first one by hand so you see there's nothing magic: it's
   ordinary git.

**Expected result:** both changes land on your branch with no conflicts,
`pytest` passes in the main checkout, `git worktree list` is back to one
entry.

**Think about it:** why did the two merges not conflict? Construct a variant
of the task where they *would* (hint: both agents editing `CLAUDE.md`'s
"Commands" section). What should you do in that case — sequence, or
merge-and-resolve?

### Exercise 3 — See the race you avoided (optional)

**Goal:** understand what isolation protects you from, by removing it.

1. In **Terminal A**, ask for the same two jobs **without** worktrees:

   > Redo the two jobs in parallel, but in the current directory — no
   > worktree isolation. Do not commit.

2. In **Terminal B**, while they run, poll:

   ```bash
   watch -n1 'git status --short; echo; git diff --stat'
   ```

3. When done, look at `git status`. Then `git checkout -- .` to discard.

**Expected result:** usually it "works" — the files are different, so the
edits land side by side. But you now have one mixed working tree, no
per-job branch, and whether the tests agent's `pytest` run saw the docs
agent's half-written `CLAUDE.md` is a matter of timing. Nothing enforced
the separation; you got lucky.

**Think about it:** "it worked when I tried it" — why is that a weak
argument for skipping isolation?

## 5. How to monitor

Everything from Lab 5 (progress tree, `/tasks`, `Ctrl+O`, `agent-*.jsonl`
transcripts) still applies. Writing agents add git as a monitoring surface:

- **`git worktree list`** — one line per isolated agent while it's alive.
  Worktrees that end up unchanged are removed automatically; changed ones
  stay for you to inspect. Run this in **Terminal B** during Exercise 1 and
  watch entries appear.
- **`git branch --list`** — one branch per agent. Orphaned agent branches
  accumulate if you skip cleanup; this is where to look when the list gets
  noisy.
- **Inside a worktree:** `cd` into an agent's worktree path and run
  `git status` / `git log` / `pytest` while the agent is still working. You
  are reading its private checkout; you can't disturb your own.
- **Disk:** `du -sh <worktree-path>` — each worktree is a full checkout of
  tracked files (sharing the `.git` object store). Isolation costs disk and
  setup time; that's why Lab 5's read-only agents don't use it.
- **Processes:** as in Lab 5, still one `claude` process. But agents'
  `pytest` runs appear briefly as children — `pgrep -af pytest` during
  Exercise 1 may catch one, running with a *worktree path* as its cwd.

## Wrap-up

| | **Shared checkout** | **Worktree per agent** |
|---|---|---|
| **Working directory** | One, shared | One per agent, private |
| **Git index** | Shared — concurrent `git add` races | Separate |
| **Result arrives as** | Dirty files in your tree | A branch you can diff, test, merge, or drop |
| **Undo one agent's work** | Manual, by file | `git branch -D` |
| **Cost** | None | Disk + a few hundred ms per agent |
| **Cleanup** | None needed | `git worktree remove`, `git branch -d` |
| **Use when** | One writer at a time | Two or more writers at once |

### Review questions

1. In Exercise 1 the two agents edited different files. Explain why a
   shared checkout was still a race, naming at least two shared resources
   besides the files themselves.

2. Isolation removes conflicts *during* the work, but not at merge time.
   Describe a two-agent task where both worktree branches merge cleanly
   and the result is nonetheless broken (hint: tests written against an
   API the other agent renamed).

3. A colleague proposes running five worktree agents to refactor five
   modules at once, "since they're separate files." What questions would
   you ask before agreeing, and which of the checklist conditions are they
   most likely to be wrong about?
