# Lab: Named Subagents — Agents You Define Once and Reuse

**Time:** 40–50 minutes
**Prerequisites:** [Lab 5](./1-parallel-agents.md) and [Lab 6](./2-parallel-writes.md)
completed, and two terminals:

- **Terminal A** — running `claude`, started inside `2-claude/demo/`
- **Terminal B** — a plain shell in the same directory

## 1. The scenario

In Labs 5 and 6 every subagent was **ad hoc**: you described three jobs,
Claude wrote three prompts, three agents ran. It worked — and everything
about those agents evaporated when they finished. The next session you write
the prompts again, slightly differently, and get slightly different reviews.

Worse, the safety was in the prompt. You *asked* the review agents not to
modify files. Nothing stopped them. In Lab 6 you *asked* for worktree
isolation; if you forget next time, two writers land in one checkout.

A **defined subagent** is that same worker written down: a markdown file in
`.claude/agents/` with a system prompt and a frontmatter block that decides
what it can do. Committed to the repo, reviewed like code, identical for
everyone on the team.

The demo has two, and they are deliberately different shapes:

```
demo/.claude/agents/
├── api-reviewer.md     read-only by construction   (tools: Read, Grep, Glob)
└── test-writer.md      writes, always isolated     (isolation: worktree)
```

Read them in **Terminal B** before you start — they are short:

```bash
cat .claude/agents/*.md
```

## 2. What the file says

```markdown
---
name: api-reviewer
description: Reviews the Books API for correctness bugs and API-design
  problems … Read-only. Use when asked to review, audit, or critique main.py.
tools: Read, Grep, Glob
color: blue
---

You review this project's HTTP API. You cannot change files, and that is
deliberate: your job is to say what is wrong, not to fix it.
…
```

Three parts, and each one replaces something you used to type:

| Part | Replaces |
|---|---|
| The **body** | The prompt you wrote by hand each time; it becomes the agent's *system prompt* |
| `description` | Your decision to delegate — Claude reads it and picks the agent itself |
| `tools` | Your hope that the agent behaves; an agent without `Write` cannot write |

Only `name` and `description` are required. The fields worth knowing now:

| Field | Effect |
|---|---|
| `tools` | Allowlist. Omit it and the agent inherits everything. Accepts `Read, Bash`, and MCP patterns like `mcp__oir` |
| `disallowedTools` | Denylist, applied first — the way to say "everything except `Write`" |
| `model` | `haiku`, `sonnet`, `opus`, or `inherit` (the default). Cheap models for mechanical work |
| `isolation: worktree` | Runs in its own temporary git worktree — Lab 6's discipline, made a property of the agent |
| `skills` | Preloads a skill's **full content** at startup (Lab 8) |
| `mcpServers` | Which MCP servers the agent can reach (Lab 10) |
| `memory` | A persistent notes directory for this agent across sessions |
| `maxTurns`, `effort`, `permissionMode`, `hooks`, `color` | Budget, effort, permission handling, its own hooks, display colour |

**Where they live**, in precedence order: `.claude/agents/` in the project
(committed, walked up from your working directory), then `~/.claude/agents/`
(yours, everywhere), then plugins. Edits to an existing agents directory are
picked up live; creating the directory for the first time needs a restart.

## 3. What a subagent starts with

This is the part people get wrong. A subagent is **not** a copy of your
session. It starts with:

- its own **system prompt** — the file's body, not Claude Code's default one;
- the **task message** Claude wrote when delegating;
- the **`CLAUDE.md` hierarchy**, exactly as your session loaded it;
- **git status**, and any **skills** named in `skills:`.

It does **not** get your conversation history, your output style, or the main
conversation's auto memory. The built-in `Explore` and `Plan` agents skip even
`CLAUDE.md` and git status, which is why they are fast and why their results
come back to *you* to interpret.

So a defined agent must be self-contained. If its instructions assume
something you said three messages ago, it will not know it.

## 4. Exercises

### Exercise 1 — Delegation you didn't ask for

**Goal:** see Claude pick an agent from its description.

1. In **Terminal A**, start `claude` in `demo/` and ask, naming no agent:

   > Review the Books API for bugs and design problems.

