---
name: registry-status
description: Triage every open Ondura application — what state each one is in and what it needs next.
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PROJECT_DIR}/.claude/skills/oir-registration/scripts/oir_cli.py *)
---

# Open applications

!`python3 ${CLAUDE_PROJECT_DIR}/.claude/skills/oir-registration/scripts/oir_cli.py status`

## Instructions

The registry's reply is above — don't fetch it again. For each application,
report the state and the single next action:

| State | Next action |
|---|---|
| `pending`, `ticks_in_state` 0–1 | Attest **now**: `oir_cli.py attest <id>` |
| `pending`, `ticks_in_state` 2 | Attest this turn — one more tick and it lapses |
| `provisional`, fewer than 3 ticks | Wait. Report the ticks remaining; do not tick |
| `provisional`, 3+ ticks | `oir_cli.py seal <id>` |
| `lapsed` | Terminal. A fresh application is the only route; say so |
| `sealed` | Nothing. Report the seal |

Then answer the one question that decides everything else: **is it safe to
tick?** It is safe only when no application is `pending`. Ticking advances
every open application at once, so a tick to release one book's probation
can lapse another book's oath window. If any application is `pending`, say
so explicitly and attest those first.

If the block above shows a connection error, the registry isn't running.
Report that and stop — don't guess at the state of any application.
