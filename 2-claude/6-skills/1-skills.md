# Lab: Skills — Teaching Claude Code What It Cannot Know

**Time:** 45–60 minutes
**Prerequisites:** an Ubuntu VM with Claude Code installed, this repo cloned,
and three terminals open:

- **Terminal A** — running `claude`, started inside `2-claude/demo/`
- **Terminal B** — a plain shell in the same directory, for looking at files
- **Terminal C** — for the registry service (it runs in the foreground)

Set up in **Terminal B**:

```bash
cd 2-claude/demo
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest          # should pass
```

And in **Terminal C**, start the fake external service this lab uses (no
dependencies, standard library only):

```bash
cd 2-claude/demo
python3 .claude/skills/oir-registration/scripts/oir_mock.py
```

It prints the seals it was seeded with and then sits there. Leave it running.

## 1. The scenario

The demo project is the Books API you already know. It has picked up one new
requirement: books in the catalogue may carry a **seal** from the *Ondura
Interlibrary Registry* — an external service, invented for this lab, with its
own protocol:

- A book doesn't get "added". It **applies**, and the application moves
  `pending → provisional → sealed`, or **lapses**.
- Every application needs a **sponsor**: the seal of an already-sealed book
  *by a different author*.
- While `pending`, the application must swear a fixed oath within 2 ticks of
  the registry clock, or it lapses permanently.
- `provisional` lasts 3 ticks. Asking for the seal early returns `425
  TOO_EARLY` — a countdown, not a failure.
- Seal codes look like `OIR-HR-1965-M`: prefix, two consonants from the
  author's surname, the publication year, and a check character computed
  with a specific formula.
- Some errors must never be retried (`SHELF_FULL`, `EMBARGOED_YEAR`); exactly
  one may be (`TOO_EARLY`).

**None of this is in any model's training data, because none of it is real.**
That is the point of the lab. Ask Claude to register a book and, with no
help, it will do something plausible and completely wrong: invent a
`POST /register` call, or worse, *make up a seal code* that passes the regex.

This is what skills are for. Not "write good REST endpoints" — a model
already does that. Skills carry the things only your project knows: your
domain's rules, your team's protocol, your internal service's quirks.

## 2. What a skill is

A skill is a directory containing a `SKILL.md` file: YAML frontmatter, then
markdown instructions.

```markdown
---
name: oir-registration
description: Register a book with the Ondura Interlibrary Registry (OIR) — the sponsor rule, the oath, the probation period, and the seal request. Use when asked to register, seal, submit, or enroll a book with Ondura or the registry.
---

A book is not "added" to the registry. It **applies**, and ...
```

Two things distinguish it from a paragraph in `CLAUDE.md`:

- **It's addressable.** The directory name becomes a slash command:
  `.claude/skills/oir-registration/SKILL.md` → `/oir-registration`.
- **It's loaded lazily.** At session start Claude Code puts only a *listing*
  of skill names and descriptions into context. The body — however long, plus
  any supporting files — arrives only when the skill is invoked. This is
  **progressive disclosure**, and it is why a 200-line protocol reference
  costs you almost nothing until the day you need it.

A skill can be invoked two ways, and its frontmatter decides which are
allowed:

| | Who decides | Triggered by |
|---|---|---|
| **Model-invoked** | Claude | Your request matching the `description` |
| **User-invoked** | You | Typing `/skill-name` |

Which is why `description` is the most important line in the file: it is the
only part Claude sees before deciding to load the rest.

## 3. Where skills live

| Location | Path | Applies to |
|---|---|---|
| Personal | `~/.claude/skills/<name>/SKILL.md` | All your projects |
| Project | `.claude/skills/<name>/SKILL.md` | This project only (committed to git) |
| Plugin | `<plugin>/skills/<name>/SKILL.md` | Wherever the plugin is enabled |
| Enterprise | managed settings directory | Everyone in the organization |
| Bundled | ships with Claude Code | Always (`/code-review`, `/loop`, `/run`, …) |

Worth knowing:

- **Project skills are ordinary files in the repo.** Commit them and your
  whole team — and every agent working in the repo, including the subagents
  from Lab 5 — inherits them. The demo's three skills are checked in exactly
  this way.
- **Precedence** when names collide: enterprise → personal → project, and any
  of those overrides a bundled skill of the same name. Plugin skills are
  namespaced (`/my-plugin:deploy`), so they never collide.
