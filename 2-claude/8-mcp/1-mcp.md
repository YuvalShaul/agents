# Lab: MCP — Giving Claude Tools Instead of Instructions

**Time:** 45–60 minutes
**Prerequisites:** [Lab 8](../6-skills/1-skills.md) and [Lab 9](../7-hooks/1-hooks.md)
completed, and three terminals:

- **Terminal A** — running `claude`, started inside `2-claude/demo/`
- **Terminal B** — a plain shell in the same directory
- **Terminal C** — the registry:
  `python3 .claude/skills/oir-registration/scripts/oir_mock.py`

Start the registry in **Terminal C** now and leave it running — this lab is
about talking to it.

## 1. The scenario

You have reached the Ondura registry three ways already:

- **Lab 8** gave Claude a **skill** — the procedure — and a CLI to run.
- **Lab 9** added **hooks** — enforcement around the parts that must not go
  wrong.
- Under both, the actual mechanism was the same: Claude wrote a shell
  command, Claude Code ran it, and Claude read text back.

That works, and it cost nothing until it was used. But look at what Claude is
doing: constructing `python3 .../oir_cli.py apply --title "..." --sponsor ...`
as a *string*, then parsing JSON out of stdout. Nothing tells it which
arguments exist. Nothing validates `year` before the call. A typo in a flag
name is discovered by failing.

**MCP** — the Model Context Protocol — is the other shape. A server exposes
*typed tools*: names, descriptions, and JSON schemas for their arguments.
Claude Code lists them alongside its built-in tools, and Claude calls them
the same way it calls `Read` or `Bash` — no shell, no string building, no
output parsing.

`demo/mcp/oir_mcp_server.py` is that server for the registry you already
know. It is 150 lines of standard library, and the whole protocol is JSON-RPC
messages over stdin and stdout.

## 2. What MCP actually is

A client/server protocol. **Claude Code is the client.** A **server** is any
process that speaks it, and offers some mix of:

| Server offers | Claude Code surfaces it as |
|---|---|
| **Tools** | Callable tools, named `mcp__<server>__<tool>` |
| **Resources** | Content you can `@`-mention into the conversation |
| **Prompts** | Slash commands |

Servers reach Claude Code over one of four transports: `stdio` (a local
child process — what this lab uses), `http`, `sse`, and `ws` (remote
services, usually authenticated).

The exchange is small enough to read. In **Terminal B**, speak the protocol
by hand — this is exactly what Claude Code does at startup:

```bash
printf '%s\n' \
 '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"you","version":"0"}}}' \
 '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
 '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"verify_seal","arguments":{"seal":"OIR-HR-1965-M"}}}' \
 | python3 mcp/oir_mcp_server.py
```

Three messages: *who I am*, *what have you got*, *run this one*. Everything
else in MCP is detail on top of that.

> **The one gotcha worth knowing up front:** stdout is the protocol channel.
> A stray `print()` in a stdio server corrupts the stream and the server
> "mysteriously fails to connect". Log to stderr.

## 3. Configuring servers

Three scopes, and the choice is about *who gets the server*:

| Scope | Stored in | Shared with the team | Use for |
|---|---|---|---|
| `local` (default) | `~/.claude.json` | No | Your own experiments in this project |
| `project` | `.mcp.json` in the repo | **Yes, via git** | Servers the project needs |
| `user` | `~/.claude.json` | No | Servers you want everywhere |

The demo uses project scope, so the server travels with the repo —
[`demo/.mcp.json`](../demo/.mcp.json):

```json
{
  "mcpServers": {
    "oir": {
      "type": "stdio",
      "command": "python3",
      "args": ["mcp/oir_mcp_server.py"],
      "env": {
        "OIR_URL": "${OIR_URL:-http://127.0.0.1:8787}"
      }
    }
  }
}
```

`${VAR}` and `${VAR:-default}` expand in `command`, `args`, `env`, `url` and
`headers` — which is how a committed `.mcp.json` can point at a service
whose token lives only in your environment.

You can also add servers from the CLI instead of editing the file:

```bash
claude mcp add --transport stdio oir -- python3 mcp/oir_mcp_server.py
claude mcp add --transport http some-service --scope user https://mcp.example.com/mcp
claude mcp list          # status of every configured server
claude mcp get oir       # scope, transport, command, status
claude mcp remove oir -s project
```

**Approval.** A server in a committed `.mcp.json` is code the repository asks
to run on your machine, so Claude Code will not start it until you approve
it in an interactive session. Until then `claude mcp list` shows
`⏸ Pending approval`. That prompt is the security model — read what you're
approving, exactly as with hooks.

## 4. Exercises

### Exercise 1 — Approve it and look at what arrived

**Goal:** connect the server and see its tools in the session.

1. In **Terminal B**, before approving:

   ```bash
   claude mcp list
   ```

   `oir` is listed as `⏸ Pending approval`.