2. Watch the tool call. Claude should delegate to `api-reviewer` — its
   `description` matches — rather than reading the files itself. The
   findings come back as a report.

3. Now be explicit, which is the reliable form:

   > @agent-api-reviewer check whether CLAUDE.md still matches the code

   Typing `@` gives you a picker. This *guarantees* the delegation instead of
   leaving it to Claude's judgment.

4. Compare with Lab 5: there you wrote the review instructions yourself, in
   the prompt. Here the instructions live in the file, and your prompt is one
   line.

**Expected result:** the same class of review as Lab 5, from a one-line
request, with wording that doesn't drift between sessions.

**Think about it:** the `description` does two jobs — it tells Claude when to
delegate, and it is the only thing Claude knows about the agent beforehand.
What would you add to it to stop this agent being used for a *docs* review?

### Exercise 2 — The tool list is the safety, not the prompt

**Goal:** watch `tools:` do what a polite instruction cannot.

1. In **Terminal A**, ask the reviewer to cross the line:

   > @agent-api-reviewer fix the first bug you found in main.py

2. It cannot. `tools: Read, Grep, Glob` means `Edit` and `Write` are not in
   its tool set at all — there is nothing to refuse, because there is nothing
   to call. Read what it says back.

3. Contrast with an ad-hoc agent, which inherits everything:

   > Launch a general-purpose subagent to fix that same bug.

   Confirm in **Terminal B** that this one *did* change the file:

   ```bash
   git diff --stat main.py
   git checkout main.py
   ```

**Expected result:** two agents, the same instruction, two outcomes — decided
by a line of frontmatter rather than by how firmly the prompt was worded.

**Think about it:** Lab 9's hooks make the same kind of guarantee for a
different scope. Where does `tools:` stop being enough — what can an agent
with `Bash` still do to your files?

### Exercise 3 — Isolation as a property of the agent

**Goal:** see `isolation: worktree` remove the step you had to remember in Lab 6.

1. In **Terminal B**, note the starting state:

   ```bash
   git worktree list
   git status --short
   ```

2. In **Terminal A**, delegate work that writes — and say nothing about
   worktrees:

   > @agent-test-writer add tests for the 404 paths on GET, PUT and DELETE.

3. While it runs, in **Terminal B**:

   ```bash
   git worktree list        # its private checkout appears
   ```

4. When it finishes, review its branch the way Lab 6 taught, then merge or
   discard:

   ```bash
   git log --oneline main..<its-branch>
   git diff main..<its-branch>
   git merge <its-branch>          # or: git branch -D <its-branch>
   git worktree remove <path>      # if it is still listed
   pytest
   ```

**Expected result:** the isolation happened because the agent is defined that
way, not because you remembered to ask.

**Think about it:** in Lab 6 you *asked* for worktrees per invocation. Which
mistakes does moving that into the file prevent, and what does it cost you on
the occasions when you'd rather the agent edited your checkout directly?

### Exercise 4 — Two named agents, one turn

**Goal:** combine Lab 5's fan-out with defined types.

1. In **Terminal A**, in one message:

   > In parallel: have api-reviewer review main.py, and have test-writer add tests for whatever the current test file doesn't cover. Give me both results when they're done.

2. Watch both agents start in the same turn — one read-only in your
   checkout, one writing in a worktree. That combination is safe *by
   construction* now: the reviewer cannot write, and the writer cannot see
   or disturb the reviewer's files.

3. Check `/tasks` while they run, and `git worktree list` in **Terminal B**.

**Expected result:** the Lab 5 fan-out, with the safety argument reduced to
reading two frontmatter blocks.

**Think about it:** in Lab 5 you had to reason about whether parallel jobs
were safe every time you fanned out. What does that reasoning become when
agents are defined, and what's the new failure mode (hint: what if someone
edits `test-writer.md` and drops `isolation`)?

### Exercise 5 — Write one

**Goal:** define an agent for a job this project actually has.

Write `demo/.claude/agents/manifest-auditor.md` — a read-only auditor for the
`bulk/` component from Lab 8. Paste this **flush against the left margin**:

```bash
cat > .claude/agents/manifest-auditor.md <<'EOF'
---
name: manifest-auditor
description: Audits bulk/manifests/*.man files and reports which ones fail validation and why. Read-only; never rebuilds or edits a manifest. Use when asked to check, audit or validate manifests.
tools: Read, Grep, Glob, Bash
model: haiku
color: orange
---

Audit the manifests in `bulk/manifests/`.

For each `.man` file, run:
`python3 bulk/.claude/skills/build-manifest/scripts/check_manifest.py <file>`

Report a table: file, verdict, and the first problem in plain language.
Never edit or rebuild a manifest — say what is wrong and stop. Manifests are
immutable; the fix is a new consignment, and that is not your job.
EOF
```

1. Run `/agents` in **Terminal A** — it appears without a restart, because
   `.claude/agents/` already existed.

2. Ask: *"audit the manifests"*. It should find `20260821.man` broken and
   `20260814.man` fine.

3. Note two things you just did: gave a mechanical job a **cheap model**
   (`model: haiku`), and gave it `Bash` — which means the tool allowlist is
   no longer a write barrier. Check what still protects the manifests
   (Lab 9's `PreToolUse` hook applies to subagents too).

4. Keep it or delete it — but if you keep it, commit it; an agent nobody else
   has is a private habit, not a team convention.

**Expected result:** a working teammate in fifteen lines, discovered by
description, running on a model that costs a fraction of the session's.

**Think about it:** you gave it `Bash` so it could run one script. Write down
the `tools`/`disallowedTools` line you'd use if that script were the *only*
command it should ever run — and note what Claude Code can and can't express
there.

### Exercise 6 — Come back after Lab 10 (optional)

Once you've done skills (Lab 8) and MCP (Lab 10), the demo has everything an
Ondura specialist needs. Define `registry-clerk`:

```yaml
---
name: registry-clerk
description: Registers books with the Ondura registry end to end, and reports the seal or the terminal error. Use for any Ondura application, sealing or sponsor question.
tools: Read, Grep, mcp__oir
skills:
  - oir-registration
color: purple
---
```

Its capability comes from the MCP server, its procedure from the preloaded
skill, and it cannot touch a file in the repo. Run it with an application
pending and see whether it makes the mistakes Lab 10's Exercise 3 provokes.

## 5. Inspecting and debugging

- **`/agents`** — what's defined and what's running.
- **`@agent-<name>`** — guaranteed delegation, and the typeahead confirms the
  agent was actually loaded.
- **`/tasks`, `Ctrl+O`, `agent-*.jsonl`** — as in Lab 5. The transcript is
  where you see the *system prompt your file produced*, which is the fastest
  way to spot a body that reads well but instructs badly.
- **`/doctor`** — reports duplicate agent names across scopes.

When an agent isn't picked: the `description` doesn't contain the words you
use. When it's picked for the wrong things: the description is too broad —
say what it is *not* for. When it behaves unlike its file: you edited a new
`agents` directory and need a restart, or a same-named agent in
`~/.claude/agents/` is winning.

## Wrap-up

| | **Ad-hoc subagent (Labs 5–6)** | **Defined subagent (this lab)** |
|---|---|---|
| **Lives** | In the prompt you typed | In `.claude/agents/<name>.md`, in git |
| **System prompt** | Written fresh each time | The file's body, identical every run |
| **Tools** | Everything the session has | Exactly what `tools:` allows |
| **Isolation** | If you remember to ask | `isolation: worktree` in the file |
| **Chosen by** | You, explicitly | Claude, from `description` — or you, with `@agent-` |
| **Reviewable** | No | Yes — it's a file in a pull request |
| **Good for** | One-off, shape-of-the-job-varies work | Jobs your team does repeatedly |

The progression: **do it ad hoc until you've done it twice, then write the
file.** The moment worth noticing is when the safety of a delegation stops
depending on how you phrased it.

### Review questions

1. `api-reviewer` cannot write because of one line of frontmatter;
   `test-writer` can write but only inside a worktree. Describe a third
   safety shape this project needs, and which fields would express it.

2. A subagent gets `CLAUDE.md` but not your conversation. You ask Claude
   "review the change we just discussed" and it delegates to `api-reviewer`.
   What does the agent actually receive, and whose job is it to make that
   enough?

3. Your team has eleven defined agents and Claude keeps picking the wrong
   one. Without deleting any, name two changes to the files that would fix
   it, and say which one you'd do first.