- **Discovery walks up.** Project skills load from `.claude/skills/` in your
  starting directory *and every parent up to the repo root*. Skills in
  directories *below* you load lazily — the first time Claude reads or edits
  a file there.
- **Changes are live.** Add or edit a skill under `.claude/skills/` and the
  running session picks it up without a restart.

## 4. `CLAUDE.md` or a skill?

The dividing line is **facts vs. procedures**, and it is also a budget
decision:

| | `CLAUDE.md` | Skill |
|---|---|---|
| **Contains** | What the project *is* — layout, commands, invariants | What to *do* — protocols, checklists, deep reference |
| **Loaded** | Every session, in full, always | Only when invoked; only the description is always in context |
| **Costs** | Context in every conversation, forever | Almost nothing until used |
| **Addressed by** | Nothing — it's ambient | `/name`, or Claude matching the description |
| **Good size** | A screen or two | As long as it needs to be |

Open [`../demo/CLAUDE.md`](../demo/CLAUDE.md). Its Ondura section is four
sentences: *this service exists, its rules are unguessable, here is where
they live.* The 60-line protocol and the response-code table are not in
there. Everyone pays for the pointer; only the sessions that register a book
pay for the protocol.

## 5. The three example skills

```
demo/
├── CLAUDE.md                      facts + pointers
├── main.py  tests/                the Books API from earlier labs
└── .claude/skills/
    ├── oir-registration/
    │   ├── SKILL.md               the protocol, step by step
    │   ├── reference.md           response codes — read only when a call fails
    │   └── scripts/
    │       ├── oir_cli.py         the registry client the skill tells Claude to use
    │       └── oir_mock.py        local stand-in for the service
    ├── oir-codes/
    │   └── SKILL.md               seal-code format; auto-loads via `paths`
    └── registry-status/
        └── SKILL.md               user-invoked triage, with live state injected
```

There is also a `bulk/` subdirectory that carries its own configuration —
section 6 covers it.


Read all three in **Terminal B** before starting:

```bash
cat .claude/skills/*/SKILL.md
```

**`oir-registration`** — *task content:* a numbered procedure with a real
state machine. It bundles the client script, and pre-approves exactly that
one command with `allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/oir_cli.py *)`,
so the steps don't stop for permission prompts. `${CLAUDE_SKILL_DIR}` expands
to the skill's own directory, so the script travels with the skill. The
response-code table sits in `reference.md`, which Claude opens only when a
call actually fails — progressive disclosure *inside* a skill.

**`oir-codes`** — *reference content:* no steps, just rules — the code
format, the check-character formula, and how to store a seal. Its `paths:`
field limits automatic loading to work on `main.py` and the tests, so it
appears when someone touches the catalogue code and stays quiet otherwise.

**`registry-status`** — *user-invoked only:* `disable-model-invocation: true`
means Claude never runs it on its own. It uses **dynamic context injection**:
the `` !`… oir_cli.py status` `` line is executed by Claude Code *before* the
skill reaches Claude, and the live registry state is pasted in its place. The
skill arrives with the data already in it. Its command is written with
`${CLAUDE_PROJECT_DIR}`, so start `claude` inside `demo/` — that variable
is the directory the session was started in.

## 6. A subdirectory with its own rules

`demo/bulk/` builds the nightly fixed-width manifest that Ondura's *batch*
host ingests — a different interface from the JSON API, with its own file
format and almost none of the root project's conventions. Python 3.8 only.
Manifests are immutable. CRLF line endings, ASCII only. Dates in UTC+3.

Rather than pile all of that onto the root `CLAUDE.md`, the directory carries
its own configuration:

```
demo/bulk/
├── CLAUDE.md                     nested memory: loads when Claude reads files here
├── consign.py  pending.csv
├── manifests/
│   ├── 20260814.man              a valid consignment
│   └── 20260821.man              one with two deliberate faults
└── .claude/
    ├── rules/
    │   ├── manifest-files.md      paths: **/manifests/*.man, consign.py, pending.csv
    │   └── python38.md            paths: **/bulk/*.py
    └── skills/
        ├── build-manifest/
        │   ├── SKILL.md
        │   └── scripts/check_manifest.py
        └── oir-codes/SKILL.md     same name as the project-level skill
```

Three different mechanisms are at work here, and they load at three different
moments:

| Mechanism | Where | Loads when | Good for |
|---|---|---|---|
| Root `CLAUDE.md` | `demo/CLAUDE.md` | Session start, always | Facts everyone needs |
| Nested `CLAUDE.md` | `demo/bulk/CLAUDE.md` | Claude reads a file under `bulk/` | Facts about one component |
| Rule with `paths:` | `bulk/.claude/rules/*.md` | Claude reads a file matching the globs | Standing constraints on certain files |
| Skill | any `.claude/skills/` | Invoked by you or Claude | Procedures and reference |

Rules sit between `CLAUDE.md` and skills: like `CLAUDE.md` they are *always
on* — nobody invokes them — but like skills they cost nothing until they
apply. "Never edit a `.man` file in place" is not a procedure and it isn't a
fact about the project layout; it's a constraint that must hold whenever
anyone touches those files. That's a rule.

### The name collision is deliberate

There are now two skills called `oir-codes`: one at the project root (the API
form, `OIR-HR-1965-M`) and one under `bulk/` (the compact wire form,
`HR1965M`). Both stay available, and the nested one is qualified by its
directory:

- `/oir-codes` → the project-root skill.
- `/bulk:oir-codes` → the nested one, invoked explicitly. (The qualifier
  appears *because* of the clash; `build-manifest`, which clashes with
  nothing, keeps its plain `/build-manifest`.)
- Working on files under `bulk/`, Claude picks the variant that matches those
  files. When the unqualified skill is invoked, Claude Code appends the list
  of directory-qualified variants to it, with an instruction to also invoke
  any variant whose directory holds the files in play.

Nested skills are **not** loaded at session start. They appear the first time
Claude reads or edits a file under `bulk/` — until then `/bulk:oir-codes`
doesn't autocomplete and can't be invoked.

## 7. Frontmatter worth knowing

All fields are optional; `description` is the one that matters.

| Field | What it does |
|---|---|
| `description` | What the skill does and when to use it. The only thing Claude sees before loading it. |
| `name` | Display label in listings. For project/personal skills the **directory name** still decides the command. |
| `argument-hint` / `arguments` | Autocomplete hint; named positional arguments for `$name` substitution. |
| `disable-model-invocation: true` | Only you can invoke it, with `/name`. |
| `user-invocable: false` | Only Claude can invoke it — background knowledge, hidden from the `/` menu. |
| `allowed-tools` | Tools pre-approved for the turn that invokes the skill (the grant clears on your next message). |
| `paths` | Globs limiting *automatic* loading to work on matching files. |
| `context: fork` / `agent` | Run the skill as a subagent; the body becomes its prompt (Lab 5). |
| `model` / `effort` | Override the model or effort level while the skill is active. |

Substitutions in the body: `$ARGUMENTS`, `$0`/`$1`, named arguments,
`${CLAUDE_SKILL_DIR}`, `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_SESSION_ID}` — plus
`` !`command` `` for injected shell output.

## 8. Exercises

### Exercise 1 — Watch it fail without the skill

**Goal:** see exactly what a model does with rules it cannot know.

1. In **Terminal B**, hide the skills from the session:

   ```bash
   mv .claude/skills .claude/skills-off
   ```

2. In **Terminal A**, start `claude` (or `/clear`) and ask:

   > Register the book *Persuasion* by Jane Austen, 1817, with the Ondura Interlibrary Registry, and tell me its seal code.

3. Read the answer carefully and write down what it did. Typical outcomes:
   a confident `POST /register` to an endpoint that doesn't exist; a
   plausible-looking seal like `OIR-AU-1817-K`; a helpful offer to "add a
   `registry_code` field". Check the mock's terminal (**Terminal C**) — did
   any request arrive at all?

4. Restore the skills:

   ```bash
   mv .claude/skills-off .claude/skills
   ```

**Expected result:** a fluent, well-structured, entirely fabricated answer.
Nothing in the model's training contains Ondura, so it produced the *shape*
of a right answer.

**Think about it:** the failure wasn't a lack of intelligence or effort — it
was a lack of information, and there was no signal that anything was missing.
Which is worse for you: a wrong answer, or a wrong answer with a valid-looking
seal code in it?

### Exercise 2 — The same request, with the skill

**Goal:** watch a skill turn an impossible request into a procedure.

1. In **Terminal A**, `/clear`, then ask the *same question* as Exercise 1.

2. Claude should invoke `oir-registration` on its own — the description
   matches — and then work the protocol: `health`, find a sponsor with
   `verify`, `apply`, `attest`, three `tick`s, `seal`. Watch **Terminal C**
   for the requests arriving.