2. Start `claude` in **Terminal A**, inside `demo/`. Approve the project
   server when asked.

3. Run `/mcp`. You should see `oir` connected, with its tool count. Then ask:

   > What oir tools do you have, and what arguments does the apply tool take?

   Claude can answer *precisely* — the schema is in front of it, including
   `year` having a minimum of 1450.

4. Run `/context` and find the **MCP tools** row. Note the number, and note
   how it compares to the **Skills** row. Skills cost only their descriptions
   until invoked; MCP tools cost their schemas for the whole session — though
   depending on your version and settings, schemas may be *deferred* and
   fetched on demand, which `/context` will tell you.

**Expected result:** seven tools, with argument schemas, available from the
first message of the session without anyone invoking anything.

**Think about it:** the skill's `description` is one line; each MCP tool
carries a name, a description and a JSON schema. Which of those two costs
scale with how much your integration can do, and which with how often you
use it?

### Exercise 2 — The same job, without the shell

**Goal:** watch a task you already know run through tools instead of commands.

1. With the registry up in **Terminal C**, ask in **Terminal A**:

   > Register *Persuasion* by Jane Austen, 1817, with the registry, and tell me the seal.

2. Watch the tool calls. Instead of `Bash(python3 … oir_cli.py apply …)` you
   should see `mcp__oir__verify_seal`, `mcp__oir__apply`, `mcp__oir__attest`,
   `mcp__oir__tick`, `mcp__oir__request_seal` — structured calls with named
   arguments.

3. Note which calls stopped to ask permission. `demo/.claude/settings.json`
   pre-approves the read-only three:

   ```json
   "mcp__oir__health", "mcp__oir__verify_seal", "mcp__oir__list_applications"
   ```

   Everything that changes registry state still prompts. This is the same
   permission system as `Bash(pytest*)`, applied to MCP tool names.

4. Compare with your Lab 8 transcript for the identical task.

**Expected result:** the same seal, reached with no shell command, no output
parsing, and a permission boundary drawn along "reads vs writes" rather than
along a command string.

**Think about it:** in Lab 8 the equivalent guard would have been a
`Bash(python3 *oir_cli.py verify*)` permission rule. Why is
`mcp__oir__verify_seal` a more honest thing to grant?

### Exercise 3 — Tools are capability, not procedure

**Goal:** the point of this lab. Find out what MCP does *not* give you.

1. In **Terminal B**, hide the skill that carries the procedure:

   ```bash
   mv .claude/skills/oir-registration .claude/skills/oir-registration-off
   ```

2. In **Terminal A**, `/clear` (the skill list refreshes live), then ask:

   > Register *Northanger Abbey* by Jane Austen, 1817, using the oir tools. Get it sealed.

3. Watch carefully. Claude has every tool it needs and good descriptions —
   and the failure modes are the interesting part. Look for: sponsoring with
   a seal by the *same* author; ticking while the application is still
   `pending` and lapsing it; treating `425 TOO_EARLY` as an error to route
   around rather than a countdown; giving up and reporting the seal it
   "expects".

4. Restore the skill and repeat the same request in a fresh session:

   ```bash
   mv .claude/skills/oir-registration-off .claude/skills/oir-registration
   ```

**Expected result:** with tools alone Claude usually gets there, but not
reliably, and its mistakes are the ones the *procedure* prevents — order,
timing and which errors are terminal. With the skill back, the same tools
are driven correctly.

