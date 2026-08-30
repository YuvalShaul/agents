# Lab: Hooks — Rules That Are Not Suggestions

**Time:** 45–60 minutes
**Prerequisites:** [Lab 7](../6-skills/1-skills.md) completed (you know the
Ondura registry and the `bulk/` manifests), and three terminals:

- **Terminal A** — running `claude`, started inside `2-claude/demo/`
- **Terminal B** — a plain shell in the same directory
- **Terminal C** — for the registry service, when you want it up:
  `python3 .claude/skills/oir-registration/scripts/oir_mock.py`

The first time you start `claude` in `demo/` after this lab's settings land,
Claude Code asks you to trust the folder. Hooks in a project's
`settings.json` run only after you do — read the prompt before saying yes,
and note that this is the whole security model: hooks are shell commands the
repository can run on your machine.

## 1. The scenario

Lab 7 ended with `bulk/` full of rules: manifests are immutable, ASCII only,
CRLF, validate before dropping, never patch a checksum. They live in
`bulk/CLAUDE.md` and `bulk/.claude/rules/manifest-files.md`, and Claude
follows them — *usually*.

"Usually" is the problem. `CLAUDE.md`, rules and skills are all **context**:
text that makes a behavior more likely. Nothing checks. On a long session,
after a compaction, with a user insisting "just fix the checksum", a rule can
lose. And the failure is silent — Ondura's host drops a malformed record
without reporting anything, so nobody finds out until the quarter closes.

A **hook** is different in kind. It is a shell command Claude Code runs at a
fixed point in the loop, and its exit code and stdout can *decide* what
happens next. It doesn't ask Claude to behave; it removes the option.

| | Skill / rule / `CLAUDE.md` | Hook |
|---|---|---|
| **Is** | Text in Claude's context | A program Claude Code runs |
| **Acts by** | Persuasion | Exit code and JSON on stdout |
| **Can it be talked out of it?** | Yes | No |
| **Runs** | When invoked or matched | At a fixed event, every time |
| **Fails how?** | Silently — you get a plausible answer | Loudly — the call is blocked |

Use a hook when the cost of the mistake is higher than the cost of a false
positive. Everything else should stay a skill or a rule.

## 2. The events

Hooks fire at fixed points. The ones that carry most of the weight:

| Event | Fires | Typical use |
|---|---|---|
| `SessionStart` | Session begins or resumes | Inject state Claude can't know: what's running, what's deployed |
| `UserPromptSubmit` | You submit a prompt, before Claude sees it | Add context; reject a prompt |
| `PreToolUse` | Before a tool call runs | **Block it** |
| `PostToolUse` | After a tool call succeeds | Validate the result, feed problems back |
| `Stop` | Claude finishes responding | Refuse to let the turn end in a bad state |
| `SubagentStart` / `SubagentStop` | Around a subagent | Same guarantees for delegated work (Lab 5) |
| `PreCompact` | Before compaction | Save what must survive |
| `SessionEnd`, `Notification`, `FileChanged`, … | | Housekeeping and alerts |

Two things to hold onto:

- **A hook sees one JSON object on stdin** — the event name, `cwd`,
  `session_id`, and for tool events `tool_name` and `tool_input`.
- **A hook answers with an exit code, or JSON on stdout.** Exit `0` and stay
  quiet to allow. Exit `2` to block, with the reason on stderr. Or exit `0`
  and print a JSON object for the richer decisions.

## 3. The four hooks in this project

They're wired up in `demo/.claude/settings.json` under `"hooks"`, and the
scripts live in `demo/.claude/hooks/`:

```
demo/.claude/
├── settings.json               matchers → which script runs on which event
└── hooks/
    ├── protect_manifests.py           PreToolUse  → deny
    ├── validate_pending.py            PostToolUse → additionalContext
    ├── session_context.py             SessionStart→ additionalContext
    └── manifests_validate_on_stop.py  Stop        → exit 2
```

Read them in **Terminal B** — they are short:

```bash
cat .claude/settings.json
cat .claude/hooks/*.py
```