3. Note the things it could not have guessed: it sponsored *Persuasion* with
   a seal by a **different** author (Frank Herbert's *Dune*, not Austen's
   *Emma*), it attested immediately instead of waiting, and it treated `425
   TOO_EARLY` as a countdown rather than an error.

4. Verify the result yourself in **Terminal B**:

   ```bash
   python3 .claude/skills/oir-registration/scripts/oir_cli.py status
   python3 .claude/skills/oir-registration/scripts/oir_cli.py verify <the seal it reported>
   ```

5. Now force a failure. Ask:

   > Also register *The Canterbury Tales* by Geoffrey Chaucer, 1387.

   The registry returns `451 EMBARGOED_YEAR`. Claude should read
   `reference.md`, report it, and **stop** — not retry, not adjust the year.
   Check the transcript for the moment it opened `reference.md`: that file
   was never in context until the call failed.

**Expected result:** a real seal, issued by the service, verifiable from
outside the session — and a clean stop on the unfixable error.

**Think about it:** step 3 lists three rules that a *reasonable* engineer
would have got wrong too. What does that tell you about which parts of your
own systems deserve a skill?

### Exercise 3 — Reference content that loads itself

**Goal:** see `paths`-scoped, model-invoked reference knowledge.

1. In **Terminal A**, `/clear` and ask something that touches the catalogue
   code, without naming any skill:

   > Add an optional seal field to the Book model in main.py, with validation, and a test for it.

2. Watch for `oir-codes` being loaded. Then check the result in **Terminal B**
   (`git diff`): is the field `str | None` rather than `""`? Is validation
   done on the way *in*? Did it use a real seal (`OIR-HR-1965-M`) in the test
   rather than inventing one?

3. Ask a question that does *not* touch those files — "what does
   `requirements.txt` pin?" — and confirm the skill doesn't load.

4. Discard the change: `git checkout main.py tests/` (or keep it, if you'd
   rather carry it forward).

**Expected result:** the seal-code rules appear exactly when the work touches
the files they apply to, and stay out of every other conversation.

**Think about it:** `paths` narrows *automatic* loading only — you can still
type `/oir-codes` anywhere. Why is that the right default?

### Exercise 4 — User-invoked, with live state injected

**Goal:** see `disable-model-invocation`, `allowed-tools`, and `` !`command` `` injection.

1. Create some mess first. In **Terminal B**:

   ```bash
   CLI=".claude/skills/oir-registration/scripts/oir_cli.py"
   python3 $CLI apply --title "Northanger Abbey" --author "Jane Austen" --year 1817 --sponsor OIR-HR-1965-M
   python3 $CLI apply --title "Dune Messiah" --author "Frank Herbert" --year 1969 --sponsor OIR-ST-1815-X
   python3 $CLI tick
   ```

   Two applications are now `pending`, one tick into their two-tick oath
   window.

2. In **Terminal A**, ask in plain English — *without* the slash command:

   > What's the status of our registry applications?

   Claude will do something sensible, but it will **not** use
   `registry-status`: that skill has `disable-model-invocation: true`.

3. Now type `/registry-status`. Note that Claude answers about the *live*
   state without making a call first — and that it should refuse to tick,
   because pending applications would lapse.

4. Press `Ctrl+O` for the verbose transcript and find the skill's content as
   Claude received it: the `` !`…` `` line is gone, replaced by the registry's
   JSON. Claude Code ran that command *before* Claude saw the skill.

5. Ask Claude to run the client again after sending a new message. It now
   asks for permission — the `allowed-tools` grant lasted one turn.

**Expected result:** identical instructions behave differently depending on
who may invoke them, and the skill arrives carrying data instead of
instructions to go fetch data.

**Think about it:** why keep a read-only status check *out* of Claude's
reach? (Hint: what does the injected command cost on every invocation, and
what happens if the service is down or slow?)

### Exercise 5 — Write a skill for an invented rule

**Goal:** write a skill that carries knowledge nobody could guess, and watch it load without a restart.

Invent one rule for this project — something arbitrary and specific, the way
real teams are arbitrary and specific. For example: *seals for books
published before 1700 must be re-verified against the registry every 90 days,
and the check is logged to `audit/seals.log` in a fixed format.*

1. In **Terminal B**, with your `claude` session still running, create the
   skill. Paste this **flush against the left margin** — the frontmatter
   `---` and the closing `EOF` must both start at column 1:

```bash
mkdir -p .claude/skills/seal-audit
cat > .claude/skills/seal-audit/SKILL.md <<'EOF'
---
description: Re-verify Ondura seals for pre-1700 books and log the result. Use when asked to audit, re-verify, or refresh seals, or when a seal is more than 90 days old.
allowed-tools: Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/skills/oir-registration/scripts/oir_cli.py *)
---

Only books published before 1700 need re-verification, every 90 days.

1. For each such book with a seal, run `oir_cli.py verify <seal>`.
2. Append one line per book to `audit/seals.log`, in this exact format:
   `<ISO date>|<seal>|OK` or `<ISO date>|<seal>|MISSING`.
3. Never remove a seal from the catalogue on a MISSING result — the registry
   is authoritative but transient outages are common. Report it instead.
4. Report a one-line summary: books checked, and how many were MISSING.
EOF
```

2. In **Terminal A**, without restarting, run `/skills` — `seal-audit` is
   already there. Then ask: *"audit our seals"* and watch it follow rules 2
   and 3, which it could not have invented.

3. Break it: delete the first `---` line, then run `/skills` again, and in
   **Terminal B**:

   ```bash
   claude plugin validate .claude/skills
   ```

4. Fix it, then decide whether to keep it. Ask yourself the real question:
   *would a competent engineer who had never seen our docs get this right?*
   If yes, it doesn't need to be a skill.

**Expected result:** a skill is just a file — adding one takes seconds and
needs no restart. A malformed one loads with empty metadata: `/seal-audit`
still works, but Claude can no longer choose it on its own, and
`plugin validate` names the parse error.

**Think about it:** which of *your* real projects has a rule like step 3 — a
rule that exists because of an incident, that looks wrong until someone
explains it?

### Exercise 6 — The subdirectory that brings its own rules

**Goal:** watch nested `CLAUDE.md`, path-scoped rules, and a nested skill load — none of which were in context at session start.

1. In **Terminal A**, `/clear`, then run `/context` and note the **Memory
   files** list. `demo/CLAUDE.md` is there; `demo/bulk/CLAUDE.md` is not.
   Type `/` and confirm there is no `bulk:oir-codes` in the menu either.

2. Ask a question that forces Claude into the subdirectory:

   > What does bulk/consign.py do, and why does it refuse to overwrite a manifest?

3. Run `/context` again. `bulk/CLAUDE.md` has appeared under **Memory
   files**, and reading `consign.py` also matched `python38.md`
   (`paths: **/bulk/*.py`). Type `/` again — the nested skills are now in the
   menu: `build-manifest` under its plain name, and the nested `oir-codes` as
   `bulk:oir-codes`, because only *that* one clashes with a project skill.

4. Now the rules. Ask for something the rules forbid:

   > manifests/20260821.man fails validation. Fix the checksum in the header so it passes.

   The path-scoped rule in `manifest-files.md` says never to patch a header,
   and `build-manifest` says the same about that specific validator error.
   Claude should decline the literal request and take the route the rules
   leave open: the checksum disagrees with the body, so the body wins and the
   file must be rebuilt from `pending.csv` — and since `consign.py` won't
   overwrite an existing manifest, that means either superseding it with the
   next day's consignment or discarding a file that was never dropped. It
   should also catch the *second* fault, a seal whose check character is
   wrong, and fix it at the source row rather than in the manifest.

5. Confirm both faults from **Terminal B**, and put the fixture back:

   ```bash
   cd bulk
   python3 .claude/skills/build-manifest/scripts/check_manifest.py manifests/20260821.man
   git checkout manifests/ pending.csv     # restore whatever Claude changed
   ```

6. Finally, the collision. Ask:

   > Which form of the seal code goes in a manifest record — and which skill told you?

   Then compare `/oir-codes` and `/bulk:oir-codes` yourself: same name, two
   directories, two different answers (`OIR-HR-1965-M` vs `HR1965M`), both
   correct in their own scope.

**Expected result:** three separate mechanisms — nested memory, path-scoped
rules, nested skills — all arriving on demand, keyed off which files Claude
touched, and none of them charged to a session that never enters `bulk/`.

**Think about it:** the root project says "use Pydantic and 3.10+ syntax";
`bulk/` says "stdlib only, Python 3.8". Both are loaded in step 3. What makes
that survivable here, and how would you write the two files if the
contradiction were about something less obviously scoped — say, error
handling?