**Think about it:** you can push some of this into tool descriptions (the
demo's already warn about ticking). Where does that stop working, and why is
a 60-line procedure a bad fit for a field that is loaded into every session?

### Exercise 4 — Pay for it, then stop paying for it

**Goal:** measure the cost of a connected server.

1. In **Terminal A**, `/context`. Record the **MCP tools** row.

2. Quit, and restart with the project config ignored:

   ```bash
   claude --strict-mcp-config
   ```

   Run `/context` again and compare. Ask Claude to check the registry — it
   falls back to the CLI, and can still do it, because the *skill* is still
   there.

3. Turn the server off for the project instead, in
   `.claude/settings.local.json` (personal, not committed):

   ```json
   {"disabledMcpjsonServers": ["oir"]}
   ```

   Start a normal session and confirm with `/mcp`, then delete the file.

**Expected result:** the tools' cost is real, constant, and paid by every
session in the project — including the ones that never touch the registry.
For scale: in one session I measured, 37 MCP tools from three servers cost
~15.6k tokens, while 18 skills cost ~2.9k, because skills only ship their
descriptions.

**Think about it:** a server with 60 tools is a common thing to install.
What does that do to a project where most sessions are about something else,
and what would you do about it?

### Exercise 5 — Add a tool

**Goal:** extend the server and watch the new tool appear.

1. In **Terminal B**, add a tool that answers a question the current set
   makes Claude compute by hand — "is it safe to tick?". Add to the `TOOLS`
   list in `mcp/oir_mcp_server.py`:

```python
    {
        "name": "tick_safety",
        "description": "Whether ticking the registry clock is currently safe. "
                       "Returns the pending applications that a tick would lapse.",
        "inputSchema": {"type": "object", "properties": {}},
    },
```

   and to `ROUTES`:

```python
    "tick_safety": lambda a: ("GET", "/v1/applications", None),
```

2. Test it without Claude, the way you'd debug any server:

   ```bash
   printf '%s\n' \
    '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{}}}' \
    '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"tick_safety","arguments":{}}}' \
    | python3 mcp/oir_mcp_server.py
   ```

3. Restart the session in **Terminal A** — a stdio server is a child process,
   so its tool list is read at startup — and run `/mcp` to see eight tools.
   Ask: *"is it safe to tick right now?"*

4. Notice what you just did: the answer to "is it safe" is a *rule*
   (`registry-status` in Lab 8 states it), and you have now encoded a piece
   of it in a tool that returns raw applications. Decide whether that was an
   improvement, and revert if it wasn't: `git checkout mcp/oir_mcp_server.py`.

**Expected result:** a new tool in three lines, and a real design question
about where the judgment should live.

**Think about it:** the honest version of `tick_safety` would return
`{"safe": false, "would_lapse": [...]}` — the server making the judgment.
What do you gain by moving that decision out of the model, and what do you
lose when the rule changes?

## 5. Choosing between the three

Same registry, three mechanisms, and they are not alternatives so much as
layers:

| | **Skill** | **MCP server** | **Hook** |
|---|---|---|---|
| **Gives Claude** | Knowledge and procedure | Capability — typed tools, live data | A constraint it cannot escape |
| **Costs** | A description always; the body when used | Tool schemas for the whole session, plus a process | A subprocess per matching event |
| **Fails by** | Being ignored | Being called wrongly, or being down | Blocking something legitimate |
| **Best at** | *How* and *when* | *Access* — remote, authenticated, structured | *Never* |
| **Wrong for** | Anything that must hold | Anything requiring judgment about order | Anything subjective |

The rule of thumb this project demonstrates:

- **MCP** when Claude needs to *reach* something — a live service, an
  authenticated API, a database — with typed arguments and structured errors.
- **A skill** for the procedure that drives it, because tool descriptions are
  a terrible place for a six-step protocol with timing rules.
- **A hook** for the one or two invariants that must hold even when the model
  is wrong.

And a fourth option people forget: a CLI plus a skill, as in Lab 8. If the
thing is local, unauthenticated and cheap to shell out to, that combination
costs nothing when idle and needs no server. MCP earns its constant cost when
the integration is remote, authenticated, or used in most sessions.

## 6. Inspecting and debugging

- **`/mcp`** — connected servers, tool counts, auth status, reconnect.
- **`claude mcp list` / `claude mcp get <name>`** — status and scope from the
  shell, without a session.
- **Speak to the server directly** (section 2). A stdio server is a program;
  debug it as one.
- **`claude --debug`** — the startup handshake and every failure with reason.
- **`/context`** — what the tools cost you.
- **`--strict-mcp-config`** — run ignoring `.mcp.json`, to bisect "is it the
  server?"

Failure modes in the order you'll meet them: `⏸ Pending approval` (you never
approved it); a `print()` to stdout corrupting the stream; a relative path in
`args` resolving against a different working directory; a server that starts
but exposes nothing because `tools/list` returned the wrong shape; a remote
server needing OAuth (`/mcp` shows *needs authentication*).

## Wrap-up

| | **Lab 8 (skill + CLI)** | **This lab (MCP)** |
|---|---|---|
| **How Claude calls it** | Writes a shell command | Calls a typed tool |
| **Arguments** | A string it composed | Schema-checked fields |
| **Errors** | Text on stdout it must parse | Structured, with `isError` |
| **Cost when unused** | Nothing | Tool schemas, every session |
| **Needs** | The CLI on disk | A running server process |
| **Permissions** | `Bash(...)` patterns | `mcp__oir__<tool>` |
| **Carries the procedure** | Yes | No |

### Review questions

1. Exercise 3 removed the skill and kept the tools. Describe the failure you
   saw in terms of the distinction between *capability* and *procedure*, and
   name a system at your work where the same split applies.

2. The demo's `.mcp.json` is committed, so approving it runs repository-
   supplied code on your machine. Compare that risk with the hooks from Lab
   8: which is worse, and what would you require before approving either in a
   repo you don't control?

3. You are asked to expose an internal service to Claude Code for a team of
   twenty. Give the two-question test you'd use to decide between shipping an
   MCP server and shipping a CLI plus a skill — and say which way you'd go if
   the service is used in one session out of fifty.