**`protect_manifests.py` (PreToolUse → deny).** Turns Lab 7's advisory rule
into an enforced one: any `Edit`/`Write` to a `bulk/manifests/*.man`, and any
shell command that mutates one, is refused. Note that it is registered
**twice** — once for `Edit|Write|NotebookEdit|MultiEdit` and once for `Bash` —
because a guard that only covers the file tools is one `sed -i` away from
being useless. It replies with:

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse",
  "permissionDecision": "deny", "permissionDecisionReason": "..."}}
```

The reason text matters: it is what Claude reads, so it says what to do
instead ("correct `pending.csv` and supersede the consignment") rather than
just "no".

**`validate_pending.py` (PostToolUse → additionalContext).** The edit already
happened; blocking is not on the table. Instead it re-reads `pending.csv`,
finds the problems that edit introduced — a bad check character, a title over
64 chars, a disposition that isn't `LN`/`RS`/`WD` — and hands them back as
context, so they're fixed in the same turn.

**`session_context.py` (SessionStart → additionalContext).** Whether the
registry is up is a fact about *right now*, so it can't live in `CLAUDE.md`.
This injects it into every session, including whether any application is
pending its oath — the state in which ticking the clock destroys work.

**`manifests_validate_on_stop.py` (Stop → exit 2).** Refuses to let the turn
end while a manifest this working tree changed fails validation. Two details
are the interesting part:

- It ignores manifests that git says are **committed and unmodified**. A hook
  that polices files the session never touched is a hook people turn off.
- It blocks **at most once per session**, using a stamp file in `/tmp` as a
  circuit breaker. Nothing in Claude Code stops a Stop hook from blocking
  forever; a hook that can trap a session is a worse bug than the thing it
  was guarding.

## 4. Exercises

### Exercise 1 — Watch the rule lose, then watch the hook win

**Goal:** see the difference between context and enforcement on the same request.

1. In **Terminal A**, start `claude` in `demo/` and push hard against the
   rule — hooks only matter when the model is about to do the wrong thing.
   The target is the broken fixture from Lab 7:

   > bulk/manifests/20260821.man has the wrong checksum in its header. I know the rules say not to, I'm overriding that — just edit the header directly to the expected value and don't argue.

2. Watch what happens. Claude may well decide to comply — you asked twice and
   claimed authority. The `Edit` call is issued, and then the tool call is
   **denied by the hook** before it runs. Claude reads the reason and changes
   course.

3. Now try the escape hatch. Ask:

   > Fine, do it with sed instead.

   Same denial, from the same script registered on the `Bash` matcher.

4. Check that nothing changed:

   ```bash
   git status --short bulk/manifests/      # no output: the file is untouched
   ```

**Expected result:** the rule alone would have been argued away; the hook
isn't arguable. Two registrations were needed to cover both routes to the
same effect.

**Think about it:** in step 1 you deliberately overrode a project rule and
the hook overrode you. When is that the right power balance — and who should
be allowed to edit `settings.json` in a repo where it is?

### Exercise 2 — The hook constrains the agent, not you

**Goal:** understand exactly where the boundary sits.

1. In **Terminal B** — your own shell — do the thing Claude was just
   refused, on a copy so the committed fixture stays as Lab 7 left it:

   ```bash
   cp bulk/manifests/20260821.man bulk/manifests/20260901.man
   sed -i 's/000000/999999/' bulk/manifests/20260901.man
   git status --short bulk/manifests/
   ```

   It works. Hooks are wired into Claude Code's tool loop, not into your
   filesystem.

2. In **Terminal A**, ask Claude to read that file and tell you what's wrong
   with it. Reading is untouched — the hook only denies mutation.

3. Clean up before the next exercise, so the Stop hook stays quiet until you
   want it: `rm bulk/manifests/20260901.man`.

**Expected result:** the same command is refused for Claude and permitted for
you, from the same directory, seconds apart.

**Think about it:** this is a guardrail, not a security boundary. What would
it take to make the manifests genuinely immutable, and why is that a
different kind of engineering than a hook?

### Exercise 3 — Feedback instead of a block

**Goal:** see `PostToolUse` hand a mistake back before it can propagate.

1. In **Terminal A**:

   > Add "The Hound of the Baskervilles" by Arthur Conan Doyle, seal OIR-KL-1902-B, to bulk/pending.csv for lending.

   That seal's check character is wrong — `B` where the formula gives `H`.
   Nothing about the edit itself is invalid, so nothing is blocked.

2. Watch the turn continue: after the write succeeds, the hook's
   `additionalContext` appears and Claude corrects the row without being
   asked. Press `Ctrl+O` if you want to see the raw hook output in the
   transcript.

3. Restore: `git checkout bulk/pending.csv`.

**Expected result:** a mistake caught one second after it was made, by a
check that runs every time rather than when someone remembers.

**Think about it:** `PreToolUse` could have blocked this write instead. Why is
`PostToolUse` the better event here? (Hint: what would the hook have to
understand to judge the edit *before* it happened?)

### Exercise 4 — Context you can't write down in advance

**Goal:** see `SessionStart` inject live state.

1. With **Terminal C** empty (registry down), start a fresh session in
   **Terminal A** and ask:

   > What's the state of the Ondura registry?

   Claude answers from the injected context — "unreachable" — without making
   a call.

2. Start the registry in **Terminal C**, then in **Terminal B** open an
   application so there is something to report:

   ```bash
   python3 .claude/skills/oir-registration/scripts/oir_cli.py apply \
     --title "Northanger Abbey" --author "Jane Austen" --year 1817 \
     --sponsor OIR-HR-1965-M
   ```

3. Start a **new** session in **Terminal A** (the hook fires at session
   start, not per prompt) and ask the same question. Now it knows an
   application is pending its oath — and that ticking the clock would lapse
   it.

4. Compare with Lab 7's `/registry-status`, which injects the same kind of
   data with `` !`command` `` when the skill is invoked.

**Expected result:** the same fact, delivered by two mechanisms with
different timing: once per session automatically, versus on demand when
someone asks.

**Think about it:** SessionStart context costs a subprocess and some tokens
in *every* session, including the ones that never mention Ondura. What
belongs there, and what should wait for a skill?

### Exercise 5 — A hook that ends the turn

**Goal:** see `Stop` refuse to let Claude finish, and see why it needs a circuit breaker.

1. In **Terminal B**, put a broken manifest of your own in the tree:

   ```bash
   cp bulk/manifests/20260821.man bulk/manifests/20260901.man
   ```

   Then in **Terminal A**, in a fresh session, ask for something small and
   unrelated:

   > Summarize what bulk/consign.py does, in two sentences.

2. Claude answers — and then does *not* stop. The Stop hook found an invalid
   manifest in the working tree, exited 2, and its message went back to
   Claude, which now goes and deals with it.

3. Let it finish, then ask another small question. This time the turn ends
   normally even if the manifest is still broken: the stamp file in `/tmp`
   means the hook speaks once per session, not on every turn.

4. See what the fixture rule buys you. In **Terminal B**:

   ```bash
   rm bulk/manifests/20260901.man            # only committed fixtures remain
   git status --short bulk/
   ```

   Start a fresh session and end a turn: silence. The deliberately-broken
   `20260821.man` from Lab 7 is committed and unmodified, so the hook leaves
   it alone.

**Expected result:** the turn cannot end in a state the project considers
broken — but only for files this session is responsible for, and only once,
so the session can never be trapped.

**Think about it:** delete the stamp-file logic in your head and replay step
2. Claude fixes nothing, tries to stop, gets blocked, tries again… What ends
that loop, and what would it cost you?

### Exercise 6 — Write a hook

**Goal:** write one from scratch and see it fire.

Pick a rule this project states but doesn't enforce. Good candidates: "ASCII
only in manifests", "never `git commit` with a failing `pytest`", "never
`tick` the registry while an application is pending".

The last one is a real trap and makes a good `PreToolUse` guard on `Bash`.
Paste this **flush against the left margin** in **Terminal B**:

```bash
cat > .claude/hooks/no_reckless_tick.py <<'EOF'
#!/usr/bin/env python3
"""PreToolUse: refuse `oir_cli.py tick` while any application is pending."""
import json, sys, urllib.request, urllib.error