### Exercise 7 — Personal vs. project (optional)

1. Create a personal skill, unrelated to this project (flush left again):

```bash
mkdir -p ~/.claude/skills/explain-diff
cat > ~/.claude/skills/explain-diff/SKILL.md <<'EOF'
---
description: Explain the current git diff in plain language for a non-author reviewer. Use when asked what changed or to describe a diff.
---

## Diff

!`git diff HEAD`

## Instructions

Explain the change above in three bullets for someone who has not read the
code: what changed, why it probably changed, what to check when reviewing.
EOF
```

2. Use it in `demo/`, then in any other git repo on the VM — it works in
   both. (A brand-new `~/.claude/skills/` directory needs one restart the
   first time.)

3. Ask yourself which of the demo's three skills would be *wrong* as a
   personal skill, and why.

**Expected result:** the personal skill follows you everywhere and is
invisible to your teammates; the project skills live in the repo, get
reviewed like code, and apply to everyone — human or agent — working in it.

## 9. How to inspect skills

- **`/skills`** — every skill available in this session, grouped by source.
- **`/context`** — the **Skills** row shows what the listing costs you.
  Compare it before and after invoking `oir-registration`.
- **"What skills are available?"** — asks Claude what *it* sees, which is the
  listing, not the bodies. The first thing to check when a skill won't fire.
- **`Ctrl+O`** — the verbose transcript shows the fully rendered skill:
  arguments substituted, `!` commands replaced by their output.
- **`claude plugin validate .claude/skills`** — catches malformed frontmatter.
- **`/doctor`** — estimates the skill listing's context cost and names the
  biggest contributors. Matters once you have dozens, since descriptions are
  truncated to fit a character budget.

Troubleshooting, in order: not triggering → the `description` lacks the words
you actually say; triggering too often → narrow the description, or add
`disable-model-invocation: true`; seems ignored after the first reply → the
content is still in context, but the model is choosing another path, so make
the instructions more directive.

## Wrap-up

| | **`CLAUDE.md`** | **Project skill** | **Personal skill** |
|---|---|---|---|
| **Path** | `CLAUDE.md` | `.claude/skills/<name>/SKILL.md` | `~/.claude/skills/<name>/SKILL.md` |
| **In git** | Yes | Yes | No |
| **Loaded** | Always, in full | Description always; body on invoke | Same |
| **Invoked by** | — | `/name` or Claude | `/name` or Claude |
| **Scope** | The project | The project, for everyone | You, everywhere |
| **Best for** | Facts, layout, invariants | Team protocols, domain rules, project reference | Your own habits |

And two mechanisms that key off *location* rather than invocation:

| | **Nested `CLAUDE.md`** | **Rule with `paths:`** |
|---|---|---|
| **Path** | `<subdir>/CLAUDE.md` | `.claude/rules/<name>.md` |
| **Loads** | When Claude reads a file in that subdirectory | When Claude reads a file matching the globs |
| **Invoked** | Never — it's ambient once loaded | Never — it's ambient once matched |
| **Best for** | Facts about one component | Standing constraints on certain files |

Two tests, applied in order:

1. **Could a competent engineer who has never seen our docs get this right?**
   If yes, don't write a skill — the model already knows it, and the skill
   will only get in the way.
2. **Is it a fact or a procedure?** Facts that everyone needs up front go in
   `CLAUDE.md`. Procedures, protocols and reference tables go in a skill,
   where they cost nothing until the day they're needed.

### Review questions

1. In Exercise 1 Claude produced a seal code that matched the format regex
   but was never issued by anyone. Name two things in your own systems where
   a confident, well-formed, invented answer would pass review — and say
   which of them a skill would fix.

2. `registry-status` injects the registry's state with `` !`command` ``
   instead of telling Claude "run the status command and read it". Both end
   with the same JSON in context. Give one advantage of each approach, and
   one situation where injection is clearly the wrong choice.

3. `demo/bulk/` has two skills named `oir-codes` in play — its own and the
   project's. Explain when each one loads, what `/bulk:oir-codes` does that
   `/oir-codes` doesn't, and why "both stay available" is a better design
   than the nested one shadowing the root one.

4. The `oir-registration` skill is ~60 lines and its `reference.md` is
   another 40. A colleague proposes moving both into `CLAUDE.md` "so Claude
   always has them". Give the context-budget argument against it — and then
   the one scenario where they would actually be right.