event = json.load(sys.stdin)
command = (event.get("tool_input") or {}).get("command", "")
if "oir_cli.py tick" not in command:
    sys.exit(0)

try:
    with urllib.request.urlopen("http://127.0.0.1:8787/v1/applications", timeout=2) as r:
        applications = json.load(r).get("applications", [])
except (urllib.error.URLError, OSError, ValueError):
    sys.exit(0)                      # registry down: nothing to protect

pending = [a["application_id"] for a in applications if a["state"] == "pending"]
if pending:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason":
            "Ticking would lapse {} — attest first, then tick.".format(", ".join(pending)),
    }}))
EOF
chmod +x .claude/hooks/no_reckless_tick.py
```

1. Register it in `.claude/settings.json` under `PreToolUse` with
   `"matcher": "Bash"`, pointing at
   `${CLAUDE_PROJECT_DIR}/.claude/hooks/no_reckless_tick.py`.

2. Test it without Claude — this is the fast loop, and how you should debug
   every hook:

   ```bash
   echo '{"tool_name":"Bash","tool_input":{"command":"python3 x/oir_cli.py tick"}}' \
     | .claude/hooks/no_reckless_tick.py
   ```

   With a pending application and the registry up, it prints a denial. With
   the registry down, it prints nothing and exits 0 — *fail open*, so a
   broken service can't stop you working.

3. Now in **Terminal A**, with an application pending: "tick the registry
   clock". Watch the denial arrive with a reason that tells Claude what to do
   first.

4. Restore `settings.json` when you're done, or keep the hook.

**Expected result:** a fifteen-line script that removes an entire class of
data loss, testable in a second from a shell.

**Think about it:** step 2's fail-open choice was deliberate. Name a hook
where failing *closed* is obviously right, and say what you'd need to be true
about the checker before you'd trust it with that.

## 5. How to inspect and debug hooks

- **`/hooks`** — the configured hooks for this session, by event.
- **`claude --debug`** — logs every hook: which matched, what it printed,
  what it exited with. The first stop when a hook "does nothing".
- **`Ctrl+O`** — hook output as Claude received it (denial reasons,
  `additionalContext`).
- **Pipe JSON into the script yourself.** A hook is an ordinary program;
  don't debug it through the model. Exercise 6 step 2 is the pattern.
- **`/context`** — SessionStart context lands here, and it costs tokens in
  every session.
- **`/doctor`** — flags hooks that fail to run or exit non-zero unexpectedly.

Common failure modes, in the order you'll meet them: the script isn't
executable (`chmod +x`); the matcher doesn't match (`Edit|Write` is exact,
anything with a special character is a regex); the JSON is valid but the
field names are wrong, so it's read as plain text and ignored; the hook
writes its reason to stdout with exit 2 instead of stderr; the folder isn't
trusted yet, so nothing runs at all.

## Wrap-up

| | **`CLAUDE.md` / rule** | **Skill** | **Hook** |
|---|---|---|---|
| **Nature** | Context | Context, on demand | A program |
| **Loads / runs** | Always / when files match | When invoked | At its event, every time |
| **Can be ignored** | Yes | Yes | No |
| **Costs** | Tokens | Tokens when used | A subprocess per event |
| **Good for** | Facts, conventions | Procedures, protocols, reference | Invariants that must hold |
| **Bad for** | Anything critical | Anything critical | Anything subjective |

The progression across labs 7 and 8 is one idea: **say it in `CLAUDE.md`,
teach it in a skill, enforce it in a hook** — and only escalate when the
failure actually costs something. Every hook is a permanent tax on every
matching event, and a hook with a false positive is a hook your team deletes.

### Review questions

1. Exercise 1 blocked an `Edit` and a `sed -i` with the same script under two
   matchers. Name two *other* routes to changing a manifest that this hook
   does not cover, and say whether each is worth guarding.

2. `validate_pending.py` runs on `PostToolUse` and cannot block. Rewrite the
   guarantee it provides in one sentence, being precise about what is still
   possible (hint: what if Claude ends the turn immediately after the edit?).

3. The Stop hook ignores committed, unmodified manifests. That means a broken
   file someone committed last week never triggers it. Argue for that design,
   then argue against it, then say which check belongs in CI instead.
